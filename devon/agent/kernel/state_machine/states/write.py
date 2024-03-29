from ..state import State
from agent.tools.file_system.fs import FileSystemTool

class WriteState(State):
    def execute(self, context):
        plan = context["reasoning_result"][0]
        create = context["reasoning_result"][1]
        modify = context["reasoning_result"][2]
        delete = context["reasoning_result"][3]

        file_system_tool = context["file_system_tool"]
        git_tool = context["git_tool"]

        file_system_tool.modify_files(plan, create, modify, delete)
        git_tool.commit_changes("Implemented task based on plan")