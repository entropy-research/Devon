import logging
import sys
from typing import Any, TypedDict

LOGGER_NAME = "devon"

logger = logging.getLogger(LOGGER_NAME)

stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(logging.DEBUG)
logger.addHandler(stdout_handler)

logger.setLevel(logging.DEBUG)


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
