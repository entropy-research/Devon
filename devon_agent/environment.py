import os
import traceback
from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable, Dict, Tuple, Protocol


if TYPE_CHECKING:
    from devon_agent.session import Session
    from devon_agent.tool import Tool


@dataclass(frozen=False)
class EnvironmentModule(Protocol):
    # tools : list[]

    @property
    def name(self):
        pass

    def setup(self, session: "Session", **kwargs): ...

    def teardown(self, **kwargs): ...

    def __enter__(self):
        self.setup()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.teardown(exc_type, exc_value, traceback)

    def execute(self, input: str, timeout_duration=25) -> Tuple[str, int]: ...

    def register_tools(self, tools: Dict[str, "Tool"]): ...

    def set_default_tool(self, tool: "Tool"): ...

    @property
    def tools(self) -> Dict[str, "Tool"]: ...

    """
    in session, if tool in env.tools, then call tool with env in context
    """


@dataclass(frozen=False)
class LocalEnvironment:
    path: str

    @property
    def name(self):
        return "local"

    def setup(self, session: "Session", **kwargs):
        self.old_dir = os.getcwd()
        os.chdir(self.path)
        self.session = session

        import queue
        import subprocess
        import threading

        # Function to read output and error streams in separate threads
        def enqueue_output(pipe, queue):
            for line in iter(pipe.readline, ""):
                queue.put(line)
            pipe.close()

        # Start a new shell process
        self.process = subprocess.Popen(
            ["/bin/bash"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
            text=True,
        )

        # Queues to hold stdout and stderr
        # self.stdout_queue = queue.Queue()
        # self.stderr_queue = queue.Queue()

        # # Threads to read stdout and stderr
        # self.stdout_thread = threading.Thread(target=enqueue_output, args=(self.process.stdout, self.stdout_queue))
        # self.stderr_thread = threading.Thread(target=enqueue_output, args=(self.process.stderr, self.stderr_queue))

        # Start the threads
        # self.stdout_thread.start()
        # self.stderr_thread.start()
        # self.process = subprocess.Popen(["/bin/bash"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    def teardown(self, **kwargs):
        os.chdir(self.old_dir)

    def get_cwd(self):
        return self.execute("pwd")[0]

    def communicate(self, input: str, timeout_duration=25):
        return self.execute(input, timeout_duration=timeout_duration)

    def execute(self, input: str, timeout_duration=25):
        try:
            self.session.event_log.append(
                {
                    "type": "EnvironmentRequest",
                    "content": input,
                    "producer": "tool",
                    "consumer": self.name,
                }
            )

            self.process.stdin.write(input + "\n")
            self.process.stdin.write('echo "\n$?"\n')
            self.process.stdin.write("echo 'EOL'\n")
            self.process.stdin.write(f"echo 'EOL' >&2\n")
            self.process.stdin.flush()

            output = ""
            error = ""

            while (line := self.process.stdout.readline()) != "EOL\n":
                output += line

            while (line := self.process.stderr.readline()) != "EOL\n":
                error += line

            # print(output.splitlines())
            return_code = int(output.splitlines()[-1])
            output = "\n".join(output.splitlines()[:-1])
            # print(return_code)
            output = output if return_code == 0 else error

            self.session.event_log.append(
                {
                    "type": "EnvironmentResponse",
                    "content": output,
                    "producer": self.name,
                    "consumer": "tool",
                }
            )

            return output, return_code
        except Exception as e:
            traceback.print_exc()
            return str(e), -1

    def __enter__(self):
        self.setup()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.teardown(exc_type, exc_value, traceback)

    def register_tools(self, tools: Dict[str, "Tool"]):
        if "_tools" not in self.__dict__:
            self._tools = {}
        if self._tools is None:
            self._tools = {}
        self._tools.update(tools)

    def set_default_tool(self, tool: "Tool"):
        self.default_tool = tool

    @property
    def tools(self) -> Dict[str, "Tool"]:
        return self._tools


# @dataclass(frozen=False)
# class SWEBenchEnvironment:


@dataclass(frozen=False)
class UserEnvironment:
    user_func: Callable

    @property
    def name(self):
        return "user_environment"

    def setup(self, session: "Session", **kwargs):
        self.session = session

    def teardown(self, **kwargs):
        pass

    def execute(self, input: str, timeout_duration=25):
        self.session.event_log.append(
            {
                "type": "UserRequest",
                "content": input,
                "producer": "tool",
                "consumer": self.name,
            }
        )
        response = self.user_func()
        self.session.event_log.append(
            {
                "type": "UserResponse",
                "content": response,
                "producer": self.name,
                "consumer": "tool",
            }
        )
        return response

    def register_tools(self, tools: Dict[str, "Tool"]):
        if "_tools" not in self.__dict__:
            self._tools = {}
        if self._tools is None:
            self._tools = {}
        self._tools.update(tools)

    def set_default_tool(self, tool: "Tool"):
        self.default_tool = tool

    @property
    def tools(self) -> Dict[str, "Tool"]:
        return self._tools


if __name__ == "__main__":
    from devon_agent.session import Session, SessionArguments

    # from devon_agent.agent import Agent
    command = "cat /Users/mihirchintawar/agent/devon_swe_bench_experimental/swebenchenv/environment/swe_env.py"

    session = Session(
        args=SessionArguments(
            path=".", user_input=lambda: "Hello, World!", name="test"
        ),
        agent=None,
    )

    localEnv = LocalEnvironment(path=".")

    localEnv.setup(session)
    output, code = localEnv.execute(command)
    localEnv.teardown()
    print(output, code)

    # process = subprocess.Popen(["/bin/bash"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, text=True)

    # process.stdin.write(command + '\n')
    # process.stdin.write("echo 'EOL'\n")
    # process.stdin.write(f"echo 'EOL' >&2\n")
    # process.stdin.flush()

    # output = ""
    # error = ""

    # while (line := process.stdout.readline()) != 'EOL\n':
    #     output += line

    # while (line := process.stderr.readline()) != 'EOL\n':
    #     error += line

    # print("\n".join(output.splitlines()))
    # print("ERROR",error)
