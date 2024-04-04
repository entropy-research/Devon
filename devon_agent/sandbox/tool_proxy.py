from abc import ABC, abstractmethod
from dataclasses import dataclass
import os
from typing import List

from devon_agent.agent.clients.tool_utils.tools import Toolbox
from devon_agent.agent.tools.file_system.fs import FileSystemTool
from devon_agent.agent.tools.git_tool.git_tool import GitTool
from devon_agent.agent.tools.github.github_tool import GitHubTool


@dataclass
class ToolProxy(ABC):

    @abstractmethod
    def file_system(self, path) -> FileSystemTool:
        pass

    @abstractmethod
    def git(self, path) -> GitTool:
        pass

    @abstractmethod
    def github(self) -> GitHubTool:
        pass

@dataclass
class LocalToolProxy(ToolProxy):

    def file_system(self, path=os.getcwd()) -> Toolbox:
        return FileSystemTool(base_path=path)

    def git(self, path=os.getcwd()) -> Toolbox:
        return GitTool(path=path)

    def github(self) -> Toolbox:
        return GitHubTool(token=os.getenv("AGENT_GITHUB_TOKEN"))
