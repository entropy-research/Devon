from devon_agent.agent.clients.client import GPT4, Message
from devon_agent.agent.clients.tool_utils.tools import Tool, Toolbox

from pydantic import Field
from openai import OpenAI
import json

from devon_agent.agent.tools.file_system.fs import FileSystemTool
from devon_agent.agent.tools.git_tool.git_tool import GitTool

def get_n_day_weather_forecast(
    location: str = Field(..., description="The city and state, e.g. San Francisco, CA"),
    format: str = Field("celsius", description="The temperature unit to use. Infer this from the user's location."),
    num_days: int = Field(..., description="The number of days to forecast")
) -> str:
    """Get an N-day weather forecast"""
    # Placeholder implementation
    return json.dumps({"location": location, "format": format, "num_days": num_days, "forecast": "Sunny"})

if __name__ == "__main__":
    git_tools = Toolbox()

    g = GitTool(path="..")
    file_system_tool = FileSystemTool(base_path=".")

    git_tools.add_tools_from_class(g)
    git_tools.add_tools_from_class(file_system_tool)

    client = OpenAI()

    model = GPT4(client, system_message="You are a helpful assistant", max_tokens=1000, tools_enabled=True)

    messages = [
            Message(role="user", content="""
                somewhere nested in the current director is a file called test_github_tool.py
                first create a new branch and switch to it,
                then on the new branch, copy test_github_tool.py it to the file_system folder,
                after you copy the file, make sure to commit the file to git
                """
            )
        ]

    while True:

        message, tool_calls = model.chat(
            messages=messages,
            tools=git_tools
        )

        print(tool_calls)

        if not tool_calls:
            exit(0)

        tool_results = git_tools.execute_tool_calls(tool_calls)

        print(tool_results)

        messages += [{**res, "content":json.dumps(res["content"])} for res in tool_results]
