import json
import logging
from dataclasses import dataclass, field
from typing import Optional, Tuple

from devon_agent.model import AnthropicModel, ModelArguments
from devon_agent.prompt import (
    commands_to_command_docs,
    history_to_bash_history,
    last_user_prompt_template_v3,
    parse_response,
    system_prompt_template_v3,
)

from devon_agent.utils import LOGGER_NAME
from tenacity import RetryError

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from devon_agent.session import Session

# from devon.environment.cli import ChatEnvironment


logger = logging.getLogger(LOGGER_NAME)


@dataclass(frozen=False)
class Agent:
    name: str
    model: str
    temperature: float = 0.0
    chat_history: list[dict[str, str]] = field(default_factory=list)
    interrupt: str = ""
    api_key: Optional[str] = None

    def run(self, session: "Session", observation: str = None): ...


class TaskAgent(Agent):
    def _format_editor_entry(self, k, v, PAGE_SIZE=50):
        path = k
        page = v["page"]
        content_lines = v["lines"].splitlines()

        all_lines_len = len(content_lines)
        last_idx = all_lines_len // PAGE_SIZE
        if page == last_idx:
            content_len = all_lines_len % PAGE_SIZE
        else:
            content_len = PAGE_SIZE

        start_idx = page * PAGE_SIZE
        lines = content_lines[start_idx : start_idx + content_len]
        window_lines = "\n".join(
            [str(i + start_idx).zfill(4) + line for i, line in enumerate(lines)]
        )

        return f"""
************ FILE: {path}, WINDOW STARTLINE: {start_idx}, WINDOW ENDLINE: {start_idx+content_len}, TOTAL FILE LINES: {all_lines_len} ************
{window_lines}
************************************
"""

    def _convert_editor_to_view(self, editor, PAGE_SIZE=50):
        return "\n".join(
            [self._format_editor_entry(k, v, PAGE_SIZE) for k, v in editor.items()]
        )

    def predict(
        self,
        task: str,
        observation: str,
        session: "Session",
    ) -> Tuple[str, str, str]:
        if self.interrupt:
            observation = observation + ". also " + self.interrupt
            self.interrupt = ""

        self.current_model = AnthropicModel(
            args=ModelArguments(
                model_name=self.model,
                temperature=self.temperature,
                api_key=self.api_key,
            )
        )
        try:
            editor = self._convert_editor_to_view(
                session.state.editor, session.state.PAGE_SIZE
            )

            self.chat_history.append(
                {"role": "user", "content": observation, "agent": self.name}
            )

            commands = (
                "Avaliable Custom Commands:\n"
                + "\n".join(
                    [f"{command}" for command in session.get_available_actions()]
                )
                + "\n"
            )

            command_docs = (
                "Custom Commands Documentation:\n"
                + commands_to_command_docs(
                    list(session.generate_command_docs().values())
                )
                + "\n"
            )

            system_prompt = system_prompt_template_v3(commands + command_docs)

            last_observation = None
            second_last_observation = None
            if len(self.chat_history) > 2:
                last_observation = self.chat_history[-1]["content"]
                second_last_observation = self.chat_history[-3]["content"]
            if (
                last_observation
                and second_last_observation
                and "Failed to edit file" in last_observation
                and "Failed to edit file" in second_last_observation
            ):
                self.chat_history = self.chat_history[:-6]
                history = history_to_bash_history(self.chat_history)
                self.current_model.args.temperature += (
                    0.2 if self.current_model.args.temperature < 0.8 else 0
                )
            else:
                history = history_to_bash_history(self.chat_history)

            last_user_prompt = last_user_prompt_template_v3(
                task, history, editor, session.environment.get_cwd(), session.base_path
            )

            messages = [{"role": "user", "content": last_user_prompt}]

            output = self.current_model.query(messages, system_message=system_prompt)

            # logger.debug(
            #     "<MODEL_OUT>"
            #     + json.dumps({"input": messages[0], "output": output})
            #     + "<MODEL_OUT>"
            # )

            thought, action = parse_response(output)

            self.chat_history.append(
                {
                    "role": "assistant",
                    "content": output,
                    "thought": thought,
                    "action": action,
                    "agent": self.name,
                }
            )

            logger.info(f"""
\n\n\n\n****************\n\n
NAME: {self.name}                        

THOUGHT: {thought}

ACTION: {action}

OBSERVATION: {observation}
\n\n****************\n\n\n\n""")

            return thought, action, output
        except KeyboardInterrupt:
            raise
        except RuntimeError as e:
            session.event_log.append(
                {
                    "type": "Error",
                    "content": str(e),
                    "producer": self.name,
                    "consumer": "none",
                }
            )
            logger.error(f"Runtime error: {e}")
            return (
                f"Exit due to runtime error: {e}",
                "exit_error",
                f"exit due to runtime error: {e}",
            )
        except RetryError as e:
            session.event_log.append(
                {
                    "type": "Error",
                    "content": str(e),
                    "producer": self.name,
                    "consumer": "none",
                }
            )
            logger.error(f"Retry error: {e}")
            return (
                f"Exit due to retry error: {e}",
                "exit_api",
                f"exit due to retry error: {e}",
            )
        except Exception as e:
            session.event_log.append(
                {
                    "type": "Error",
                    "content": str(e),
                    "producer": self.name,
                    "consumer": "none",
                }
            )
            logger.error(f"Exception: {e}")
            return (
                f"Exit due to exception: {e}",
                "exit_error",
                f"exit due to exception: {e}",
            )


