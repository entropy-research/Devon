import inspect
import json
import logging
import os
import random
import traceback
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from devon_agent.agent import TaskAgent
from devon_agent.environment import EnvironmentModule, LocalEnvironment, UserEnvironment
from devon_agent.telemetry import Posthog, SessionEventEvent, SessionStartEvent
from devon_agent.tool import  ToolNotFoundException
from devon_agent.tools import (
    parse_command,
)
from devon_agent.tools.editortools import CreateFileTool, DeleteFileTool, OpenFileTool, ScrollDownTool, ScrollToLineTool, ScrollUpTool, save_create_file, save_delete_file
from devon_agent.tools.edittools import EditFileTool, save_edit_file
from devon_agent.tools.filesearchtools import FindFileTool, GetCwdTool, ListDirsRecursiveTool, SearchDirTool
from devon_agent.tools.filetools import SearchFileTool
from devon_agent.tools.lifecycle import NoOpTool, SubmitTool
from devon_agent.tools.shelltool import ShellTool
from devon_agent.tools.usertools import AskUserTool

from devon_agent.utils import DotDict, Event
from devon_agent.vgit import  get_current_diff, get_or_create_repo, make_new_branch, stash_and_commit_changes, subtract_diffs


@dataclass(frozen=False)
class SessionArguments:
    path: str
    # environments: List[str]
    user_input: Any
    name: str


"""
The Event System

To generalize over several things that can happen. We have decided to use an event log to communicate every "event" that happens in the system. The following are a type of some events.

ModelResponse
- Content: Response by the model (currently in the format <THOUGHT></THOUGHT><ACTION></ACTION>)
- Next: The action is parsed and the right tool is chosen or user response is requested

ToolResponse
- Content: Response from the tool
- Next: The model is called with the reponse as the observation

UserRequest
- Content: User input
- Next: The output is sent as ToolRequest

Interrupt
- Content: The interrupt message
- Next: ModelResponse, the model is interrupted

Stop
- Content: None
- Next: None

Task
- Content: The next task/object the agent has to complete
- Next: ModelResponse

Error
- Content: The error message
- Next: None

Event Transitions
```
stateDiagram
    [*] --> ModelResponse
    ModelResponse --> ToolResponse: Action parsed, tool chosen
    ModelResponse --> UserRequest: User response requested
    ToolResponse --> ModelResponse: Tool response as observation
    UserRequest --> ModelResponse: User input as ToolRequest
    Interrupt --> ModelResponse: Model interrupted
    ModelResponse --> Task: Next task/object to complete
    Task --> ModelResponse
    User --> Interrupt
    User --> UserRequest
    ModelResponse --> [*]: Stop
```

"""


def get_git_root(fpath=None):
    path = fpath

    if path is None:
        path = os.getcwd()

    while True:
        if os.path.exists(os.path.join(path, ".git")):
            return path
        parent_dir = os.path.dirname(path)
        if parent_dir == path:
            return fpath
        path = parent_dir


