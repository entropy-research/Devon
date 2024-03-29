import json

from devon.agent.clients.client import Message
from ..state import State
from agent.evaluate.evaluate import EvaluatePrompts

class EvaluateState(State):
    def execute(self, context):
        # Evaluate the code changes
        critic = context["critic"]
        task = context["task"]
        reasoning_result = context["reasoning_result"]
        old_code = context["old_code"]
        new_code = context["new_code"]

        eval_result = critic.chat(messages=[
            Message(
                role="user",
                content=EvaluatePrompts.user_msg(goal=task, requirements=reasoning_result, old_code=json.dumps(old_code), new_code=json.dumps(new_code))
            )
        ])

        context["success"] = EvaluatePrompts.parse_success(eval_result)
        pass