import base64
import logging
import re
import sys
from typing import Any, TypedDict

LOGGER_NAME = "devon"

logger = logging.getLogger(LOGGER_NAME)

stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(logging.DEBUG)
logger.addHandler(stdout_handler)

logger.setLevel(logging.DEBUG)


def encode_path(path):
    # Encode the path to base64
    encoded = base64.b64encode(path.encode()).decode()
    # Replace non-alphanumeric characters
    return re.sub(r'[^a-zA-Z0-9]', '', encoded)

def decode_path(encoded_path):
    # Add padding if necessary
    padding = 4 - (len(encoded_path) % 4)
    if padding < 4:
        encoded_path += '=' * padding
    # Decode the path from base64
    return base64.b64decode(encoded_path).decode()


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
