import difflib
from devon.agent.tools.unified_diff.create_diff import FileDiff, MultiFileDiff, construct_versions_from_diff_hunk, extract_diffs, parse_multi_file_diff2
import os

from devon.agent.tools.unified_diff.diff_types import MultiFileDiff2

def apply_diff_to_file(original_code: str, diff: FileDiff) -> str:
    result_lines = original_code.splitlines()
    hunks = reversed(diff.hunks)
    
    for hunk in hunks:
        src_start = hunk.src_start - 1
        src_end = src_start + hunk.src_lines
        
        # Create a new list to store the modified lines
        modified_lines = []
        
        # Iterate over the lines in the hunk
        for line in hunk.lines:
            if line.type == "added" or line.type == "unchanged":
                # Add the line to the modified lines list
                modified_lines.append(line.content)
        
        # Replace the original lines with the modified lines
        result_lines[src_start:src_end] = modified_lines
    
    return "\n".join(result_lines)

def first_and_last_content_lines(lines):
    start = 0
    for i, line in enumerate(lines):
        if line != '':
            start = i
            break
    
    end = 0
    for i, line in enumerate(reversed(lines)):
        if line != '':
            end = i + 1
            break
    
    return start, end


def match_stripped_lines(file_lines, old_lines):

    stripped_file_lines = [(i, line.strip()) for i, line in enumerate(file_lines)]

    assert len(stripped_file_lines) == len(file_lines)

    old_lines = [line.strip() for line in old_lines]

    start, end  = first_and_last_content_lines(old_lines)

    print(old_lines)
    # print(start, end)
    
    i = 0
    while i < len(stripped_file_lines):
        if len(old_lines) > 0 and stripped_file_lines[i][1] == old_lines[start]:
            print("matched", i, stripped_file_lines[i][1], old_lines[start] )
            print("\n".join([ " ".join([str(entry[0]), entry[1]]) for entry in list(stripped_file_lines)]))
            j = 1
            while i + j < len(stripped_file_lines) and stripped_file_lines[i + j][1] != old_lines[-end]:
                j += 1

            start_line = stripped_file_lines[i][0]  # Add 1 to convert from 0-based index to 1-based line number
            end_line = stripped_file_lines[i + j][0]

            print(start_line, end_line)
            print(stripped_file_lines[i])
            print(stripped_file_lines[i + j])

            if len(old_lines) <= i + j:
                return start_line, end_line
            else:
                print("skipped match")
                i += 1
        else:
            i += 1
    
    return None, None


def apply_diff_to_file_map(file_code_mapping: dict, diff: MultiFileDiff) -> (dict, list):
    updated_files = {}
    touched_files = []

    for file_diff in diff.files:
        file_path = file_diff.tgt_file
        if file_path in file_code_mapping:
            original_code = file_code_mapping[file_path]
            result_lines = apply_diff_to_file(original_code, file_diff)
            updated_files[file_path] = result_lines
            touched_files.append(file_path)
        else:
            file_code_mapping[file_path] = apply_diff_to_file("", file_diff)
            # print(f"Warning: File '{file_path}' not found in the file code mapping.")

    # Add untouched files to the updated_files dictionary
    for file_path, original_code in file_code_mapping.items():
        if file_path not in touched_files:
            updated_files[file_path] = original_code

    return updated_files, touched_files

def apply_diff(multi_file_diff: MultiFileDiff):
    for file_diff in multi_file_diff.files:
        src_file = file_diff.src_file
        tgt_file = file_diff.tgt_file

        if src_file == "/dev/null":
            # Creating a new file
            with open(tgt_file, "w") as f:
                for hunk in file_diff.hunks:
                    to_write = [line.content for line in hunk.lines if line.type != "removed"]
                    f.write("\n".join(to_write))
        elif tgt_file == "/dev/null":
            # Deleting a file
            os.remove(src_file)
        else:
            # Modifying an existing file
            with open(src_file, "r") as src, open(tgt_file, "w") as tgt:
                src_lines = src.readlines()
                tgt_lines = []
                src_idx = 0

                for hunk in file_diff.hunks:
                    # Copy unchanged lines until the hunk start

                    while src_idx < hunk.src_start - 1 and src_idx < len(src_lines):
                        print(src_idx)
                        print(len(src_lines))
                        print(hunk.src_start)
                        tgt_lines.append(src_lines[src_idx])
                        src_idx += 1

                    # Process hunk lines
                    for line in hunk.lines:
                        if line.type == "added":
                            tgt_lines.append(line.content)
                        elif line.type == "removed":
                            src_idx += 1
                        else:
                            tgt_lines.append(line.content)
                            src_idx += 1
                    src_idx += 1

                tgt.write("\n".join(tgt_lines))

