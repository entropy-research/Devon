import datetime
import os
from dataclasses import dataclass
import time
from typing import Optional

from anthropic import Anthropic
import anthropic


@dataclass(frozen=False)
class ModelArguments:
    model_name: str
    temperature: float = 1.0
    top_p: float = 1.0
    api_key: Optional[str] = None


class HumanModel:
    def __init__(self, args: ModelArguments):
        self.args = args
        self.api_key = os.environ.get("ANTHROPIC_API_KEY")
        self.model = Anthropic(api_key=self.api_key)

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
            self.api = Anthropic(api_key=args.api_key)
        else:
            self.api = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    def query(self, messages: list[dict[str, str]], system_message: str = "") -> str:

        retries = 0
        max_retries = 5
        backoff_factor = 0.5
        while retries < max_retries:
            try:
                response = (
                    self.api.messages.create(
                        messages=messages,
                        max_tokens=self.model_metadata["max_tokens"],
                        model=self.api_model,
                        temperature=self.args.temperature,
                        system=system_message,
                        stop_sequences=["</COMMAND>"],
                    )
                )
                return response.content[0].text + "</COMMAND>"
            except anthropic.RateLimitError as e:
                if retries == max_retries - 1:
                    raise e
                else:
                    sleep_time = backoff_factor * (2 ** retries)
                    print(f"Request failed. Retrying in {sleep_time} seconds...")
                    time.sleep(sleep_time)
                    retries += 1

