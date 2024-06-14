import datetime
import hashlib
import logging
import os
import select
import signal
import subprocess
import tarfile
import tempfile
import time
import traceback
from dataclasses import dataclass
from io import BytesIO
from subprocess import PIPE, STDOUT
from typing import Dict, Optional, Tuple

import docker
from swebench import (MAP_VERSION_TO_INSTALL, get_environment_yml,
                      get_requirements)

from devon_agent.environment import EnvironmentModule
from devon_agent.tool import Tool

LOGGER_NAME = "intercode"
START_UP_DELAY = 5
TIMEOUT_DURATION = 25


logger = logging.getLogger(LOGGER_NAME)


LONG_TIMEOUT = 500
PATH_TO_REQS = "/root/requirements.txt"
PATH_TO_ENV_YML = "/root/environment.yml"


def copy_file_to_container(container, contents, container_path):
    """
    Copies a given string into a Docker container at a specified path.

    Args:
    - container: Docker SDK container object.
    - contents: The string to copy into the container.
    - container_path: The path inside the container where the string should be copied to.

    Returns:
    - None
    """
    temp_file_name = None

    try:
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file_name = temp_file.name
            # Write the string to the temporary file and ensure it's written to disk
            temp_file.write(contents.encode("utf-8"))
            temp_file.flush()
            os.fsync(temp_file.fileno())

        # Create a TAR archive in memory containing the temporary file
        with tempfile.NamedTemporaryFile() as temp_tar:
            with open(temp_file_name, "rb") as temp_file:
                # Prepare the TAR archive
                with BytesIO() as tar_stream:
                    with tarfile.open(fileobj=tar_stream, mode="w") as tar:
                        tar_info = tarfile.TarInfo(
                            name=os.path.basename(container_path)
                        )
                        tar_info.size = os.path.getsize(temp_file_name)
                        tar.addfile(tarinfo=tar_info, fileobj=temp_file)
                    tar_stream.seek(0)
                    # Copy the TAR stream to the container
                    container.put_archive(
                        path=os.path.dirname(container_path), data=tar_stream.read()
                    )

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        logger.error(traceback.format_exc())
    finally:
        # Cleanup: Remove the temporary file if it was created
        if temp_file_name and os.path.exists(temp_file_name):
            os.remove(temp_file_name)


def read_with_timeout(container, pid_func, timeout_duration):
    """
    Read data from a subprocess with a timeout.
    This function uses a file descriptor to read data from the subprocess in a non-blocking way.

    Args:
        container (subprocess.Popen): The subprocess container.
        pid_func (function): A function that returns a list of process IDs (except the PID of the main process).
        timeout_duration (int): The timeout duration in seconds.

    Returns:
        str: The data read from the subprocess, stripped of trailing newline characters.

    Raises:
        TimeoutError: If the timeout duration is reached while reading from the subprocess.
    """
    buffer = b""
    fd = container.stdout.fileno()
    end_time = time.time() + timeout_duration

    while time.time() < end_time:
        pids = pid_func()
        if len(pids) > 0:
            # There are still PIDs running
            time.sleep(0.05)
            continue
        ready_to_read, _, _ = select.select([fd], [], [], 0.1)
        if ready_to_read:
            data = os.read(fd, 4096)
            if data:
                buffer += data
        else:
            # No more data to read
            break
        time.sleep(0.05)  # Prevents CPU hogging

    if container.poll() is not None:
        raise RuntimeError(
            "Subprocess exited unexpectedly.\nCurrent buffer: {}".format(
                buffer.decode()
            )
        )
    # if time.time() >= end_time:
    #     # raise TimeoutError("Timeout reached while reading from subprocess.\nCurrent buffer: {}\nRunning PIDs: {}".format(buffer.decode(), pids))
    #     print(traceback.print_exc())
    #     raise TimeoutError("Timeout reached while reading from subprocess.\nRunning PIDs: {}".format(pids))

    return buffer.decode()


class timeout:
    def __init__(self, seconds=TIMEOUT_DURATION, error_message="Timeout"):
        self.seconds = seconds
        self.error_message = error_message

    def handle_timeout(self, signum, frame):
        raise TimeoutError(self.error_message)

    def __enter__(self):
        signal.signal(signal.SIGALRM, self.handle_timeout)
        signal.alarm(self.seconds)

    def __exit__(self, type, value, traceback):
        signal.alarm(0)


