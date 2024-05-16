from dataclasses import dataclass
import json
import logging
import os
import inspect
from pathlib import Path
import re
import traceback
from typing import List, Optional
from datasets import load_dataset, load_from_disk
from ghapi.all import GhApi

from devon_agent.environments.swebenchenv import SWEEnvEnvironment
from devon_agent.tool import ToolNotFoundException
from devon_agent.tools import parse_command
from devon_agent.utils import DotDict

from devon_agent.tools.editortools import CreateFileTool, DeleteFileTool, OpenFileTool, ScrollDownTool, ScrollToLineTool, ScrollUpTool
from devon_agent.tools.edittools import EditFileTool
from devon_agent.tools.filesearchtools import FindFileTool, GetCwdTool, ListDirsRecursiveTool, SearchDirTool
from devon_agent.tools.filetools import SearchFileTool
from devon_agent.tools.lifecycle import NoOpTool, SubmitTool
from devon_agent.tools.shelltool import ShellTool


GITHUB_ISSUE_URL_PATTERN = re.compile(r"github\.com\/(.*?)\/(.*?)\/issues\/(\d+)")


def get_commit(api: GhApi, owner: str, repo: str, base_commit: str = None):
    if base_commit:
        commit = api.repos.get_commit(owner, repo, base_commit)
    else:
        commit = api.repos.list_commits(owner, repo)[0]
    return commit


def get_data_path_name(data_path: str):
    # if data_path is a file, return the file stem
    # elif it's a github url, return the owner__repo_name
    match = GITHUB_ISSUE_URL_PATTERN.search(data_path)
    if match:
        owner, repo, issue_number = match.groups()
        return f"{owner}__{repo}"
    return Path(data_path).stem


def is_from_github_url(data_path: str):
    return GITHUB_ISSUE_URL_PATTERN.search(data_path) is not None


def get_instances(
    file_path: str,
    base_commit: str = None,
    split: str = None,
    token: str = None,
    specific_issues: List[str] = None,
    run_all=False,
):
    """
    Getter function for handling json, jsonl files

    Arguments:
        file_path (str): Path to file
    Returns:
        List of instances
    """
    # If file_path is a directory, attempt load from disk
    if os.path.isdir(file_path):
        return load_from_disk(file_path, split=split)

    # If file_path is a github issue url, fetch the issue and return a single instance
    if is_from_github_url(file_path):
        match = GITHUB_ISSUE_URL_PATTERN.search(file_path)
        api = GhApi(token=token)
        if match:
            owner, repo, issue_number = match.groups()
            record = dict()
            issue = api.issues.get(owner, repo, issue_number)
            title = issue.title if issue.title else ""
            body = issue.body if issue.body else ""
            text = f"{title}\n{body}\n"
            record["repo"] = f"{owner}/{repo}"
            record["base_commit"] = (
                base_commit
                if base_commit
                else get_commit(api, owner, repo, base_commit).sha
            )
            record["version"] = record["base_commit"][:7]
            record["problem_statement"] = text
            record["instance_id"] = f"{owner}__{repo}-i{issue_number}"
            return [
                record,
            ]
    elif base_commit is not None:
        raise ValueError(
            "base_commit must be None if data_path is not a github issue url"
        )

    # If file_path is a file, load the file
    if file_path.endswith(".json"):
        return json.load(open(file_path))
    if file_path.endswith(".jsonl"):
        return [json.loads(x) for x in open(file_path, "r").readlines()]

    try:
        # Attempt load from HF datasets as a last resort
        if specific_issues:
            if run_all:
                return [
                    task
                    for task in load_dataset(file_path, split=split)
                    if task["instance_id"] in specific_issues
                ] + [task for task in load_dataset(file_path, split=split)]
            else:
                return [
                    task
                    for task in load_dataset(file_path, split=split)
                    if task["instance_id"] in specific_issues
                ]
        else:
            return load_dataset(file_path, split=split)
    except:
        raise ValueError(
            f"Could not load instances from {file_path}. "
            "Please ensure --data_path is a GitHub URL, a SWE-bench HuggingFace dataset, or a JSON/JSONL file."
        )


