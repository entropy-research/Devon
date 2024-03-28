import os
from devon.agent.clients.client import ClaudeOpus, Message
from devon.agent.tools.unified_diff.diff_types import FileDiff, Hunk, HunkLine, MultiFileDiff
import dotenv
import re

from devon.agent.tools.unified_diff.prompts.udiff_prompts import UnifiedDiffPrompts

dotenv.load_dotenv()

def parse_multi_file_diff(diff: str) -> MultiFileDiff:
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
                    match = re.findall(r"@@ -(\d+),(\d+) \+(\d+),(\d+) @@", lines[i])[0]
                    src_start, src_lines, tgt_start, tgt_lines = map(int, match)
                    i += 1
                    
                    while i < len(lines) and not lines[i].startswith("@@") and not lines[i].startswith("---"):
                        if lines[i].startswith("-"):
                            hunk_lines.append(HunkLine(type="removed", content=lines[i][1:]))
                        elif lines[i].startswith("+"):
                            hunk_lines.append(HunkLine(type="added", content=lines[i][1:]))
                        else:
                            hunk_lines.append(HunkLine(type="unchanged", content=lines[i][1:]))
                        i += 1
                    
                    hunks.append(Hunk(src_start=src_start, src_lines=src_lines, tgt_start=tgt_start, tgt_lines=tgt_lines, lines=hunk_lines))
                else:
                    i += 1
            
            file_diffs.append(FileDiff(src_file=src_file, tgt_file=tgt_file, hunks=hunks))
        else:
            i += 1
    
    return file_diffs

def extract_diffs(diff_text):
    return [diff.replace("<DIFF>", "").strip() for diff in diff_text.split("</DIFF>")[:-1] if "<DIFF>" in diff]

def format_diff_input(goal, code, plan, create, modify, delete, failure_context):
    return f"""
<GOAL>
{goal}
</GOAL>
<CODE>
{code}
</CODE>
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

def generate_unified_diff(client, goal, original_code, plan, create, modify, delete, failure_context):

    res = client.chat([
        Message(
            role="user",
            content=format_diff_input(goal, original_code, plan, create, modify, delete, failure_context)
        )
    ])

    print(res)

    diffs = extract_diffs(res)

    all_diffs = []
    for diff in diffs:
        file_diffs = parse_multi_file_diff(diff)
        all_diffs.extend(file_diffs)

    changes = MultiFileDiff(files=all_diffs)

    return changes

if __name__ == "__main__":
    example = """--- /Users/blackout/workspace/agent/devon/tests/state_functions.py
+++ /Users/blackout/workspace/agent/devon/tests/state_functions.py
@@ -31,8 +31,6 @@
                 full_path = os.path.join(path, file_path)
                 code, code_with_lines = get_code_from_file(shell, full_path)
                 if code is not None and code != "":
-                    parsed_ast = parse_ast(code)
-                    serialized_ast = serialize_ast(parsed_ast)
                     files[full_path] = CodeFile(filepath=full_path, code=code, code_with_lines=code_with_lines, ast=parsed_ast, serialized_ast=serialized_ast)
         for directory in dirs:
             if not directory.startswith('.'):  # Avoid hidden directories
@@ -58,19 +56,6 @@
 def ask(prompt):
     return input(prompt)
 
-def parse_ast(code):
-    try:
-        return ast.parse(code)
-    except SyntaxError as e:
-        print(f"SyntaxError: {e}")
-        return None
-
-def serialize_ast(tree):
-    if tree is None:
-        return ""
-    return ast.unparse(tree)
-
 def reason(client, input, goal):
     message = client.messages.create(
         max_tokens=1024,"""
    
    print(parse_multi_file_diff(example))