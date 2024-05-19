import os
import litellm
import logging
from litellm import completion
from dataclasses import dataclass
from typing import Optional

# litellm.telemetry = False

# litellm.set_verbose=True

logger = logging.getLogger("LiteLLM")
logger.disabled = True

@dataclass(frozen=False)
class ModelArguments:
    model_name: str
    temperature: float = 1.0
    top_p: float = 1.0
    api_key: Optional[str] = None


class HumanModel:
    def __init__(self, args: ModelArguments):
        self.args = args

    def query(self, messages: list[dict[str, str]], system_message: str = "") -> str:
        thought = ""
        print(messages[-1])
        command = input("enter your command here")
        print(f"<THOUGHT>\n{thought}\n</THOUGHT>\n<COMMAND>\n{command}\n</COMMAND>")
        return f"<THOUGHT>\n{thought}\n</THOUGHT>\n<COMMAND>\n{command}\n</COMMAND>"


class AnthropicModel:
    MODELS = {
        "claude-3-opus-20240229": {
            "max_tokens": 4096,
        },
        "claude-3-sonnet-20240229": {
            "max_tokens": 4096,
        },
        "claude-3-haiku-20240307": {
            "max_tokens": 4096,
        },
    }

    SHORTCUTS = {
        "claude-opus": "claude-3-opus-20240229",
        "claude-sonnet": "claude-3-sonnet-20240229",
        "claude-haiku": "claude-3-haiku-20240307",
    }

    def __init__(self, args: ModelArguments):
        self.args = args
        self.api_model = self.SHORTCUTS.get(args.model_name, args.model_name)
        self.model_metadata = self.MODELS[self.api_model]

        if args.api_key is not None:
            self.api = args.api_key
        else:
            self.api = os.getenv("ANTHROPIC_API_KEY")

    def query(self, messages: list[dict[str, str]], system_message: str = "") -> str:
        model_completion = completion(
                messages=[{"role": "system", "content": system_message}] + messages,
                max_tokens=self.model_metadata["max_tokens"],
                model=self.api_model,
                temperature=self.args.temperature,
                stop=["</COMMAND>"],
            )
        
        response = model_completion.choices[0].message.content.rstrip("</COMMAND>")
        return response + "</COMMAND>"


class OpenAiModel:
    MODELS = {
        "gpt-4o": {
            "max_tokens": 4096,
        },
        "gpt-4-turbo": {
            "max_tokens": 4096,
        },
        "gpt-4-0125-preview": {
            "max_tokens": 4096,
        },
    }

    SHORTCUTS = {
        "gpt4-turbo": "gpt-4-turbo",
        "gpt4-o": "gpt-4o",
        "gpt4": "gpt-4-0125-preview",
    }

    def __init__(self, args: ModelArguments):
        self.args = args
        self.api_model = self.SHORTCUTS.get(args.model_name, args.model_name)
        self.model_metadata = self.MODELS[self.api_model]

        if args.api_key is not None:
            self.api_key = args.api_key
        else:
            self.api_key = os.getenv("OPENAI_API_KEY")

    def query(self, messages: list[dict[str, str]], system_message: str = "") -> str:
        model_completion = completion(
                messages=[{"role": "system", "content": system_message}] + messages,
                max_tokens=self.model_metadata["max_tokens"],
                model=self.api_model,
                temperature=self.args.temperature,
                stop=["</COMMAND>"],
            )
        
        response = model_completion.choices[0].message.content.rstrip("</COMMAND>")
        return response + "</COMMAND>"


class GroqModel:
    MODELS = {
        "groq/llama3-70b-8192": {
            "max_tokens": 4096,
        }
    }

    SHORTCUTS = {
        "llama-3-70b": "groq/llama3-70b-8192",
    }

    def __init__(self, args: ModelArguments):
        self.args = args
        self.api_model = self.SHORTCUTS.get(args.model_name, args.model_name)
        self.model_metadata = self.MODELS[self.api_model]

        if args.api_key is not None:
            self.api_key = args.api_key
        else:
            self.api_key = os.getenv("GROQ_API_KEY")

    def query(self, messages: list[dict[str, str]], system_message: str = "") -> str:
        model_completion = completion(
                messages=[{"role": "system", "content": system_message}] + messages,
                max_tokens=self.model_metadata["max_tokens"],
                model=self.api_model,
                temperature=self.args.temperature,
                stop=["</COMMAND>"],
            )
        
        response = model_completion.choices[0].message.content.rstrip("</COMMAND>")
        return response + "</COMMAND>"


class OllamaModel:

    def __init__(self, args: ModelArguments):
        self.args = args
        self.api_model = args.model
        self.model_metadata = {
            "max_tokens": 4096,
        }

        self.api_key = "ollama"

    def query(self, messages: list[dict[str, str]], system_message: str = "") -> str:
        model_completion = completion(
                messages=[{"role": "system", "content": system_message}] + messages,
                max_tokens=self.model_metadata["max_tokens"],
                model=self.api_model,
                temperature=self.args.temperature,
                stop=["</COMMAND>"],
                api_base="http://localhost:11434"
            )
        
        response = model_completion.choices[0].message.content.rstrip("</COMMAND>")
        return response + "</COMMAND>"
