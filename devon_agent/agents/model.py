import logging
import os
from dataclasses import dataclass
from typing import Optional

import litellm
from litellm import completion

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
    api_base: Optional[str] = None
    prompt_type: Optional[str] = None


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
        "claude-3-5-sonnet-20240620": {
            "max_tokens": 4096,
        },
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
        "claude-3-5-sonnet": "claude-3-5-sonnet-20240620",
        "claude-opus": "claude-3-opus-20240229",
        "claude-sonnet": "claude-3-sonnet-20240229",
        "claude-haiku": "claude-3-haiku-20240307",
    }

    def __init__(self, args: ModelArguments):
        self.args = args
        self.api_model = self.SHORTCUTS.get(args.model_name, args.model_name)
        self.model_metadata = self.MODELS[self.api_model]
        self.prompt_type = "anthropic"
        if args.api_key is not None:
            self.api_key = args.api_key
        else:
            self.api_key = os.getenv("ANTHROPIC_API_KEY")

    def query(self, messages: list[dict[str, str]], system_message: str = "") -> str:
        print(self.api_key)
        model_completion = completion(
            messages=[{"role": "system", "content": system_message}] + messages,
            max_tokens=self.model_metadata["max_tokens"],
            model=self.api_model,
            temperature=self.args.temperature,
            stop=["</COMMAND>"],
            api_key=self.api_key,
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
        self.model_metadata = self.MODELS.get(self.api_model, {})
        self.prompt_type = "openai"

        if args.api_key is not None:
            self.api_key = args.api_key
        else:
            self.api_key = os.getenv("OPENAI_API_KEY")

        if args.api_base is not None:
            self.api_base = args.api_base

        if args.prompt_type is not None:
            self.prompt_type = args.prompt_type

    def query(self, messages: list[dict[str, str]], system_message: str = "") -> str:
        model_completion = completion(
            messages=[{"role": "system", "content": system_message}] + messages,
            max_tokens=self.model_metadata.get("max_tokens", 4096),
            model=self.api_model,
            temperature=self.args.temperature,
            api_key=self.api_key,
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
        self.prompt_type = "llama3"
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
            api_key=self.api_key,
        )

        response = model_completion.choices[0].message.content.rstrip("</COMMAND>")
        return response + "</COMMAND>"


class OllamaModel:
    def __init__(self, args: ModelArguments):
        self.args = args
        self.api_model = args.model_name
        self.model_metadata = {
            "max_tokens": 4096,
        }

        self.api_key = "ollama"
        self.prompt_type = "ollama"

    def query(self, messages: list[dict[str, str]], system_message: str = "") -> str:
        model_completion = completion(
            messages=[{"role": "system", "content": system_message}] + messages,
            max_tokens=self.model_metadata["max_tokens"],
            model=self.api_model,
            temperature=self.args.temperature,
            stop=["</command>"],
            api_base="http://localhost:11434",
            api_key=self.api_key,
        )

        response = model_completion.choices[0].message.content.rstrip("</command>")
        return response + "</command>"


if __name__ == "__main__":
    from outlines import models, generate
    from outlines.models.openai import OpenAIConfig
    from openai import OpenAI


    json_grammar = outlines.grammars.json

    client = OpenAI()
    config = OpenAIConfig("gpt-4o")
    litellm.drop_params=True
    client.chat.completions.create = litellm.acompletion
    model = models.openai(client, config)
    generator = generate.cfg(model, json_grammar)
    answer = generator("What is 2+2?")
    print(answer)