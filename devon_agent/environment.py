import asyncio
import datetime
import hashlib
import os
import re
import subprocess
import select

from dataclasses import dataclass, field
import sys
import tempfile
import time
import traceback

from typing import Callable, Dict, List, Optional, Protocol,TYPE_CHECKING, Tuple
import uuid

from git import Repo



if TYPE_CHECKING:
    from devon_agent.tool import Tool
    from devon_agent.session import Session


@dataclass(frozen=False)
class EnvironmentModule(Protocol):
    # tools : list[]

    @property
    def name(self):
        pass

    def setup(self, session : 'Session', **kwargs): ...

    def teardown(self, **kwargs): ...

    def __enter__(self):
        self.setup()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.teardown(exc_type, exc_value, traceback)

    def execute(self, input: str, timeout_duration=25) -> Tuple[str, int]: ...

    def register_tools(self, tools: Dict[str,'Tool']):...

    def set_default_tool(self, tool: 'Tool'):...

    @property
    def tools(self) -> Dict[str, 'Tool']:...

    """
    in session, if tool in env.tools, then call tool with env in context
    """


@dataclass(frozen=False)
class LocalEnvironment:
    path: str

    @property
    def name(self):
        return "local"
    
    def setup(self, session : 'Session', **kwargs):
        self.old_dir = os.getcwd()
        os.chdir(self.path)
        self.session = session

        import subprocess
        # Start a new shell process
        self.process = subprocess.Popen(["/bin/bash"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, text=True)

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

            self.session.event_log.append({
                "type" : "EnvironmentRequest",
                "content" : input,
                "producer" : "tool",
                "consumer" : self.name,
            })

            self.process.stdin.write(input + '\n')
            self.process.stdin.write('echo "$?"\n')
            self.process.stdin.write("echo 'EOL'\n")
            self.process.stdin.write(f"echo 'EOL' >&2\n")
            self.process.stdin.flush()

            output = ""
            error = ""

            while (line := self.process.stdout.readline()) != 'EOL\n':
                output += line

            while (line := self.process.stderr.readline()) != 'EOL\n':
                error += line

            # print(output.splitlines())
            return_code = int(output.splitlines()[-1])
            output = "\n".join(output.splitlines()[:-1])
            # print(return_code)
            output = (
                output
                if return_code == 0
                else error
            )

            self.session.event_log.append({
                "type" : "EnvironmentResponse",
                "content" : output,
                "producer" : self.name,
                "consumer" : "tool",
            })

            return output, return_code
        except Exception as e:
            traceback.print_exc()
            return str(e), -1
    
    def __enter__(self):
        self.setup()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.teardown(exc_type, exc_value, traceback)

    def register_tools(self, tools: Dict[str, 'Tool']):
        if "_tools" not in self.__dict__:
            self._tools = {}
        if self._tools is None:
            self._tools = {}
        self._tools.update(tools)
    
    def set_default_tool(self, tool: 'Tool'):
        self.default_tool = tool

    @property
    def tools(self) -> Dict[str, 'Tool']:
        return self._tools
    
class Job:
    named_pipe_stdout : str
    named_pipe_stderr : str
    command : str
    status : str
    start_time : datetime.datetime
    end_time : datetime.datetime
    exit_code : Optional[int]
    stdout : str
    stderr : str

class JobShellEnvironment:
    path: str
    jobs : List[Job]

    @property
    def name(self):
        return "job_shell"
    
    def setup(self, session : 'Session', **kwargs):
        self.session = session
        self.jobs = []

        self.old_dir = os.getcwd()
        os.chdir(self.path)
        self.session = session

        import subprocess
        # Start a new shell process
        self.process = subprocess.Popen(["/bin/bash"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, text=True)

    def teardown(self, **kwargs):
        os.chdir(self.old_dir)

    def get_cwd(self):
        return self.execute("pwd")[0]

    def communicate(self, input: str, timeout_duration=25):
        return self.execute(input, timeout_duration=timeout_duration)
    
    def _execute_in_shell(self, command: str):
        try:

            self.session.event_log.append({
                "type" : "EnvironmentRequest",
                "content" : command,
                "producer" : "tool",
                "consumer" : self.name,
            })

            self.process.stdin.write(command + '\n')
            self.process.stdin.write('echo "$?"\n')
            self.process.stdin.write("echo 'EOL'\n")
            self.process.stdin.write(f"echo 'EOL' >&2\n")
            self.process.stdin.flush()

            output = ""
            error = ""

            while (line := self.process.stdout.readline()) != 'EOL\n':
                output += line

            while (line := self.process.stderr.readline()) != 'EOL\n':
                error += line

            # print(output.splitlines())
            return_code = int(output.splitlines()[-1])
            output = "\n".join(output.splitlines()[:-1])
            # print(return_code)
            output = (
                output
                if return_code == 0
                else error
            )

            self.session.event_log.append({
                "type" : "EnvironmentResponse",
                "content" : output,
                "producer" : self.name,
                "consumer" : "tool",
            })

            return output, return_code
        except Exception as e:
            traceback.print_exc()
            return str(e), -1

    def execute(self, input: str, timeout_duration=25):
        # make a named pipe
        # start background process that writes to the pipe
        # after every second for fifteen seconds check if process ended
        # if ended, then read from pipe
        # if not ended, then raise exception
        # returm with output and continue letting it run in the background

        # Job System
        # 0. named pipe
        # 1. Job Id (process Id)
        # 2. Command
        # 3. Status (running, returned, failed)
        # 4. Start Time
        # 5. End Time
        # 6. Exit Code
        # 7. Stdout
        # 8. Stderr

        named_pipe = os.mkfifo("named_pipe")
        output,rc = self._execute_in_shell(f"{command} > {named_pipe} &\n" + "echo 'EOJ' > " + named_pipe)
        for i in range(15):
            # read from named pipe
            # if EOJ, then break
            # if not EOJ, then raise exception
            # if EOJ, then return output and exit code
            # if not EOJ, then continue




            while (line := named_pipe.readline()) != 'EOJ\n':
                output += line
            


            
        





    





# @dataclass(frozen=False)
# class SWEBenchEnvironment:


@dataclass(frozen=False)
class UserEnvironment:
    user_func: Callable

    @property
    def name(self):
        return "user_environment"

    def setup(self, session : 'Session', **kwargs):
        self.session = session

    def teardown(self, **kwargs):
        pass

    def execute(self, input: str, timeout_duration=25):
        self.session.event_log.append({
                "type" : "UserRequest",
                "content" : input,
                "producer" : "tool",
                "consumer" : self.name,
            })
        response =  self.user_func()
        self.session.event_log.append({
                "type" : "UserResponse",
                "content" : response,
                "producer" : self.name,
                "consumer" : "tool",
            })
        return response

    def register_tools(self, tools: Dict[str,'Tool']):
        if "_tools" not in self.__dict__:
            self._tools = {}
        if self._tools is None:
            self._tools = {}
        self._tools.update(tools)

    def set_default_tool(self, tool: 'Tool'):
        self.default_tool = tool

    @property
    def tools(self) -> Dict[str, 'Tool']:
        return self._tools


if __name__ == "__main__":
    from devon_agent.session import Session,SessionArguments
    # from devon_agent.agent import Agent
    command = "cat /Users/mihirchintawar/agent/devon_swe_bench_experimental/swebenchenv/environment/swe_env.py"

    session = Session(
        args = SessionArguments(
            path=".",
            user_input=lambda: "Hello, World!",
            name="test"
        ),
        agent=None
    )

    localEnv = LocalEnvironment(path=".")

    localEnv.setup(session)
    output,code =localEnv.execute(command)
    localEnv.teardown()
    print(output,code)

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

from datetime import datetime
import select

@dataclass
class Job:
    named_pipe_stdout: str
    named_pipe_stderr: str
    command: str
    status: str
    start_time: datetime
    pid: Optional[int] = None
    end_time: Optional[datetime] = None
    exit_code: Optional[int] = None
    stdout: str = ""
    stderr: str = ""

@dataclass(frozen=False)
class JobShellEnvironment:
    path: str
    jobs: Dict[str, Job] = field(default_factory=dict)

    @property
    def name(self):
        return "local"

    def setup(self, **kwargs):
        self.old_dir = os.getcwd()
        os.chdir(self.path)
        # self.session = session
        self.process = subprocess.Popen(
            ["/bin/bash"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

    def teardown(self, **kwargs):
        os.chdir(self.old_dir)
        self.process.terminate()
        for job in self.jobs.values():
            os.unlink(job.named_pipe_stdin)
            os.unlink(job.named_pipe_stdout)
            os.unlink(job.named_pipe_stderr)

    def get_cwd(self):
        return self.execute("pwd").stdout.strip()

    def execute(self, input: str, timeout_duration=15) -> Job:
        try:
            # self.session.event_log.append({
            #     "type": "EnvironmentRequest",
            #     "content": input,
            #     "producer": "tool",
            #     "consumer": self.name,
            # })


            stdout_pipe_path = tempfile.mkstemp()[1]
            stderr_pipe_path = tempfile.mkstemp()[1]
            # os.mkfifo(stdout_pipe_path)
            # os.mkfifo(stderr_pipe_path)

            job = Job(
                named_pipe_stdout=stdout_pipe_path,
                named_pipe_stderr=stderr_pipe_path,
                command=input,
                status="running",
                start_time=datetime.now(),
            )
            self.jobs[input] = job

            self.process.stdin.write(f"({input}; echo 'EXIT_CODE: '$? >&2; echo 'PID: '$! >&2; echo 'EOL' > {stdout_pipe_path}; echo 'EOL' >&2) > {stdout_pipe_path} 2> {stderr_pipe_path} &\n")
            print(f"({input}; echo 'EXIT_CODE: '$? >&2; echo 'PID: '$! >&2; echo 'EOL' > {stdout_pipe_path}; echo 'EOL' >&2) > {stdout_pipe_path} 2> {stderr_pipe_path} &\n")
            self.process.stdin.flush()


            for i in range(int(timeout_duration / 0.1)):
                print(i)
                stdout, stderr, exit_code, pid = self.read_background_output(job)
                job.stdout += stdout
                job.stderr += stderr
                print(exit_code)
                if exit_code is not None:
                    job.exit_code = exit_code
                    job.pid = pid
                    job.status = "finished"
                    job.end_time = datetime.now()

                    break
                time.sleep(0.1)  # Add a small delay to avoid excessive CPU usage


            if job.status == "finished":
                # self.session.event_log.append({
                #     "type": "EnvironmentResponse",
                #     "content": job.stdout,
                #     "producer": self.name,
                #     "consumer": "tool",
                # })
                if job.exit_code == 0:
                    return job.stdout, job.exit_code
                else:
                    return job.stderr, job.exit_code
            else:
                return job

        except Exception as e:
            traceback.print_exc()
            raise e
            # job.status = "error"
            # job.end_time = datetime.now()
            # job.stderr = str(e)
            # return job

    def read_background_output(self, job: Job) -> Tuple[str, str, Optional[int], Optional[int]]:
        stdout = ""
        stderr = ""
        exit_code = None
        pid = None

        

        stdout_fd = os.open(job.named_pipe_stdout, os.O_RDONLY | os.O_NONBLOCK)
        stderr_fd = os.open(job.named_pipe_stderr, os.O_RDONLY | os.O_NONBLOCK)

        returned = False
        no_data = False
        while True:
            print("test")
            try:
                stdout_data = os.read(stdout_fd, 1024).decode()
                if not stdout_data:
                    no_data = True
                    
                stdout += stdout_data
            except BlockingIOError:
                break
                pass

            try:
                stderr_data = os.read(stderr_fd, 1024).decode()
                print(stderr_data)
                if not stderr_data and no_data:
                    print("no data")
                    break
                elif no_data:
                    no_data = False

                stderr += stderr_data
                if 'EXIT_CODE: ' in stderr_data:
                    exit_code_match = re.search(r'EXIT_CODE: (\d+)', stderr_data)
                    if exit_code_match:
                        exit_code = int(exit_code_match.group(1))
                if 'PID: ' in stderr_data:
                    pid_match = re.search(r'PID: (\d+)', stderr_data)
                    if pid_match:
                        pid = int(pid_match.group(1))
            except BlockingIOError:
                break
                pass

            if 'EOL\n' in stdout and 'EOL\n' in stderr:
                returned = True
                break


            time.sleep(0.1)

        os.close(stdout_fd)
        os.close(stderr_fd)

        stdout = stdout.split('EOL\n')[0]
        stderr = stderr.split('EOL\n')[0]

        if returned:
            job.status = "returned"
            job.end_time = datetime.now()
            job.stdout += stdout
            job.stderr += stderr
            job.stderr = "\n".join(job.stderr.splitlines()[:-2])
            job.exit_code = exit_code
            job.pid = pid
        

        return stdout, stderr, exit_code, pid

    def write_to_stdin(self, job: Job, data: str):
        with open(job.named_pipe_stdin, "w") as stdin_pipe:
            stdin_pipe.write(data)