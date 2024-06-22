import logging
import math
import re
from typing import List, Optional

from pydantic import BaseModel

from devon_agent.utils import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)
DATA_LOGGER_NAME = "udiff_data"
data_logger = logging.getLogger(DATA_LOGGER_NAME)


def log_successful_diff(diff, file_content, src_file, tgt_file):
    data_logger.info(f"<SUCCESS>")
    data_logger.info(f"<DIFF>")
    data_logger.info(f"{diff}")
    data_logger.info(f"</DIFF>")
    data_logger.info(f"<FILECONTENT>")
    data_logger.info(f"{file_content}")
    data_logger.info(f"</FILECONTENT>")
    data_logger.info(f"<SRCFILE>")
    data_logger.info(f"{src_file}")
    data_logger.info(f"</SRCFILE>")
    data_logger.info(f"<TGTFILE>")
    data_logger.info(f"{tgt_file}")
    data_logger.info(f"</TGTFILE>")
    data_logger.info(f"</SUCCESS>")


def log_failed_diff(diff, file_content, src_file, tgt_file):
    data_logger.info(f"<FAIL>")
    data_logger.info(f"<DIFF>")
    data_logger.info(f"{diff}")
    data_logger.info(f"</DIFF>")
    data_logger.info(f"<FILECONTENT>")
    data_logger.info(f"{file_content}")
    data_logger.info(f"</FILECONTENT>")
    data_logger.info(f"<SRC FILE>")
    data_logger.info(f"{src_file}")
    data_logger.info(f"</SRCFILE>")
    data_logger.info(f"<TGTFILE>")
    data_logger.info(f"{tgt_file}")
    data_logger.info(f"</TGTFILE>")
    data_logger.info(f"</FAIL>")


class Hallucination(Exception):
    pass


class HunkLine(BaseModel):
    type: str  # "added", "removed", or "unchanged"
    content: str


class Hunk(BaseModel):
    src_start: int
    src_lines: int
    tgt_start: int
    tgt_lines: int
    lines: List[HunkLine]


class ContextHunk(BaseModel):
    lines: List[HunkLine]
    start_lines: Optional[List[HunkLine]] = None
    end_lines: Optional[List[HunkLine]] = None


class FileContextDiff(BaseModel):
    src_file: str
    tgt_file: str
    hunks: List[ContextHunk]


class MultiFileContextDiff(BaseModel):
    files: List[FileContextDiff]


def create_recover_prompt(src_lines, original_diff, diff, errors):
    error_block_content = [e[1].args for e in errors]

    return f"""
<SOURCE_FILE>
{src_lines}
</SOURCE_FILE>
<ORIGINAL_DIFF>
{original_diff}
</ORIGINAL_DIFF>
<NEWEST_DIFF>
{diff}
</NEWEST_DIFF>
<ERRORS>
Here are the resulting errors from applying the newest diff:
    {error_block_content}
</ERRORS>

Please answer the following questions thinking step by step:

What are the exact section content lines from the src_file that the ORIGINAL_DIFF targets?
Copy, and paste this section with additional context lines EXACTLY with an additional 3 context lines on either side.

The ORIGINAL_DIFF may source code lines that have typos! These are ok to change! I inaccurately wrote the diff anyways.

Was enough context added to the original diff to make it work?
Do all source lines actually exist in the ORIGINAL_DIFF?

Are the NEWEST_DIFF lines target the lines you copied above? If not, how can you fix this?
Was enough context added to the newest diff to make it work?
Do all source lines actually exist in the NEWEST_DIFF?

Please point out all the lines that are added lines but not marked as added.
Please point out all the source lines that were accidentally marked as added.

Does the new diff only create a hunk for the content/source lines the original diff targets?

Once those questions are answered, please provide the improved diff according to the guidelines. If you get it right, I'll buy you Taylor Swift tickets.
"""


def extract_diff_from_response(diff_text):
    if "```diff" in diff_text:
        return [
            diff.split("```")[0].strip()
            for diff in diff_text.split("```diff")[1:]
            if "```" in diff
        ]

    if "<DIFF>" in diff_text:
        return [
            diff.replace("<DIFF>", "").strip()
            for diff in diff_text.split("</DIFF>")[:-1]
            if "<DIFF>" in diff
        ]

    return [
        diff.replace("<<<", "").strip()
        for diff in diff_text.split(">>>")[:-1]
        if "<<<" in diff
    ]


