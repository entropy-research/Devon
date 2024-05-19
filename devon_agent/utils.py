import logging
import sys
from typing import Any, TypedDict
import json
import os

LOGGER_NAME = "devon"

logger = logging.getLogger(LOGGER_NAME)

stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(logging.DEBUG)
logger.addHandler(stdout_handler)

logger.setLevel(logging.DEBUG)

def get_model_name_from_config(config_path=".devon.config"):
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file {config_path} not found.")
    
    with open(config_path, "r") as file:
        config = json.load(file)
    
    return config.get("modelName")

class DotDict:
    """
    Wrapper class for accessing dictionary keys as attributes
    """

    def __init__(self, data):
        self.data = data

    def __getattr__(self, key):
        return self.data.get(key)

    def to_dict(self):
        return self.__dict__


class Event(TypedDict):
    type: str  # types: ModelResponse, ToolResponse, UserRequest, Interrupt, Stop
    content: Any
    producer: str | None
    consumer: str | None
