import logging
import re
import traceback
from typing import List, Optional

from pydantic import BaseModel

from devon.swebenchenv.environment.utils import LOGGER_NAME
from devon_agent.agent.clients.client import Message

logger = logging.getLogger(LOGGER_NAME)

DATA_LOGGER_NAME = "udiff_data"

data_logger = logging.getLogger(DATA_LOGGER_NAME)

data_handler = logging.FileHandler('udiff_data.log')

data_logger.setLevel(logging.DEBUG)
data_logger.addHandler(data_handler)


def log_data(diff, file_content, src_file, tgt_file):
    data_logger.info(f"=======================")
    data_logger.info(f"DIFF: {diff}")
    data_logger.info(f"FILE CONTENT: {file_content}")
    data_logger.info(f"SRC FILE: {src_file}")
    data_logger.info(f"TGT FILE: {tgt_file}")
    data_logger.info(f"=======================")


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
        end_fence = list(reversed(find_nth_content_line(list(reversed(old_lines)), fence_len)))

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


# def match_stripped_lines_context(stripped_file_lines, old_lines):

#     #given stripped file lines and stripped old lines,
#     stripped_old_lines = [line.strip() for line in old_lines]
#     stripped_old_lines = [line for line in stripped_old_lines if line != ""]

#     #create code fence based on lines. i.e. first N content lines
#     begin_fence, stop_fence = create_code_fence(old_lines=stripped_old_lines)
#     # print(begin_fence, stop_fence)

#     #Match N content lines. This means that the first N content lines will be matched on and the last N content lines will be matched on.
#     begin_start, begin_end, src_idx = match_fence(stripped_file_lines, begin_fence)

#     #find all begin matches
#     #find all end matches
#     #for each begin match, find first end match
    
#     #given all pairs filter out the ones longer than size of old_lines
#     #if none throw error
#     #return

#     if src_idx is not None:
#         stop_start, stop_end, _ = match_fence(stripped_file_lines, stop_fence, src_idx)
#     else:
#         stop_start, stop_end, _ = match_fence(stripped_file_lines, stop_fence)

#     start = begin_start
#     end = stop_end

#     return start, end


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


def match_stripped_lines_context(stripped_file_lines, old_lines):
    #given stripped file lines and stripped old lines,
    stripped_old_lines = [line.strip() for line in old_lines]
    stripped_old_lines = [line for line in stripped_old_lines if line != ""]
    
    #create code fence based on lines. i.e. first N content lines
    begin_fence, stop_fence = create_code_fence(old_lines=stripped_old_lines)
    
    #Match N content lines. This means that the first N content lines will be matched on and the last N content lines will be matched on.
    begin_matches = match_fence_all(stripped_file_lines, begin_fence)
    end_matches = match_fence_all(stripped_file_lines, stop_fence)
    
    #for each begin match, find first end match
    valid_pairs = []
    for begin_start, begin_end, src_idx in begin_matches:
        for stop_start, stop_end, end_idx in end_matches:
            if src_idx <= end_idx and (stop_end - begin_start + 1) <= len(old_lines) + 4:
                valid_pairs.append((begin_start, stop_end))
                break
    
    #if none throw error
    if not valid_pairs:
        raise ValueError("No valid matches found.")
    
    return valid_pairs[0]


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
                        content = lines[i][1:]

                        if lines[i].startswith("-"):
                            hunk_lines.append(HunkLine(type="removed", content=content))
                            changed_lines += 1
                        elif lines[i].startswith("+"):
                            hunk_lines.append(HunkLine(type="added", content=content))
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


def get_indent(line):
    base_indent = "    "
    if line.startswith(base_indent):
        # find multiple of base_indent present as prefix in line
        count = 0
        while line.startswith(base_indent):
            count += 1
            line = line[len(base_indent):]
        return count
    else:
        return 0
        

def get_prefix_whitespace(line):
    
    count = 0
    while line.startswith(" "):
        count += 1
        line = line[1:]
    return count

def get_relative_indents(lines):
    assert type(lines) == list
    assert all(type(line) == str for line in lines)
    spaces = []
    for line in lines:
        space = get_prefix_whitespace(line)
        spaces.append(space)
    return spaces

def apply_indent_to_new_lines(src_lines, src_start, src_end, new_lines):

    base_indent_match = get_indent(src_lines[src_start][1])
    base_indent_hunk = get_indent(new_lines[0])
    indented_new_lines = new_lines

    if base_indent_match != base_indent_hunk:
        if base_indent_match > base_indent_hunk:
            indented_new_lines = ["    " * (base_indent_match - base_indent_hunk) + line for line in new_lines]
        else:
            indented_new_lines = [line.replace("    " * (base_indent_hunk - base_indent_match), "") for line in new_lines]
    
    return indented_new_lines


# single diff apply rules
# 4. Try to match on lines -> if no match -> try again with more context = retry loop
#     1. If match on lines doesn’t match the first 3 and last 3 bail
# 5. Generate indent error -> auto fix indentation after match