@dataclass
class SWEEnvSessionArguments:
    sweenv: SWEEnvEnvironment
    # image_name: str
    # data_path: str
    # split: str = "dev"
    # container_name: Optional[str] = None
    # install_environment: bool = True
    # timeout: int = 35
    # verbose: bool = False
    # no_mirror: bool = False
    # specific_issues: Optional[List[str]] = None
    record: Optional[dict] = None



class SWEEnvSession:

    def __init__(self, args: SWEEnvSessionArguments, agent):

        self.event_log = []
        self.event_index = 0
        self.state = DotDict({})
        self.agent = agent

        # if not self.args.verbose:
        #     self.logger.disabled = True

        self.logger = logging.getLogger(__name__)

        # self.data_path = args.data_path
        # specific_issues = (
        #     self.args.specific_issues if self.args.specific_issues else None
        # )
        # self.data = get_instances(
        #     self.data_path,
        #     self.args.base_commit,
        #     self.args.split,
        #     token=self.token,
        #     specific_issues=specific_issues,
        # )  # Load data from path
        # self.logger.info(f"💽 Loaded dataset from {self.data_path}")
        # self.issues = specific_issues

        self.idx = 1
        self.record = args.record
        
        sweenv = args.sweenv

        sweenv.register_tools({
            "create_file" : CreateFileTool(),
            "open_file" : OpenFileTool(),
            "scroll_up" : ScrollUpTool(),
            "scroll_down" : ScrollDownTool(),
            "scroll_to_line" : ScrollToLineTool(),
            "search_file" : SearchFileTool(),
            "edit_file" : EditFileTool(),
            "search_dir" : SearchDirTool(),
            "find_file" : FindFileTool(),
            # "list_dirs_recursive" : ListDirsRecursiveTool(),
            "get_cwd" : GetCwdTool(),
            "no_op" : NoOpTool(),
            "submit" : SubmitTool(),
            "delete_file" : DeleteFileTool(),

        })
        sweenv.set_default_tool(ShellTool())
        self.default_environment = sweenv

        self.environments = {
            "swebenchenv": sweenv
        }


    def enter(self):
        self.environments["swebenchenv"].setup()
        self.environments["swebenchenv"].reset(self.record)

        self.base_path = self.environments["swebenchenv"].base_path

        for tool in self.environments["swebenchenv"].tools.values():
            tool.setup({
                "environment" : self.environments["swebenchenv"],
                "session" : self,
                "state" : self.state,
            })


    def exit(self):
        self.environments["swebenchenv"].teardown()

    def run_event_loop(self):
        event_id = 0
        # current event
        submission = None

        while True and not (event_id == len(self.event_log)):

            event = self.event_log[event_id]

            self.logger.info(f"Event: {event}")
            # self.logger.info(f"State: {self.state}")

            if event["type"] == "Stop":
                # handle swebench logic issue logic
                # self.idx += 1
                # self.record = self.data[self.idx]
                # self.environments["swebenchenv"].reset(self.record)

                command = """submit() {
    cd $ROOT

    # Check if the patch file exists and is non-empty
    if [ -s "/root/test.patch" ]; then
        # Apply the patch in reverse
        git apply -R < "/root/test.patch"
    fi

    echo "\nbuild" >> .gitignore
    git add -A
    git diff --cached > model.patch
    echo "<<SUBMISSION||"
    cat model.patch
    echo "||SUBMISSION>>"
}
submit"""

                submission, rc =  self.environments["swebenchenv"].execute(command)
                break

            events = self.step_event(event)
            self.event_log.extend(events)

            event_id += 1
        
        return submission

    def step_event(self, event):

        new_events = []
        match event["type"]:
            case "Error":
                new_events.append(
                    {
                        "type": "Stop",
                        "content": "Stopped task",
                        "producer": event["producer"],
                        "consumer": "user",
                    }
                )

            case "ModelRequest":
                thought, action, output = self.agent.predict(
                    self.record["problem_statement"], event["content"], self
                )
                if action == "hallucination":
                    new_events.append(
                        {
                            "type": "ModelRequest",
                            "content": output,
                            "producer": self.agent.name,
                            "consumer": event["producer"],
                        }
                    )
                else:
                    new_events.append(
                        {
                            "type": "ModelResponse",
                            "content": json.dumps(
                                {"thought": thought, "action": action, "output": output}
                            ),
                            "producer": self.agent.name,
                            "consumer": event["producer"],
                        }
                    )

            case "ToolRequest":
                tool_name, args = event["content"]["toolname"], event["content"]["args"]

                match tool_name:
                    case "submit" | "exit" | "stop" | "exit_error" | "exit_api":
                        new_events.append(
                            {
                                "type": "Stop",
                                "content": "Stopped task",
                                "producer": event["producer"],
                                "consumer": "user",
                            }
                        )

                    case _:
                        try:

                            toolname = event["content"]["toolname"]
                            args = event["content"]["args"]
                            raw_command = event["content"]["raw_command"]

                            env = None

                            for _env in list(self.environments.values()):
                                if toolname in _env.tools:
                                    env = _env

                            if not env:
                                raise ToolNotFoundException(toolname, self.environments)

                            response = env.tools[toolname](
                                {
                                    "environment": env,
                                    "session": self,
                                    "state": self.state,
                                    "raw_command": raw_command,
                                },
                                *args,
                            )

                            new_events.append(
                                {
                                    "type": "ToolResponse",
                                    "content": response,
                                    "producer": toolname,
                                    "consumer": event["producer"],
                                }
                            )

                        except ToolNotFoundException as e:

                            if not (
                                self.default_environment
                                and self.default_environment.default_tool
                            ):
                                raise e

                            try:

                                response = self.default_environment.default_tool(
                                    {
                                        "state": self.state,
                                        "environment": self.default_environment,
                                        "session": self,
                                        "raw_command": event["content"]["raw_command"],
                                    },
                                    event["content"]["toolname"],
                                    event["content"]["args"],
                                )

                                new_events.append(
                                    {
                                        "type": "ToolResponse",
                                        "content": response,
                                        "producer": self.default_environment.name,
                                        "consumer": event["producer"],
                                    }
                                )
                            except Exception as e:
                                self.logger.error(traceback.format_exc())
                                self.logger.error(f"Error routing tool call: {e}")
                                new_events.append(
                                    {
                                        "type": "ToolResponse",
                                        "content": f"Error calling command, command failed with: {e.args[0] if len(e.args) > 0 else 'unknown'}",
                                        "producer": self.default_environment.name,
                                        "consumer": event["producer"],
                                    }
                                )
                        except Exception as e:
                            self.logger.error(traceback.format_exc())
                            self.logger.error(f"Error routing tool call: {e}")
                            new_events.append(
                                {
                                    "type": "ToolResponse",
                                    "content": e.args[0],
                                    "producer": self.default_environment.name,
                                    "consumer": event["producer"],
                                }
                            )

            case "ToolResponse":
                new_events.append(
                    {
                        "type": "ModelRequest",
                        "content": event["content"],
                        "producer": event["producer"],
                        "consumer": event["consumer"],
                    }
                )

            case "ModelResponse":
                content = json.loads(event["content"])["action"]
                toolname, args = parse_command(content)
                new_events.append(
                    {
                        "type": "ToolRequest",
                        "content": {
                            "toolname": toolname,
                            "args": args,
                            "raw_command": content,
                        },
                        "producer": event["producer"],
                        "consumer": event["consumer"],
                    }
                )

            case _:
                pass

        return new_events
    
    def get_available_actions(self) -> list[str]:
        # get all tools for all environments

        tools = []
        for env in self.environments.values():
            tools.extend(env.tools)

        return tools


    def generate_command_docs(self, format="manpage"):
        """
        Generates a dictionary of function names and their docstrings.
        """
        docs = {}
        for env in self.environments.values():
            for name,tool in env.tools.items():
                signature = inspect.signature(tool.function)
                docs[name] = {
                    "docstring" : tool.documentation(format),
                    "signature" : str(signature),
                }

        return docs
