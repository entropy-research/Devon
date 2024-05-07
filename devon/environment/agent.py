import json
import logging
from dataclasses import dataclass, field
from typing import Tuple

from devon.agent.model import AnthropicModel, ModelArguments
from devon.environment.prompt import (
    commands_to_command_docs,
    history_to_bash_history,
    last_user_prompt_template_v3,
    parse_response,
    system_prompt_template_v3,
)

from devon.environment.utils import LOGGER_NAME, Event
from tenacity import RetryError

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from devon.environment.session import Session

# from devon.environment.cli import ChatEnvironment


logger = logging.getLogger(LOGGER_NAME)


@dataclass(frozen=False)
class Agent:
    name: str
    model: str
    temperature: float = 0.0
    chat_history: list[dict[str, str]] = field(default_factory=list)
    interrupt: str = ""

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
            args=ModelArguments(model_name=self.model, temperature=self.temperature)
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
                task, history, editor, session.environment.get_cwd()
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
        except Exception as e:
            raise e



#     def run(self,session: 'Session', observation: str = None):

#         self.current_model = AnthropicModel(
#             args=ModelArguments(model_name=self.model, temperature=self.temperature)
#         )

#         done = False
#         task = self.get_last_task() or "Task unspecified ask user to specify task"

#         while not done:

#             if self.interrupt:
#                 observation = self.interrupt
#                 self.interrupt = ""

#             thought, action, output = self.forward(
#                 task=task,
#                 observation=observation,
#                 session=session,
#             )

#             observations = list()
#             if action == "exit":
#                 done = True

#             try:
#                 obs,done = session.step(action, thought)
#             except AssertionError as e:
#                 logger.error(traceback.format_exc())
#                 obs = str(e)

#             observations.append(obs)

#             if action.strip() == "submit":
#                 done = True

#             observation = "\n".join(
#                 [json.dumps(obs) for obs in observations if obs is not None]
#             )

#             logger.info(f"""
# \n\n\n\n****************\n\n
# NAME: {self.name}

# THOUGHT: {thought}

# ACTION: {action}

# OBSERVATION: {observation}
# \n\n****************\n\n\n\n""")


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


# class TaskAgent:
#     def __init__(self, name="Devon", args=None, model="claude-opus", temperature=0.0):

#         self.current_model = AnthropicModel(
#             args=ModelArguments(model_name="claude-opus", temperature=temperature)
#         )
#         # self.default_model = self.opus
#         # self.current_model = self.opus
#         # self.default_model = HumanModel(args=ModelArguments(
#         #     model_name="gpt-4-0314",
#         #     # total_cost_limit=0.0,
#         #     # per_instance_cost_limit=2.0,
#         #     temperature=0.5,
#         #     top_p=0.95
#         # ))
#         # self.current_model = self.default_model

#         self.name = name
#         self.history = []
#         self.max_steps = 15
#         self.stop = False
#         self.interrupt = ""

#     def stop(self):
#         self.stop = True

#     def interupt(self,message):
#         self.interrupt = message

#     def get_state(self):
#         return self.history

#     def _format_editor_entry(self, k, v):

#         path = k
#         page = v["page"]
#         content_lines = v["lines"].splitlines()

#         all_lines_len = len(content_lines)
#         last_idx = all_lines_len // self.PAGE_SIZE
#         if page == last_idx:
#             content_len = all_lines_len % self.PAGE_SIZE
#         else:
#             content_len = self.PAGE_SIZE

#         start_idx = page * self.PAGE_SIZE
#         lines = content_lines[start_idx : start_idx + content_len]
#         window_lines = "\n".join(
#             [str(i + start_idx).zfill(4) + line for i, line in enumerate(lines)]
#         )

#         return f"""
# ************ FILE: {path}, WINDOW STARTLINE: {start_idx}, WINDOW ENDLINE: {start_idx+content_len}, TOTAL FILE LINES: {all_lines_len} ************
# {window_lines}
# ************************************
# """

#     def _convert_editor_to_view(self, editor):
#         result = []

#         for k, v in editor.items():

#             result.append(self._format_editor_entry(k, v))

#         return "\n".join(result)

#     def forward(
#         self,
#         task: str,
#         observation: str,
#         available_actions: list[str],
#         state: dict,
#         commanddoc: dict,
#         # step: int,
#     ) -> Tuple[str, str, str]:

#         try:

#             issue, editor, working_dir = (
#                 task,
#                 self._convert_editor_to_view(state["editor"]),
#                 state["file_root"],
#             )

#             self.history.append(
#                 {"role": "user", "content": observation, "agent": self.name}
#             )

