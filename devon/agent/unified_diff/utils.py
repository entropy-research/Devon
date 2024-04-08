import difflib
from devon_agent.agent.tools.unified_diff.create_diff import FileDiff, MultiFileDiff, construct_versions_from_diff_hunk, extract_diffs, parse_multi_file_diff2
import os

from devon_agent.agent.tools.unified_diff.diff_types import MultiFileDiff2

import docker
import os

class DockerOSEmulator:
    def __init__(self, container_id):
        self.client = docker.from_env()
        self.container = self.client.containers.get(container_id)

    def path_exists(self, path):
        """
        Check if a file or directory exists in the container.
        """
        try:
            self.container.exec_run(f"test -e {path}")
            return True
        except docker.errors.ContainerError:
            return False

    def makedirs(self, path):
        """
        Create directories recursively in the container.
        """
        self.container.exec_run(f"mkdir -p {path}")

    def remove(self, path):
        """
        Remove a file from the container.
        """
        self.container.exec_run(f"rm {path}")

    def is_abs(self, path):
        """
        Check if a path is absolute in the container.
        """
        return os.path.isabs(path)

    def dirname(self, path):
        """
        Get the directory name of a path in the container.
        """
        return os.path.dirname(path)

    def open(self, path, mode="r"):
        """
        Open a file in the container.
        """
        return DockerFile(self.container, path, mode)

class DockerFile:
    def __init__(self, container, path, mode):
        self.container = container
        self.path = path
        self.mode = mode

    def write(self, content):
        """
        Write content to the file in the container.
        """
        self.container.exec_run(f"echo '{content}' > {self.path}")

    def read(self):
        """
        Read the content of the file from the container.
        """
        result = self.container.exec_run(f"cat {self.path}")
        return result.output.decode("utf-8")

    def close(self):
        """
        Close the file (no-op).
        """
        pass

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
    stripped_file_lines = [(i, line.strip()) for i, line in file_lines]
    old_lines = [line.strip() for line in old_lines]

    start, end  = first_and_last_content_lines(old_lines)

    i = 0
    while i < len(stripped_file_lines):
        if len(old_lines) > 0 and stripped_file_lines[i][1] == old_lines[start]:

            j = 1
            while i + j < len(stripped_file_lines) and stripped_file_lines[i + j][1] != old_lines[-end]:
                j += 1

            start_line = stripped_file_lines[i][0]  # Add 1 to convert from 0-based index to 1-based line number
            end_line = stripped_file_lines[i + j][0]

            return start_line, end_line
        else:
            i += 1
    
    return None, None

def apply_diff2(container, multi_file_diff: MultiFileDiff2, file_tree_root: str):
    for file_diff in multi_file_diff.files:
        src_file = file_diff.src_file
        tgt_file = file_diff.tgt_file

        # Ensure src_file and tgt_file are valid paths, if not, make them absolute paths from file_tree_root
        src_file_abs = os.path.join(file_tree_root, src_file.lstrip("/")) if not os.path.isabs(src_file) else src_file
        tgt_file_abs = os.path.join(file_tree_root, tgt_file.lstrip("/")) if not os.path.isabs(tgt_file) else tgt_file

        src_file_exists = container.exec_run(f"test -e {src_file_abs} && echo 'exists'").output.decode().strip() == 'exists'
        tgt_file_exists = container.exec_run(f"test -e {tgt_file_abs} && echo 'exists'").output.decode().strip() == 'exists'

        if src_file == "/dev/null" or not src_file_exists:
            # Creating a new file
            container.exec_run(f"mkdir -p {os.path.dirname(tgt_file_abs)}")  # Ensure the directory exists
            is_dir = container.exec_run(f"test -d {tgt_file_abs} && echo 'dir'").output.decode().strip() == 'dir'
            if is_dir:
                continue
            content_to_write = "\n".join([line.content for file_diff in multi_file_diff.files for line in file_diff.hunks if line.type != "removed"])
            container.exec_run(f"echo `{content_to_write}` > {tgt_file_abs}")
        elif tgt_file == "/dev/null":
            # Deleting a file
            container.exec_run(f"rm -f {src_file_abs}")
        else:
            # Modifying an existing file
            src_content = container.exec_run(f"cat {src_file_abs}").output.decode()
            src_lines = [(i, line) for i, line in enumerate(src_content.splitlines())]

            tgt_lines = list(src_lines)

            for hunk in file_diff.hunks:
                old_lines, new_lines = construct_versions_from_diff_hunk(hunk)
                src_start, src_end = match_stripped_lines(src_lines, old_lines)

                i = 0
                while i < len(tgt_lines):
                    if tgt_lines[i][0] == src_start:
                        j = 0
                        while i + j < len(tgt_lines) and tgt_lines[i+j][0] != src_end:
                            j += 1
                        
                        tgt_lines[i:i+j+1] = [(-1, line) for line in new_lines]
                        break
                        
                    i += 1
            
            new_code = "\n".join([entry[1] for entry in list(tgt_lines)])
            container.exec_run(f"echo '{new_code}' > {tgt_file_abs}")

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
+from devon_agent.agent.kernel.state_machine.state_types import State
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
+fromdevon_agent.agent.kernel.state_machine.state import State
+
+class ReasonState(State):
+    def execute(self, context):
+        # Implement reasoning logic here
</DIFF>

<DIFF>
--- /dev/null
+++ agent/kernel/state_machine/states/write.py
@@ -0,0 +1,5 @@
+fromdevon_agent.agent.kernel.state_machine.state import State
+
+class WriteState(State):
+    def execute(self, context):
+        # Implement code writing logic here
</DIFF>

<DIFF>
--- /dev/null
+++ agent/kernel/state_machine/states/execute.py
@@ -0,0 +1,5 @@
+fromdevon_agent.agent.kernel.state_machine.state import State
+
+class ExecuteState(State):
+    def execute(self, context):
+        # Implement code execution logic here
</DIFF>

<DIFF>
--- /dev/null
+++ agent/kernel/state_machine/states/evaluate.py
@@ -0,0 +1,5 @@
+fromdevon_agent.agent.kernel.state_machine.state import State
+
+class EvaluateState(State):
+    def execute(self, context):
+        # Implement code evaluation logic here
</DIFF>

<DIFF>
--- /dev/null
+++ agent/kernel/state_machine/states/terminate.py
@@ -0,0 +1,5 @@
+fromdevon_agent.agent.kernel.state_machine.state import State
+
+class TerminateState(State):
+    def execute(self, context):
+        # Implement termination logic here
</DIFF>

<DIFF>
--- agent/kernel/thread.py
+++ agent/kernel/thread.py
@@ -10,6 +10,7 @@ from devon_agent.agent.tools.unified_diff.utils import apply_diff, apply_diff2, apply_
 from devon_agent.sandbox.environments import EnvironmentProtocol
 from devon_agent.format import reformat_code
 from devon_agent.agent.reasoning.reason import ReasoningPrompts
+fromdevon_agent.agent.kernel.state_machine.state_machine import StateMachine
 fromdevon_agent.agentevaluate.evaluate import EvaluatePrompts
 from anthropic import Anthropic
 from devon_agent.agent.clients.client import ClaudeHaiku, ClaudeOpus, ClaudeSonnet, Message
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