class Session:
    def __init__(self, args: SessionArguments, agent):
        logger = logging.getLogger(__name__)

        self.state = DotDict({})
        self.state.PAGE_SIZE = 200
        self.logger = logger
        self.agent: TaskAgent = agent
        self.base_path = args.path
        self.event_log: List[Event] = []
        self.event_index = 0
        self.get_user_input = args.user_input
        self.telemetry_client = Posthog()
        self.name = args.name
        self.agent_branch = "devon_agent_" + self.name


        local_environment = LocalEnvironment(args.path)
        local_environment.register_tools({
            "create_file" : CreateFileTool().register_post_hook(save_create_file),
            "open_file" : OpenFileTool(),
            "scroll_up" : ScrollUpTool(),
            "scroll_down" : ScrollDownTool(),
            "scroll_to_line" : ScrollToLineTool(),
            "search_file" : SearchFileTool(),
            "edit_file" : EditFileTool().register_post_hook(save_edit_file),
            "search_dir" : SearchDirTool(),
            "find_file" : FindFileTool(),
            # "list_dirs_recursive" : ListDirsRecursiveTool(),
            "get_cwd" : GetCwdTool(),
            "no_op" : NoOpTool(),
            "submit" : SubmitTool(),
            "delete_file" : DeleteFileTool().register_post_hook(save_delete_file),
        })
        local_environment.set_default_tool(ShellTool())
        self.default_environment = local_environment

        user_environment = UserEnvironment(args.user_input)

        user_environment.register_tools({
            "ask_user" : AskUserTool(),
        })

        print(user_environment.tools["ask_user"].post_funcs)

        self.environments = {
            "local" : local_environment,
            "user" : user_environment,
        }

        self.path = args.path
        self.base_path = args.path


    def get_last_task(self):
        for event in self.event_log[::-1]:
            if event["type"] == "Task":
                return event["content"]
        return "Task unspecified ask user to specify task"
    
    def run_event_loop(self):
        event_id = 0
        #current event
        while True and not (event_id == len(self.event_log)):

            event = self.event_log[event_id]

            self.logger.info(f"Event: {event}")
            self.logger.info(f"State: {self.state}")

            # Collect only event name and content only in case of error
            telemetry_event = SessionEventEvent(
                event_type=event["type"],
                message="" if not event["type"] == "Error" else event["content"],
            )

            self.telemetry_client.capture(telemetry_event)

            if event["type"] == "Stop":
                break

            events = self.step_event(event)
            self.event_log.extend(events)

            event_id += 1
            

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
                    self.get_last_task(), event["content"], self
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
                    case "set_task":
                        new_events.append(
                            {
                                "type": "Task",
                                "content": args[0],
                                "producer": event["producer"],
                                "consumer": self.agent.name,
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

                            print(tool_name, args) 
                            response = env.tools[toolname]({
                                "environment": env,
                                "session": self,
                                "state": self.state,
                                "raw_command": raw_command
                            }, *args)


                            new_events.append(
                                {
                                    "type": "ToolResponse",
                                    "content": response,
                                    "producer": toolname,
                                    "consumer": event["producer"],
                                }
                            )

                        except ToolNotFoundException as e:
                            
                            if not (self.default_environment and self.default_environment.default_tool):
                                raise e
                            
                            try:
                        
                                response  = self.default_environment.default_tool({
                                    "state" : self.state,
                                    "environment" : self.default_environment,
                                    "session" : self,
                                    "raw_command" : event["content"]["raw_command"],
                                }, event["content"]["toolname"], event["content"]["args"])

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
                try:
                    toolname, args = parse_command(content)
                    new_events.append(
                        {
                            "type": "ToolRequest",
                            "content": {
                                "toolname" : toolname,
                                "args" : args,
                                "raw_command" : content
                            },
                            "producer": event["producer"],
                            "consumer": event["consumer"],
                        }
                    )
                except ValueError as e:
                    new_events.append(
                        {
                            "type": "ToolResponse",
                            "content": e.args[0] if len(e.args) > 0 else "Failed to parse command please follow the specified format",
                            "producer": event["producer"],
                            "consumer": event["consumer"],
                        }
                    )

            case "Interrupt":
                if self.agent.interrupt:
                    self.agent.interrupt += (
                        "You have been interrupted, pay attention to this message "
                        + event["content"]
                    )
                else:
                    self.agent.interrupt = event["content"]

            case "Task":
                task = event["content"]
                self.logger.info(f"Task: {task}")
                if task is None:
                    task = "Task unspecified ask user to specify task"

                new_events.append(
                    {
                        "type": "ModelRequest",
                        "content": "",
                        "producer": event["producer"],
                        "consumer": event["consumer"],
                    }
                )
            case _:
                pass

        return new_events

    # def parse_command_to_function(self, command_string) -> tuple[str, bool]:
    #     """
    #     Parses a command string into its function name and arguments.
    #     """
    #     ctx = self

    #     fn_name, args = parse_command(ctx, command_string)
    #     if fn_name in ["vim", "nano"]:
    #         return "Interactive Commands are not allowed", False

    #     if (
    #         fn_name == "python"
    #         and len([line for line in command_string.splitlines() if line]) != 1
    #     ):
    #         return "Interactive Commands are not allowed", False

    #     fn_names = [fn.__name__ for fn in self.tools]

    #     try:
    #         if fn_name == "edit_file":
    #             try:
    #                 return real_write_diff(self, command_string), False
    #             except Exception as e:
    #                 ctx.logger.error(traceback.print_exc())
    #                 raise e
    #         elif fn_name in fn_names:
    #             for fn in self.tools:
    #                 if fn.__name__ == fn_name:
    #                     return fn(ctx, *args), False
    #         else:
    #             # try:
    #             output, rc = ctx.environment.communicate(fn_name + " " + " ".join(args))
    #             if rc != 0:
    #                 raise Exception(output)
    #             return output, False
    #             # except Exception as e:
    #             #     ctx.logger.error(
    #             #         f"Failed to execute bash command '{fn_name}': {str(e)}"
    #             #     )
    #             #     return "Failed to execute bash command", False
    #     except Exception as e:
    #         ctx.logger.error(traceback.print_exc())
    #         return e.args[0] if len(e.args) > 0 else "Failed to execute command due to internal error", False

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


    def enter(self):
        print("Entering session")
        print(self.environments)
        for name, env in self.environments.items():
            print("Setting up env")
            env.setup(self)
            for tool in env.tools.values():
                print("Setting up tool")
                tool.setup({
                    "environment" : env,
                    "session" : self,
                    "state" : self.state,
                })

        # get_or_create_repo(
        #     self.default_environment,
        #     self.base_path,
        # )
        self.original_branch = self.default_environment.execute("git branch --show-current")[0]
        self.agent_branch = self.agent_branch + "-" + self.original_branch + "-" + str(random.randint(0, 1000))
        make_new_branch(self.default_environment, self.agent_branch)
        stash_and_commit_changes(self.default_environment, self.agent_branch,"test")

        # base_diff = get_current_diff(self.default_environment)
        # print(base_diff,file=open("base_diff.txt", "w"))
        

        self.telemetry_client.capture(SessionStartEvent(self.name))
        

    def exit(self):

        self.default_environment.execute("git checkout " + self.original_branch)

        for env in self.environments.values():
            env.teardown()
            for tool in env.tools.values():
                tool.setup({
                    "environment" : env,
                    "session" : self,
                    "state" : self.state,
                })

        
