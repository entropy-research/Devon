from pydantic import BaseModel
from typing import List, Optional


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

class Hunk2(BaseModel):
    lines: List[HunkLine]
    start_lines: Optional[List[HunkLine]] = None
    end_lines: Optional[List[HunkLine]] = None



class ContextHunk(BaseModel):
    lines: List[HunkLine]
    start_lines: Optional[List[HunkLine]] = None
    end_lines: Optional[List[HunkLine]] = None

class FileContextDiff(BaseModel):
    src_file: str
    tgt_file: str
    hunks: List[ContextHunk]


class MultiFileContextDiff(BaseModel):
    files: List[FileContextDiff]

class FileDiff2(BaseModel):
    src_file: str
    tgt_file: str
    hunks: List[Hunk2]

class MultiFileDiff2(BaseModel):
    files: List[FileDiff2]