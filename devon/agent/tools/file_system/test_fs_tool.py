from devon.agent.clients.client import GPT4, Message
from devon.agent.clients.tool_utils.tools import Tool, Toolbox

from pydantic import Field
from openai import OpenAI
import json
import os

from devon.agent.tools.file_system.fs import FileSystemTool
from devon.agent.tools.git_tool.git_tool import GitManager
from devon.agent.tools.github.github_tool import GitHubTool
from devon.agent.tools.directory.directory import DirectoryObserverTool

if __name__ == "__main__":
    tool_bank = Toolbox()
    g = GitManager()
    token = os.getenv("AGENT_GITHUB_TOKEN")
    gh = GitHubTool(token=token)
    directory_tool = DirectoryObserverTool(base_path=".")
    file_system_tool = FileSystemTool(base_path=".")

    tool_bank.add_tools_from_class(file_system_tool)
    tool_bank.add_tools_from_class(gh)
    tool_bank.add_tools_from_class(g)
    tool_bank.add_tools_from_class(directory_tool)

    client = OpenAI()

    model = GPT4(client, system_message="You are a helpful assistant", max_tokens=1000, tools_enabled=True)

    messages = [
        Message(role="user", content="""
                somewhere nested under the current directory there is a file called test_github_tool.py
                find it and copy it to the file_system folder under tools
                """)
    ]

    print(len(tool_bank.get_all_tools()))

    message, tool_calls = model.chat(
        messages=messages,
        tools=tool_bank
    )

    print(tool_calls)

    if not tool_calls:
        exit(0)

    tool_results = tool_bank.execute_tool_calls(tool_calls)

    print(tool_results)

    messages += [{**res, "content":json.dumps(res["content"])} for res in tool_results]

    message, tool_calls = model.chat(
        messages=messages,
        tools=tool_bank
    )

    print(tool_calls)

    if not tool_calls:
        exit(0)

    tool_results = tool_bank.execute_tool_calls(tool_calls)

    print(tool_results)

    messages += [{**res, "content":json.dumps(res["content"])} for res in tool_results]

    message, tool_calls = model.chat(
        messages=messages,
        tools=tool_bank
    )

    print(tool_calls)

    if not tool_calls:
        exit(0)

    tool_results = tool_bank.execute_tool_calls(tool_calls)

    print(tool_results)