import json
import logging
from pathlib import Path
from typing import Optional, Tuple, Dict
from devon.agent.model import AnthropicModel, ModelArguments
from tenacity import RetryError
from devon.agent.prompt import (
    commands_to_command_docs,
    history_to_bash_history,
    last_user_prompt_template_v1,
    system_prompt_template_v1,
)
from devon.agent.prompt import parse_response


from devon.swebenchenv.environment.swe_env import SWEEnv
from devon.swebenchenv.environment.utils import LOGGER_NAME


logger = logging.getLogger(LOGGER_NAME)


class Agent:
    def __init__(self, name="Devon", args=None):
        self.model: AnthropicModel = AnthropicModel(
            args=ModelArguments(model_name="claude-sonnet", temperature=1)
        )
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

    def forward_with_error_check(
        self,
        observation: str,
        state: str,
        avaliable_actions: list[str],
        commanddoc: dict,
    ) -> Tuple[str, str, str]:
        try:
            output = self.forward_model(
                observation, state, avaliable_actions, commanddoc
            )
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
        except Exception:
            raise ValueError(f"Multiple actions found in response: {output}")

        return thought, action, output

    def forward_model(
        self,
        observation: str,
        state: Dict[str, str],
        available_actions,
        commanddoc: dict,
    ) -> str:
        """Query the model with the current state and observation with the appropriate template.

        Returns the model output."""

        # REPLACE WITH OUR PROMPT TEMPLATES
        f_tree = state["file_tree"]
        logger.debug("EDITOR %s", state["editor"])

        issue, filetree, editor, working_dir = (
            state["issue"],
            json.dumps(f_tree),
            json.dumps(state["editor"]),
            state["cwd"],
        )

        self.history.append(
            {"role": "user", "content": observation, "agent": self.name}
        )

        commands = (
            "Avaliable Custom Commands:\n"
            + "\n".join([f"{command}" for command in available_actions])
            + "\n"
        )
        command_docs = (
            "Custom Commands Documentation:\n"
            + commands_to_command_docs(list(commanddoc.values()))
            + "\n"
        )

        system_prompt = system_prompt_template_v1(commands + command_docs)

        history = history_to_bash_history(self.history)

        last_user_prompt = last_user_prompt_template_v1(
            issue, history, filetree, editor, working_dir
        )

        messages = [{"role": "user", "content": last_user_prompt}]

        return self.model.query(messages, system_message=system_prompt)

    def forward(
        self,
        observation: str,
        available_actions: list[str],
        state: dict,
        commanddoc: dict,
    ) -> Tuple[str, str, str]:
        thought, action, output = self.forward_with_error_check(
            observation, state, available_actions, commanddoc
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
        logger.info(f"OBSERVATION ({self.name})\n{observation}")
        logger.info(f"THOUGHT ({self.name})\n{thought}")
        logger.info(f"ACTION ({self.name})\n{action}")

        return thought, action, output

    def save_trajectory(self, trajectory, traj_dir, env, info):
        log_path = traj_dir / (env.record["instance_id"] + ".traj")
        log_dict = {
            "environment": env.name,
            "trajectory": trajectory,
            "history": [],
            "info": info,
        }
        with log_path.open("w") as f:
            json.dump(log_dict, f, indent=2)
        logger.info(f"Saved trajectory to {log_path}")

    def run(
        self,
        setup_args,
        env: SWEEnv,
        observation: str = None,
        traj_dir: Optional[Path] = None,
        return_type: Optional[str] = "info",
        init_model_stats=None,
    ):
        available_actions = env.get_available_actions()
        commanddoc = env.generate_command_docs()

        commands = (
            "Avaliable Custom Commands:\n"
            + "\n".join([f"{command}" for command in available_actions])
            + "\n"
        )
        command_docs = (
            "Custom Commands Documentation:\n"
            + commands_to_command_docs(list(commanddoc.values()))
            + "\n"
        )

        system_prompt = system_prompt_template_v1(commands + command_docs)
        self.history.append({"role": "system", "content": system_prompt})
        trajectory = []
        info = {}
        done = False
        for i in range(self.max_steps):
            if done:
                break

            # state = Get state
            state = env.get_state()
            state["issue"] = setup_args["issue"]
            thought, action, output = self.forward(
                observation,
                env.get_available_actions(),
                state,
                env.generate_command_docs(),
            )

            observations = list()
            if action == "exit":
                done = True

            try:
                # assert output.count("<COMMAND>") == 1
                # assert output.count("<THOUGHT>") == 1
                obs, _, done, info = env.step(action, thought)
            except AssertionError as e:
                print(output)
                print(e)
                obs = "Too many commands in previous output, could not execute. Please remember to only pass one command."

            observations.append(obs)

            if action.strip() == "submit":
                done = True

            observation = "\n".join(
                [json.dumps(obs) for obs in observations if obs is not None]
            )

            trajectory.append(
                {
                    "action": action,
                    "observation": observation,
                    "response": output,
                    "state": state,
                    "thought": thought,
                }
            )

        if not done:
            # sumbit the last thing
            action = "submit"
            _, _, done, info = env.step(action, thought)

        self.history = []

        #  save trajectory as jsonl
        self.save_trajectory(trajectory, traj_dir, env, info)

        logger.debug(info)
        return info

