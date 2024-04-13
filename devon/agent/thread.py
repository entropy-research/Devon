from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any, List, Optional, Tuple, Dict
from devon.agent.model import AnthropicModel, HumanModel, ModelArguments
from devon.agent.history_processors import HistoryProcessor, DefaultHistoryProcessor
from devon.environment.environment import Environment
from tenacity import RetryError
from devon.agent.prompt import commands_to_command_docs, editor_repr, history_to_bash_history, last_user_prompt_template, object_to_xml, print_tree, system_prompt_template, user_prompt_template, system_prompt
from devon.agent.prompt import parse_response
from simple_parsing.helpers import field, FrozenSerializable, FlattenedAccess

from devon.swebenchenv.environment.swe_env import SWEEnv

"""
    system_template: str
    instance_template: str
    next_step_template: Optional[str] = None  # defaults to instance_template
    next_step_no_output_template: Optional[str] = None  # defaults to next_step_template
    strategy_template: Optional[str] = None
    demonstration_template: Optional[str] = None
    demonstrations: list[str] = field(default_factory=list)
    put_demos_in_history: bool = False  # if True, add demonstration to history instead of as a single message
    format_error_template: str = None # defaults to format_error_template in ParseFunction
    command_files: list[str] = field(default_factory=list)
    env_variables: dict[str, str] = field(default_factory=dict)
    util_functions: list[str] = field(default_factory=list)

        blocklist: Tuple[str] = (
        "vim",
        "vi",
        "emacs",
        "nano",
        "nohup",
        "git",
    )
    blocklist_standalone: Tuple[str] = (
        "python",
        "python3",
        "ipython",
        "bash",
        "sh",
        "exit",
        "/bin/bash",
        "/bin/sh",
        "nohup",
        "vi",
        "vim",
        "emacs",
        "nano",
    )

"""

@dataclass(frozen=True)
class AgentConfig(FrozenSerializable):

    submit_command: str = "submit"
    parse_function: str = "ThoughtActionParser"
    parse_command: str = "ParseCommandBash"
    history_processor: str = "DefaultHistoryProcessor"
    history_processor_args: dict[str, Any] = field(default_factory=dict)
    command_docs: str = None
    blocklist_error_template: str = "Interactive operation '{name}' is not supported by this environment"

    # TO REFACTOR
    # state_command: Command = Command(
    #     name="state",
    #     code="""state() {
    #         echo '{"working_dir": "'$(realpath --relative-to=$ROOT/.. $PWD)'"}';
    #     };""",
    # )

    # TO REFACTOR
    # _commands: list[Command] = field(default_factory=list)


    # def __post_init__(self):
    #     # if self.next_step_template is None:
    #     #     object.__setattr__(self, "next_step_template", self.instance_template)
    #     # if self.next_step_no_output_template is None:
    #     #     object.__setattr__(
    #     #         self, "next_step_no_output_template", self.next_step_template
    #     #     )

    #     # object.__setattr__(self, "parse_command", ParseCommand.get(self.parse_command))
    #     for file in self.command_files:
    #         commands = self.parse_command.parse_command_file(file)

    #         util_functions = [
    #             command for command in commands if command.name.startswith("_")
    #         ]
    #         commands = [
    #             command for command in commands if not command.name.startswith("_")
    #         ]

    #         object.__setattr__(
    #             self, "util_functions", self.util_functions + util_functions
    #         )
    #         object.__setattr__(self, "_commands", self._commands + commands)
        
    #     for subroutine in self.subroutine_types:
    #         if subroutine.name == 'submit':
    #             raise ValueError("Cannot use 'submit' as a subroutine name")
    #         agent_args = AgentArguments(
    #             model=subroutine.model,
    #             config_file=subroutine.agent_file,
    #             )
    #         object.__setattr__(subroutine, "agent_args", agent_args)
    #         object.__setattr__(self, "_subroutines", {**self._subroutines, subroutine.name: subroutine})

    #     multi_line_command_endings = {
    #         command.name: command.end_name
    #         for command in [*self._commands, *self._subroutines.values()]
    #         if command.end_name is not None
    #     }
    #     object.__setattr__(self, "multi_line_command_endings", multi_line_command_endings)
    #     object.__setattr__(
    #         self,
    #         "command_docs",
    #         self.parse_command.generate_command_docs(
    #             self._commands,
    #             self.subroutine_types,
    #             **self.env_variables,
    #             ),
    #         )
    #     # object.__setattr__(self, "parse_function", ParseFunction.get(self.parse_function))
    #     if self.format_error_template is None:
    #         object.__setattr__(
    #             self,
    #             "format_error_template",
    #             self.parse_function.format_error_template,
    #             )
    #     object.__setattr__(self, "format_error_template", self.format_error_template.format(**self.__dict__))
    #     for command in self._commands:
    #         if command.name == self.submit_command:
    #             object.__setattr__(self, "submit_command_end_name", command.end_name)
    #             break
    #     object.__setattr__(
    #         self, "history_processor",
    #         HistoryProcessor.get(self.history_processor, **self.history_processor_args)
    #         )

