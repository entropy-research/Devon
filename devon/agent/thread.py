from datetime import datetime
import json
import logging
from pathlib import Path
import random
from typing import Optional, Tuple, Dict
from devon.agent.model import AnthropicModel, ModelArguments
from tenacity import RetryError
from devon.agent.prompt import (
    commands_to_command_docs,
    history_to_bash_history,
    last_user_prompt_template_v1,
    last_user_prompt_template_v2,
    last_user_prompt_template_v3,
    system_prompt_template_v1,
    system_prompt_template_v2,
    system_prompt_template_v3,
)
from devon.agent.prompt import parse_response


from devon.swebenchenv.environment.swe_env import SWEEnv
from devon.swebenchenv.environment.utils import LOGGER_NAME


logger = logging.getLogger(LOGGER_NAME)


class Agent:
    def __init__(self, name="Devon", args=None):
        self.sonnet: AnthropicModel = AnthropicModel(
            args=ModelArguments(model_name="claude-sonnet", temperature=0.5)
        )
        self.opus: AnthropicModel = AnthropicModel(
            args=ModelArguments(model_name="claude-opus", temperature=0.0)
        )
        self.default_model = self.opus
        self.current_model = self.opus
        # self.model = HumanModel(args=ModelArguments(
        #     model_name="gpt-4-0314",
        #     # total_cost_limit=0.0,
        #     # per_instance_cost_limit=2.0,
        #     temperature=0.5,
        #     top_p=0.95
        # ))

        self.name = name
        self.history = []
        self.max_steps = 15

    def forward_model(
        self,
        observation: str,
        state: Dict[str, str],
        available_actions,
        commanddoc: dict,
        step: int
    ) -> str:
        """Query the model with the current state and observation with the appropriate template.

        Returns the model output."""

        issue, editor, working_dir = (
            state["issue"],
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

        system_prompt = system_prompt_template_v3(commands + command_docs)

        history = history_to_bash_history(self.history)

        last_user_prompt = last_user_prompt_template_v3(
            issue, history, editor, working_dir
        )

        messages = [{"role": "user", "content": last_user_prompt}]

        output = self.current_model.query(messages, system_message=system_prompt)

        logger.debug("<MODEL_OUT>" + json.dumps({
            "step": step, 
            "input": messages[0],
            "output": output
        }) + "<MODEL_OUT>")

        return output

    def forward_with_error_check(
        self,
        observation: str,
        state: str,
        avaliable_actions: list[str],
        commanddoc: dict,
        step: int
    ) -> Tuple[str, str, str]:
        try:
            output = self.forward_model(
                observation, state, avaliable_actions, commanddoc, step
            )
        except KeyboardInterrupt:
            raise
        except RuntimeError as e:
            logger.error(f"Runtime error: {e}")
            return (
                f"Exit due to runtime error: {e}",
                "exit_error",
                f"exit due to runtime error: {e}",
            )
        except RetryError as e:
            logger.error(f"Retry error: {e}")
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

    def forward(
        self,
        observation: str,
        available_actions: list[str],
        state: dict,
        commanddoc: dict,
        step: int
    ) -> Tuple[str, str, str]:
        thought, action, output = self.forward_with_error_check(
            observation, state, available_actions, commanddoc, step
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

        return thought, action, output

    def save_trajectory(self, trajectory, traj_dir, env, info, run_id):
        log_path = traj_dir / (str(run_id) + ".traj")
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
        self.history = []

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

        system_prompt = system_prompt_template_v3(commands + command_docs)
        self.history.append({"role": "system", "content": system_prompt})
        trajectory = []
        info = {}
        run_id = hash(str(datetime.now()))
        done = False
        for i in range(self.max_steps):

            if done:
                break

            state = env.get_state()
            state["issue"] = setup_args["issue"]

            thought, action, output = self.forward(
                observation,
                env.get_available_actions(),
                state,
                env.generate_command_docs(),
                i
            )

            observations = list()
            if action == "exit":
                done = True

            if action == "no_op" and self.current_model == self.sonnet:
                self.current_model = self.opus
            else:
                self.current_model = self.default_model

            try:
                # assert output.count("<COMMAND>") == 1
                # assert output.count("<THOUGHT>") == 1
                obs, _, done, info = env.step(action, thought)
            except AssertionError as e:
                # logger.error(output)
                # logger.error(e)
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

            logger.info(f"""
\n\n\n\n****************\n\n
NAME: {self.name}                        

STEP: {i}

THOUGHT: {thought}

ACTION: {action}

OBSERVATION: {observation}
\n\n****************\n\n\n\n"""
            )

        if not done:
            # sumbit the last thing
            action = "submit"
            _, _, done, info = env.step(action, thought)

        self.history = []

        #  save trajectory as jsonl
        self.save_trajectory(trajectory, traj_dir, env, info, env.record["instance_id"])

        logger.debug(info)
        return info