def strip_new_lines_from_ends(lines):
    content_lines_start = 0
    while content_lines_start < len(lines) and lines[content_lines_start] == "":
        content_lines_start += 1

    content_lines_end = 0
    while (
        content_lines_end < len(lines)
        and list(reversed(lines[content_lines_start])) == ""
    ):
        content_lines_start += 1

    return lines[content_lines_start : len(lines) - content_lines_end]


def construct_versions_from_diff_hunk(hunk: ContextHunk):
    old_lines = []
    new_lines = []

    for line in hunk.lines:
        if line.type == "removed":
            old_lines.append(line.content)
        elif line.type == "added":
            new_lines.append(line.content)
        else:
            old_lines.append(line.content)
            new_lines.append(line.content)

    return old_lines, new_lines


def find_nth_content_line(lines, n):
    start = 0
    for i, line in enumerate(lines):
        if line != "":
            start = i
            break

    count = 0
    end = start
    while end < len(lines) and count < n:
        if lines[end] != "":
            count += 1

        end += 1

    return lines[start:end]  # maybe off by one? dont think so though, need to test


def create_code_fence(old_lines, fence_len=3):
    if len(old_lines) < 4:
        start_fence = find_nth_content_line(old_lines, len(old_lines))
        end_fence = start_fence
    else:
        start_fence = find_nth_content_line(old_lines, fence_len)
        end_fence = list(
            reversed(find_nth_content_line(list(reversed(old_lines)), fence_len))
        )

    return start_fence, end_fence


def levenshtein_distance(s1, s2):
    m, n = len(s1), len(s2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i - 1] == s2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = min(dp[i][j - 1], dp[i - 1][j], dp[i - 1][j - 1]) + 1

    return dp[m][n]


def is_fuzzy_match(s1, s2, threshold=1):
    for a, b in zip(s1, s2):
        distance = levenshtein_distance(a, b)
        if distance > threshold:
            return False
    return True


def match_fence(lines, fence, start_index=0):
    subset_length = len(fence)

    if subset_length > 0:
        for i in range(start_index, len(lines) - subset_length + 1):
            match = [line[1] for line in lines[i : i + subset_length]]

            if is_fuzzy_match(match, fence, 1):
                return lines[i][0], lines[i + subset_length - 1][0], i

    return None, None, None


def match_fence_all(stripped_file_lines, fence):
    matches = []
    src_idx = 0
    while src_idx < len(stripped_file_lines):
        start, end, src_idx = match_fence(stripped_file_lines, fence, src_idx)
        if src_idx is not None:
            matches.append((start, end, src_idx))
            src_idx += 1
        else:
            break

    return matches


def strip_comment_from_line(line):
    comment_index = line.find("#")

    # If '#' is found, return the line up to that index (stripped of leading/trailing whitespace)
    if comment_index != -1:
        return line[:comment_index].strip()

    # If '#' is not found, return the original line (stripped of leading/trailing whitespace)
    return line.strip()


def match_stripped_lines_context_with_fence_len(
    stripped_file_lines, stripped_old_lines, old_lines, fence_len
):
    # create code fence based on lines. i.e. first N content lines

    # Match single line changes
    if len(stripped_old_lines) == 1:
        begin_fence = stripped_old_lines
        stop_fence = stripped_old_lines
        begin_matches = match_fence_all(stripped_file_lines, begin_fence)

        # If we allowed a single line match, but the match is not unique, bail
        if len(stripped_old_lines) == 1 and len(begin_matches) > 1:
            raise Hallucination(not_enough_context_prompt)
        elif len(begin_matches) == 1:
            return (
                [list(begin_matches[0][:2]) + list(begin_matches[0][:2])],
                begin_matches,
                begin_matches,
            )
        else:
            raise Hallucination(incorrect_context_prompt)

    else:
        begin_fence, stop_fence = create_code_fence(
            old_lines=stripped_old_lines, fence_len=fence_len
        )

    # Match N content lines. This means that the first N content lines will be matched on and the last N content lines will be matched on.
    begin_matches = match_fence_all(stripped_file_lines, begin_fence)
    end_matches = match_fence_all(stripped_file_lines, stop_fence)

    # for each begin match, find first end match
    valid_pairs = []
    for begin_start, begin_end, src_idx in begin_matches:
        for stop_start, stop_end, end_idx in end_matches:
            # TODO: add a line count error here

            if src_idx <= end_idx and (end_idx - src_idx + fence_len) == len(
                stripped_old_lines
            ):
                valid_pairs.append((begin_start, stop_end, stop_start, begin_end))
                break

    return valid_pairs, begin_matches, end_matches