#             commands = (
#                 "Avaliable Custom Commands:\n"
#                 + "\n".join([f"{command}" for command in available_actions])
#                 + "\n"
#             )

#             command_docs = (
#                 "Custom Commands Documentation:\n"
#                 + commands_to_command_docs(list(commanddoc.values()))
#                 + "\n"
#             )

#             system_prompt = system_prompt_template_v3(commands + command_docs)

#             last_observation = None
#             second_last_observation = None
#             if len(self.history) > 2:
#                 last_observation = self.history[-1]["content"]
#                 second_last_observation = self.history[-3]["content"]
#             if (
#                 last_observation
#                 and second_last_observation
#                 and "Failed to edit file" in last_observation
#                 and "Failed to edit file" in second_last_observation
#             ):
#                 self.history = self.history[:-6]
#                 history = history_to_bash_history(self.history)
#                 self.current_model.args.temperature += (
#                     0.2 if self.current_model.args.temperature < 0.8 else 0
#                 )
#             else:
#                 history = history_to_bash_history(self.history)

#             last_user_prompt = last_user_prompt_template_v3(
#                 issue, history, editor, working_dir
#             )

#             messages = [{"role": "user", "content": last_user_prompt}]

#             output = self.current_model.query(messages, system_message=system_prompt)

#             logger.debug(
#                 "<MODEL_OUT>"
#                 + json.dumps({"input": messages[0], "output": output})
#                 + "<MODEL_OUT>"
#             )
#             # output = self.forward(
#             #     observation, state, available_actions, commanddoc, step
#             # )

#             thought, action = parse_response(output)

#             self.history.append(
#                 {
#                     "role": "assistant",
#                     "content": output,
#                     "thought": thought,
#                     "action": action,
#                     "agent": self.name,
#                     "state": state,
#                 }
#             )

#             return thought, action, output
#         except KeyboardInterrupt:
#             raise
#         except RuntimeError as e:
#             logger.error(f"Runtime error: {e}")
#             return (
#                 f"Exit due to runtime error: {e}",
#                 "exit_error",
#                 f"exit due to runtime error: {e}",
#             )
#         except RetryError as e:
#             logger.error(f"Retry error: {e}")
#             return (
#                 f"Exit due to retry error: {e}",
#                 "exit_api",
#                 f"exit due to retry error: {e}",
#             )

#         except Exception as e:
#             raise e

#     def run(
#         self,
#         task: str,
#         env: TaskEnvironment,
#         observation: str = None,
#     ):
#         logger.info("Running agent")
#         available_actions = env.get_available_actions()
#         commanddoc = env.generate_command_docs()
#         self.history = []
#         self.PAGE_SIZE = env.PAGE_SIZE

#         commands = (
#             "Avaliable Custom Commands:\n"
#             + "\n".join([f"{command}" for command in available_actions])
#             + "\n"
#         )
#         command_docs = (
#             "Custom Commands Documentation:\n"
#             + commands_to_command_docs(list(commanddoc.values()))
#             + "\n"
#         )

#         system_prompt = system_prompt_template_v3(commands + command_docs)
#         self.history.append({"role": "system", "content": system_prompt})
#         info = {}
#         done = False
#         while not done:
#         # for i in range(self.max_steps):

#             # if done:
#             #     break

#             state = env.get_state()

#             if self.interrupt:
#                 observation = self.interrupt
#                 self.interrupt = ""


#             thought, action, output = self.forward(
#                 task,
#                 observation,
#                 env.get_available_actions(),
#                 state,
#                 env.generate_command_docs(),
#                 # i,
#             )

#             observations = list()
#             if action == "exit":
#                 done = True

#             try:
#                 # assert output.count("<COMMAND>") == 1
#                 # assert output.count("<THOUGHT>") == 1
#                 obs, _, done, info = env.step(action, thought)
#             except AssertionError as e:
#                 # logger.error(output)
#                 # logger.error(e)
#                 logger.error(traceback.format_exc())
#                 obs = str(e)

#             observations.append(obs)

#             if action.strip() == "submit":
#                 done = True

#             observation = "\n".join(
#                 [json.dumps(obs) for obs in observations if obs is not None]
#             )

#             logger.info(f"""
# \n\n\n\n****************\n\n
# NAME: {self.name}

# THOUGHT: {thought}

# ACTION: {action}

# OBSERVATION: {observation}
# \n\n****************\n\n\n\n""")

#         if self.max_steps == 0:
#             _, _, done, info = env.step("submit", "im done")

#         if not done:
#             # sumbit the last thing
#             action = "submit"
#             _, _, done, info = env.step(action, thought)

#         self.history = []

#         logger.debug(info)
#         return info
