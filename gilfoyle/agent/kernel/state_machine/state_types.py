from typing import Literal, Union
from pydantic import BaseModel

class State(BaseModel):
    state: Union[Literal["reason"], Literal["write"], Literal["execute"], Literal["evaluate"], Literal["success"]]