def match_stripped_lines_context(stripped_file_lines, old_lines):
    # given stripped file lines and stripped old lines,
    stripped_old_lines = [line.strip() for line in old_lines]
    stripped_old_lines = [line for line in stripped_old_lines if line != ""]

    fence_len = 3
    results = []
    while not results and fence_len > 1:
        results, b, e = match_stripped_lines_context_with_fence_len(
            [
                (i, line)
                for i, line in [(i, line.strip()) for i, line in stripped_file_lines]
                if line != ""
            ],
            [
                line
                for line in [line.strip() for line in stripped_old_lines]
                if line != ""
            ],
            old_lines,
            fence_len=fence_len,
        )

        if len(results) > 0:
            break

        results, b, e = match_stripped_lines_context_with_fence_len(
            [
                (i, line)
                for i, line in [
                    (i, strip_comment_from_line(line))
                    for i, line in stripped_file_lines
                ]
                if line != ""
            ],
            [
                line
                for line in [
                    strip_comment_from_line(line) for line in stripped_old_lines
                ]
                if line != ""
            ],
            old_lines,
            fence_len=fence_len,
        )

        if len(results) > 0:
            break

        fence_len -= 1

    # if none throw error
    if not results:
        if b and len(b) == 1:
            return b[0][0], None, None, None
        elif e and len(e) == 1:
            return None, e[0][1], None, None

        return None, None, None, None

    return results[0]


def parse_multi_file_diffs(diff: str) -> List[FileContextDiff]:
    file_diffs: List[FileContextDiff] = []
    lines = diff.strip().split("\n")

    changed_lines = 0

    i = 0
    while i < len(lines):
        if lines[i].startswith("---"):
            src_file = re.findall(r"--- (.*)", lines[i])[0]
            tgt_file = re.findall(r"\+\+\+ (.*)", lines[i + 1])[0]
            hunks = []
            i += 2

            while i < len(lines) and not lines[i].startswith("---"):
                if lines[i].startswith("@@"):
                    hunk_lines = []
                    # match = re.findall(r"@@ .* @@(.*)", lines[i])[1]
                    i += 1

                    # if match != "":
                    #     hunk_lines.append(match)

                    while (
                        i < len(lines)
                        and not lines[i].startswith("@@")
                        and not lines[i].startswith("---")
                    ):
                        # content = lines[i][1:]
                        content = lines[i][:]

                        if lines[i].startswith("-"):
                            hunk_lines.append(
                                HunkLine(type="removed", content=content[1:])
                            )
                            changed_lines += 1
                        elif lines[i].startswith("+"):
                            hunk_lines.append(
                                HunkLine(type="added", content=content[1:])
                            )
                            changed_lines += 1
                        else:
                            hunk_lines.append(
                                HunkLine(type="unchanged", content=content)
                            )

                        i += 1

                    start_lines = []
                    for line in hunk_lines:
                        if line.type != "unchanged":
                            break

                        start_lines.append(line)

                    end_lines = []
                    for line in reversed(hunk_lines):
                        if line.type != "unchanged":
                            break

                        end_lines.append(line)

                    hunks.append(
                        ContextHunk(
                            start_lines=start_lines,
                            end_lines=end_lines,
                            lines=hunk_lines,
                        )
                    )
                else:
                    i += 1

            file_diffs.append(
                FileContextDiff(src_file=src_file, tgt_file=tgt_file, hunks=hunks)
            )
        else:
            i += 1

    return file_diffs, changed_lines


def get_indent(line, indent_size):
    if indent_size == 0:
        return 0
    base_indent = " " * indent_size
    if line.startswith(base_indent):
        # find multiple of base_indent present as prefix in line
        count = 0
        while line.startswith(base_indent):
            count += 1
            line = line[len(base_indent) :]
        return count
    else:
        return 0


def get_prefix_whitespace(line):
    count = 0
    while line.startswith(" "):
        count += 1
        line = line[1:]
    return count


