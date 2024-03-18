import docker
from typing import Optional

"""
This module contains the PythonContainer class, which represents a Docker container running Python.

The primary method of interacting with the container is the `execute` method, which runs a command inside the container and returns the output.
"""

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