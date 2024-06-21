import json
import logging
import time
import traceback
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional, Tuple, TypedDict

from pydantic import BaseModel
from tenacity import RetryError

from devon_agent.agents.default.anthropic_prompts import (
    anthropic_commands_to_command_docs, anthropic_history_to_bash_history,
    anthropic_last_user_prompt_template_v3,
    anthropic_system_prompt_template_v3, parse_response)
from devon_agent.agents.default.codegemma_prompts import (
    llama3_7b_commands_to_command_docs, llama3_7b_history_to_bash_history,
    llama3_7b_last_user_prompt_template_v1, llama3_7b_parse_response,
    llama3_7b_system_prompt_template_v1)
from devon_agent.agents.default.llama3_prompts import (
    llama3_commands_to_command_docs, llama3_history_to_bash_history,
    llama3_last_user_prompt_template_v1, llama3_parse_response,
    llama3_system_prompt_template_v1)
from devon_agent.agents.default.openai_prompts import (
    openai_commands_to_command_docs, openai_last_user_prompt_template_v3,
    openai_system_prompt_template_v3)
from devon_agent.agents.model import (AnthropicModel, GroqModel,
                                      ModelArguments, OllamaModel, OpenAiModel)
from devon_agent.tools.utils import get_cwd
from devon_agent.udiff import Hallucination
from devon_agent.utils import LOGGER_NAME, DotDict

if TYPE_CHECKING:
    from devon_agent.session import Session


logger = logging.getLogger(LOGGER_NAME)


class AgentArguments(BaseModel):
    model: str
    # api_key: Optional[str] = None
    api_base: Optional[str] = None
    prompt_type: Optional[str] = None
    # temperature: float = 0.0


@dataclass(frozen=False)
class Agent:
    name: str
    args: AgentArguments
    chat_history: list[dict[str, str]] = field(default_factory=list)
    interrupt: str = ""
    temperature: float = 0.0
    api_key: Optional[str] = None

    def run(self, session: "Session", observation: str = None): ...


