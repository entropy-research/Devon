from abc import ABC, abstractmethod
from dataclasses import dataclass
import os
from typing import Dict, List

from anthropic import Anthropic

@dataclass
class Message:
    role: str
    content: str

class LanguageModel(ABC):
    @abstractmethod
    def chat(self, messages: List[Dict]) -> str:
        pass

class LanguageModelWrapper:
    def __init__(self, language_model: LanguageModel):
        self.language_model = language_model

    def chat(self, messages: List[Message]) -> str:
        return self.language_model.chat(messages)
    
class ClaudeOpus(LanguageModel):

    #os.environ.get("ANTHROPIC_API_KEY")

    def __init__(self, api_key, system_message, max_tokens) -> None:
        self.client = Anthropic(api_key=api_key)
        self.system_message = system_message
        self.max_tokens = max_tokens
    
    def chat(self, messages: List[Message]):
        message = self.client.messages.create(
            max_tokens=self.max_tokens,
            system=self.system_message,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            model="claude-3-opus-20240229",
        )
        return message.content[0].text

class ClaudeSonnet(LanguageModel):

    def __init__(self, api_key, system_message, max_tokens) -> None:
        self.client = Anthropic(api_key=api_key)
        self.system_message = system_message
        self.max_tokens = max_tokens
    
    def chat(self, messages: List[Message]):
        message = self.client.messages.create(
            max_tokens=self.max_tokens,
            system=self.system_message,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            model="claude-3-opus-20240229",
        )
        return message.content[0].text
    
class ClaudeHaiku(LanguageModel):

    def __init__(self, api_key, system_message, max_tokens) -> None:
        self.client = Anthropic(api_key=api_key)
        self.system_message = system_message
        self.max_tokens = max_tokens
    
    def chat(self, messages: List[Message]):
        message = self.client.messages.create(
            max_tokens=self.max_tokens,
            system=self.system_message,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            model="claude-3-opus-20240229",
        )
        return message.content[0].text
