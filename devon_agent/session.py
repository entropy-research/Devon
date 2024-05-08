import inspect
import json
import logging
import traceback
from dataclasses import dataclass
from typing import Any, List
from devon_agent.agent import TaskAgent
from devon_agent.environment import LocalEnvironment
from devon_agent.tools import (
    ask_user,
    close_file,
    create_file,
    delete_file,
    edit_file,
    exit,
    extract_signature_and_docstring,
    find_class,
    find_file,
    find_function,
    get_cwd,
    list_dirs_recursive,
    no_op,
    open_file,
    parse_command,
    real_write_diff,
    scroll_down,
    scroll_to_line,
    scroll_up,
    search_dir,
    search_file,
    submit,
)
from devon_agent.utils import DotDict, Event


@dataclass(frozen=False)
class SessionArguments:
    path: str
    environment: str
    user_input: Any


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
        self.event_index = 0
        self.get_user_input = args.user_input

        self.state.editor = {}

        self.path = args.path
        self.environment_type = args.environment

        if args.environment == "local":
            self.environment = LocalEnvironment(args.path)
        else:
            raise ValueError("Unknown environment type")

        self.tools = [
            list_dirs_recursive,
            close_file,
            create_file,
            open_file,
            search_dir,
            find_function,
            find_class,
            search_file,
            get_cwd,
            delete_file,
            submit,
            no_op,
            scroll_up,
            scroll_down,
            scroll_to_line,
            find_file,
            ask_user,
            exit,
            edit_file,
        ]

    def to_dict(self):
        return {
            "path": self.path,
            "environment": self.environment_type,
            "event_history": [event for event in self.event_log],
            "state": self.state.to_dict(),
            "cwd": self.environment.get_cwd(),
            "agent": {
                "name": self.agent.name,
                "model": self.agent.model,
                "temperature": self.agent.temperature,
                "chat_history": self.agent.chat_history,
            },
        }

    @classmethod
    def from_dict(cls, data):
        instance = cls(
            args=SessionArguments(
                path=data["path"],
                environment=data["environment"],
                user_input=data["user_input"],
            ),
            agent=TaskAgent(
                name=data["agent"]["name"],
                model=data["agent"]["model"],
                temperature=data["agent"]["temperature"],
                chat_history=data["agent"]["chat_history"],
            ),
        )

        instance.state = DotDict(data["state"])
        instance.state.editor = {}
        instance.event_log = data["event_history"]
        instance.environment.communicate("cd " + data["cwd"])

        return instance

    def step(self, action: str, thought: str) -> tuple[str, bool]:
        # parse command
        # run command/tool
        # return reponse as observation

        if action == "exit":
            return "Exited task", True

        try:
            return self.parse_command_to_function(command_string=action)
        except Exception as e:
            return e.args[0], False

    def get_last_task(self):
        for event in self.event_log[::-1]:
            if event["type"] == "Task":
                return event["content"]
        return "Task unspecified ask user to specify task"

    def step_event(self):
        if self.event_index == len(self.event_log):
            return "No more events to process", True
        event = self.event_log[self.event_index]
        self.logger.info(f"Event: {event}")
        self.logger.info(f"State: {self.state.editor}")

        if event["type"] == "ModelRequest":
            thought, action, output = self.agent.predict(
                self.get_last_task(), event["content"], self
            )
            self.event_log.append(
                {
                    "type": "ModelResponse",
                    "content": json.dumps(
                        {"thought": thought, "action": action, "output": output}
                    ),
                    "producer": self.agent.name,
                    "consumer": event["producer"],
                }
            )

        if event["type"] == "ToolRequest":
            tool_name, args = parse_command(self, event["content"])

            if tool_name == "ask_user":
                self.event_log.append(
                    {
                        "type": "UserRequest",
                        "content": args[0],
                        "producer": event["producer"],
                        "consumer": "user",
                    }
                )
            elif tool_name in ["submit", "exit", "stop"]:
                self.event_log.append(
                    {
                        "type": "Stop",
                        "content": "Stopped task",
                        "producer": event["producer"],
                        "consumer": "user",
                    }
                )
            elif tool_name == "set_task":
                self.event_log.append(
                    {
                        "type": "Task",
                        "content": args[0],
                        "producer": event["producer"],
                        "consumer": self.agent.name,
                    }
                )
            elif tool_name == "send_message":
                self.event_log.append(
                    {
                        "type": "ModelRequest",
                        "content": args[1],
                        "producer": event["producer"],
                        "consumer": args[0],
                    }
                )

            else:
                output, done = self.parse_command_to_function(
                    command_string=event["content"]
                )
                self.event_log.append(
                    {
                        "type": "EnvironmentRequest",
                        "content": event["content"],
                        "producer": event["producer"],
                        "consumer": self.environment.__class__.__name__,
                    }
                )
                self.event_log.append(
                    {
                        "type": "EnvironmentResponse",
                        "content": output,
                        "producer": self.environment.__class__.__name__,
                        "consumer": event["consumer"],
                    }
                )
                self.event_log.append(
                    {
                        "type": "ToolResponse",
                        "content": output,
                        "producer": self.environment.__class__.__name__,
                        "consumer": event["consumer"],
                    }
                )

        if event["type"] == "EnvironmentRequest":
            pass

        if event["type"] == "EnvironmentResponse":
            pass

        if event["type"] == "ToolResponse":
            self.event_log.append(
                {
                    "type": "ModelRequest",
                    "content": event["content"],
                    "producer": event["producer"],
                    "consumer": event["consumer"],
                }
            )

        if event["type"] == "ModelResponse":
            content = json.loads(event["content"])["action"]
            self.event_log.append(
                {
                    "type": "ToolRequest",
                    "content": content,
                    "producer": event["producer"],
                    "consumer": event["consumer"],
                }
            )

        if event["type"] == "UserRequest":
            user_input = self.get_user_input()
            if user_input is None:
                self.logger.info("No user input provided")
                self.event_log.append(
                    {
                        "type": "Stop",
                        "content": "No user input provided",
                        "producer": "user",
                        "consumer": event["consumer"],
                    }
                )
                return "No user input provided", True

            self.event_log.append(
                {
                    "type": "UserResponse",
                    "content": user_input,
                    "producer": "user",
                    "consumer": event["producer"],
                }
            )
            self.event_log.append(
                {
                    "type": "ToolResponse",
                    "content": user_input,
                    "producer": "user",
                    "consumer": event["producer"],
                }
            )

        if event["type"] == "Interrupt":
            if self.agent.interrupt:
                self.agent.interrupt += (
                    "You have been interrupted, pay attention to this message "
                    + event["content"]
                )
            else:
                self.agent.interrupt = event["content"]

        if event["type"] == "Stop":
            return "Stopped task", True

        if event["type"] == "Task":
            task = event["content"]
            self.logger.info(f"Task: {task}")
            if task is None:
                task = "Task unspecified ask user to specify task"

            self.event_log.append(
                {
                    "type": "ModelRequest",
                    "content": "",
                    "producer": event["producer"],
                    "consumer": event["consumer"],
                }
            )

        self.event_index += 1
        return self.step_event()

    def parse_command_to_function(self, command_string) -> tuple[str, bool]:
        """
        Parses a command string into its function name and arguments.
        """
        ctx = self

        fn_name, args = parse_command(ctx, command_string)
        if fn_name in ["vim", "nano"]:
            return "Interactive Commands are not allowed", False

        if (
            fn_name == "python"
            and len([line for line in command_string.splitlines() if line]) != 1
        ):
            return "Interactive Commands are not allowed", False

        fn_names = [fn.__name__ for fn in self.tools]

        try:
            if fn_name == "edit_file":
                try:
                    return real_write_diff(self, command_string), False
                except Exception as e:
                    ctx.logger.error(traceback.print_exc())
                    raise e
            elif fn_name in fn_names:
                for fn in self.tools:
                    if fn.__name__ == fn_name:
                        return fn(ctx, *args), False
            else:
                try:
                    output, rc = ctx.environment.communicate(
                        fn_name + " " + " ".join(args)
                    )
                    if rc != 0:
                        raise Exception(output)
                    return output, False
                except Exception as e:
                    ctx.logger.error(
                        f"Failed to execute bash command '{fn_name}': {str(e)}"
                    )
                    return "Failed to execute bash command", False
        except Exception as e:
            ctx.logger.error(traceback.print_exc())
            return e.args[0], False

    def get_available_actions(self) -> list[str]:
        return [fn.__name__ for fn in self.tools]

    def generate_command_docs(self):
        """
        Generates a dictionary of function names and their docstrings.
        """

        funcs = self.tools
        docs = {}

        for func in funcs:
            name = func.__name__
            code = inspect.getsource(func)
            sig, docstring = extract_signature_and_docstring(code)
            docs[name] = {"signature": sig, "docstring": docstring}

        return docs

    def enter(self):
        self.environment.enter()

    def exit(self):
        self.environment.exit()