def get_background_pids(container_obj):
    pids = (
        container_obj.exec_run("ps -eo pid,comm --no-headers")
        .output.decode()
        .split("\n")
    )
    pids = [x.split() for x in pids if x]
    pids = [x for x in pids if x[1] not in {"ps"} and x[0] != "1"]
    bash_pids = [x for x in pids if x[1] == "bash"]
    other_pids = [x for x in pids if x[1] not in {"bash"}]
    return bash_pids, other_pids


def _get_non_persistent_container(
    ctr_name: str, image_name: str
) -> Tuple[subprocess.Popen, set]:
    startup_cmd = [
        "docker",
        "run",
        "-i",
        "--rm",
        "--name",
        ctr_name,
        image_name,
        "/bin/bash",
        # "-e", "DEBIAN_FRONTEND=noninteractive",
        "-l",
        # "-m",
    ]
    container = subprocess.Popen(
        startup_cmd,
        stdin=PIPE,
        stdout=PIPE,
        stderr=STDOUT,
        text=True,
        bufsize=1,  # line buffered
    )
    time.sleep(START_UP_DELAY)
    # try to read output from container setup (usually an error), timeout if no output
    ready, _, _ = select.select([container.stdout], [], [], 2)
    if ready:
        output = container.stdout.readline().strip()
        if output:
            logger.error(f"Unexpected container setup output: {output}")
    return container, {
        "1",
    }  # bash PID is always 1 for non-persistent containers


def get_archive(path, ctr_name: str):
    client = docker.from_env()
    conatiner = client.containers.get(ctr_name)
    archive = conatiner.get_archive(path=path)

    return archive


def _get_persistent_container(
    ctr_name: str, image_name: str, persistent: bool = False
) -> Tuple[subprocess.Popen, set]:
    client = docker.from_env()
    containers = client.containers.list(all=True, filters={"name": ctr_name})
    if ctr_name in [c.name for c in containers]:
        container_obj = client.containers.get(ctr_name)
        if container_obj.status in {"created"}:
            container_obj.start()
        elif container_obj.status in {"running"}:
            pass
        elif container_obj.status in {"exited"}:
            container_obj.restart()
        elif container_obj.status in {"paused"}:
            container_obj.unpause()
        else:
            raise RuntimeError(f"Unexpected container status: {container_obj.status}")
    else:
        container_obj = client.containers.run(
            image_name,
            command="/bin/bash -l -m",
            name=ctr_name,
            stdin_open=True,
            tty=True,
            detach=True,
            auto_remove=not persistent,
        )
        container_obj.start()
    startup_cmd = [
        "docker",
        "exec",
        "-i",
        ctr_name,
        "/bin/bash",
        "-l",
        "-m",
    ]
    container = subprocess.Popen(
        startup_cmd,
        stdin=PIPE,
        stdout=PIPE,
        stderr=STDOUT,
        text=True,
        bufsize=1,  # line buffered
    )
    time.sleep(START_UP_DELAY)
    # try to read output from container setup (usually an error), timeout if no output
    ready, _, _ = select.select([container.stdout], [], [], 2)
    if ready:
        output = container.stdout.readline().strip()
        if output:
            logger.error(f"Unexpected container setup output: {output}")
    # Get the process IDs of the container
    # There should be at least a head process and possibly one child bash process
    bash_pids, other_pids = get_background_pids(container_obj)
    bash_pid = 1
    if len(bash_pids) == 1:
        bash_pid = bash_pids[0][0]
    elif len(bash_pids) > 1 or len(other_pids) > 0:
        raise RuntimeError(
            f"Detected alien processes attached or running. Please ensure that no other agents are running on this container. PIDs: {bash_pids}, {other_pids}"
        )
    return container, set(
        map(
            str,
            [
                bash_pid,
                1,
            ],
        )
    )


def get_container(
    ctr_name: str, image_name: str, persistent: bool = False
) -> subprocess.Popen:
    """
    Get a container object for a given container name and image name

    Arguments:
        ctr_name (str): Name of container
        image_name (str): Name of image
        persistent (bool): Whether to use a persistent container or not
    Returns:
        Container object
    """
    if persistent:
        return _get_persistent_container(ctr_name, image_name)
    else:
        return _get_non_persistent_container(ctr_name, image_name)


