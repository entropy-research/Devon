import os
from pydantic import BaseModel, Field
from typing import List, Dict, Any

from gilfoyle.agent.clients.tool_utils.tools import tool

class DirectoryObserverTool(BaseModel):
    base_path: str = Field(..., description="The base path of the directory to observe")

    @tool("list_directory_recursive", "List the contents of a directory recursively")
    def list_directory_recursive(self, path: str = Field("", description="The relative path from the base path")) -> Dict[str, Any]:
        full_path = os.path.join(self.base_path, path)
        if not os.path.exists(full_path):
            raise ValueError(f"Path does not exist: {full_path}")

        def build_tree(current_path):
            entries = {}
            for entry in os.listdir(current_path):
                entry_path = os.path.join(current_path, entry)
                relative_path = os.path.relpath(entry_path, self.base_path)
                if os.path.isfile(entry_path):
                    entries[entry] = {
                        "type": "file",
                        "path": relative_path
                    }
                else:
                    entries[entry] = {
                        "type": "directory",
                        "path": relative_path,
                        "children": build_tree(entry_path)
                    }
            return entries

        return build_tree(full_path)