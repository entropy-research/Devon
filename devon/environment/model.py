import os
from dataclasses import dataclass

from anthropic import Anthropic


@dataclass(frozen=False)
class ModelArguments:
    model_name: str
    temperature: float = 1.0
    top_p: float = 1.0


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

        self.api = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    def history_to_messages(
        self, history: list[dict[str, str]]
    ) -> list[dict[str, str]]:
        messages = [
            {k: v for k, v in entry.items() if k in ["role", "content"]}
            for entry in history
            if entry["role"] != "system"
        ]
        for message in messages:
            if message["content"].strip() == "":
                message["content"] = "(No output)"
        return messages

    def query(self, messages: list[dict[str, str]], system_message: str = "") -> str:
        # def query(self, history: list[dict[str, str]]) -> str:
        # system_message = "\n".join([
        #     entry["content"] for entry in history if entry["role"] == "system"
        # ])
        # messages = self.history_to_messages(history)

        response = (
            self.api.messages.create(
                messages=messages,
                max_tokens=self.model_metadata["max_tokens"],
                model=self.api_model,
                temperature=self.args.temperature,
                # top_p=self.args.top_p,
                system=system_message,
                stop_sequences=["</COMMAND>"],
            )
            .content[0]
            .text
        )

        return response + "</COMMAND>"


# Simple shim for providing commands
def process_command(model, command):
    history = [{"role": "user", "content": command}]
    response = model.query(history)
    return response