@dataclass(frozen=True)
class AgentArguments(FlattenedAccess, FrozenSerializable):
    model: ModelArguments = None

    config: Optional[AgentConfig] = field(default=None, cmd=False)

    def __post_init__(self):
        if self.config is None and self.config_file is not None:
            # If unassigned, we load the config from the file to store its contents with the overall arguments
            config = AgentConfig.load_yaml(self.config_file)
            object.__setattr__(self, "config", config)
        assert self.config is not None


class Agent:

    def __init__(self, name="Devon",args=None):
        self.model : AnthropicModel = AnthropicModel(args=ModelArguments(
            model_name="claude-opus",
            temperature=0.5
        ))
        # self.model = HumanModel(args=ModelArguments(
        #     model_name="gpt-4-0314",
        #     # total_cost_limit=0.0,
        #     # per_instance_cost_limit=2.0,
        #     temperature=0.5,
        #     top_p=0.95
        # ))
        self.name = name
        self.history = []
        self.max_steps = 10

    def forward_with_error_check(self, observation: str, state: str, avaliable_actions: list[str], commanddoc: dict) -> Tuple[str, str, str]:
        try:


            output = self.forward_model(observation, state,avaliable_actions, commanddoc)
        except KeyboardInterrupt:
            raise
        except RuntimeError as e:
            print(f"Runtime error: {e}")
            return (
                f"Exit due to runtime error: {e}",
                "exit_error",
                f"exit due to runtime error: {e}",
            )
        except RetryError as e:
            print(f"Retry error: {e}")
            return (
                f"Exit due to retry error: {e}",
                "exit_api",
                f"exit due to retry error: {e}",
            )

        try:
            thought, action = parse_response(output)
        except Exception as e:
            raise ValueError(f"Multiple actions found in response: {output}")

        return thought, action, output
    
    def forward_model(self, observation: str, state: Dict[str,str],available_actions,commanddoc: dict) -> str:
        """Query the model with the current state and observation with the appropriate template.

        Returns the model output."""

        # REPLACE WITH OUR PROMPT TEMPLATES
        f_tree = state["file_tree"]

        issue,filetree,editor,working_dir = state["issue"],json.dumps(f_tree),json.dumps(state["editor"]),state["cwd"]

        # print("FILE TREE",f_tree)

        self.history.append({"role": "user", "content": observation, "agent": self.name})

        commands = "Avaliable Custom Commands:\n" + "\n".join([f"{command}" for command in available_actions]) + "\n"
        command_docs = "Custom Commands Documentation:\n" + commands_to_command_docs(list(commanddoc.values())) + "\n"

        system_prompt = system_prompt_template(commands + command_docs)

        # print(editor)

        history = history_to_bash_history(self.history)

        last_user_prompt = last_user_prompt_template(issue,history,filetree,editor,working_dir)

        messages = [{"role": "user", "content": last_user_prompt}]
        # print("OBSERVATION",observation)
        return self.model.query(messages, system_message=system_prompt)

    def forward(self, observation: str, available_actions: list[str], state: dict,commanddoc: dict) -> Tuple[str, str, str]:
        thought, action, output = self.forward_with_error_check(
                observation, 
                state,
                available_actions,
                commanddoc
            )

        self.history.append(
            {
                "role": "assistant",
                "content": output,
                "thought": thought,
                "action": action,
                "agent": self.name,
                "state": state,
            }
        )
        print(f"OBSERVATION ({self.name})\n{observation}")
        print(f"THOUGHT ({self.name})\n{thought}")
        print(f"ACTION ({self.name})\n{action}")
        # print(f"RESULT ({self.name})\n{output}")

        return thought, action, output

    def run(
            self,
            setup_args,
            env: SWEEnv,
            observation: str = None,
            traj_dir: Optional[Path] = None,
            return_type: Optional[str] = "info",
            init_model_stats = None
        ):

        # print(env.get_available_actions())
        # Run action/observation loop

        available_actions = env.get_available_actions()
        commanddoc = env.generate_command_docs()

        commands = "Avaliable Custom Commands:\n" + "\n".join([f"{command}" for command in available_actions]) + "\n"
        command_docs = "Custom Commands Documentation:\n" + commands_to_command_docs(list(commanddoc.values())) + "\n"

        system_prompt = system_prompt_template(commands + command_docs)
        self.history.append({
            "role":"system",
            "content": system_prompt
        })
        trajectory = []
        info = {}
        done = False
        for i in range(self.max_steps):

            if done:
                break

            #state = Get state
            state = env.get_state()
            state["issue"] = setup_args["issue"]
            thought, action, output = self.forward(
                observation,
                env.get_available_actions(),
                state,
                env.generate_command_docs()
            )

            observations = list()
            if action == "exit":
                done = True
            obs, _, done, info = env.step(action, thought)
            print(info)
            observations.append(obs)

            print(action.strip())
            if action.strip() == "submit":
                done = True

            observation = '\n'.join([json.dumps(obs) for obs in observations if obs is not None])

            # print("EDITOR",env.virtual_filesystem)
            trajectory.append(
                {
                    "action": action,
                    "observation": observation,
                    "response": output,
                    "state": state,
                    "thought": thought,
                }
            )

        self.history = []
        print(info)
        return info

if __name__ == "__main__":
    agent = Agent()
    env = Environment(path=".")
    agent.run({}, env)

    