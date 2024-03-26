import os
from pydantic import BaseModel, Field
from typing import List, Dict, Any

from gilfoyle.agent.clients.tool_utils.tools import tool

class DirectoryObserverTool(BaseModel):
    base_path: str = Field(..., description="The base path of the directory to observe")

    @tool("list_directory_recursive", "List the contents of a directory recursively")
    def list_directory_recursive(self, path: str = Field("", description="The relative path from the base path")) -> List[Dict[str, Any]]:
        full_path = os.path.join(self.base_path, path)
        if not os.path.exists(full_path):
            raise ValueError(f"Path does not exist: {full_path}")

        entries = []
        for root, dirs, files in os.walk(full_path):
            for entry in dirs + files:
                entry_path = os.path.join(root, entry)
                relative_path = os.path.relpath(entry_path, self.base_path)
                entry_type = "file" if os.path.isfile(entry_path) else "directory"
                entry_info = {
                    "name": entry,
                    "path": relative_path,
                    "type": entry_type
                }
                entries.append(entry_info)

        return entries