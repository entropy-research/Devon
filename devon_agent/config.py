from typing import Any, List, Literal, Optional
from pydantic import BaseModel


class AgentConfig(BaseModel):
    model: str    
    agent_name : str
    agent_type : str
    api_base: Optional[str] = None
    prompt_type: Optional[str] = None
    api_key: Optional[str] = None
    temperature: float = 0.0


class Config(BaseModel):
    path: str
    environments: List[str]
    default_environment: str
    user_input: Any
    name: str
    db_path : str
    agent_configs : List[AgentConfig]
    task: Optional[str] = None
    headless: Optional[bool] = False
    versioning : Optional[Literal["git", "fossil"]] = None
    ignore_files : Optional[bool]
    devon_ignore_file : Optional[str]

    