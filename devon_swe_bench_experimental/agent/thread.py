from datetime import datetime
import json
import logging
from pathlib import Path
import random
from typing import Optional, Tuple, Dict
from devon_swe_bench_experimental.agent.model import AnthropicModel, HumanModel, ModelArguments
from tenacity import RetryError
from devon_swe_bench_experimental.agent.prompt import (
    commands_to_command_docs,
    history_to_bash_history,
    last_user_prompt_template_v1,
    last_user_prompt_template_v2,
    last_user_prompt_template_v3,
    system_prompt_template_v1,
    system_prompt_template_v2,
    system_prompt_template_v3,
)
from devon_swe_bench_experimental.agent.prompt import parse_response


from devon_swe_bench_experimental.swebenchenv.environment.swe_env import SWEEnv
from devon_swe_bench_experimental.swebenchenv.environment.utils import LOGGER_NAME


logger = logging.getLogger(LOGGER_NAME)


class Agent:
    def __init__(self, name="Devon", args=None, model="claude-opus", temperature=0.0):
        self.sonnet: AnthropicModel = AnthropicModel(
            args=ModelArguments(model_name="claude-sonnet", temperature=1)
        )
        self.opus: AnthropicModel = AnthropicModel(
            args=ModelArguments(model_name="claude-opus", temperature=temperature)
        )
        self.default_model = self.opus
        self.current_model = self.opus
        # self.default_model = HumanModel(args=ModelArguments(
        #     model_name="gpt-4-0314",
        #     # total_cost_limit=0.0,
        #     # per_instance_cost_limit=2.0,
        #     temperature=0.5,
        #     top_p=0.95
        # ))
        # self.current_model = self.default_model

        self.name = name
        self.history = []
        self.max_steps = 15

    def _format_editor_entry(self, k, v):

        path = k
        page = v["page"]
        content_lines = v["lines"].splitlines()

        all_lines_len = len(content_lines)
        last_idx = all_lines_len // self.PAGE_SIZE
        if page == last_idx:
            content_len = all_lines_len % self.PAGE_SIZE
        else:
            content_len = self.PAGE_SIZE

        start_idx = page * self.PAGE_SIZE
        lines = content_lines[start_idx:start_idx+content_len]
        window_lines = "\n".join([str(i + start_idx).zfill(4) + line for i, line in enumerate(lines)])

        return f"""
************ FILE: {path}, WINDOW STARTLINE: {start_idx}, WINDOW ENDLINE: {start_idx+content_len}, TOTAL FILE LINES: {all_lines_len} ************
{window_lines}
************************************
"""

    def _convert_editor_to_view(self, editor):
        result = []

        for k, v in editor.items():

            result.append(self._format_editor_entry(k, v))
        
        return "\n".join(result)

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
            self._convert_editor_to_view(state["editor"]),
            state["file_root"],
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
        # print("HISTORY: ", history)
        last_user_prompt = last_user_prompt_template_v3(
            issue, history, editor, working_dir
        )

        messages = [{"role": "user", "content": last_user_prompt}]
        # print(system_prompt)
        # print(last_user_prompt)

        print("requesting model")
        output = self.current_model.query(messages, system_message=system_prompt)
        print("received model output")

        print(output)

        logger.debug("<MODEL_OUT>" + json.dumps({
            "step": step, 
            "input": messages[0],
            "output": output
        }) + "<MODEL_OUT>")

        try:
            thought, action = parse_response(output)
        except Exception:
            raise ValueError(f"Multiple actions found in response: {output}")

        last_observation = None
        second_last_observation = None
        if len(self.history) > 2:
            last_observation = self.history[-1]["content"]
            second_last_observation = self.history[-2]["content"]
            third_last_observation = self.history[-3]["content"]
        if last_observation and second_last_observation and "Failed to edit file" in last_observation and ("Failed to edit file" in second_last_observation or "Failed to edit file" in third_last_observation):
            self.history = self.history[:-6]

            thought = """
I need to stop and consider why my edits are not applying. I think I may have incorrectly written out the source lines and that may be the cause of the failures.

In order to move forward, I am going to look at the lines exactly, and then only make one change.
I know that if I make more than one change at a time it might cause me to incorrectly read the lines and that will make the user's patch tool fail.

I can also try to reduce the number of source lines I am changing so that I have an easier time matching them.

I am only going to make one change at a time.

I will take a deep breath and methodically make a sequence of changes.
"""
            action = "no_op"

        return thought, action, output

    def forward_with_error_check(
        self,
        observation: str,
        state: str,
        avaliable_actions: list[str],
        commanddoc: dict,
        step: int
    ) -> Tuple[str, str, str]:
        try:
            thought, action, output = self.forward_model(
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
        print("Running agent")
        available_actions = env.get_available_actions()
        commanddoc = env.generate_command_docs()
        self.history = []
        self.PAGE_SIZE = env.PAGE_SIZE

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
                self.current_model = self.current_model
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
                    "state": repr(state),
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

        if self.max_steps == 0:
            _,_,done,info = env.step("submit","im done")

        if not done:
            # sumbit the last thing
            action = "submit"
            _, _, done, info = env.step(action, thought)

        self.history = []

        #  save trajectory as jsonl
        self.save_trajectory(trajectory, traj_dir, env, info, env.record["instance_id"])

        logger.debug(info)
        return info
