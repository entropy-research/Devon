from dataclasses import dataclass
import json
import os
import traceback
from devon_agent.agent.clients.client import LanguageModel
from devon_agent.agent.kernel.context import BaseStateContext
from devon_agent.agent.kernel.state_machine.states.reason import ReasoningResult

from devon_agent.agent.tools.unified_diff.create_diff import generate_unified_diff2
from devon_agent.agent.tools.unified_diff.utils import apply_diff2
from ..state import State
from devon_agent.agent.tools.file_system.fs import FileSystemTool

@dataclass
class WriteParameters:
    diff_model: LanguageModel

@dataclass
class WriteContext:
    task: str
    global_context: BaseStateContext
    reasoning_result: ReasoningResult

@dataclass
class WriteResult:
    success: bool
    failure_context: list

class WriteState(State):

    def __init__(self, parameters: WriteParameters):
        self.parameters = parameters

    def execute(self, context: WriteContext):
        file_context = context.global_context.load_file_context(context.global_context.fs_root)
        task = context.task
        diff_model = self.parameters.diff_model
        failure_context = []

        modify = context.reasoning_result.modify
        if context.reasoning_result.create is not None:
            modify += [p for p in context.reasoning_result.create if os.path.exists(p)]

        files_to_change = [os.path.join(context.global_context.fs_root, path.strip()) for path in context.reasoning_result.files_to_change if path != '']

        print("Read Only: ", [os.path.basename(f) for f in context.reasoning_result.read_only])
        print("To Change: ", [os.path.basename(f) for f in files_to_change])

        read_code_w_line_numbers = {path: data.code for path, data in file_context.file_glob.items() if path in context.reasoning_result.read_only}
        edit_code_w_line_numbers = {path: data.code for path, data in file_context.file_glob.items() if path in files_to_change}

        try:
            out = generate_unified_diff2(
                    client=diff_model,
                    goal=task,
                    read_only_code=json.dumps(read_code_w_line_numbers),
                    original_code=json.dumps(edit_code_w_line_numbers),
                    plan=context.reasoning_result.plan,
                    create=context.reasoning_result.create,
                    modify=modify,
                    delete=context.reasoning_result.delete,
                    failure_context=failure_context,
                    file_tree=file_context.file_tree
                )
            apply_diff2(multi_file_diff=out, file_tree_root=context.global_context.fs_root)
            success = True
        except Exception as e:
            error = traceback.format_exc()
            print(error)
            failure_context.append(error)
            success = False

        return WriteResult(success=success, failure_context=failure_context)
