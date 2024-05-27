import asyncio
import inspect
import json
import logging
import os
import random
import traceback
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from sqlalchemy import create_engine, text
from devon_agent.agents.default.agent import TaskAgent
from devon_agent.environment import EnvironmentModule, LocalEnvironment, UserEnvironment
from devon_agent.models import _save_data, _save_session_util, get_async_session, save_data
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
from devon_agent.tools.usertools import AskUserTool, SetTaskTool

from devon_agent.utils import DotDict, Event
from devon_agent.vgit import  get_current_diff, get_last_commit, get_or_create_repo, make_new_branch, safely_revert_to_commit, stash_and_commit_changes, subtract_diffs


@dataclass(frozen=False)
class SessionArguments:
    path: str
    # environments: List[str]
    user_input: Any
    name: str
    task: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    headless: Optional[bool] = False


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





class Session:
    def __init__(self, args: SessionArguments, agent):
        logger = logging.getLogger(__name__)

        self.state = DotDict({})
        self.state.PAGE_SIZE = 200
        self.logger = logger
        self.agent: TaskAgent = agent
        self.base_path = args.path
        self.event_log: List[Event] = []
        self.get_user_input = args.user_input
        self.telemetry_client = Posthog()
        self.name = args.name
        self.agent_branch = "devon_agent_" + self.name
        self.global_config = args.config
        self.excludes = self.global_config["excludes"] if self.global_config else []

        local_environment = LocalEnvironment(args.path)
        local_environment.register_tools({
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
        local_environment.set_default_tool(ShellTool())
        self.default_environment = local_environment

        if args.headless:
            self.task = args.headless

            self.environments = {
                "local" : local_environment
            }
        else:
            self.task = args.task
            user_environment = UserEnvironment(args.user_input)
            user_environment.register_tools({
                "ask_user" : AskUserTool(),
                "set_task" : SetTaskTool()
            })

            self.environments = {
                "local" : local_environment,
                "user" : user_environment,
            }

        self.path = args.path
        self.base_path = args.path
        self.event_id = 0

    def to_dict(self):
        return {
            "task": self.task,
            "path": self.path,
            "name": self.name,
            "config": self.global_config,
            "event_history": [event for event in self.event_log],
            "cwd": self.environments["local"].get_cwd(),
            "agent": {
                "name": self.agent.name,
                "model": self.agent.model,
                "temperature": self.agent.temperature,
                "chat_history": self.agent.chat_history,
            },
        }

    @classmethod
    def from_dict(cls, data, user_input, config):
        print(data)
        instance = cls(
            args=SessionArguments(
                path=data["path"],
                # environment=data["environment"],
                user_input=user_input,
                name=data["name"],
                task=data["task"] if "task" in data else None,
                config=config,
            ),
            agent=TaskAgent(
                name=data["agent"]["name"],
                model=config["modelName"],
                temperature=data["agent"]["temperature"],
                chat_history=data["agent"]["chat_history"],
            )
        )

        # instance.state = DotDict(data["state"])
        instance.state = DotDict({})
        instance.state.editor = {}
        instance.event_log = data["event_history"]
        instance.event_id = len(data["event_history"])

        # instance.environments["local"].communicate("cd " + data["cwd"])

        return instance

    def get_last_task(self):
        if self.task:
            return self.task
        return "Task unspecified ask user to specify task"
    
    def run_event_loop(self):
        while True and not (self.event_id == len(self.event_log)):

            event = self.event_log[self.event_id]

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

            self.event_id += 1


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

            case "GitRequest" :
                if event["content"]["type"] == "revert_to_commit":
                    
                    safely_revert_to_commit(self.default_environment, event["content"]["commit_to_revert"], event["content"]["commit_to_go_to"])

            case "ModelRequest":

                #Need some quantized timestep for saving persistence that isn't literally every 0.1s

                asyncio.run(_save_session_util(self.name, self.to_dict()))
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

        self.event_log.append({
            "type": "GitEvent",
            "content" : {
                "commit" : get_last_commit(self.default_environment),
                "files" : [],
            }
        })

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

