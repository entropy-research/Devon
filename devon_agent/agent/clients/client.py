from abc import ABC, abstractmethod
from dataclasses import dataclass
import os
from typing import Dict, List, Optional, Any, Union

from anthropic import Anthropic
from openai import OpenAI

from devon_agent.agent.clients.tool_utils.tools import Toolbox

import logging

# Create a logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Set the log level

# Create a file handler and set the level to debug
fh = logging.FileHandler('PROMPT')
fh.setLevel(logging.INFO)

# Create a formatter and add it to the handler
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)

# Add the handler to the logger
logger.addHandler(fh)



@dataclass
class Message:
    role: str
    content: str

@dataclass
class LanguageModel(ABC):
    client: Union[OpenAI, Anthropic]
    system_message: str
    max_tokens: int
    tools_enabled: bool = False
    temperature: float = 0.5

    @abstractmethod
    def chat(self, messages: List[Union[Message, Dict[str, Any]]], tools: Optional[Toolbox]) -> str:
        pass

@dataclass
class GPT4(LanguageModel):
    model="gpt-4-0125-preview"
    
    def __post_init__(self):
        if not isinstance(self.client, OpenAI):
            raise Exception("Passed incorrect client type")
    
    def chat(self, messages: List[Message], tools: Toolbox = None, tool_choice="auto"):

        if not self.tools_enabled and tools is not None:
            raise Exception("Passed tools to a model that does not support tools")

        response = self.client.chat.completions.create(
            max_tokens=self.max_tokens,
            messages=[{"role":"system", "content":self.system_message}] + [{"role": m.role, "content": m.content} if isinstance(m, Message) else m for m in messages],
            model=self.model,
            tools=[tool for tool in tools.get_all_tools()] if tools else [],
            tool_choice=tool_choice
        )

        message = response.choices[0].message
        if "tool_calls" in message.__dict__:
            return message, message.tool_calls
        
        return message

class ClaudeOpus(LanguageModel):
    model="claude-3-opus-20240229"

    def __post_init__(self):
        if not isinstance(self.client, Anthropic):
            raise Exception("Passed incorrect client type")
    
    def chat(self, messages: List[Message], tools: Toolbox = None, tool_choice="auto",stop_sequences=[]):

        # logger.info("SYSTEM",str(self.system_message))
        # logger.info("PROMPT",str([{"role": m.role, "content": m.content} for m in messages]))

        if not self.tools_enabled and tools is not None:
            raise Exception("Passed tools to a model that does not support tools")
        # print("SYSTEM",self.system_message)
        # print("PROMPT",[{"role": m.role, "content": m.content} for m in messages])
        message = self.client.messages.create(
            max_tokens=self.max_tokens,
            system=self.system_message,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            model=self.model,
            stop_sequences=stop_sequences,
            temperature=self.temperature
        )
        # logger.info("REPONSE", message.content[0].text)
        print("REPONSE", message.content[0].text)
    
        return message.content[0].text

class ClaudeSonnet(LanguageModel):
    model="claude-3-sonnet-20240229"

    def __post_init__(self):
        if not isinstance(self.client, Anthropic):
            raise Exception("Passed incorrect client type")
    
    def chat(self, messages: List[Message], tools: Toolbox = None, tool_choice="auto"):

        # logger.info("SYSTEM",self.system_message)
        # logger.info("PROMPT",[{"role": m.role, "content": m.content} for m in messages])

        if not self.tools_enabled and tools is not None:
            raise Exception("Passed tools to a model that does not support tools")
        
        message = self.client.messages.create(
            max_tokens=self.max_tokens,
            system=self.system_message,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            model=self.model,
            temperature=self.temperature
        )

        # logger.info("REPONSE", message.content[0].text)
        print("REPONSE", message.content[0].text)
        return message.content[0].text
    
class ClaudeHaiku(LanguageModel):
    model="claude-3-haiku-20240307"

    def __post_init__(self):
        if not isinstance(self.client, Anthropic):
            raise Exception("Passed incorrect client type")
    
    def chat(self, messages: List[Message], tools: Toolbox = None, tool_choice="auto"):

        # logger.info("SYSTEM",self.system_message)
        # logger.info("PROMPT",[{"role": m.role, "content": m.content} for m in messages])

        if not self.tools_enabled and tools is not None:
            raise Exception("Passed tools to a model that does not support tools")
        
        message = self.client.messages.create(
            max_tokens=self.max_tokens,
            system=self.system_message,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            model=self.model,
            temperature=self.temperature
        )


        # logger.info("REPONSE", message.content[0].text)

        return message.content[0].text
