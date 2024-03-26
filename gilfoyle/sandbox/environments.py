import docker
from typing import Optional

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

    def execute(self, command: List[str]) -> str:
        """
        Executes a given command within the environment and returns the output.

        :param command: A list of strings representing the command and its arguments.
        :return: The output from executing the command as a string.
        """
        ...




class LocalEnvironment:
    cwd: str = "./.devant"

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def create(self):
        print("Local environment ready.")

    def destroy(self):
        print("Local environment cleaned up.")

    def execute(self, command: list[str]) -> str:
        import subprocess
        import os
        if not os.path.exists(self.cwd):
            os.makedirs(self.cwd)
        result = subprocess.run(command, capture_output=True, text=True, cwd=self.cwd)
        if result.returncode == 0:
            return result.stdout
        else:
            print(f"Error executing command: {result.stderr}")
            return ""
    

class PythonContainer:
    image: str = "python:latest"
    client: docker.DockerClient
    cwd: str = "/"

    def __init__(self):
        self.client = docker.from_env()
        self.container: Optional[docker.models.containers.Container] = None

    def __enter__(self):
        self.create()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.destroy()

    def create(self):
        try:
            self.container = self.client.containers.run(
                self.image,
                detach=True,
                stdin_open=True,
                tty=True,
                command=["/bin/bash", "-c", "apt-get update && apt-get install -y git && bash"]
            )
            print(f"Container created with ID: {self.container.id}")
        except docker.errors.APIError as e:
            print(f"Error creating container: {e}")

    def destroy(self):
        if self.container:
            try:
                self.container.stop()
                self.container.remove()
                print("Container destroyed.")
            except docker.errors.APIError as e:
                print(f"Error destroying container: {e}")
        else:
            print("No container to destroy.")

    def execute(self, command: list[str]) -> str:
        if self.container:
            try:
                exit_code, output = self.container.exec_run(command, workdir=self.cwd)
                return output.decode("utf-8")
            except docker.errors.APIError as e:
                print(f"Error executing command: {e}")
        else:
            print("No container found. Please create a container first.")