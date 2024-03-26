from gilfoyle.agent.clients.client import GPT4, Message
from gilfoyle.agent.clients.tool_utils.tools import Tool, Toolbox

from pydantic import Field
from openai import OpenAI
import json
import os

from gilfoyle.agent.tools.git_tool.git_tool import GitManager
from gilfoyle.agent.tools.github.github_tool import GitHubTool
from gilfoyle.agent.tools.directory.directory import DirectoryObserverTool

def get_n_day_weather_forecast(
    location: str = Field(..., description="The city and state, e.g. San Francisco, CA"),
    format: str = Field("celsius", description="The temperature unit to use. Infer this from the user's location."),
    num_days: int = Field(..., description="The number of days to forecast")
) -> str:
    """Get an N-day weather forecast"""
    # Placeholder implementation
    return json.dumps({"location": location, "format": format, "num_days": num_days, "forecast": "Sunny"})

if __name__ == "__main__":
    tool_bank = Toolbox()
    g = GitManager()
    token = os.getenv("AGENT_GITHUB_TOKEN")
    gh = GitHubTool(token=token)
    directory_tool = DirectoryObserverTool(base_path=".")
    tool_bank.add_tool(
        Tool.from_function(
            function=g.clone,
            name="git_clone",
            description="Clone a Git repository",
        )
    )
    tool_bank.add_tool(
        Tool.from_function(
            function=g.get_branches,
            name="git_get_branches",
            description="Get the branches of a Git repository",
        )
    )
    tool_bank.add_tool(
        Tool.from_function(
            function=g.get_commits,
            name="git_get_commits",
            description="Get the commits of a branch in a Git repository",
        )
    )
    tool_bank.add_tool(
        Tool.from_function(
            function=g.get_commit,
            name="git_get_commit",
            description="Get a specific commit from a Git repository",
        )
    )
    tool_bank.add_tool(
        Tool.from_function(
            function=g.get_file,
            name="git_get_file",
            description="Get a file from a specific commit in a Git repository",
        )
    )
    tool_bank.add_tool(
        Tool.from_function(
            function=gh.search_repositories,
            name="github_search_repositories",
            description="Search for repositories",
        )
    )
    tool_bank.add_tool(
        Tool.from_function(
            function=directory_tool.list_directory,
            name="list_directory",
            description="List the contents of a directory",
        )
    )

    client = OpenAI()

    model = GPT4(client, system_message="You are a helpful assistant", max_tokens=1000, tools_enabled=True)

    messages = [
        Message(role="user", content="""
                the entropy-research github org has a repo called 'agent' on github.
                clone it locally under a folder of your choice.
                to do this youll need to search github and list the local file structure
                then clone the repo after you know what path you want to put it under
                """)
    ]

    message, tool_calls = model.chat(
        messages=messages,
        tools=tool_bank
    )

    tool_results = tool_bank.execute_tool_calls(tool_calls)

    print(tool_results)

    messages += [{**res, "content":json.dumps(res["content"])} for res in tool_results]

    message, tool_calls = model.chat(
        messages=messages,
        tools=tool_bank
    )

    tool_results = tool_bank.execute_tool_calls(tool_calls)

    print(tool_results)

    messages += [{**res, "content":json.dumps(res["content"])} for res in tool_results]

    message, tool_calls = model.chat(
        messages=messages,
        tools=tool_bank
    )

    print(tool_calls)

    tool_results = tool_bank.execute_tool_calls(tool_calls)

    print(tool_results)