import logging
import re
from typing import List, Optional

from pydantic import BaseModel

from devon.swebenchenv.environment.utils import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)


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
            # if match[0] == fence[0]:
            # print(match, fence)
            if match == fence:
                return lines[i][0], lines[i + subset_length - 1][0]

    return None, None


def match_stripped_lines_context(file_lines, old_lines):

    stripped_file_lines = [(i, line.strip()) for i, line in file_lines]
    stripped_old_lines = [line.strip() for line in old_lines]

    stripped_file_lines = [t for t in stripped_file_lines if t[1] != ""]
    stripped_old_lines = [line for line in stripped_old_lines if line != ""]

    begin_fence, stop_fence = create_code_fence(old_lines=stripped_old_lines)

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
                    i += 1

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
    print("LINE", line)
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
        print("LINE", line, "SPACE", space)
        spaces.append(space)
    print()
    return spaces



def apply_context_diff(file_content: str, file_diff: FileContextDiff) -> str:

    src_lines = [(i, line) for i, line in enumerate(file_content.splitlines())]

    tgt_lines = list(src_lines)

    for hunk in file_diff.hunks:
        old_lines, new_lines = construct_versions_from_diff_hunk(hunk)
        logger.debug("%s, %s", old_lines, new_lines)
        src_start, src_end = match_stripped_lines_context(src_lines, old_lines)
        logger.debug("LOCATED DIFF: %s, %s", src_start, src_end)

        if not (src_start and src_end):
            raise Hallucination(
                "Applying this diff failed! The context lines and the src lines from the diff did not match the real code in the file!"
            )
        
        base_indent_match = get_indent(src_lines[src_start][1])

        base_indent_hunk = get_indent(new_lines[0])

        # print("BASE INDENT MATCH", base_indent_match, "BASE INDENT HUNK", base_indent_hunk)
        print("SPACES", get_relative_indents([line[1] for line in src_lines[src_start:src_end]]), get_relative_indents(new_lines))
        if base_indent_match != base_indent_hunk:
            if base_indent_match > base_indent_hunk:
                new_lines = ["    " * (base_indent_match - base_indent_hunk) + line for line in new_lines]
            else:
                new_lines = [line.replace("    " * (base_indent_hunk - base_indent_match), "") for line in new_lines]
        

        
        i = 0
        while i < len(tgt_lines):
            if tgt_lines[i][0] == src_start:
                j = 0
                while i + j < len(tgt_lines) and tgt_lines[i + j][0] != src_end:
                    j += 1

                tgt_lines[i : i + j + 1] = [(-1, line) for line in new_lines]
                break

            i += 1

    return "\n".join([entry[1] for entry in list(tgt_lines)])


