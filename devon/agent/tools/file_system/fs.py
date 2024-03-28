import os
import shutil
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

from devon.agent.clients.tool_utils.tools import tool

class CodeFile(BaseModel):
    filepath: str
    code: str
    code_with_lines: str
    raw: Optional[str] = None

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

    def read_file(self, path):
        with open(path, "r") as f:
            content = f.read()
        
        return content
    
    def list_directory_contents(self, path):
        if not os.path.isdir(path):
            raise NotADirectoryError(f"{path} is not a directory")
        
        dirs = []
        files = []

        for entry in os.listdir(path):
            print(entry)
            entry = os.path.join(path, entry)
            if os.path.isfile(entry):
                files.append(entry)
            elif os.path.isdir(entry):
                dirs.append(entry)
        
        return dirs, files

    def get_code_from_file(self, file_path):
        try:
            code_lines = self.read_file(file_path).split('\n')
            numbered_lines = []
            for i, line in enumerate(code_lines, start=1):
                numbered_lines.append(f"{i}: {line}")
            return "\n".join(code_lines), "\n".join(numbered_lines)
        except FileNotFoundError:
            print(f"File not found: {file_path}")
            return None
        except IOError as e:
            print(f"Error reading file: {e}")
            return None

    def glob_repo_code(self, path):
        files = {}
        def extract_code_recursive(path: str):
            dirs, file_names = self.list_directory_contents(path)
            for file_name in file_names:
                if not file_name.startswith('.') and file_name.endswith(".py"):  # Avoid hidden directories and files
                    full_path = os.path.join(path, file_name)
                    code, code_with_lines = self.get_code_from_file(full_path)
                    if code is not None and code != "":
                        files[full_path] = CodeFile(filepath=full_path, code=code, code_with_lines=code_with_lines, raw=code)
            for directory in dirs:
                if not directory.startswith('.'):  # Avoid hidden directories
                    extract_code_recursive(os.path.join(path, directory))

        extract_code_recursive(path)
        return files
