from dataclasses import dataclass
from typing import Optional
from devon_agent.agent.tools.file_system.fs import FileSystemTool
from devon_agent.agent.tools.git_tool.git_tool import GitTool
from devon_agent.agent.tools.github.github_tool import GitHubTool

@dataclass
class FileContext:
    file_glob: dict
    file_tree: dict
    file_code_mapping: dict

@dataclass
class BaseStateContext:
    github_tool: GitHubTool
    git_tool: GitTool
    file_system: FileSystemTool
    fs_root: str
    
    def load_file_context(self, path) -> FileContext:
        repo_data = self.file_system.glob_repo_code(path=path)
        file_tree = self.file_system.list_directory_recursive(path=path)
        file_code_mapping = {path: data.code for path, data in repo_data.items()}

        return FileContext(file_glob=repo_data, file_tree=file_tree, file_code_mapping=file_code_mapping)