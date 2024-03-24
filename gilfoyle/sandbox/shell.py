import os
import uuid
from pydantic import BaseModel, validator
from typing import Optional

from .container import PythonContainer

"""
This module contains the Shell class, which grants some high-level operations on a PythonContainer.
"""

class Shell:
    def __init__(self, repo_url: str):
        self.repo_url = repo_url
        self.repo_name = repo_url.split("/")[-1].split(".")[0]
        self.container = None

    def __enter__(self):
        self.container = PythonContainer()
        self.container.create()
        self.clone_repo()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.container:
            self.container.destroy()

    def clone_repo(self):
        if self.container:
            # Pull code & cd into directory
            self.container.execute(["bash", "-c", f"git clone {self.repo_url} && echo 'Cloning completed'"])
            self.change_directory(self.repo_name)
            pwd = self.container.execute(["bash", "-c", "pwd"])
            print(f"pwd: {pwd}")
            print(f"Repository {self.repo_url} cloned inside the container.")
        else:
            print("No container found. Please create a container first.")

    def read_file(self, file_path: str) -> str:
        if self.container:
            output = self.container.execute(["cat", file_path])
            return output
        else:
            print("No container found. Please create a container first.")
            return ""

    def write_file(self, file_path: str, content: str):
        if self.container:
            # Create file & parent directories if doesn't exist
            self.container.execute(["mkdir", "-p", file_path])
            self.container.execute(["touch", file_path])
            # Write content to temp file and swap with existing file
            # This gets around special character issues with echo.
            uniqueId = str(uuid.uuid4())
            self.container.execute(["bash", "-c", f"cat << 'EOF' > /usr/src/temp-{uniqueId}\n{content}\nEOF"])
            self.container.execute(["mv", f"/usr/src/temp-{uniqueId}", file_path])
            print(f"File {file_path} written inside the container.")
        else:
            print("No container found. Please create a container first.")

    def delete_file(self, file_path: str):
        if self.container:
            self.container.execute(["rm", file_path])
            print(f"File {file_path} deleted inside the container.")
        else:
            print("No container found. Please create a container first.")

    def move_file(self, source_path: str, destination_path: str):
        if self.container:
            # Create destination_path file & directories if needed
            self.container.execute(["mkdir", "-p", destination_path])
            self.container.execute(["touch", destination_path])
            # Move source file to destination
            self.container.execute(["mv", source_path, destination_path])
            print(f"File moved from {source_path} to {destination_path} inside the container.")
        else:
            print("No container found. Please create a container first.")

    def change_directory(self, path: str):
        if self.container:
            self.container.cwd = os.path.join(self.container.cwd, path)  # Update current working directory correctly relative to cwd
            print(f"Changed directory to {self.container.cwd} inside the container.")
        else:
            print("No container found. Please create a container first.")

    def list_directory_contents(self, path: str = "."):
        if self.container:
            # List contents of the directory inside the container
            output = self.container.execute(["ls", "-l", path])
            # Splitting the output to process each line
            lines = output.split('\n')
            directories = []
            files = []
            for line in lines:
                if line.startswith('d'):
                    directories.append(line.split()[-1])
                elif line.startswith('-'):
                    files.append(line.split()[-1])
            print(f"Directories: {directories}")
            print(f"Files: {files}")
            return directories, files
        else:
            print("No container found. Please create a container first.")
            return [], []