@dataclass(frozen=False)
class DockerEnvironment(EnvironmentModule):
    logger: logging.Logger
    image_name: str
    timeout: int
    container_name: Optional[str] = None
    persistent: bool = False

    def setup(self, **kwargs):
        if hasattr(self, "container"):
            try:
                self.container.terminate()
            except KeyboardInterrupt:
                raise
            except:
                pass

        if self.container_name is None:
            process_id = str(os.getpid())
            current_time = str(datetime.datetime.now())
            unique_string = current_time + process_id
            hash_object = hashlib.sha256(unique_string.encode())
            self.container_name = f"{self.image_name}-{hash_object.hexdigest()[:10]}"

        # this is what creates the actual container
        self.container, self.parent_pids = get_container(
            self.container_name, self.image_name, persistent=self.persistent
        )

        try:
            client = docker.from_env()
        except docker.errors.DockerException as e:
            if "Error while fetching server API version" in str(e):
                raise RuntimeError(
                    "Docker is not runninsg. Please start Docker and try again."
                ) from e
            raise e
        # ... why does this need to exist. the container already exists above...
        self.container_obj = client.containers.get(self.container_name)
        # self.logger.info("🌱 Environment Initialized")

        # self.communicate(
        #     "source /root/.bashrc",
        #     error_msg="Failed to source .bashrc",
        # )
        # self.communicate(
        #     "mkdir -p /root/commands",
        #     error_msg="Failed to create commands directory",
        # )
        # self.communicate(
        #     "touch /root/commands/__init__.py",
        #     error_msg="Failed to create __init__.py",
        # )
        # self.communicate(
        #     "export PATH=$PATH:/root/commands",
        #     error_msg="Failed to add commands directory to PATH",
        # )

    # They use commands because python tools wouldn't work without some sort of tool proxy
    def _communicate(
        self,
        input: str,
        timeout_duration=25,
    ) -> str:
        # Add \n, stdin write, flush => execute commant
        try:
            self.returncode = None
            cmd = input if input.endswith("\n") else input + "\n"
            self.container.stdin.write(cmd)
            time.sleep(0.1)
            self.container.stdin.flush()
        except BrokenPipeError:
            traceback.print_exc()
            self.logger.error(
                "Failed to communicate with container. Check docker logs for more information."
            )
            raise RuntimeError("Failed to communicate with container")

        # echo back last command
        try:
            buffer = read_with_timeout(self.container, self.get_pids, timeout_duration)
            self.container.stdin.write("echo $?\n")
            time.sleep(0.1)
            self.container.stdin.flush()
            exit_code = read_with_timeout(self.container, self.get_pids, 5).strip()
        except Exception as e:
            self.logger.error(f"Read with timeout failed on input:\n---\n{input}\n---")
            raise e

        # exit code bad => report bad
        if not exit_code.isdigit():
            raise RuntimeError(
                f"Container crashed. Failed to get exit code. Output:\n---\n{buffer}\n---"
            )

        self.returncode = int(exit_code)
        return buffer

    # Send shell commands in a format the container understands
    # Sends to stdin, and then gets the last stdout response (really should be that + stderr)
    def communicate(
        self,
        input: str,
        timeout_duration=25,
    ) -> str:
        """
        Sends input to container and returns output

        Args:
            input (`str`) - input to send to container shell

        Returns:
            output (`str`) - output from container
        """
        if input.strip() != "exit":
            output, valid = self._check_syntax(input)
            if not valid:
                return output  # shows syntax errors
            output = self._communicate(
                input,
                timeout_duration=timeout_duration,
            )
            self.communicate_output = output
            return output
        else:
            self.container.terminate()
            self.returncode = 0
            self.communicate_output = ""
            return ""

    def execute(self, input: str, timeout_duration=25):
        return self.communicate(input, timeout_duration=timeout_duration)

    def teardown(self, **kwargs):
        """
        Handle environment shutdown
        """
        self.logger.info("Beginning environment shutdown...")
        try:
            self.communicate(input="exit")
        except KeyboardInterrupt:
            raise
        except:
            pass
        self.container.terminate()
        if self.persistent:
            if self.container_obj.status not in {"paused", "exited"}:
                self.container_obj.pause()
                self.logger.info("Agent container paused")
            else:
                self.logger.info(f"Agent container status: {self.container_obj.status}")
        else:
            try:
                self.container_obj.remove(force=True)
            except KeyboardInterrupt:
                raise
            except:
                pass
            self.logger.info("Agent container stopped")