class PlanningAgent:
    def __init__(self, name="PlanningAgent", model="claude-opus", temperature=0.0):
        self.name = name
        self.current_model = AnthropicModel(
            args=ModelArguments(model_name="claude-haiku", temperature=temperature)
        )
        self.history = [
            {"role": "user", "content": "Hey How are you?"},
            {
                "role": "assistant",
                "content": """<THOUGHT>
I should ask the user what they want
</THOUGHT>
<COMMAND>
ask_user "Hi, What can I help you with?"
</COMMAND>
""",
            },
        ]

        self.interrupt = ""

    def forward(self, observation, available_actions, env):
        try:
            system_prompt_template = f"""You are a user-facing software engineer. Your job is to communicate with the user, understand user needs, plan and delegate. You may perform actions to acheive this.
Actions:
{available_actions}

Docs:
{env.generate_command_docs()}

You must respond in the following format:ONLY ONE COMMAND AT A TIME
<THOUGHT>

</THOUGHT>
<COMMAND>
</COMMAND>
"""

            user_prompt_template = f"""<OBSERVATION>
        {observation}
        </OBSERVATION>"""

            self.history.append({"role": "user", "content": user_prompt_template})
            logger.info(self.history[-1]["content"])
            output = self.current_model.query(self.history, system_prompt_template)

            thought, action = parse_response(output)

            self.history.append({"role": "assistant", "content": output})

            return thought, action, output

        except Exception as e:
            raise e

    def stop(self):
        pass

    def interupt(self):
        pass

    def get_state(self):
        pass

    def run(
        self,
        env,
        observation: str = None,
    ):
        # system_prompt = system_prompt_template_v3(commands + command_docs)
        # self.history.append({"role": "system", "content": system_prompt})
        info = {}
        done = False
        while not done:
            if self.interrupt:
                observation = self.interrupt
                self.interrupt = ""

            thought, action, output = self.forward(
                observation, env.get_available_actions(), env
            )

            observations = list()
            if action == "exit":
                done = True

            try:
                # assert output.count("<COMMAND>") == 1
                # assert output.count("<THOUGHT>") == 1
                obs, done = env.step(action, thought)
            except AssertionError as e:
                # logger.error(output)
                logger.error(e)
                obs = str(e)
            except Exception as e:
                raise e
            observations.append(obs)

            if action.strip() == "submit":
                done = True

            observation = "\n".join(
                [json.dumps(obs) for obs in observations if obs is not None]
            )

        return info
