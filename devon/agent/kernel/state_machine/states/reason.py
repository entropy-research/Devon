from ..state import State
from agent.reasoning.reason import ReasoningPrompts

class ReasonState(State):
    def execute(self, context):
        reasoning_model = context["reasoning_model"]
        task = context["task"]
        file_tree = context["file_tree"]
        code = context["code"]
        reasoning_result = reasoning_model.chat(ReasoningPrompts.user_msg(goal=task, file_tree=str(file_tree), code=code))
        context["reasoning_result"] = ReasoningPrompts.parse_msg(reasoning_result)