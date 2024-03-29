from ..state import State
from agent.tools.git_tool.git_tool import GitTool

class ExecuteState(State):
    def execute(self, context):
        git_tool = context["git_tool"]
        github_tool = context["github_tool"]
        repo_url = github_tool.get_repo_url(context["cwd"])

        git_tool.clone_repo(repo_url)
        git_tool.create_branch("task-implementation")