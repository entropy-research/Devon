import difflib
import os
from devon.agent.clients.client import ClaudeOpus, Message
from devon.agent.tools.unified_diff.diff_types import FileDiff, FileDiff2, Hunk, Hunk2, HunkLine, MultiFileDiff, MultiFileDiff2
import dotenv
import re

from devon.agent.tools.unified_diff.prompts.udiff_prompts import UnifiedDiffPrompts

dotenv.load_dotenv()

# def parse_multi_file_diff(diff: str) -> MultiFileDiff:
#     file_diffs = []
#     lines = diff.strip().split("\n")
    
#     i = 0
#     while i < len(lines):
#         if lines[i].startswith("---"):
#             src_file = re.findall(r"--- (.*)", lines[i])[0]
#             tgt_file = re.findall(r"\+\+\+ (.*)", lines[i+1])[0]
#             hunks = []
#             i += 2
            
#             while i < len(lines) and not lines[i].startswith("---"):
#                 if lines[i].startswith("@@"):
#                     hunk_lines = []
#                     match = re.findall(r"@@ -(\d+),(\d+) \+(\d+),(\d+) @@", lines[i])
#                     if len(match) == 0:
#                         match = re.findall(r"@@ -(\d+),(\d+) \+(\d+) @@", lines[i]) + ["1"]
                    
#                     match = match[0]
#                     src_start, src_lines, tgt_start, tgt_lines = map(int, match)
#                     i += 1
                    
#                     while i < len(lines) and not lines[i].startswith("@@") and not lines[i].startswith("---"):
#                         if lines[i].startswith("-"):
#                             hunk_lines.append(HunkLine(type="removed", content=lines[i][1:]))
#                         elif lines[i].startswith("+"):
#                             hunk_lines.append(HunkLine(type="added", content=lines[i][1:]))
#                         else:
#                             hunk_lines.append(HunkLine(type="unchanged", content=lines[i][1:]))
#                         i += 1
                    
#                     hunks.append(Hunk(src_start=src_start, src_lines=src_lines, tgt_start=tgt_start, tgt_lines=tgt_lines, lines=hunk_lines))
#                 else:
#                     i += 1
            
#             file_diffs.append(FileDiff(src_file=src_file, tgt_file=tgt_file, hunks=hunks))
#         else:
#             i += 1
    
#     return file_diffs

def parse_multi_file_diff2(diff: str) -> MultiFileDiff:
    file_diffs = []
    lines = diff.strip().split("\n")
    
    i = 0
    while i < len(lines):
        if lines[i].startswith("---"):
            src_file = re.findall(r"--- (.*)", lines[i])[0]
            tgt_file = re.findall(r"\+\+\+ (.*)", lines[i+1])[0]
            hunks = []
            i += 2
            
            while i < len(lines) and not lines[i].startswith("---"):
                if lines[i].startswith("@@"):
                    hunk_lines = []
                    match = re.search(r"@@ .* @@", lines[i])[0]

                    i += 1

                    while i < len(lines) and not lines[i].startswith("@@") and not lines[i].startswith("---"):
                        
                        content = lines[i][1:]

                        if lines[i].startswith("-"):
                            hunk_lines.append(HunkLine(type="removed", content=content))
                        elif lines[i].startswith("+"):
                            hunk_lines.append(HunkLine(type="added", content=content))
                        else:
                            hunk_lines.append(HunkLine(type="unchanged", content=content))
                        
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

                    hunks.append(Hunk2(start_lines=start_lines, end_lines=end_lines, lines=hunk_lines))
                else:
                    i += 1
            
            file_diffs.append(FileDiff2(src_file=src_file, tgt_file=tgt_file, hunks=hunks))
        else:
            i += 1
    
    return file_diffs

def construct_versions_from_diff_hunk(hunk: Hunk2):
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

def generate_unified_diff2(client, goal, original_code, plan, create, modify, delete, failure_context, file_tree):

    res = client.chat([
        Message(
            role="user",
            content=format_diff_input(goal, original_code, plan, create, modify, delete, failure_context, file_tree)
        )
    ])

    print(res)

    diffs = extract_diffs(res)

    all_diffs = []
    for diff in diffs:
        file_diffs = parse_multi_file_diff2(diff)
        all_diffs.extend(file_diffs)

    changes = MultiFileDiff2(files=all_diffs)

    return changes

# def find_line_numbers(lines, line1, line2):
#     for index in range(len(lines) - 1):
#         if lines[index].strip() == line1.strip():
#             return index + 1

#     return None

def extract_diffs(diff_text):
    return [diff.replace("<DIFF>", "").strip() for diff in diff_text.split("</DIFF>")[:-1] if "<DIFF>" in diff]

def format_diff_input(goal, code, plan, create, modify, delete, failure_context, file_tree):
    return f"""
<GOAL>
{goal}
</GOAL>
<CODE>
{code}
</CODE>
<FILE_TREE>
{file_tree}
</FILE_TREE>
<PLAN>
{plan}
</PLAN>
<CREATE>
{create}
</CREATE>
<MODIFY>
{modify}
</MODIFY>
<DELETE>
{delete}
</DELETE>
"""

# def generate_unified_diff(client, goal, original_code, plan, create, modify, delete, failure_context, file_tree):

#     res = client.chat([
#         Message(
#             role="user",
#             content=format_diff_input(goal, original_code, plan, create, modify, delete, failure_context, file_tree)
#         )
#     ])

#     diffs = extract_diffs(res)

#     all_diffs = []
#     for diff in diffs:
#         file_diffs = parse_multi_file_diff(diff)
#         all_diffs.extend(file_diffs)

#     changes = MultiFileDiff(files=all_diffs)

#     return changes
