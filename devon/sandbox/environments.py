import os
import docker
from typing import Optional

from devon.sandbox.tool_proxy import LocalToolProxy, ToolProxy

"""
This module contains the PythonContainer class, which represents a Docker container running Python.

The primary method of interacting with the container is the `execute` method, which runs a command inside the container and returns the output.
"""

from typing import Protocol, runtime_checkable, List

@runtime_checkable
class EnvironmentProtocol(Protocol):
    """
    Defines a protocol for environment classes to follow, ensuring they provide
    methods for creation, destruction, and command execution within the environment.
    """

    def __enter__(self):
        ...

    def __exit__(self, exc_type, exc_val, exc_tb):
        ...

    def create(self) -> None:
        """
        Prepares the environment for use.
        """
        ...

    def destroy(self) -> None:
        """
        Cleans up the environment, removing any temporary resources.
        """
        ...

    @property
    def tools(self) -> ToolProxy:
        """
        Exposes tools available in the environment
        """
        ...

class LocalEnvironment:
    tool_proxy: ToolProxy = LocalToolProxy()
    cwd: str = os.getcwd()

    def __enter__(self):
        self.create()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.destroy()

    @property
    def tools(self):
        return self.tool_proxy

    def create(self):
        print("Local environment ready.")

    def destroy(self):
        print("Local environment cleaned up.")
