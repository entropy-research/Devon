from dataclasses import dataclass
import json
from devon.agent.clients.client import LanguageModel, Message
from devon.agent.kernel.context import BaseStateContext
from ..state import State
from agent.reasoning.reason import ReasoningPrompts

# 1. Reasoning
    # Identify which files are necessary for the change
    # Create a mapping on a file level of what changes need to be made to each file
    # Review plan
@dataclass
class ReasoningParameters:
    model: LanguageModel

@dataclass
class ReasoningContext:
    task: str
    global_context: BaseStateContext

@dataclass
class ReasoningResult:
    plan: str
    create: list
    modify: list
    delete: list
    files_to_change: list
    read_only: list

class ReasonState(State):

    def __init__(self, parameters: ReasoningParameters):
        self.parameters = parameters

    def execute(self, context: ReasoningContext):
        reasoning_model = self.parameters.model
        task = context.task

        file_context = context.global_context.load_file_context(context.global_context.fs_root)

        # print(context.global_context.fs_root)
        # print(file_context.file_tree)
        # print(file_context.file_code_mapping.keys())

        print("Reasoning")
        plan, create, modify, delete, files_to_edit, read_only = ReasoningPrompts.parse_msg(reasoning_model.chat([
            Message(role="user", 
                content=ReasoningPrompts.user_msg(
                    goal=task,
                    file_tree=str(file_context.file_tree),
                    code=json.dumps(file_context.file_code_mapping)
                )
            )
        ]))

        print(plan)

        reasoning_result_obj = ReasoningResult(
            plan=plan,
            create=create,
            modify=modify,
            delete=delete,
            files_to_change=files_to_edit,
            read_only=read_only
        )

        return reasoning_result_obj, file_context.file_code_mapping
