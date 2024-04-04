from typing import Any
import json

from devon_agent.agent.clients.client import LanguageModel, Message
from devon_agent.agent.evaluate.evaluate import EvaluatePrompts
from devon_agent.agent.kernel.state_machine.state import State
from devon_agent.agent.kernel.context import BaseStateContext

from dataclasses import dataclass
from devon_agent.agent.kernel.context import BaseStateContext
from devon_agent.agent.kernel.state_machine.states.reason import ReasoningResult

@dataclass
class EvaluateParameters:
    model: LanguageModel

@dataclass
class EvaluateContext:
    task: str
    global_context: BaseStateContext
    reasoning_result: ReasoningResult
    old_code: dict

class EvaluateState(State):

    def __init__(self, parameters: EvaluateParameters):
        self.parameters = parameters

    def execute(self, context: EvaluateContext) -> Any:
        reasoning_result = context.reasoning_result
        fs_context = context.global_context.load_file_context(context.global_context.fs_root)

        eval_result = self.parameters.model.chat(messages=[
            Message(
                role="user",
                content=EvaluatePrompts.user_msg(
                    goal=context.task,
                    requirements=reasoning_result.plan,
                    old_code=context.old_code,
                    new_code=json.dumps(fs_context.file_code_mapping)
                )
            ),
            Message(
                role="assistant",
                content=EvaluatePrompts.success
            )
        ])

        print(eval_result)

        success = EvaluatePrompts.parse_msg(eval_result)

        if success:
            print("Requirements met successfully!")
        else:
            print("Requirements not met, trying again...")

        return success