import difflib
import os
from devon_agent.agent.clients.client import Message
from devon.swebenchenv.environment.unified_diff.diff_types import FileDiff, FileDiff2, Hunk, Hunk2, HunkLine, MultiFileDiff, MultiFileDiff2
import dotenv
import re

from devon_agent.agent.tools.unified_diff.prompts.udiff_prompts import UnifiedDiffPrompts

def create_line_type(line):
    content = line.lstrip()
    if line.startswith("-"):
        return HunkLine(type="removed", content=content[1:])
    elif line.startswith("+"):
        return HunkLine(type="added", content=content[1:])
    else:
        return HunkLine(type="unchanged", content=content)

def parse_multi_file_diff2(diff: str) -> MultiFileDiff:
    file_diffs = []
    lines = diff.strip().split("\n")
    
    i = 0
    while i < len(lines):
        if lines[i].startswith("---"):

            print(lines[i])

            src_file = re.findall(r"--- (.*)", lines[i])[0]
            tgt_file = re.findall(r"\+\+\+ (.*)", lines[i+1])[0]
            hunks = []
            i += 2

            while i < len(lines) and not lines[i].startswith("---"):
                if lines[i].startswith("@@"):

                    hunk_lines = []
                    match = re.search(r"@@ .* @@(.*)", lines[i])[1]

                    if match.strip() != '':
                        hunk_lines.append(create_line_type(match))

                    i += 1

                    while i < len(lines) and not lines[i].startswith("@@") and not lines[i].startswith("---"):

                        hunk_lines.append(create_line_type(lines[i]))

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

def generate_unified_diff2(client, thought, input_diff, file_tree, code, files):

    res = client.chat([
        Message(
            role="user",
            content=format_diff_input(thought, input_diff, file_tree, code, files)
        )
    ])
    
    return res

def extract_diffs(diff_text):
    return [diff.replace("<DIFF>", "").strip() for diff in diff_text.split("</DIFF>")[:-1] if "<DIFF>" in diff]

def extract_diffs2(diff_text):
    if "<DIFF>" in diff_text:
        return [diff.replace("<DIFF>", "").strip() for diff in diff_text.split("</DIFF>")[:-1] if "<DIFF>" in diff]
    
    return [diff.replace("<<<", "").strip() for diff in diff_text.split(">>>")[:-1] if "<<<" in diff]

def format_diff_input(thought, input_diff, file_tree, code, files):
    return f"""
<GOAL>
{thought}
</GOAL>
<ORIGINAL>
{input_diff}
</ORIGINAL>
<CODE>
{code}
</CODE>
<FILE_TREE>
{file_tree}
</FILE_TREE>
<FILES>
{files}
</FILES>
"""

if __name__ == "__main__":
    d = """
edit_file <<<
--- /django__django/django/views/debug.py
+++ /django__django/django/views/debug.py
@@ -60,8 +60,8 @@
                         cleansed[i] = self.cleanse_setting(None, v)
             else:
                 cleansed = value
-        except TypeError:
-            cleansed = value
+        except TypeError:  
+            cleansed = value  
 
         if callable(cleansed):
             cleansed = CallableSettingWrapper(cleansed)
>>>
"""
    res = parse_multi_file_diff2(d)
    print(res)