@dataclass(frozen=False)
class SWEEnvEnvironment(EnvironmentModule):
    logger: logging.Logger
    image_name: str
    container_name: Optional[str] = None
    persistent: bool = False
    timeout: Optional[int] = None
    no_mirror: bool = True
    token: str = None
    install_environment: bool = True

    def setup(self, **kwargs):
        if hasattr(self, "container"):
            try:
                self.container.terminate()
            except KeyboardInterrupt:
                raise
            except:
                pass

        if self.container_name is None:
            process_id = str(os.getpid())
            current_time = str(datetime.datetime.now())
            unique_string = current_time + process_id
            hash_object = hashlib.sha256(unique_string.encode())
            self.container_name = f"{self.image_name}-{hash_object.hexdigest()[:10]}"

        # this is what creates the actual container
        self.container, self.parent_pids = get_container(
            self.container_name, self.image_name, persistent=self.persistent
        )

        try:
            client = docker.from_env()
        except docker.errors.DockerException as e:
            if "Error while fetching server API version" in str(e):
                raise RuntimeError(
                    "Docker is not runninsg. Please start Docker and try again."
                ) from e
            raise e
        # ... why does this need to exist. the container already exists above...
        self.container_obj = client.containers.get(self.container_name)
        self.logger.info("🌱 Environment Initialized")

        self.communicate(
            "source /root/.bashrc",
            # error_msg="Failed to source .bashrc",
        )
        self.communicate(
            "mkdir -p /root/commands",
            # error_msg="Failed to create commands directory",
        )
        self.communicate(
            "touch /root/commands/__init__.py",
            # error_msg="Failed to create __init__.py",
        )
        self.communicate(
            "export PATH=$PATH:/root/commands",
            # error_msg="Failed to add commands directory to PATH",
        )

    def get_pids(self, all_pids=False) -> list[str]:
        """
        Gets list of processes running inside docker container
        """
        pids = (
            self.container_obj.exec_run("ps -eo pid,comm --no-headers")
            .output.decode()
            .split("\n")
        )
        pids = [x.split() for x in pids if x]
        if not all_pids:
            pids = [x for x in pids if x[1] != "ps" and x[0] not in self.parent_pids]
        return pids

    # They use commands because python tools wouldn't work without some sort of tool proxy
    def _communicate(
        self,
        input: str,
        timeout_duration=25,
    ) -> str:
        # Add \n, stdin write, flush => execute commant
        try:
            returncode = None
            cmd = input if input.endswith("\n") else input + "\n"
            self.container.stdin.write(cmd)
            time.sleep(0.1)
            self.container.stdin.flush()
        except BrokenPipeError:
            traceback.print_exc()
            self.logger.error(
                "Failed to communicate with container. Check docker logs for more information."
            )
            raise RuntimeError("Failed to communicate with container")

        # echo back last command
        try:
            buffer = read_with_timeout(self.container, self.get_pids, timeout_duration)
            self.container.stdin.write("echo $?\n")
            time.sleep(0.1)
            self.container.stdin.flush()
            exit_code = read_with_timeout(self.container, self.get_pids, 5).strip()
        except Exception as e:
            self.logger.error(f"Read with timeout failed on input:\n---\n{input}\n---")
            raise e

        # exit code bad => report bad
        if not exit_code.isdigit():
            raise RuntimeError(
                f"Container crashed. Failed to get exit code. Output:\n---\n{buffer}\n---"
            )

        return buffer, int(exit_code)

    # Send shell commands in a format the container understands
    # Sends to stdin, and then gets the last stdout response (really should be that + stderr)
    def communicate(
        self,
        input: str,
        timeout_duration=25,
    ) -> Tuple[str, int]:
        """
        Sends input to container and returns output

        Args:
            input (`str`) - input to send to container shell

        Returns:
            output (`str`) - output from container
        """
        if input.strip() != "exit":
            # output = self._communicate(input)
            # if not valid:
            #     return output  # shows syntax errors
            output, rc = self._communicate(
                input,
                timeout_duration=timeout_duration,
            )
            return output, rc
        else:
            self.container.terminate()
            rc = 0
            return "", rc

    def execute(self, input: str, timeout_duration=25):
        return self.communicate(input, timeout_duration=timeout_duration)

    def teardown(self, **kwargs):
        """
        Handle environment shutdown
        """
        self.logger.info("Beginning environment shutdown...")
        try:
            self.communicate(input="exit")
        except KeyboardInterrupt:
            raise
        except:
            pass
        self.container.terminate()
        if self.persistent:
            if self.container_obj.status not in {"paused", "exited"}:
                self.container_obj.pause()
                self.logger.info("Agent container paused")
            else:
                self.logger.info(f"Agent container status: {self.container_obj.status}")
        else:
            try:
                self.container_obj.remove(force=True)
            except KeyboardInterrupt:
                raise
            except:
                pass
            self.logger.info("Agent container stopped")

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

    def install_env(self, record) -> None:
        """
        Creates conda environment and installs third party dependencies to allow code execution
        """

        repo_name = record["repo"].replace("/", "__")
        # Create environment if does not exist yet

        # Check for env
        env_name = f"{repo_name}__{record['version']}"
        env_check, _ = self.communicate(
            f"conda env list | grep {env_name}", timeout_duration=LONG_TIMEOUT
        )

        # Map version to install?? based on task I guess. this seems relatively dumb. This probably makes up for like 5%-10% of would be failures lol
        install_configs = MAP_VERSION_TO_INSTALL[record["repo"]][str(record["version"])]

        # If env doesnt exist -> setup env bullshit (reqs.txt, or env.yaml, etc. not sure whats up here, what types of dependencies are needed)
        if env_check.strip() == "":
            self.logger.info(f"{env_name} conda env not found, creating...")
            packages = install_configs.get("packages", "")
            if packages == "requirements.txt":
                # Create conda environment
                self.communicate(
                    f"conda create -n {env_name} python={install_configs['python']} -y",
                    # error_msg="Failed to create conda environment",
                    timeout_duration=LONG_TIMEOUT,
                )
                # Write reqs to requirements.txt in docker container
                content_reqs = get_requirements(record)
                copy_file_to_container(self.container_obj, content_reqs, PATH_TO_REQS)

                # Create conda environment + install reqs
                self.communicate(
                    f"conda activate {env_name}",
                    # error_msg="Failed to activate conda environment",
                )
                self.communicate(
                    f"pip install -r {PATH_TO_REQS}",
                    # error_msg="Failed to install requirements.txt",
                    timeout_duration=LONG_TIMEOUT,
                )
                self.communicate(f"rm {PATH_TO_REQS}")
            elif packages == "environment.yml":
                # Write environment.yml to file
                content_env_yml = get_environment_yml(self.record, env_name)
                copy_file_to_container(
                    self.container_obj, content_env_yml, PATH_TO_ENV_YML
                )
                if "no_use_env" in install_configs and install_configs["no_use_env"]:
                    # Create conda environment
                    self.communicate(
                        f"conda create -c conda-forge -n {env_name} python={install_configs['python']} -y",
                        # error_msg="Failed to create conda environment",
                        timeout_duration=LONG_TIMEOUT,
                    )
                    # Install packages
                    self.communicate(
                        f"conda env update -f {PATH_TO_ENV_YML}",
                        # error_msg="Failed to install environment.yml",
                        timeout_duration=LONG_TIMEOUT,
                    )
                else:
                    # Create environment + install packages
                    self.communicate(
                        f"conda env create --file {PATH_TO_ENV_YML}",
                        # error_msg="Failed to create conda environment with environment.yml",
                        timeout_duration=LONG_TIMEOUT,
                    )
                self.communicate(f"rm {PATH_TO_ENV_YML}")
            else:
                # Create environment + install packages
                self.communicate(
                    f"conda create -n {env_name} python={install_configs['python']} {packages} -y",
                    # error_msg="Failed to create conda environment",
                    timeout_duration=LONG_TIMEOUT,
                )
            # Install extra pip packages if specified
            if "pip_packages" in install_configs:
                self.communicate(
                    f"source activate {env_name} && pip install {install_configs['pip_packages']}",
                    # error_msg="Failed to install pip packages",
                    timeout_duration=LONG_TIMEOUT,
                )

        # Activate environment
        self.communicate(
            f"conda activate {env_name}",
            # error_msg="Failed to activate conda environment"
        )

        # Install repo at base commit
        if "pre_install" in install_configs:
            self.logger.info("Running pre-install commands...")
            for pre_install_cmd in install_configs["pre_install"]:
                self.communicate(
                    pre_install_cmd,
                    # error_msg="Pre-install commands failed to execute successfully",
                )
        self.logger.info(f"Installing {repo_name} at base commit...")
        if "install" in install_configs:
            install_cmd = install_configs["install"]
            self.communicate(
                install_cmd,
                # error_msg="Install command failed to execute successfully",
                timeout_duration=LONG_TIMEOUT,
            )
        if "post_install" in install_configs:
            self.logger.info("Running post-install commands...")
            for post_install_cmd in install_configs["post_install"]:
                self.communicate(
                    post_install_cmd,
                    # error_msg="Post-install commands failed to execute successfully",
                )

    def get_cwd(self):
        return self.execute("pwd")[0]

    def reset(self, record):
        self.communicate("cd /")

        base_commit = record["base_commit"]
        query = record["problem_statement"]
        folders = self.communicate(input="ls")[0].split("\n")
        print(folders)
        repo_name = record["repo"].replace("/", "__")
        self.base_path = "/" + record["repo"].replace("/", "__")
        print(self.communicate("ls " + self.base_path)[0])

        if repo_name not in folders:
            if not self.no_mirror:
                self.logger.info(f"{repo_name} not found in container, cloning...")
                error, rc = self.communicate(
                    input=f"git clone https://{self.token}@github.com/{record['repo']}.git {repo_name}",
                    # error_msg="Failed to clone repository from mirror",
                    timeout_duration=LONG_TIMEOUT,
                )
                if rc != 0:
                    raise RuntimeError("Failed to clone repository from mirror" + error)
                # self.logger.info(f"{repo_name} not found in container, cloning...")
            else:
                logger.info(f"Trying to clone from non-mirror...")
                _, rc = self.communicate(
                    input=f"git clone https://{self.token}@github.com/{record['repo']}.git {repo_name}",
                    # error_msg="Failed to clone repository from non-mirror",
                    timeout_duration=LONG_TIMEOUT,
                )
                if rc != 0:
                    raise RuntimeError("Failed to clone repository from non-mirror")
        print(self.communicate("ls " + self.base_path)[0])

        for cmd in [
            "echo -n > /root/files_to_edit.txt",
            f"cd {repo_name}",
            "export ROOT=$(pwd -P)",
            "git status",
            "git restore .",
            f"git reset --hard {base_commit}",
            "git clean -fdxq",
        ]:
            _, rc = self.communicate(
                input=cmd,
                # error_msg="Failed to clean repository",
            )
            if rc != 0:
                raise RuntimeError("Failed to reset repository")

        for cmd in [
            "export CURRENT_FILE=" "",
            "export CURRENT_LINE=0",
            "export SEARCH_RESULTS=()",
            "export SEARCH_FILES=()",
            "export SEARCH_INDEX=0",
        ]:
            _, rc = self.communicate(
                input=cmd,
                # error_msg="Failed to reset environment variables",
            )
            if rc != 0:
                raise RuntimeError("Failed to reset environment variables")

        _, rc = self.communicate(
            "source /root/miniconda3/etc/profile.d/conda.sh",
            # error_msg="Failed to source conda",
        )
        if rc != 0:
            raise RuntimeError("Failed to source conda")

        system = self.communicate("uname -s")[0].strip().lower()
        arch = self.communicate("uname -m")[0].strip().lower()
        if system == "linux" and arch == "x86_64":
            self.communicate(
                f"apt update; apt install build-essential -y",
                timeout_duration=LONG_TIMEOUT,
            )

        if self.install_environment:
            self.install_env(record)

    def create_tar(self, file_path):
        tar_data, _ = self.container_obj.get_archive(path=file_path)

        return tar_data
