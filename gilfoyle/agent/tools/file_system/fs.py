import os
import shutil
from pydantic import BaseModel, Field
from typing import List, Dict, Any

from gilfoyle.agent.clients.tool_utils.tools import tool

class FileSystemTool(BaseModel):
    base_path: str = Field(..., description="The base path for file system operations")

    @tool("ls", "List the contents of a directory")
    def ls(self, path: str = Field("", description="The relative path from the base path")) -> List[Dict[str, Any]]:
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

    @tool("cp", "Copy a file from source to destination")
    def cp(self, source: str = Field(..., description="The source file path"), 
           destination: str = Field(..., description="The destination file path")):
        source_path = os.path.join(self.base_path, source)
        destination_path = os.path.join(self.base_path, destination)

        if not os.path.exists(source_path):
            raise ValueError(f"Source path does not exist: {source_path}")

        shutil.copy2(source_path, destination_path)
        return f"File copied from {source_path} to {destination_path}"

    @tool("mv", "Move a file from source to destination")
    def mv(self, source: str = Field(..., description="The source file path"), 
           destination: str = Field(..., description="The destination file path")):
        source_path = os.path.join(self.base_path, source)
        destination_path = os.path.join(self.base_path, destination)

        if not os.path.exists(source_path):
            raise ValueError(f"Source path does not exist: {source_path}")

        shutil.move(source_path, destination_path)
        return f"File moved from {source_path} to {destination_path}"

    @tool("touch", "Create a new file")
    def touch(self, path: str = Field(..., description="The file path")):
        full_path = os.path.join(self.base_path, path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'a'):
            os.utime(full_path, None)
        return f"File created: {full_path}"
    
    @tool("mkdir", "Create a new directory")
    def mkdir(self, path: str = Field(..., description="The directory path")):
        full_path = os.path.join(self.base_path, path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        return f"Directory created: {full_path}"