def apply_diff2(multi_file_diff: MultiFileDiff2):
    for file_diff in multi_file_diff.files:
        src_file = file_diff.src_file
        tgt_file = file_diff.tgt_file

        print(src_file, tgt_file)

        if src_file == "/dev/null":
            # Creating a new file
            with open(tgt_file, "w") as f:
                for hunk in file_diff.hunks:
                    to_write = [line.content for line in hunk.lines if line.type != "removed"]
                    # f.write("\n".join(to_write))
        elif tgt_file == "/dev/null":
            # Deleting a file
            # os.remove(src_file)
            pass
        else:
            # Modifying an existing file
            with open(src_file, "r") as src:
                src_lines = src.readlines()
                tgt_lines = src_lines
                src_idx = 0

                for hunk in reversed(file_diff.hunks):
                    # Copy unchanged lines until the hunk start

                    old_lines, new_lines  = construct_versions_from_diff_hunk(hunk)

                    start, end = match_stripped_lines(src_lines, old_lines)

                    print(start, end)
                    if start and end:
                        tgt_lines[start:end] = ["\n" + line for line in new_lines]

                    # while src_idx < hunk.src_start - 1 and src_idx < len(src_lines):
                    #     print(src_idx)
                    #     print(len(src_lines))
                    #     print(hunk.src_start)
                    #     tgt_lines.append(src_lines[src_idx])
                    #     src_idx += 1

                    # # Process hunk lines
                    # for line in hunk.lines:
                    #     if line.type == "added":
                    #         tgt_lines.append(line.content)
                    #     elif line.type == "removed":
                    #         src_idx += 1
                    #     else:
                    #         tgt_lines.append(line.content)
                    #         src_idx += 1

                # Copy remaining unchanged lines after the last hunk
                # while src_idx < len(src_lines):
                #     tgt_lines.append(src_lines[src_idx])
                #     src_idx += 1
                
                
                # print("\n".join(tgt_lines))
                # with open(tgt_file, "w") as tgt:
                #     tgt.write("".join(tgt_lines))



if __name__ == "__main__":
    res = """<DIFF>
--- /dev/null
+++ agent/kernel/state_machine/__init__.py
@@ -0,0 +1,1 @@
+from .state_machine import *
</DIFF>

<DIFF>
--- /dev/null
+++ agent/kernel/state_machine/state_types.py
@@ -0,0 +1,4 @@
+from typing import Literal, Union
+
+type State = Union[Literal["reason"], Literal["write"], Literal["execute"], Literal["evaluate"], Literal["terminate"]]
+
</DIFF>

<DIFF>
--- /dev/null
+++ agent/kernel/state_machine/state_machine.py
@@ -0,0 +1,19 @@
+from devon.agent.kernel.state_machine.state_types import State
+
+class StateMachine:
+
+    def __init__(self, state: State):
+        self.state = state
+        self.state_dict = {}
+
+    def add_state(self, name: State, state_class):
+        self.state_dict[name] = state_class
+
+    def execute_state(self, name, context):
+        state = self.state_dict[name]
+        state.execute(context)
+
+    def transition(self, new_state):
+        self.state = new_state
+
</DIFF>

<DIFF>
--- /dev/null
+++ agent/kernel/state_machine/state.py
@@ -0,0 +1,7 @@
+from abc import ABC, abstractmethod
+
+class State(ABC):
+
+    @abstractmethod
+    def execute(self, context):
+        pass
</DIFF>

<DIFF>
--- /dev/null
+++ agent/kernel/state_machine/states/reason.py
@@ -0,0 +1,5 @@
+from agent.kernel.state_machine.state import State
+
+class ReasonState(State):
+    def execute(self, context):
+        # Implement reasoning logic here
</DIFF>

<DIFF>
--- /dev/null
+++ agent/kernel/state_machine/states/write.py
@@ -0,0 +1,5 @@
+from agent.kernel.state_machine.state import State
+
+class WriteState(State):
+    def execute(self, context):
+        # Implement code writing logic here
</DIFF>

<DIFF>
--- /dev/null
+++ agent/kernel/state_machine/states/execute.py
@@ -0,0 +1,5 @@
+from agent.kernel.state_machine.state import State
+
+class ExecuteState(State):
+    def execute(self, context):
+        # Implement code execution logic here
</DIFF>

<DIFF>
--- /dev/null
+++ agent/kernel/state_machine/states/evaluate.py
@@ -0,0 +1,5 @@
+from agent.kernel.state_machine.state import State
+
+class EvaluateState(State):
+    def execute(self, context):
+        # Implement code evaluation logic here
</DIFF>

<DIFF>
--- /dev/null
+++ agent/kernel/state_machine/states/terminate.py
@@ -0,0 +1,5 @@
+from agent.kernel.state_machine.state import State
+
+class TerminateState(State):
+    def execute(self, context):
+        # Implement termination logic here
</DIFF>

<DIFF>
--- agent/kernel/thread.py
+++ agent/kernel/thread.py
@@ -10,6 +10,7 @@ from devon.agent.tools.unified_diff.utils import apply_diff, apply_diff2, apply_
 from devon.sandbox.environments import EnvironmentProtocol
 from devon.format import reformat_code
 from devon.agent.reasoning.reason import ReasoningPrompts
+from agent.kernel.state_machine.state_machine import StateMachine
 from agent.evaluate.evaluate import EvaluatePrompts
 from anthropic import Anthropic
 from devon.agent.clients.client import ClaudeHaiku, ClaudeOpus, ClaudeSonnet, Message
@@ -40,7 +41,7 @@ class Thread:
             success = False
             failure_context = []
             state_manager = StateMachine(state="reason")
-            file_system = env.tools.file_system(path=os.getcwd())
+            state_manager.add_state("reason", ReasonState)
 
             plan = None
             create = None
@@ -48,6 +49,8 @@ class Thread:
             delete = None
 
             # while not state_manager.state == "success":
+            file_system = env.tools.file_system(path=os.getcwd())
+            context = {"goal": self.task, "env": env}
 
                 #Define run context
             repo_data = file_system.glob_repo_code(os.getcwd())
@@ -89,6 +92,9 @@ class Thread:
             # print(new, touched_files)
 
             # file_code_mapping = {path: data.code for path, data in repo_data.items()}
+            
+            state_manager.transition("terminate")
+            state_manager.execute_state("terminate", context)
 
     #         match state_manager.state:
     #             case "reason":
</DIFF>"""
    
    diffs = extract_diffs(res)

    all_diffs = []
    for diff in diffs:
        file_diffs = parse_multi_file_diff2(diff)
        all_diffs.extend(file_diffs)

    changes = MultiFileDiff2(files=all_diffs)

    apply_diff2(changes)