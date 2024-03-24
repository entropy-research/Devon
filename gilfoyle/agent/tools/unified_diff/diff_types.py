from pydantic import BaseModel
from typing import List


class HunkLine(BaseModel):
    type: str  # "added", "removed", or "unchanged"
    content: str

class Hunk(BaseModel):
    src_start: int
    src_lines: int
    tgt_start: int
    tgt_lines: int
    lines: List[HunkLine]

class FileDiff(BaseModel):
    src_file: str
    tgt_file: str
    hunks: List[Hunk]

class MultiFileDiff(BaseModel):
    files: List[FileDiff]