import logging
import re
import traceback
from typing import List, Optional

from pydantic import BaseModel

from devon.swebenchenv.environment.utils import LOGGER_NAME

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


def extract_diff_from_response(diff_text):
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


def create_code_fence(old_lines):
    if len(old_lines) < 4:
        start_fence = find_nth_content_line(old_lines, len(old_lines))
        end_fence = start_fence
    else:
        start_fence = find_nth_content_line(old_lines, 3)
        end_fence = list(reversed(find_nth_content_line(list(reversed(old_lines)), 3)))

    return start_fence, end_fence


def match_fence(lines, fence):
    subset_length = len(fence)

    if subset_length > 0:
        for i in range(len(lines) - subset_length + 1):
            match = [line[1] for line in lines[i : i + subset_length]]
            if match == fence:
                return lines[i][0], lines[i + subset_length - 1][0]

    return None, None


def match_stripped_lines_context(stripped_file_lines, old_lines):

    #given stripped file lines and stripped old lines,
    stripped_old_lines = [line.strip() for line in old_lines]
    stripped_old_lines = [line for line in stripped_old_lines if line != ""]

    # print(stripped_file_lines)
    # print(stripped_old_lines)

    #create code fence based on lines. i.e. first N content lines
    begin_fence, stop_fence = create_code_fence(old_lines=stripped_old_lines)

    # print(begin_fence, stop_fence)

    #Match N content lines. This means that the first N content lines will be matched on and the last N content lines will be matched on.
    begin_start, begin_end = match_fence(stripped_file_lines, begin_fence)
    stop_start, stop_end = match_fence(stripped_file_lines, stop_fence)

    start = begin_start
    end = stop_end

    return start, end


def parse_multi_file_diffs(diff: str) -> List[FileContextDiff]:
    file_diffs: List[FileContextDiff] = []
    lines = diff.strip().split("\n")

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
                        elif lines[i].startswith("+"):
                            hunk_lines.append(HunkLine(type="added", content=content))
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

    return file_diffs


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
            raise Exception()

        src_start, src_end = match_stripped_lines_context(stripped_src_lines, old_lines)

        if not (src_start is not None and src_end is not None):
            #Raise hallucination due to not matching full src lines
            raise Hallucination()

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


# 1. Capture command count -> solved by command parsing
# 2. Capture tags -> if bad return
# 3. Capture src and tgt file -> if none -> return. Bad

def apply_multi_file_context_diff(file_content, diff):
    # By the time we get here we have correctly captured a single command

    if isinstance(diff, list):
        diff= "".join(diff)
    
    diff_code = diff

    # extract diff from response
    diffs = extract_diff_from_response(diff_code)

    if len(diffs) == 0:
        #Raise exception about length of diffs
        raise Exception()

    #for each diff, actually parse the changes from it. Assume this just works for parsing the diff hunks (not formatting or anything, but rather just extracting target lines)
    all_diffs = []
    for diff in diffs:
        file_diffs = parse_multi_file_diffs(diff)
        all_diffs.extend(file_diffs)

    changes = MultiFileContextDiff(files=all_diffs)
    
    #Check to see if there are diffs that have neither src or tgt file
    error_diffs = []
    for diff in all_diffs:
        if (not (diff.src_file or diff.tgt_file)):
            error_diffs += diff

    if len(error_diffs) !=0:
        #Raise exception containing non-applicable diffs
        raise Exception()

    #deduping the diffs here
    all_diffs = list(set(all_diffs))

    succeeded = []
    failed = []

    #for each diff block, apply context diff, returns tuple result (abspath, new_content)
    for diff in all_diffs:
        try:
            result = apply_context_diff(file_content=file_content, file_diff=diff)
            succeeded.append((diff.tgt_file, result))
        except Exception as e:
            failed.append((diff, e))

    #should return files with new code to write
    return {
        "success": succeeded,
        "fail": failed
    }
