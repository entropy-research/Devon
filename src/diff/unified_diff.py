from pydantic import BaseModel
from typing import List



class Hunk(BaseModel):
    src_start: int
    src_lines: int
    tgt_start: int
    tgt_lines: int
    lines: str

class UnifiedDiff(BaseModel):
    src_file: str
    tgt_file: str
    hunks: List[Hunk]