def apply_indent_to_new_lines(src_lines, src_start, src_end, new_lines):
    base_indent_match = get_indent(src_lines[src_start][1])
    base_indent_hunk = get_indent(new_lines[0])
    indented_new_lines = new_lines

    if base_indent_match != base_indent_hunk:
        if base_indent_match > base_indent_hunk:
            indented_new_lines = [
                "    " * (base_indent_match - base_indent_hunk) + line
                for line in new_lines
            ]
        else:
            indented_new_lines = [
                line.replace("    " * (base_indent_hunk - base_indent_match), "")
                for line in new_lines
            ]

    return indented_new_lines


# single diff apply rules
# 4. Try to match on lines -> if no match -> try again with more context = retry loop
#     1. If match on lines doesn’t match the first 3 and last 3 bail
# 5. Generate indent error -> auto fix indentation after match

incorrect_context_prompt = """
IncorrectContextLines:
    It appears that the diff you provided could not be applied successfully because the deleted lines (starting with -) and the context lines did not match the content of the existing source file.

    To resolve this issue, please only include context lines that match the original source code exactly.

    To do this:
    - First copy and paste the exact source code lines you are trying to target.
    - Second, pay special attention to the differences, and then write the patch

    The user's patch tool requires at minimum the first two and last two source lines to match in order apply the patch.

    Keep in mind that even minor discrepancies between the context lines and the original code will prevent the diff from being applied correctly.
    To solve this, always makre sure you have the target lines open in the editor.
"""

not_enough_context_prompt = """
NotEnoughContextError:
    It appears that the diff you provided could not be applied successfully because the deleted lines (starting with -) and the context lines did not match the content of the existing source file.

    To resolve this issue, please generate additional context lines that match the original source code exactly.
    When selecting lines to include, carefully compare each line to the actual source file to ensure a perfect match. Aim to provide at least 3-4 lines of matching context before and after the section you want to modify.

    Keep in mind that even minor discrepancies between the context lines and the original code will prevent the diff from being applied correctly.
    In about half of these cases, the problem stems from context lines that don't precisely align with the source.

    To generate the additional lines needed:
    1. Locate the section of the source code where you want to make changes
    2. Carefully copy several lines immediately before and after the relevant section
    3. Double-check that each copied line is identical to the original source code
    4. Include these matching context lines in your diff, surrounding the lines you want to change
    5. By providing sufficient and accurate context, the diff tool will be able to pinpoint the correct location in the file and apply your changes seamlessly.
"""

unable_to_parse_old_or_new_lines = """
UnableToParseBlocksError:

    One of two issues has occurred:
        1. In the diff, the deleted lines (denoted with -), and the context lines (unchanged lines) do not exist
        2. In the diff, the added lines (denoted with +), and the context lines (unchanged lines) do not exist

    The provided deleted (-) and unchanged lines were built into code block A, and the added (+) and unchanged lines were built into code block B.
    One of the two blocks did not exist.

    Please pay more attention to the exact lines you are writing.
"""

no_diffs_found = """
NoDiffFoundError:
    No Diff was found in the response you provided. Please remember to follow the guidelines for creating diffs.
"""

non_applicable_diff_found = """
NonApplicableDiffFound:
    A diff missing either a source or target file was found.

    Without both a target and source file, the diff cannot be applied.
    Make sure to provide both a target and source file.

    Please remember to follow the guidelines for creating diffs.
"""

recover_failed_new_diff_too_different = """
ExcessiveChangedLinesInRecoveryAttempt:
    The new diff does not match the original diff. You've changed too many additional lines (x > 3) compared to the original diff.

    By not faithfully following the content of the original diff, you are changing how the code works.

    The solution to fix this error is changing fewer lines to adhere to the original diff better.
    Even though it may seem to you that you need to make additional changes, ask yourself if the new change actually exists in the source diff.
    Half of the time these additional diffs do not exist, and should not since they change the intended functionality.

    Think through which lines you need to change first, and then write the new diff.

    Please remember to follow the guidelines for creating diffs.
"""


