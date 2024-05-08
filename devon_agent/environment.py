import asyncio
import os
import re
import subprocess

from dataclasses import dataclass

from typing import Protocol


@dataclass(frozen=False)
class Environment(Protocol):
    path: str

    def enter(self): ...

    def exit(self): ...

    def __enter__(self): ...

    def __exit__(self, exc_type, exc_value, traceback): ...

    def execute(self, input: str, timeout_duration=25): ...


@dataclass(frozen=False)
class LocalEnvironment(Environment):
    path: str

    def enter(self):
        self.old_dir = os.getcwd()
        os.chdir(self.path)

    def exit(self):
        os.chdir(self.old_dir)

    def get_cwd(self):
        return self.execute("pwd")[0]

    def communicate(self, input: str, timeout_duration=25):
        return self.execute(input, timeout_duration=timeout_duration)

    def execute(self, command: str, timeout_duration=25):
        try:
            completed_process = subprocess.run(
                command, shell=True, timeout=timeout_duration, capture_output=True
            )

            if completed_process.returncode != 0:
                return completed_process.stderr.decode(
                    "utf-8"
                ), completed_process.returncode

            output = (
                completed_process.stdout.decode("utf-8")
                if completed_process.stdout
                else ""
            )
        except Exception as e:
            return str(e), -1

        return output, completed_process.returncode

    async def execute_async(self, command: str, timeout_duration=25):
        process = await asyncio.create_subprocess_shell(
            command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=timeout_duration
            )
        except asyncio.TimeoutError:
            process.kill()
            await process.communicate()
            return "Command timed out", -1

        if process.returncode != 0:
            return stderr.decode("utf-8"), process.returncode

        output = stdout.decode("utf-8") if stdout else ""
        return output, process.returncode

    def __enter__(self):
        self.enter()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.exit()
