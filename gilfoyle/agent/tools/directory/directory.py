import os
from pydantic import BaseModel, Field
from typing import List, Dict, Any

class DirectoryObserverTool(BaseModel):
    base_path: str = Field(..., description="The base path of the directory to observe")

    def list_directory(self, path: str = Field("", description="The relative path from the base path")) -> List[Dict[str, Any]]:
        full_path = os.path.join(self.base_path, path)
        if not os.path.exists(full_path):
            raise ValueError(f"Path does not exist: {full_path}")

        entries = []
        for entry in os.listdir(full_path):
            entry_path = os.path.join(full_path, entry)
            entry_type = "file" if os.path.isfile(entry_path) else "directory"
            entry_info = {
                "name": entry,
                "type": entry_type
            }
            entries.append(entry_info)

        return entries