def get_relative_indents(lines):
    assert isinstance(lines, list)
    assert all(isinstance(line, str) for line in lines)
    spaces = []
    for line in lines:
        space = get_prefix_whitespace(line)
        spaces.append(space)

    gcd = math.gcd(*spaces)

    if gcd != 0:
        spaces = [(space // gcd) for space in spaces]

    min_indent = min(spaces) if spaces else 0

    return [space - min_indent for space in spaces], gcd


def apply_indent(
    src_lines,
    new_lines,
    start_code_fence_start,
    start_code_fence_end,
    stop_code_fence_start,
    stop_code_fence_end,
):
    """
    STEPS
    1. Get indentation of matched src lines
    2. Get relative indents of diff lines
    3. Apply
    """
    # print("*" * 10)
    # print(start_code_fence_start)
    # print(start_code_fence_end)
    # print(stop_code_fence_start)
    # print(stop_code_fence_end)

    start_code_fence = src_lines[start_code_fence_start : start_code_fence_end + 1]
    stop_code_fence = src_lines[stop_code_fence_start : stop_code_fence_end + 1]

    relative_indents, indent_size = get_relative_indents(new_lines)

    # print(start_code_fence)
    # print(stop_code_fence)

    start_indents = [get_indent(line[1], indent_size) for line in start_code_fence]
    # stop_indents = [get_indent(line[1],indent_size) for line in stop_code_fence]
    # print(start_indents)
    # print(stop_indents)
    # print(new_lines)

    new_indents = [get_indent(line, indent_size) for line in new_lines]

    if not new_indents:
        return new_lines
    # print(new_indents)

    # print(relative_indents)
    base = start_indents[0] - new_indents[0]

    line_no_base = start_code_fence_start

    base = None
    print("before change")
    for i, line in enumerate(new_lines):
        current_line_no = line_no_base + i
        # print(current_line_no,start_code_fence_start,start_code_fence_end,current_line_no >= start_code_fence_start, current_line_no <= start_code_fence_end)
        if (
            current_line_no >= start_code_fence_start
            and current_line_no <= start_code_fence_end
        ):
            if src_lines[current_line_no][1].strip() == line.strip():
                # print(base,relative_indents[i],start_indents[i])
                if (
                    base
                    and base + relative_indents[i] != start_indents[i]
                    and src_lines[current_line_no][1].strip()
                ):
                    print(i)
                    print(relative_indents)
                    print(start_indents)
                    print(base, relative_indents[i], start_indents[i], indent_size)
                    raise Hallucination(
                        f"Indentation does not match for line {current_line_no-1}.Make sure you specify the exact indents to make an edit. Line: "
                        + src_lines[current_line_no - 1][1]
                    )
                base = start_indents[0] - relative_indents[0]
            # start fence processing
        elif (
            current_line_no >= stop_code_fence_start
            and current_line_no <= stop_code_fence_end
        ):
            if src_lines[current_line_no][1].strip() != line.strip():
                pass
            # stop fence processing
        if base is None:
            new_lines[i] = " " * indent_size * new_indents[i] + new_lines[i].strip()
            continue
        new_lines[i] = (
            " " * indent_size * (base + relative_indents[i]) + new_lines[i].strip()
        )
    print(new_lines)

    return new_lines


def apply_context_diff(file_content: str, file_diff: FileContextDiff) -> str:
    # create i, line pairs for diff apply
    src_lines = [(i, line) for i, line in enumerate(file_content.splitlines())]
    print(src_lines)
    # get stripped version of original file i.e. strip all lines then filter out empty lines
    stripped_src_lines = [
        t for t in [(i, line.strip()) for i, line in src_lines] if t[1] != ""
    ]
    # check if stripped_src_lines is empty and append file_diff hunks to it
    if not stripped_src_lines or all([line[1] == "" for line in stripped_src_lines]):
        old_lines, new_lines = construct_versions_from_diff_hunk(file_diff.hunks[0])
        print(new_lines)
        return "\n".join(new_lines), []

    tgt_lines = list(src_lines)

    errors = []

    for hunk in file_diff.hunks:
        try:
            old_lines, new_lines = construct_versions_from_diff_hunk(hunk)

            if not (old_lines is not None and new_lines is not None):
                # if either version is none, raise error
                raise Hallucination(unable_to_parse_old_or_new_lines)

            src_start, src_end, stop_start, begin_end = match_stripped_lines_context(
                stripped_src_lines, old_lines
            )

            new_lines = strip_new_lines_from_ends(new_lines)

            # print(src_start, src_end)

            if not (src_start is not None and src_end is not None):
                # Raise hallucination due to not matching full src lines -> this is actually a precision error not a context lines problem

                if src_start:
                    real_start = max(0, src_start - 10)
                    real_end = min(len(src_lines), src_start + 10)
                    real = "\n".join(
                        [line for _, line in src_lines[real_start:real_end]]
                    )
                    raise Hallucination(
                        "Incorrect source lines, the source lines you wrote were:\n"
                        + "\n".join(old_lines)
                        + "\nThe actual source lines are: \n"
                        + real
                    )
                elif src_end:
                    real_start = max(0, src_end - 10)
                    real_end = min(len(src_lines), src_end + 10)
                    real = "\n".join(
                        [line for _, line in src_lines[real_start:real_end]]
                    )
                    raise Hallucination(
                        "Incorrect source lines, the source lines you wrote were:\n"
                        + "\n".join(old_lines)
                        + "\nThe actual source lines are: \n"
                        + real
                    )

                raise Hallucination(incorrect_context_prompt)

            if src_end - src_start > len(old_lines) + 5:
                # Raise hallucination due to not matching full src lines -> this is actually a precision error not a context lines problem
                raise Hallucination(incorrect_context_prompt)

            # applied_code = apply_indent(
            #     src_lines, new_lines, src_start, begin_end, stop_start, src_end
            # )



            
            # applied_code = apply_indent_to_new_lines(src_lines, src_start, src_end, new_lines)
            applied_code = new_lines

            # insert lines
            i = 0
            while i < len(tgt_lines):
                if tgt_lines[i][0] == src_start:
                    j = 0
                    while i + j < len(tgt_lines) and tgt_lines[i + j][0] != src_end:
                        j += 1

                    tgt_lines[i : i + j + 1] = [(-1, line) for line in applied_code]
                    break

                i += 1
        except Hallucination as e:
            print(e)
            errors.append((hunk, e, file_content))

    # return correct code
    return "\n".join([entry[1] for entry in list(tgt_lines)]), errors


def extract_all_diffs(diff_input):
    if isinstance(diff_input, list):
        diff_input = "".join(diff_input)

    diff_code = diff_input

    # extract diff from response
    diffs = extract_diff_from_response(diff_code)

    if len(diffs) == 0:
        # Raise exception about length of diffs
        raise Hallucination(no_diffs_found)

    total_changed_lines = 0

    # for each diff, actually parse the changes from it. Assume this just works for parsing the diff hunks (not formatting or anything, but rather just extracting target lines)
    all_diffs = []
    for diff in diffs:
        file_diffs, changed_lines = parse_multi_file_diffs(diff)
        total_changed_lines += changed_lines
        all_diffs.extend(file_diffs)

    # changes = MultiFileContextDiff(files=all_diffs)

    # Check to see if there are diffs that have neither src or tgt file
    error_diffs = []
    for diff in all_diffs:
        if not (diff.src_file or diff.tgt_file):
            error_diffs += diff

    if len(error_diffs) != 0:
        # Raise exception containing non-applicable diffs
        raise Hallucination(non_applicable_diff_found)

    # deduping the diffs here
    return list(all_diffs), total_changed_lines


def apply_file_context_diffs(file_content, all_diffs):
    succeeded = []
    failed = []

    # for each diff block, apply context diff, returns tuple result (abspath, new_content)
    for diff in all_diffs:
        result, errors = apply_context_diff(file_content=file_content, file_diff=diff)
        if len(errors) == 0:
            succeeded.append((diff.tgt_file, result, file_content))
        else:
            failed.extend(errors)

    # should return files with new code to write
    return {"success": succeeded, "fail": failed}


def apply_multi_file_context_diff(file_content, diff, original_change_count):
    # By the time we get here we have correctly captured a single command

    failures = []

    try:
        all_diffs, total_new_changed = extract_all_diffs(diff)
        if original_change_count is not None and (
            total_new_changed > (original_change_count + 5)
            or total_new_changed < (original_change_count - 1)
        ):
            raise Hallucination(recover_failed_new_diff_too_different)
    except Hallucination as e:
        data_logger.error("<ERROR>")
        data_logger.error(e)
        data_logger.error("</ERROR>")
        failures.append((None, e))

    apply_res = apply_file_context_diffs(file_content=file_content, all_diffs=all_diffs)

    apply_res["fail"].extend(failures)

    return apply_res, total_new_changed
