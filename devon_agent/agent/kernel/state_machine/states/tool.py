from dataclasses import dataclass
import json
from devon_agent.agent.clients.client import LanguageModel, Message
from devon_agent.agent.clients.tool_utils.tools import Toolbox
from devon_agent.agent.kernel.context import BaseStateContext
from ..state import State
from devon_agent.agent.tools.tool_prompts import ToolPrompts


# 1. Tool
# Identify which files are necessary for the change
# Create a mapping on a file level of what changes need to be made to each file
# Review plan
@dataclass
class ToolParameters:
    model: LanguageModel


@dataclass
class ToolContext:
    task: str
    global_context: BaseStateContext
    plan: str


class ToolState(State):

    def __init__(self, parameters: ToolParameters):
        self.parameters = parameters

    def execute(self, context: ToolContext):
        task = context.task

        tools = Toolbox()
        tools.add_tools_from_class(context.global_context.file_system)
        tools.add_tools_from_class(context.global_context.git_tool)
        tools.add_tools_from_class(context.global_context.github_tool)

        # file_context = context.global_context.load_file_context(context.global_context.fs_root)

        print("Tool")
        messages = [
            Message(
                role="user", content=ToolPrompts.user_msg(goal=task, plan=context.plan)
            )
        ]

        while True:

            message, tool_calls = self.parameters.model.chat(
                messages=messages, tools=tools
            )
            print(tool_calls)

            if not tool_calls:
                break
            
            tool_results = tools.execute_tool_calls(tool_calls)
            print(tool_results)

            messages += [
                {**res, "content": json.dumps(res["content"])} for res in tool_results
            ]
