from pydantic import BaseModel

from typing import List


class LineDiff(BaseModel):
    line_number: int
    new_code: str

class GitDiff(BaseModel):
    line_diffs: List[LineDiff]