@dataclass
class TaskAgent(Agent):
    scratchpad: str = None

    default_models = {
        "gpt4-o": OpenAiModel,
        "claude-opus": AnthropicModel,
        "claude-haiku": AnthropicModel,
        "claude-sonnet": AnthropicModel,
        "claude-3-5-sonnet": AnthropicModel,
        "gpt4": OpenAiModel,
        "gpt4-turbo": OpenAiModel,
        "llama-3-70b": GroqModel,
        "ollama/deepseek-coder:6.7b": OllamaModel,
    }

    default_model_configs = {
        "gpt4-o": {
            "prompt_type": "openai",
        },
        "gpt4-turbo": {
            "prompt_type": "openai",
        },
        "gpt4-0125-preview": {
            "prompt_type": "openai",
        },
        "claude-opus": {
            "prompt_type": "anthropic",
        },
        "claude-haiku": {
            "prompt_type": "anthropic",
        },
        "claude-sonnet": {
            "prompt_type": "anthropic",
        },
        "claude-3-5-sonnet": {
            "prompt_type": "anthropic",
        },
        "llama-3-70b": {
            "prompt_type": "llama3",
        },
        "ollama/deepseek-coder:6.7b": {
            "prompt_type": "ollama",
        },
    }

    def reset(self):
        self.chat_history = []
        self.interrupt = ""
        self.temperature = 0.0
        self.scratchpad = None

    def _initialize_model(self):
        is_custom_model = self.args.model not in self.default_models
        if is_custom_model:
            if not self.api_key:
                raise Exception("API key not specified for custom model")
            if not self.args.api_base:
                raise Exception("API base not specified for custom model")
            if not self.args.prompt_type:
                raise Exception("Prompt type not specified for custom model")

            # Assume it is openai-compatible
            return OpenAiModel(
                args=ModelArguments(
                    model_name=self.args.model,
                    temperature=self.temperature,
                    api_key=self.api_key,
                    api_base=self.args.api_base,
                    prompt_type=self.args.prompt_type,
                )
            )
        # print("API KEY", self.api_key)

        return self.default_models[self.args.model](
            args=ModelArguments(
                model_name=self.args.model,
                temperature=self.temperature,
                api_key=self.api_key,
            )
        )

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

    def _prepare_anthropic(self, task, editor, session):
        command_docs = (
            "Custom Commands Documentation:\n"
            + anthropic_commands_to_command_docs(
                list(session.generate_command_docs().values())
            )
            + "\n"
        )

        history = anthropic_history_to_bash_history(self.chat_history)
        system_prompt = anthropic_system_prompt_template_v3(command_docs)
        last_user_prompt = anthropic_last_user_prompt_template_v3(
            task,
            history,
            editor,
            get_cwd(
                {
                    "session": session,
                    "environment": session.default_environment,
                    "state": session.state,
                }
            ),
            session.base_path,
            self.scratchpad,
        )

        messages = [{"role": "user", "content": last_user_prompt}]
        return messages, system_prompt

    def _prepare_openai(self, task, editor, session):
        time.sleep(3)

        command_docs = (
            "Custom Commands Documentation:\n"
            + openai_commands_to_command_docs(
                list(session.generate_command_docs().values())
            )
            + "\n"
        )

        history = [
            entry
            for entry in self.chat_history
            if entry["role"] == "user" or entry["role"] == "assistant"
        ]
        system_prompt = openai_system_prompt_template_v3(command_docs)
        last_user_prompt = openai_last_user_prompt_template_v3(
            task,
            editor,
            get_cwd(
                {
                    "session": session,
                    "environment": session.default_environment,
                    "state": session.state,
                }
            ),
            session.base_path,
            self.scratchpad,
        )

        messages = history + [{"role": "user", "content": last_user_prompt}]
        return messages, system_prompt

    def _prepare_llama3(self, task, editor, session):
        time.sleep(3)

        command_docs = (
            "Custom Commands Documentation:\n"
            + llama3_commands_to_command_docs(
                list(session.generate_command_docs().values())
            )
            + "\n"
        )

        history = llama3_history_to_bash_history(self.chat_history)
        system_prompt = llama3_system_prompt_template_v1(command_docs)
        last_user_prompt = llama3_last_user_prompt_template_v1(
            task,
            history,
            editor,
            get_cwd(
                {
                    "session": session,
                    "environment": session.default_environment,
                    "state": session.state,
                }
            ),
            session.base_path,
            self.scratchpad,
        )

        messages = [{"role": "user", "content": last_user_prompt}]
        return messages, system_prompt

    def _prepare_ollama(self, task, editor, session):
        time.sleep(3)

        command_docs = list(session.generate_command_docs(format="docstring").values())

        command_docs = (
            "Custom Commands Documentation:\n"
            + llama3_7b_commands_to_command_docs(command_docs)
            + "\n"
        )

        system_prompt = llama3_7b_system_prompt_template_v1(command_docs)
        last_user_prompt = llama3_7b_last_user_prompt_template_v1(
            task,
            editor,
            get_cwd(
                {
                    "session": session,
                    "environment": session.default_environment,
                    "state": session.state,
                }
            ),
            session.base_path,
            self.scratchpad,
        )

        if len(self.chat_history) < 3:
            messages = self.chat_history + [
                {"role": "user", "content": last_user_prompt}
            ]
        else:
            messages = self.chat_history + [
                {"role": "user", "content": last_user_prompt}
            ]

        return messages, system_prompt

    def predict(
        self,
        task: str,
        observation: str,
        session: "Session",
    ) -> Tuple[str, str, str]:
        self.current_model = self._initialize_model()

        if self.interrupt:
            observation = observation + ". also " + self.interrupt
            self.interrupt = ""

        try:
            editor = self._convert_editor_to_view(
                session.state.editor.files, session.state.editor.PAGE_SIZE
            )

            self.chat_history.append(
                {"role": "user", "content": observation, "agent": self.name}
            )

            prompts = {
                "anthropic": self._prepare_anthropic,
                "openai": self._prepare_openai,
                "llama3": self._prepare_llama3,
                "ollama": self._prepare_ollama,
            }

            if not self.args.prompt_type:
                self.args.prompt_type = self.default_model_configs[self.args.model][
                    "prompt_type"
                ]

            messages, system_prompt = prompts[self.args.prompt_type](
                task, editor, session
            )

            output = self.current_model.query(messages, system_message=system_prompt)

            thought = None
            action = None

            try:
                thought, action, scratchpad = llama3_parse_response(output)
                if scratchpad:
                    self.scratchpad = scratchpad
            except Exception:
                raise Hallucination(f"Multiple actions found in response: {output}")

            if not thought or not action:
                raise Hallucination(
                    "Agent failed to follow response format instructions"
                )

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

SCRATCHPAD: {scratchpad}
\n\n****************\n\n\n\n""")

            return thought, action, output
        except KeyboardInterrupt:
            raise
        except Hallucination as e:
            return "hallucination", "hallucination", "Incorrect response format"
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
            traceback.print_exc()
            logger.error(f"Exception: {e}")
            return (
                f"Exit due to exception: {e}",
                "exit_error",
                f"exit due to exception: {e}",
            )