not_enough_context_prompt = """
NotEnoughContextError:
    In the diff, the deleted lines (denoted with -), and the context lines you provided (unchanged lines) did not match the existing source file.

    The provided deleted (-) and unchanged lines were built into a code block that was then used to identify where the edit would be applied.
    However, this did not work. The content lines you created did not match the actual source file.

    The problem is that there were not enough context lines provided, and the provided context lines DO NOT EXIST.
    
    The solution to fix this error is to provide additional context lines matching the original source lines exactly.

    When writing the lines, ask yourself, does this line actually exist in the source code?
    About half of the time it doesn't actually exist! Make sure you only write source lines that exist.

    Please pay more attention to the exact lines you are writing.
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

def apply_context_diff(file_content: str, file_diff: FileContextDiff) -> str:

    #create i, line pairs for diff apply
    src_lines = [(i, line) for i, line in enumerate(file_content.splitlines())]

    #get stripped version of original file i.e. strip all lines then filter out empty lines
    stripped_src_lines = [t for t in [(i, line.strip()) for i, line in src_lines] if t[1] != ""]

    tgt_lines = list(src_lines)

    #for hunk in file diffs:
    #   construct code blocks
    #   match old code block on stripped lines
    #   align old code block with new code block
    #   fix new code block indentation
    #   replace old code block with new code block -> could cause an overlap error

    for hunk in file_diff.hunks:

        old_lines, new_lines = construct_versions_from_diff_hunk(hunk)

        if not (old_lines is not None and new_lines is not None):
            # if either version is none, raise error
            raise Hallucination(unable_to_parse_old_or_new_lines)

        src_start, src_end = match_stripped_lines_context(stripped_src_lines, old_lines)

        print(src_start, src_end)

        if not (src_start is not None and src_end is not None):
            #Raise hallucination due to not matching full src lines
            raise Hallucination(not_enough_context_prompt)

        if src_end - src_start > len(old_lines) + 5:
            raise Hallucination(not_enough_context_prompt)

        applied_code = apply_indent_to_new_lines(src_lines, src_start, src_end, new_lines)

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

    #return correct code
    return "\n".join([entry[1] for entry in list(tgt_lines)])

def extract_all_diffs(diff_input):
    if isinstance(diff_input, list):
        diff_input= "".join(diff_input)
    
    diff_code = diff_input

    # extract diff from response
    diffs = extract_diff_from_response(diff_code)

    print(diffs)

    if len(diffs) == 0:
        #Raise exception about length of diffs
        raise Hallucination(no_diffs_found)
    
    total_changed_lines = 0

    #for each diff, actually parse the changes from it. Assume this just works for parsing the diff hunks (not formatting or anything, but rather just extracting target lines)
    all_diffs = []
    for diff in diffs:
        file_diffs, changed_lines = parse_multi_file_diffs(diff)
        total_changed_lines += changed_lines
        all_diffs.extend(file_diffs)

    # changes = MultiFileContextDiff(files=all_diffs)
    
    #Check to see if there are diffs that have neither src or tgt file
    error_diffs = []
    for diff in all_diffs:
        if (not (diff.src_file or diff.tgt_file)):
            error_diffs += diff

    if len(error_diffs) !=0:
        #Raise exception containing non-applicable diffs
        raise Hallucination(non_applicable_diff_found)

    #deduping the diffs here
    return list(all_diffs), total_changed_lines

def apply_file_context_diffs(file_content, all_diffs):
    succeeded = []
    failed = []

    #for each diff block, apply context diff, returns tuple result (abspath, new_content)
    for diff in all_diffs:
        try:
            result = apply_context_diff(file_content=file_content, file_diff=diff)
            succeeded.append((diff.tgt_file, result, file_content))
        except Hallucination as e:
            # print(e)
            failed.append((diff, e, file_content))

    #should return files with new code to write
    return {
        "success": succeeded,
        "fail": failed
    }

# 1. Capture command count -> solved by command parsing
# 2. Capture tags -> if bad return
# 3. Capture src and tgt file -> if none -> return. Bad

def apply_multi_file_context_diff(file_content, diff, original_change_count):
    # By the time we get here we have correctly captured a single command

    # print(diff)

    failures = []

    try:
        all_diffs, total_new_changed = extract_all_diffs(diff)
        # print(all_diffs)
        if original_change_count is not None and (total_new_changed > (original_change_count + 5) or total_new_changed < (original_change_count - 1)):
            raise Hallucination(recover_failed_new_diff_too_different)
    except Hallucination as e:
        print(e)
        failures.append((None, e))

    apply_res = apply_file_context_diffs(file_content=file_content, all_diffs=all_diffs)

    apply_res["fail"].extend(failures)

    return apply_res, total_new_changed


if __name__ == "__main__":
    code = """
    asomawefsdofjn content
<DIFF>
```diff
--- django/views/debug.py
+++ django/views/debug.py
@@ -38,11 +38,17 @@
             if self.hidden_settings.search(key):
                 cleansed = self.cleansed_substitute
             elif isinstance(value, dict):
                 cleansed = {k: self.cleanse_setting(k, v) for k, v in value.items()}
+            elif isinstance(value, Iterable) and not isinstance(value, dict):
+                cleansed = [self.cleanse_setting(None, v) for v in value]
             else:
                 cleansed = value
         except TypeError:
             # If the key isn't regex-able, just return as-is.
             cleansed = value
+        from collections.abc import Iterable
+
         if callable(cleansed):
             cleansed = CallableSettingWrapper(cleansed)
 
         return cleansed
```
</DIFF>
"""

    res = extract_diff_from_response(code)

    print(res)
    delta = code.split("```diff")[1].split("```")[0]
    print(delta)