from typing import Literal, Union
from pydantic import BaseModel

type State = Union[Literal["reason"], Literal["write"], Literal["execute"], Literal["evaluate"], Literal["success"]]
