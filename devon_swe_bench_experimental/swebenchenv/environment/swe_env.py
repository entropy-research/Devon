import datetime
import difflib
import inspect
import io
import json
import tarfile
import tempfile
from anthropic import Anthropic
import docker
import gymnasium as gym
import hashlib
import logging
import os
import re
import subprocess
import traceback
import time


from dataclasses import dataclass
from git import Repo
from rich.logging import RichHandler
from simple_parsing.helpers import Serializable
from devon_swe_bench_experimental.retrieval.main import ClassTable, FunctionTable, get_class_defn, get_function_defn, initialize_repository
from devon_swe_bench_experimental.swebenchenv.environment.unified_diff.prompts.udiff_prompts import UnifiedDiffPrompts
from devon_swe_bench_experimental.swebenchenv.environment.unified_diff.udiff import DATA_LOGGER_NAME, Hallucination, create_recover_prompt, log_failed_diff, log_successful_diff
from devon_swe_bench_experimental.swebenchenv.environment.unified_diff.udiff import apply_file_context_diffs, extract_all_diffs
from devon_swe_bench_experimental.swebenchenv.environment.utils import (
    copy_file_to_container,
    extract_signature_and_docstring,
    get_container,
    get_instances,
    is_from_github_url,
    read_with_timeout,
    LOGGER_NAME,
)
from swebench import (
    get_environment_yml,
    get_requirements,
    MAP_VERSION_TO_INSTALL
)
from typing import List, Optional, Tuple

from devon_agent.agent.clients.client import GPT4, ClaudeSonnet, Message, ClaudeOpus

LONG_TIMEOUT = 500
PATH_TO_REQS = "/root/requirements.txt"
PATH_TO_ENV_YML = "/root/environment.yml"

console_handler = RichHandler(show_time=False, show_path=False)
console_handler.setLevel(logging.INFO)
file_handler = logging.FileHandler('debug.log')
file_handler.setLevel(logging.DEBUG)

logger = logging.getLogger(LOGGER_NAME)
logger.setLevel(logging.DEBUG)  # Set to debug since we want all messages to be caught by the logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)
logger.propagate = False

diff_logger = logging.getLogger(DATA_LOGGER_NAME)


data_handler = logging.FileHandler('udiff_data.log')

diff_logger.setLevel(logging.DEBUG)
diff_logger.addHandler(data_handler)

class TableCache():

    def __init__(self, dir, function_table=None, class_table=None):
        self.dir = dir
        self.function_table = function_table if function_table is not None else FunctionTable()
        self.class_table = class_table if class_table is not None else ClassTable()
    
    def save(self, issue_id):
        self.function_table.save_to_file(os.path.join(self.dir, f"function_table_{issue_id}.json"))
        self.class_table.save_to_file(os.path.join(self.dir, f"class_table_{issue_id}.json"))

    def load(self, issue_id):
        self.function_table.load_from_file(os.path.join(self.dir, f"function_table_{issue_id}.json"))
        self.class_table.load_from_file(os.path.join(self.dir, f"class_table_{issue_id}.json"))

    def exists(self, issue_id):
        return os.path.exists(os.path.join(self.dir, f"function_table_{issue_id}.json")) and os.path.exists(os.path.join(self.dir, f"class_table_{issue_id}.json"))


@dataclass(frozen=False)
class EnvironmentArguments(Serializable):
    data_path: str
    image_name: str
    split: str = "dev"
    base_commit: Optional[str] = None  # used only with data_path as url
    container_name: Optional[str] = None
    install_environment: bool = True
    timeout: int = 35
    verbose: bool = False
    no_mirror: bool = False
    specific_issues: Optional[List[str]] = None


class SWEEnv(gym.Env):
    """Gym environment for SWE-bench. This class should handle all communication with the docker container."""

    name = "swe_main"

    def __init__(self, args: EnvironmentArguments,specific_issues: Optional[List[str]] = None):
        super().__init__()
        print("SWEEnv init")
        self.args = args
        self.base_commit = None
        self.communicate_output = None
        self.container_name = args.container_name
        self.install_environment = args.install_environment
        self.logger = logger
        self.persistent = args.container_name is not None #If set then persist the container across runs
        self.returncode = None
        self.is_from_github_url = is_from_github_url(args.data_path)
        self.editor = {}
        self.class_table = ClassTable()
        self.function_table = FunctionTable()
        self.table_cache = TableCache(dir="table_cache", function_table=self.function_table, class_table=self.class_table)
        self.TESTING_TIPS = None

        print(self.container_name)
        
        # self.diff_model = ClaudeSonnet(client=anthrpoic_client, system_message=UnifiedDiffPrompts.main_system_v2, max_tokens=4096)

        if not self.args.verbose:
            self.logger.disabled = True

        # Get commit hash
        try:
            repo = Repo(search_parent_directories=True) # Identify current git repo!
            self.commit_sha = repo.head.object.hexsha
        except KeyboardInterrupt:
            raise
        except:
            logger.warning("Failed to get commit hash for this repo")
            self.commit_sha = None

        # Set GitHub Token
        self.token = os.environ.get("GITHUB_TOKEN", None) #Github token
        if (self.token is None or self.token == "") and os.path.isfile(
            os.path.join(os.getcwd(), "keys.cfg")
        ):
            self.cfg = config.Config(os.path.join(os.getcwd(), "keys.cfg"))
            self.token = self.cfg.get("GITHUB_TOKEN", "git")

        # Load Task Instances
        self.data_path = self.args.data_path
        self.data = get_instances(self.data_path, self.args.base_commit, self.args.split, token=self.token,specific_issues=specific_issues) #Load data from path
        self.logger.info(f"💽 Loaded dataset from {self.data_path}")
        self.issues = specific_issues

        # Establish connection with execution container
        self.image_name = args.image_name
        self._reset_container()
        # Set timeout
        self.timeout = self.args.timeout
        self.idx = 1
        self.clean_multi_line_functions = lambda x: x

    def reset(self, index: int = None, apply_test_patch: bool = False) -> Tuple[str, dict]:
        """
        Function to reset container between each task instance.
        * Clones instance's repository
        * Cleans repository of prior modifications
        * Resets environment variables
        * Check out base commit

        Arguments:
            index (`int`) - index of task instance to reset to
        Returns:
            observation (`str`) - output from container
            info (`dict`) - additional information (e.g. debugging information)
        """
        info = {}
        info["commit_sha"] = self.commit_sha

        self.editor = {}

        self.function_table = FunctionTable()
        self.class_table = ClassTable()

        # Get task instance
        self.idx = index if index is not None else self.idx
        self.record = self.data[self.idx] #Self.record maintains tasks specific information, idx is used to access specific tasks in the loaded dataset. sharding is the only way to parallelize, even then apikey rate limits will hit. can reduce this w env step speed.
        self.idx += 1

        # Set query, gold command
        self.base_commit = self.record["base_commit"]
        self.query = self.record["problem_statement"]
        self.reward = None

        logger.info(f"Issue {self.record['instance_id']}")

        ### Setup Container ###

        # Clone repository if not already cloned
        self.communicate(input="cd /")

        # self.create_file("something.py", "#hello")
        # r = self.communicate(input="python something.py")
        # print(r, self.returncode)
        # exit()
        folders = self.communicate(input="ls").split("\n")
        repo_name = self.record["repo"].replace("/", "__")
        self.file_root = "/" + self.record['repo'].replace('/', '__')
        if repo_name not in folders:
            if not self.args.no_mirror and not self.is_from_github_url:
                self.logger.info(f"{repo_name} not found in container, cloning...")
                self.communicate_with_handling(
                    input=f"git clone https://{self.token}@github.com/swe-bench/{repo_name}.git",
                    error_msg="Failed to clone repository from mirror",
                    timeout_duration=LONG_TIMEOUT,
                )
                self.logger.info(f"{repo_name} not found in container, cloning...")
            else:
                logger.info(f"Trying to clone from non-mirror...")
                self.communicate_with_handling(
                    input=f"git clone https://{self.token}@github.com/{self.record['repo']}.git {repo_name}",
                    error_msg="Failed to clone repository from non-mirror",
                    timeout_duration=LONG_TIMEOUT,
                )

        # Clean repository of any modifications + Checkout base commit
        # Files to edit is like the perfect oracle mode afaik. Need to isolate to not that?
        for cmd in [
            "echo -n > /root/files_to_edit.txt",
            f"cd {repo_name}",
            "export ROOT=$(pwd -P)",
            "git status",
            "git restore .",
            f"git reset --hard {self.base_commit}",
            "git clean -fdxq",
        ]:
            self.communicate_with_handling(
                input=cmd,
                error_msg="Failed to clean repository",
            )
        print(self.communicate("git status"))
        # print(self.get_cwd())
        self.table_cache.function_table = self.function_table
        self.table_cache.class_table = self.class_table
        logger.debug(f"CWD: {self.get_cwd()}")
        # print(self.communicate(input="ls"))
        if self.table_cache.exists(self.record["instance_id"]):
            self.table_cache.load(self.record["instance_id"])
        else:
            instance = self.record["instance_id"].split("-")
            instance = "-".join(instance[:-1])
            print(instance)
            self.build_index(instance, self.class_table, self.function_table)
            self.table_cache.save(self.record["instance_id"])

        # Reset environment variables
        for cmd in [
            'export CURRENT_FILE=""',
            "export CURRENT_LINE=0",
            "export SEARCH_RESULTS=()",
            "export SEARCH_FILES=()",
            "export SEARCH_INDEX=0",
        ]:
            self.communicate_with_handling(
                input=cmd,
                error_msg="Failed to reset environment variables",
            )

        self.communicate_with_handling(
            "source /root/miniconda3/etc/profile.d/conda.sh",
            error_msg="Failed to source conda",
        )

        print(self.communicate("git status"))

        # Extract arch information
        system = self.communicate("uname -s").strip().lower()
        arch = self.communicate("uname -m").strip().lower()
        if system == 'linux' and arch == 'x86_64':
            self.communicate_with_handling(
                f"apt update; apt install build-essential -y",
                error_msg="Failed to install build-essential",
                timeout_duration=LONG_TIMEOUT,
                )

        # Call install environment helper function if specified
        # install 
        if self.install_environment:
            if self.is_from_github_url:
                logger.warning((
                    "install_environment is set to True, but the data path is a GitHub URL. "
                    "Skipping conda environment installation."
                    ))
            else:
                self.install_env()
        # Install mypy for linting purposes
        self.communicate_with_handling(
            f"pip install flake8",
            error_msg="Failed to install flake8 (lint library)"
        )
        print(self.communicate("git status"))

        # Apply test patch for oracle setting
        if apply_test_patch:
            path_to_patch = "test.patch"
            with open(path_to_patch, "w") as f:
                f.write(self.record["test_patch"])
            subprocess.run(
                f"docker cp {path_to_patch} {self.container_name}:/root/test.patch",
                shell=True,
            )
            self.communicate_with_handling(
                input="git apply /root/test.patch",
                error_msg="Failed to apply test patch correctly"
            )
            os.remove(path_to_patch)

        # Write any metadata to info if necessary
        return None, info


    def step(self, action: str, thought: str) -> Tuple[str, int, bool, dict]:
        """
        Runs given action in environment and returns corresponding output

        Args:
            action (`str`) - command to run in bash shell

        Returns:
            observation (`str`) - output from container
            reward (`float`) - value between 0 and 1 quantifying correctness of output + environment state
            done (`bool`) - whether task is over
            info (`dict`) - additional information (e.g. debugging information)
        """
        info = {}

        observation = ""
        # Handle special actions
        if action.strip() == "skip":
            observation = "Skipped"
            info["exit_status"] = "skipped"
            return observation, 0, True, info
        if action in {"exit_context", "exit_cost", "exit_error", "exit_format", "exit_api"}:
            try:
                observation = self.communicate(input="submit")
                submission = self.get_submission('submit', observation)
                assert submission is not None and submission.strip() != "", AssertionError('No submission found.')
                self.logger.info(f"Found submission: {submission}")
                info["exit_status"] = f"submitted ({action})"
                info["submission"] = submission
                observation = "Exited (autosubmitted)"
                logger.info("Exiting with autosubmission")
                return observation, 0, True, info
            except KeyboardInterrupt:
                raise
            except:
                observation = "Exited"
                info["exit_status"] = action
                return observation, 0, True, info

        # Attempt to run action in container
        observation = ""
        try:
            # observation = self.communicate(input=action, timeout_duration=25)
            observation = self.parse_command_to_function(command_string=action, thought=thought)
            # print("RESULT: ", observation)
        except TimeoutError:
            try:
                self.interrupt()
                observation += "\nEXECUTION TIMED OUT"
            except RuntimeError as e:
                observation += "\nEXECUTION TIMED OUT AND INTERRUPT FAILED. RESTARTING PROCESS."
                info["exit_status"] = "early_exit"
                logger.warning(f"Failed to interrupt container: {e}\nRESTARTING PROCESS.")
                self.reset_container()
                return observation, 0, True, info
        except RuntimeError as e:
            observation += "\nCOMMAND FAILED TO EXECUTE. RESTARTING PROCESS."
            info["exit_status"] = "early_exit"
            logger.warning(f"Failed to execute command: {e}\nRESTARTING PROCESS.")
            self.reset_container()
            return observation, 0, True, info
        except BrokenPipeError as e:
            observation += "\nBROKEN PIPE ERROR. RESTARTING PROCESS."
            info["exit_status"] = "early_exit"
            logger.error(f"Broken pipe error: {e}\nRESTARTING PROCESS.")
            self.reset_container()
            return observation, 0, True, info
        except Exception as e:
            logger.error(e)
            import traceback
            traceback.print_exc()
            observation += "\nEXECUTION FAILED OR COMMAND MALFORMED"

        # Record submission and end episode if `submit` keyword found
        submission = self.get_submission(action, observation)
        if submission is not None:
            self.logger.info(f"Found submission: {submission}")
            info["exit_status"] = "submitted"
            info["submission"] = submission if submission.strip() != "" else None
            observation = submission if submission.strip() != "" else None
            return observation, 0, True, info
        return observation, 0, False, info

    # terminates container
    # if persistent, pause container
    def close(self):
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

    # MARK: Helper functions #

    def _reset_container(self) -> None: 
        # why has attr?
        if hasattr(self, "container"):
            try:
                self.container.terminate()
            except KeyboardInterrupt:
                raise
            except:
                pass
        self._init_container() 
        self._init_scripts()

    def reset_container(self) -> None:
        try:
            self.close()
        except:
            pass
        self.container = None
        self.container_obj = None
        self._reset_container()

    def _init_container(self) -> None:
        """
        Handles container initialization. Defines container name and creates it
        """

        if self.container_name is None:
            process_id = str(os.getpid())
            current_time = str(datetime.datetime.now())
            unique_string = current_time + process_id
            hash_object = hashlib.sha256(unique_string.encode())
            self.container_name = f"{self.image_name}-{hash_object.hexdigest()[:10]}"

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

        self.container_obj = client.containers.get(self.container_name)
        self.logger.info("🌱 Environment Initialized")

    def _init_scripts(self):
        """
        Initialize custom commands within container
        """
        self.communicate_with_handling(
            "source /root/.bashrc",
            error_msg="Failed to source .bashrc",
        )
        self.communicate_with_handling(
            "mkdir -p /root/commands",
            error_msg="Failed to create commands directory",
        )
        self.communicate_with_handling(
            "touch /root/commands/__init__.py",
            error_msg="Failed to create __init__.py",
        )
        self.communicate_with_handling(
            "export PATH=$PATH:/root/commands",
            error_msg="Failed to add commands directory to PATH",
        )

    def _communicate(
        self,
        input: str,
        timeout_duration=25,
    ) -> str:
        
        #Add \n, stdin write, flush => execute commant
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

        #echo back last command
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
            raise RuntimeError(f"Container crashed. Failed to get exit code. Output:\n---\n{buffer}\n---")
        
        self.returncode = int(exit_code)
        return buffer

    def _check_syntax(self, input: str) -> None:
        """
        Saves environment variables to file
        """
        output = self._communicate(f"/bin/bash -n <<'EOF'\n{input}\nEOF\n")
        return output, self.returncode == 0

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
                input, timeout_duration=timeout_duration,
            )
            self.communicate_output = output
            return output
        else:
            self.container.terminate()
            self.returncode = 0
            self.communicate_output = ""
            return ""


    def refresh_editor(self):
        for path in list(self.editor.keys()):
            self.load_file_to_editor(path)


    def get_state(self) -> dict:
        """
        Returns the entire file tree and specified files in their entirety from the docker container.

        Args:
            files (`list[str]`): List of file paths within the container to return in their entirety.

        Returns:
            dict: A dictionary with two keys: 'file_tree' containing a list of all files in the tree,
                  and 'files_content' containing a dictionary of specified files and their content.
        """
        file_tree = []


        self.refresh_editor()

        return {"editor": self.editor, "cwd": self.get_cwd(), "file_root": self.file_root}

    # Used for mission critical commands (mostly setup) to make sure that we bail from this task if there is a command failure
    def communicate_with_handling(
        self, input: str, error_msg: str, timeout_duration=25
    ):
        """
        Wrapper for communicate function that raises error if return code is non-zero
        """
        logs = self.communicate(input, timeout_duration=timeout_duration)
        if self.returncode != 0:
            self.logger.error(f"{error_msg}: {logs}")
            self.close()
            raise RuntimeError(f"{error_msg}: {logs}")

    def normalize_path(self, path, specified_path):
        if path == os.sep:
            return specified_path
        elif os.path.isabs(path):
            if path.startswith(specified_path):
                return path
            else:
                path_components = path.strip(os.sep).split(os.sep)
                path_components[0] = specified_path.strip(os.sep)
                return os.sep + os.path.join(*path_components)
        else:
            return os.path.join(specified_path, path)

    def make_abs_path(self, fpath: str) -> str:
        """
        Converts relative paths to absolute paths based on the container's root directory.

        Args:
            fpath (str): The file path to convert.

        Returns:
            str: The absolute path of the file.
        """

        # fpath = fpath.strip("'").strip('"')
        # base = fpath.split("/")[0]

        # print("FILE_ROOT: ", self.file_root)
        # print(fpath)
        # print("BASE: ", base)

        # if fpath.startswith(self.file_root):
        #     return os.path.abspath(fpath)
        # else:
        #     return os.path.join("/", self.file_root.strip("/"), fpath.strip("/"))

        return self.normalize_path(fpath, self.file_root)

    def cwd_normalize_path(self, path):
        if os.path.isabs(path):
            return self.make_abs_path(path)
        else:
            return self.make_abs_path(os.path.join(self.get_cwd(), path))
    

    def file_exists(self, fpath):
        abs_path = self.make_abs_path(fpath)
        result = self.communicate(input=f"test -f {abs_path}")

        return self.returncode == 0


    def read_file(self, file_path: str) -> str:
        """
        Reads the content of a specific file from the docker container.

        Args:
            file_path (str): The path of the file within the system to read.

        Returns:
            str: The content of the file.
        """
        result = self.communicate(f"cat '{file_path}'")
        return result


    def load_file_to_editor(self, file_path):
        abs_path = self.make_abs_path(file_path)
        contents = self.read_file(abs_path)
        self.editor[abs_path]["lines"] = contents


    def _list_files_recursive(self, files: list[str]) -> dict:
        result = self.communicate(f"find /{self.record['repo'].replace('/', '__')} -type f")
        all_files = result.split('\n')

        # Generate file tree as a nested dictionary and read specified files
        def add_to_tree(path, tree):
            parts = path.strip('/').split('/')
            current = tree
            for part in parts:
                if part not in current:
                    current[part] = {}
                current = current[part]

        directory_tree = {}
        file_tree = {}
        files_content = {}

        for file_path in all_files:
            # Add to directory tree
            directory_path = os.path.dirname(file_path)
            add_to_tree(directory_path, directory_tree)
            add_to_tree(file_path, file_tree)

            if file_path in files:
                # Read file content from container
                result = self.communicate(f"cat '{file_path}'")
                files_content[file_path] = result

        return {"directory_tree": directory_tree, "file_tree": file_tree,"files_content": files_content}

    def check_lint(seld,code_string : str,file_path: str):

        # example json
        # [{'type': 'error', 'module': 'tmp5cpif150', 'obj': 'ModelFormMetaclass.__new__', 'line': 224, 'column': 20, 'endLine': 224, 'endColumn': 60, 'path': '/tmp/tmp5cpif150', 'symbol': 'too-many-function-args', 'message': 'Too many positional arguments for classmethod call', 'message-id': 'E1121'}, {'type': 'error', 'module': 'tmp5cpif150', 'obj': 'ModelForm', 'line': 477, 'column': 0, 'endLine': 477, 'endColumn': 15, 'path': '/tmp/tmp5cpif150', 'symbol': 'invalid-metaclass', 'message': "Invalid metaclass 'ModelFormMetaclass' used", 'message-id': 'E1139'}, {'type': 'error', 'module': 'tmp5cpif150', 'obj': 'ModelChoiceField.__deepcopy__', 'line': 1250, 'column': 17, 'endLine': 1250, 'endColumn': 41, 'path': '/tmp/tmp5cpif150', 'symbol': 'bad-super-call', 'message': "Bad first argument 'ChoiceField' given to super()", 'message-id': 'E1003'}]
        from pylint.reporters.json_reporter import JSONReporter 
        from pylint.lint import Run

        pylint_output = io.StringIO()  # Custom open stream
        reporter = JSONReporter(pylint_output)

        with tempfile.NamedTemporaryFile(mode="w+") as f:
            f.write(code_string)
            f.seek(0)
            Run(args=["--disable=all", "--enable=E0602,E1101",f.name], reporter=reporter, exit=False)
        
        results = json.loads(pylint_output.getvalue())

        return results

    def open_file(self, file_path: str):
        """
        Opens a file, and displays it in the editor..

        Args:
            file_path (str): The path of the file to open.
        """
        try:

            abs_path = self.cwd_normalize_path(file_path)

            if abs_path in self.editor:
                raise Exception(f"File {abs_path} already open in editor")
            exists = self.file_exists(abs_path)
            if not exists:
                raise Exception(f"Could not open file, file does not exist: {abs_path}")

            file_contents = self.read_file(file_path=abs_path)
            self.editor[abs_path] = {}
            self.editor[abs_path]["lines"] = file_contents
            self.editor[abs_path]["page"] = 0

            return f"File {abs_path} opened in editor"

        except Exception as e:
            self.logger.error(f"Failed to open file: {abs_path}. Error: {str(e)}")
            return f"Failed to open file: {abs_path}. Error: {str(e)}"

    PAGE_SIZE = 200

    def scroll_down(self, file_path: str):
        """
    NAME
        scroll_down - scroll down by one window of size 500 in the specified file

    SYNOPSIS
        scroll_down FILE_PATH

    DESCRIPTION
        The scroll_down command scrolls down by one page in the file
        specified by FILE_PATH. If the file is not open or does not exist,
        an exception is raised.

    OPTIONS
        FILE_PATH
            The path of the file to scroll down in. The path can be either
            an absolute path or a relative path from the current working
            directory.

    RETURN VALUE
        The scroll_down command returns a string indicating the new line
        number after scrolling down.

    EXAMPLES
        To scroll down by one page in the file "/path/to/file.txt":

            scroll_down "/path/to/file.txt"

    SEE ALSO
        scroll_up(1), open_file(1), close_file(1)
    """

        abs_path = self.cwd_normalize_path(file_path)

        exists = self.file_exists(abs_path)
        if not exists:
            raise Exception(f"Could not scroll in file, file does not exist: {abs_path}")

        if not (abs_path in self.editor):
            raise Exception(f"Could not scroll in file, file is not open: {abs_path}")

        lines = self.editor[abs_path]["lines"].splitlines()

        last_page_idx = len(lines) // self.PAGE_SIZE

        old_page_number = self.editor[abs_path]["page"]

        if old_page_number == last_page_idx:
            new_page_number = last_page_idx
        else:
            new_page_number = old_page_number + 1

        self.editor[abs_path]["page"] = new_page_number

        return f"Scrolled down in file {abs_path} to line {self.PAGE_SIZE * new_page_number}"

    def scroll_up(self, file_path: str):
        """
    NAME
        scroll_up - scroll up by one page in the specified file

    SYNOPSIS
        scroll_up FILE_PATH

    DESCRIPTION
        The scroll_up command scrolls up by one page in the file specified
        by FILE_PATH. If the file is not open or does not exist, an
        exception is raised.

    OPTIONS
        FILE_PATH
            The path of the file to scroll up in. The path can be either an
            absolute path or a relative path from the current working
            directory.

    RETURN VALUE
        The scroll_up command returns a string indicating the new line
        number after scrolling up.

    EXAMPLES
        To scroll up by one page in the file "/path/to/file.txt":

            scroll_up "/path/to/file.txt"
    """
        abs_path = self.cwd_normalize_path(file_path)

        exists = self.file_exists(abs_path)
        if not exists:
            raise Exception(f"Could not scroll in file, file does not exist: {abs_path}")

        if not (abs_path in self.editor):
            raise Exception(f"Could not scroll in file, file is not open: {abs_path}")

        lines = self.editor[abs_path]["lines"].splitlines()

        old_page_number = self.editor[abs_path]["page"]

        if old_page_number == 0:
            new_page_number = 0
        else:
            new_page_number = old_page_number - 1
        
        self.editor[abs_path]["page"] = new_page_number

        return f"Scrolled up in file {abs_path} to line {self.PAGE_SIZE * new_page_number}"

    def scroll_to_line(self, file_path: str, line_number: str):
        """
        NAME
            scroll_to_line - scroll to the window containing the specified line in the file

        SYNOPSIS
            scroll_to_line FILE_PATH LINE_NUMBER

        DESCRIPTION
            The scroll_to_line command scrolls to the window containing the specified
            LINE_NUMBER in the file specified by FILE_PATH. If the file is not open or
            does not exist, an exception is raised.

        OPTIONS
            FILE_PATH
                The path of the file to scroll to the line in. The path can be either an
                absolute path or a relative path from the current working directory.

            LINE_NUMBER
                The line number to scroll to within the file.

        RETURN VALUE
            The scroll_to_line command returns a string indicating the line number at
            the start of the window after scrolling.

        EXAMPLES
            To scroll to the window containing line 1000 in the file "/path/to/file.txt":

                scroll_to_line "/path/to/file.txt" 1000

        SEE ALSO
            scroll_up(1), scroll_down(1), open_file(1), close_file(1)
        """
        abs_path = self.cwd_normalize_path(file_path)

        exists = self.file_exists(abs_path)
        if not exists:
            raise Exception(f"Could not scroll in file, file does not exist: {abs_path}")

        if not (abs_path in self.editor):
            # raise Exception(f"Could not scroll in file, file is not open: {abs_path}")
            self.open_file(abs_path)

        lines = self.editor[abs_path]["lines"].splitlines()
        total_lines = len(lines)
        line_number = int(line_number)

        if line_number < 0 or line_number > total_lines:
            raise Exception(f"Invalid line number: {line_number}. Line number should be between 1 and {total_lines}.")

        window_number = (line_number) // self.PAGE_SIZE
        self.editor[abs_path]["page"] = window_number

        window_start_line = window_number * self.PAGE_SIZE + 1
        return f"Scrolled to window containing line {line_number} in file {abs_path}. Window starts at line {window_start_line}."

    def close_file(self, file_path: str) -> bool:
        """
        Removes the target file from the editor.

        Args:
            file_path (str): The path of the file to delete from the editor.

        Returns:
            bool: True if the file was successfully deleted, False otherwise.
        """
        abs_path = self.cwd_normalize_path(file_path)

        if abs_path in self.editor:
            del self.editor[abs_path]
            return "Successfully closed file!"

        return "False, file not open in editor"

    def write_file(self, file_path: str, content: str = "") -> str:

        try:
            # Check if file doesnt already exists to avoid overwriting
            abs_path = self.make_abs_path(file_path)

            exists = self.file_exists(abs_path)
            if not exists:
                raise Exception(f"Could not write to file, file does not exist: {abs_path}")

            create_command = f"cat << 'DELIM' > {abs_path} \n" + content + "\nDELIM"
            result = self.communicate(input=create_command)

            if self.returncode == 1:
                raise Exception(result)
            
            self.editor[abs_path]["lines"] = content
            msg = f"Successfully wrote to file {abs_path}"
            logger.info(msg)

            return msg
        
        except Exception as e:
            logger.error(f"Failed to write to file: {abs_path}. Error: {str(e)}")
            raise Exception(f"Failed to write to file: {abs_path}. Error: {str(e)}")
    
    def delete_file(self, file_path: str) -> bool:
        
        try:
            # Check if file already exists to avoid overwriting
            abs_path = self.make_abs_path(file_path)

            exists = self.file_exists(abs_path)
            if not exists:
                raise Exception(f"Could not delete file, file does not exist: {abs_path}")

            # Creating the file with initial content
            result = self.communicate(f"rm -f {abs_path}")

            if abs_path in self.editor:
                del self.editor[abs_path]
            return f"Successfully deleted file {abs_path}"
        
        except Exception as e:
            logger.error(f"Failed to delete file: {abs_path}. Error: {str(e)}")
            return f"Failed to delete file: {abs_path}. Error: {str(e)}"

    def create_file(self, file_path: str, content: str = "") -> bool:
        """
NAME
       create_file - create a new file at the target path with optional initial content

SYNOPSIS
       create_file FILE_PATH [CONTENT]

DESCRIPTION
       The create_file command creates a new file at the specified FILE_PATH within the
       file system, optionally with the provided initial CONTENT.

OPTIONS
       FILE_PATH
              The path of the file to create within the system.

       CONTENT
              Optional initial content to write to the file. If not provided, the file
              will be created empty. The content should be enclosed between "<<<" and
              ">>>" delimiters, with each line of content on a separate line. For
              example:

                     create_file "/path/to/file.txt" <<<
                     import os
                     import asyncio
                     >>>

RETURN VALUE
       The create_file command returns a boolean value:

       True  If the file was successfully created.

       False If the file creation failed.

EXAMPLES
       To create an empty file at "/path/to/file.txt":

              create_file "/path/to/file.txt"

       To create a file at "/path/to/script.py" with initial content:

              create_file "/path/to/script.py" <<<
              import os
              import asyncio
              >>>
        """
        try:
            # Check if file already exists to avoid overwriting
            abs_path = self.cwd_normalize_path(file_path)
            print(abs_path)

            if self.check_path_for_tests(abs_path):
                raise Exception(f"Could not create file, the tests directory is read only, please create your testing file elsewhere. './reproduce.py' is usually a good option.")

            exists = self.file_exists(abs_path)
            if exists:
                raise Exception(f"Could not create file, file already exists: {abs_path}")
            
            # Creating the file with initial content

            create_command = f"cat << 'DELIM' > '{abs_path}' \n" + content + "\nDELIM"
            result = self.communicate(input=create_command)

            # copy_file_to_container(self.container_obj, contents=content, container_path=file_path)

            exists = self.file_exists(abs_path)

            # Verify file creation
            if not exists:
                raise Exception(f"Command failed to create file: {abs_path}")

            self.editor[abs_path] = {}
            self.editor[abs_path]["lines"] = content
            self.editor[abs_path]["page"] = 0
            return f"Successfully created file {abs_path}"

        except Exception as e:
            logger.error(f"Failed to create file: {file_path}. Error: {str(e)}")
            return f"Failed to create file: {file_path}. Error: {str(e)}"

    def view_open_files(self) -> dict:
        """
        Returns the current state of the open files.

        Returns:
            dict: A dictionary representing the open files
        """
        return json.dumps(self.editor)

    #DIFF CODE

    def edit_file(self, diff: str) -> dict:
        """NAME
      edit_file - apply a diff to files in the file system

SYNOPSIS
      edit_file [DIFF]

DESCRIPTION
      The edit_file command takes a target DIFF and applies it to files that are open
      in the file system. Someone will edit and double check your work.

      The DIFF argument is a diff string to be applied to specific files. It is similar
      to calling `diff --git "diff string"` where "diff string" is the argument you
      would pass to the edit_file command.

      You ALWAYS need to provide a source and target file represented with `---` and `+++`.

      ALWAYS make sure that the code STARTS on its own line.

RETURN VALUE
      The edit_file command returns a dictionary of all the files that were changed.

EXAMPLES
      To apply a diff string to open files in the file system:

             edit_file <<<
             --- file1.txt
             +++ file1.txt
             @@ -1,5 +1,5 @@
              Line 1
             -Line 2
             +Line Two
              Line 3
              Line 4
              Line 5>>>
        """

        pass

    def apply_diff(self, multi_file_diffs, file_tree_root: str):

        results = []

        for file_diff in multi_file_diffs:
            src_file = file_diff.src_file
            tgt_file = file_diff.tgt_file

            # diff_logger.debug(src_file + " " + tgt_file)
            if not ( src_file or tgt_file ):
                raise Hallucination("Could not apply changes, missing source or target file.")

            # diff_logger.debug("Applying diff to: %s, %s", src_file, tgt_file)

            # Ensure src_file and tgt_file are valid paths, if not, make them absolute paths from file_tree_root
            src_file_abs = self.make_abs_path(src_file)
            tgt_file_abs = self.make_abs_path(tgt_file)

            src_file_exists = self.communicate(f"test -e {src_file_abs} && echo 'exists'").strip() == 'exists'
            tgt_file_exists = self.communicate(f"test -e {tgt_file_abs} && echo 'exists'").strip() == 'exists'

            # diff_logger.debug("Applying diff to: %s, %s", src_file_abs, tgt_file_abs)
            cwd = self.get_cwd().strip()

            if tgt_file_abs.startswith(cwd):
                tgt_file_abs = self.make_abs_path(tgt_file_abs)
            else:
                tgt_file_abs = self.make_abs_path(os.path.join(cwd, tgt_file_abs))

            if src_file_abs.startswith(cwd):
                src_file_abs = self.make_abs_path(src_file_abs)
            else:
                src_file_abs = self.make_abs_path(os.path.join(cwd, src_file_abs))

            if not src_file_exists:
                raise Exception(f"Failed to write diff with source file: {src_file}, {src_file_abs} not open")

            # Modifying an existing file
            src_content = self.read_file(file_path=src_file_abs)
            # diff_logger.debug("source content: %s", src_content)

            file_diff.src_file = src_file_abs
            file_diff.tgt_file = tgt_file_abs

            apply_result = apply_file_context_diffs(src_content, [file_diff])
            results.append(apply_result)

        return results


    def check_path_for_tests(self, file_path):
        if "/tests/" in file_path:
            return True
        else:
            return False

    def check_lint_entry_equal(self, a, b):
        if (
            a["obj"] == b["obj"] 
            and a["column"] == b["column"] 
            and a["endColumn"] == b["endColumn"] 
            and a["message"] == b["message"] 
            and a["message-id"] == b["message-id"]
        ):
            print("Success, these are equal")
            return True
        else:
            return False

    def check_lint_entry_in_list(self, a, b_set):

        for entry in b_set:
            if self.check_lint_entry_equal(a, entry):
                return True
            else:
                print("Didn't match")
        
        return False

    def real_write_diff(self, diff, thought):

        diff_code = diff

        all_diffs, _ = extract_all_diffs(diff_code)
        results = self.apply_diff(all_diffs, self.file_root)
        print("diff applied")
        failures = []
        successes = []
        for result in results:
            if len(result["fail"]) > 0:
                failures.extend(result["fail"])
                for failure in result["fail"]:
                    log_failed_diff(diff=diff_code, file_content=failure[2], src_file=failure[0], tgt_file=failure[0])
            if len(result["success"]) > 0:
                successes.extend(result["success"])
                for success in result["success"]:
                    log_successful_diff(diff=diff_code, file_content=success[2], src_file=success[0], tgt_file=success[0])

        if len(failures) == 0:
            file_paths = []
            for result in successes:

                try:
                    compile(result[1], "<string>", "exec")
                except Exception as e:
                    return "Error applying diff: \n" + repr(e)

                target_path = result[0]

                if self.check_path_for_tests(target_path):
                    return "Error applying diff: tried to edit tests. Please remember to create a reproduce.py file if you would like to write tests."

                old_editor_code = "\n".join(self.editor[target_path]["lines"])
                before_results = self.check_lint(self.read_file(target_path),target_path)

                self.write_file(file_path=target_path, content=result[1])
                file_paths.append(target_path)

                new_editor_code = "\n".join(self.editor[target_path]["lines"])
                after_results = self.check_lint(result[1],target_path)

                assert(old_editor_code != new_editor_code)

                diff_results = [x for x in after_results if not self.check_lint_entry_in_list(x, before_results)]

            paths = ", ".join(file_paths)

            if diff_results:

                lint_error_message =""
                for rst in diff_results:
                    lint_error_message += f"{rst['type']}: {rst['message']} on line {rst['line']} column {rst['column']}. Line {result[1].splitlines()[int(rst['line'])-1]} \n"

                return f"Successfully edited file(s): {paths}. Please review the new contents of the files. Your change introduced the following linting errors. Please address them before you submit. \n{lint_error_message}"
            
            return f"Successfully edited file(s): {paths}. Please review the new contents of the files."

        return "\n".join(["Failed to edit file"] + [f[1].args[0] for f in failures])


    def create_tar(self, file_path):

        tar_data, _ = self.container_obj.get_archive(path=file_path)

        return tar_data


    def build_index(self, file_path, class_table, function_table):

        tar_data = self.create_tar(file_path)
        # logger.debug(tar_data)

        with tempfile.NamedTemporaryFile() as temp_file:
            for chunk in tar_data:
                temp_file.write(chunk)
            temp_file.flush()
            # print(temp_file.read())
            temp_file.seek(0)

            temp_dir = tempfile.mkdtemp()
            self.class_table.temp_dir = temp_dir
            self.function_table.temp_dir = temp_dir

            # save archive to file
            with tarfile.open(fileobj=temp_file, mode='r') as tar:
                tar.extractall(path=temp_dir)

            code_graph = initialize_repository(temp_dir, self.class_table, self.function_table)

            # os.remove(temp_file)

        return code_graph


    def find_function(self, function_name):
        """NAME 
      find_function - get location of function or method in the codebase

SYNOPSIS
      find_function [FUNCTION_NAME]

DESCRIPTION
      The find_function command searches the codebase for a function with the given name and returns its location.

OPTIONS
      FUNCTION_NAME
             The name of the function to search for. Only function name. For methods specify the class name and the method name separated by a dot.

RETURN VALUE
      The location of the function in the codebase. A dictionary containing the following keys:
      - file_path: The path to the file containing the function.
      - line_number: The line number in the file where the function is defined.

EXAMPLES
      To find the location of a function named "my_function", run the following command:

             find_function "my_function"

      The command will return a dictionary containing the file path and line number of the function:

             {
               "file_path": "/path/to/file.py",
               "line_number": 10
             }

     To find the location of a function named "my_function" in class "MyClass", run the following command:

             find_function "MyClass.my_function"

      The command will return a dictionary containing the file path and line number of the function:

             {
               "file_path": "/path/to/file.py",
               "line_number": 10
             }
        """

        return str(get_function_defn(function_name, self.function_table))
    
    def find_class(self, class_name):
        """NAME
      find_class - get location of class in the codebase

SYNOPSIS
      find_class [CLASS_NAME]

DESCRIPTION
      The find_class command searches the codebase for a class with the given name and returns its location.

OPTIONS
      CLASS_NAME
             The name of the class to search for.

RETURN VALUE
      The location of the class in the codebase. A dictionary containing the following keys:
      - file_path: The path to the file containing the class.
      - line_number: The line number in the file where the class is defined.

EXAMPLES
      To find the location of a class named "MyClass", run the following command:

             find_class "MyClass"

      The command will return a dictionary containing the file path and line number of the class:

             {
               "file_path": "/path/to/file.py",
               "line_number": 10
             }
        """

        class_defns = get_class_defn(class_name, self.class_table)
        if len(class_defns) > 1:
            if len(str(class_defns)) > 4000:
                for class_defn in class_defns:
                    del class_defn["code"]
        
        return str(get_class_defn(class_name, self.class_table))

    ## END DIFF CODE

    def submit(self):
        """NAME
      submit - submit your solution once you think you have resolved the issue

SYNOPSIS
      submit

DESCRIPTION
      The submit command submits your solution. It is used to indicate that you have resolved the issue and are ready to submit your
      solution.    
        """
        command = """submit() {
    cd $ROOT

    # Check if the patch file exists and is non-empty
    if [ -s "/root/test.patch" ]; then
        # Apply the patch in reverse
        git apply -R < "/root/test.patch"
    fi

    echo "\nbuild" >> .gitignore
    git add -A
    git diff --cached > model.patch
    echo "<<SUBMISSION||"
    cat model.patch
    echo "||SUBMISSION>>"
}
submit"""
        return self.communicate(command)

    def find_file(self, file_path: str):
        """
        NAME
            find_file - search for a file by name within the file system

        SYNOPSIS
            find_file FILE_PATH

        DESCRIPTION
            The find_file command searches for a file by its name within the file
            system starting from the root directory specified by self.file_root.
            It returns the paths of all files that match the specified filename.

        OPTIONS
            FILE_PATH
                The path of the file to search for. The function extracts the
                filename from the provided path.

        RETURN VALUE
            The find_file command returns a string containing the paths of all
            files that match the specified filename, separated by newline
            characters. If no matching files are found, an empty string is
            returned.

        EXAMPLES
            To search for a file named "example.txt" within the file system:

                find_file "/path/to/example.txt"
        """
        filename = os.path.basename(file_path)
        command = f"find {self.file_root} -type f -name '{filename}'"
        result = self.communicate(command)
        return result

    def search_dir(self, search_term: str, dir: str = ""):
        """NAME
      search_dir - search for a term in all files in a directory

SYNOPSIS
      search_dir [SEARCH_TERM] [DIR]

DESCRIPTION
      The search_dir command searches for SEARCH_TERM in all files in the specified DIR.
      If DIR is not provided, it searches in the current directory. Does not search for files but for the content of the files.

OPTIONS
      SEARCH_TERM
             The term to search for in the files.

      DIR   The directory to search in. If not provided, the command searches in the
             current directory ("./").

RETURN VALUE
      The search_dir command returns a summary of the search results as a string.

EXAMPLES
      To search for the term "hello" in all files in the current directory:

             search_dir "hello"

      To search for the term "world" in all files in the "/path/to/directory" directory:

             search_dir "world" "/path/to/directory"
        """

        if search_term.startswith("--"):
            search_term = "\"" + search_term + "\""

        abs_path = self.cwd_normalize_path(dir)

        command = f"find {abs_path} -type f ! -path '*/.*' -exec grep -nIH '{search_term}' {{}} + | cut -d: -f1 | sort | uniq -c"

        result = self.communicate(command)

        matches = result.strip()
        if not matches:
            return f"No matches found for \"{search_term}\" in {abs_path}"
        print(matches)
        try:
            num_matches = sum(int(line.split()[0]) for line in matches.split('\n'))
        except:
            raise Exception("Command not formed well. Make sure the term you are searching for is in quotes and you are providing the correct directory." + matches)
        num_files = matches.count('\n') + 1

        if num_files > 100:
            return f"More than {num_files} files matched for \"{search_term}\" in {abs_path}. Please narrow your search."

        result = f"Found {num_matches} matches for \"{search_term}\" in {abs_path}:\n{matches}"
        return result.replace('\n', '\n    ')

    def _capture_window(self, lines, index, window_size):

        start_line = index - window_size if index - window_size >= 0 else 0
        end_line = index + window_size if index + window_size <= len(lines) else len(lines)

        content_lines = "\n".join(lines[start_line:end_line])


        return f"""
Match found on line: {index}
{content_lines}
"""

    def search_file(self, search_term: str, file_path: str = None):
        """
        NAME
      search_file - search for a term in a specific file

SYNOPSIS
      search_file [SEARCH_TERM] [FILE]

DESCRIPTION
      The search_file command searches for SEARCH_TERM in the specified FILE. If FILE is
      not provided, it searches in the current open file.

OPTIONS
      SEARCH_TERM
             The term to search for in the file.

      FILE  The file to search in. If not provided, the command searches in the current
             open file.

RETURN VALUE
      The search_file command returns a summary of the search results as a string.

EXAMPLES
      To search for the term "hello" in the current open file:

             search_file "hello"

      To search for the term "world" in the file "/path/to/file.txt":

             search_file "world" "/path/to/file.txt"
        """

        abs_path = self.cwd_normalize_path(file_path)

        if not (abs_path in self.editor):
            raise Exception(f"Could not find in file, file is not open: {abs_path}")

        content_lines = self.editor[abs_path]["lines"].splitlines()

        matches = []
        tolerance = 10
        for i, line in enumerate(content_lines):
            if search_term in line:
                matches.append(self._capture_window(content_lines, i, tolerance))

        if not matches:
            return f"No matches found for \"{search_term}\" in {abs_path}"

        num_matches = len(matches)

        max_matches = 20

        if num_matches > max_matches:
            return f"More than {max_matches} lines matched for \"{search_term}\" in {abs_path}. Please narrow your search."

        matches = '\n'.join(matches)
        result = f"Found {num_matches} matches for \"{search_term}\" in {abs_path}:\n {matches}"
        return result

    def get_cwd(self) -> str:
        """
        Gets the current working directory of the container.

        Returns:
            str: The current working directory of the container.
        """
        command = "pwd"
        result = self.communicate(command)

        # logger.info(f"CWD {result}")
        
        return result.strip()

    def no_op(self) -> str:
        """
        Lets you think! This allows you to take a brief moment to think and synthesize what you know about the current state of the system.

        Make sure you think step by step!
        """

        return "No Action Taken"

    def generate_command_docs(self):

        funcs = [
            # self.list_files,
            # self.list_dirs_recursive,
            self.close_file,
            self.create_file,
            self.open_file,
            # self.get_testing_instructions,
            # self.view_open_files,
            self.search_dir,
            self.find_function,
            self.find_class,
            # self.search_file,
            # self.search_files,
            self.search_file,
            self.get_cwd,
            self.delete_file,
            self.edit_file,
            self.submit,
            self.no_op,
            self.scroll_up,
            self.scroll_down,
            self.scroll_to_line,
            self.find_file,
        ]

        docs = {}

        for func in funcs:
            name = func.__name__
            code = inspect.getsource(func)
            sig, docstring = extract_signature_and_docstring(code)
            docs[name] = {"signature": sig, "docstring": docstring}

        return docs

    def parse_command(self, command: str) -> tuple:
        """
        Parses a command string into its function name and arguments.

        Args:
            command (str): The command string to parse.

        Returns:
            tuple: A tuple containing the function name (str) and a list of arguments (list).
        """
        parts = command.split(None, 1)
        fn_name = parts[0]
        args = []

        if len(parts) > 1:
            arg_string = parts[1]

            if "<<<" in arg_string and ">>>" in arg_string:
                # Handle multiline arguments
                before_multiline, multiline_arg = arg_string.split("<<<", 1)
                multiline_arg, after_multiline = multiline_arg.split(">>>", 1)

                if before_multiline:
                    temp_pre = re.findall(r'(?:[^\s"]+|"[^"]*")+', before_multiline)
                    args.extend([arg.strip('"').strip("'") for arg in temp_pre])

                args.append(multiline_arg.strip())

                if after_multiline:
                    args.extend([arg.strip('"').strip("'") for arg in after_multiline.split()])
            else:
                # Handle single line arguments
                lines = command.strip().splitlines()
                if len(lines) > 1:
                    raise Exception("Env Error: More than one command found")
                temp_pre = re.findall(r'(?:[^\s"]+|"[^"]*")+', arg_string)
                args = [arg.strip('"').strip("'") for arg in temp_pre]

        return fn_name, args

    def parse_command_to_function(self, command_string: str, thought: str):
        try:
            fn_name, args = self.parse_command(command_string)
        except Exception as e:
            logger.error(traceback.print_exc())
            return e.args[0] + "\n Remember to only use ONE command at a time."

        if fn_name in ["vim","nano"]:
            return "Interactive Commands are not allowed"

        if fn_name == "python" and len([line for line in command_string.splitlines() if line]) != 1:
            return "Interactive Commands are not allowed"

        funcs = [
            # self.list_files,
            # self.list_dirs_recursive,
            self.close_file,
            self.create_file,
            self.open_file,
            # self.get_testing_instructions,
            # self.view_open_files,
            self.search_dir,
            self.find_function,
            self.find_class,
            # self.search_file,
            # self.search_files,
            self.search_file,
            self.get_cwd,
            self.delete_file,
            self.submit,
            self.no_op,
            self.scroll_up,
            self.scroll_down,
            self.scroll_to_line,
            self.find_file,
        ]

        fn_names = [fn.__name__ for fn in funcs]

        try:
            if fn_name == "edit_file":
                # print(args)
                try:
                    return self.real_write_diff(command_string, thought)
                except Exception as e:
                    logger.error(traceback.print_exc())
                    raise e
            elif fn_name in fn_names:
                return self.__getattribute__(fn_name)(*args)
            else:
                try:
                    return self.communicate(fn_name + " " + " ".join(args))
                except Exception as e:
                    logger.error(f"Failed to execute bash command '{fn_name}': {str(e)}")
                    return None
        except Exception as e:
            logger.error(traceback.print_exc())
            return e.args[0] + "\n Remember to only use ONE command at a time."

    def get_available_actions(self) -> list[str]:
        """
        Returns list of available actions in current environment state
        """
        return ["submit", "exit_context", "exit_cost", "exit_error", "exit_format", "exit_api", "skip"] + [str(key) for key in self.generate_command_docs().keys()]

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

    def get_submission(self, action, output: str) -> str:
        """
        Function for extracting diff patch submission at the end of an episode.

        Args:
            output (`str`) - `submit` observation
        Returns:
            submission (`str`) - diff patch submission
        """
        # print(output)
        assert isinstance(output, str), "Output must be a string"
        logger.info(output)
        pattern = r"\<\<SUBMISSION\|\|(.*)\|\|SUBMISSION\>\>"
        match = re.search(pattern, output, re.DOTALL)
        if match is None:
            return None
        return match.group(1)

    def install_env(self) -> None:
        """
        Creates conda environment and installs third party dependencies to allow code execution
        """

        repo_name = self.record["repo"].replace("/", "__")
        # Create environment if does not exist yet
        
        # Check for env
        env_name = f"{repo_name}__{self.record['version']}"
        env_check = self.communicate(
            f"conda env list | grep {env_name}", timeout_duration=LONG_TIMEOUT
        )
        
        install_configs = MAP_VERSION_TO_INSTALL[self.record["repo"]][
            str(self.record["version"])
        ]

        if env_check.strip() == "":
            self.logger.info(f"{env_name} conda env not found, creating...")
            packages = (
                install_configs.get("packages", "")
            )
            if packages == "requirements.txt":
                # Create conda environment
                self.communicate_with_handling(
                    f"conda create -n {env_name} python={install_configs['python']} -y",
                    error_msg="Failed to create conda environment",
                    timeout_duration=LONG_TIMEOUT,
                )
                # Write reqs to requirements.txt in docker container
                content_reqs = get_requirements(self.record)
                copy_file_to_container(self.container_obj, content_reqs, PATH_TO_REQS)
                
                # Create conda environment + install reqs
                self.communicate_with_handling(
                    f"conda activate {env_name}",
                    error_msg="Failed to activate conda environment",
                )
                self.communicate_with_handling(
                    f"pip install -r {PATH_TO_REQS}",
                    error_msg="Failed to install requirements.txt",
                    timeout_duration=LONG_TIMEOUT,
                )
                self.communicate(f"rm {PATH_TO_REQS}")
            elif packages == "environment.yml":
                # Write environment.yml to file
                content_env_yml = get_environment_yml(self.record, env_name)
                copy_file_to_container(self.container_obj, content_env_yml, PATH_TO_ENV_YML)
                if "no_use_env" in install_configs and install_configs["no_use_env"]:
                    # Create conda environment
                    self.communicate_with_handling(
                        f"conda create -c conda-forge -n {env_name} python={install_configs['python']} -y",
                        error_msg="Failed to create conda environment",
                        timeout_duration=LONG_TIMEOUT,
                    )
                    # Install packages
                    self.communicate_with_handling(
                        f"conda env update -f {PATH_TO_ENV_YML}",
                        error_msg="Failed to install environment.yml",
                        timeout_duration=LONG_TIMEOUT
                    )
                else:
                    # Create environment + install packages
                    self.communicate_with_handling(
                        f"conda env create --file {PATH_TO_ENV_YML}",
                        error_msg="Failed to create conda environment with environment.yml",
                        timeout_duration=LONG_TIMEOUT,
                    )
                self.communicate(f"rm {PATH_TO_ENV_YML}")
            else:
                # Create environment + install packages
                self.communicate_with_handling(
                    f"conda create -n {env_name} python={install_configs['python']} {packages} -y",
                    error_msg="Failed to create conda environment",
                    timeout_duration=LONG_TIMEOUT,
                )
            # Install extra pip packages if specified
            if "pip_packages" in install_configs:
                self.communicate_with_handling(
                    f"source activate {env_name} && pip install {install_configs['pip_packages']}",
                    error_msg="Failed to install pip packages",
                    timeout_duration=LONG_TIMEOUT
                )

        # Activate environment
        self.communicate_with_handling(
            f"conda activate {env_name}",
            error_msg="Failed to activate conda environment"
        )

        # Install repo at base commit
        if "pre_install" in install_configs:
            self.logger.info("Running pre-install commands...")
            for pre_install_cmd in install_configs["pre_install"]:
                self.communicate_with_handling(
                    pre_install_cmd,
                    error_msg="Pre-install commands failed to execute successfully",
                )
        self.logger.info(f"Installing {repo_name} at base commit...")
        if "install" in install_configs:
            install_cmd = install_configs["install"]
            self.communicate_with_handling(
                install_cmd,
                error_msg="Install command failed to execute successfully",
                timeout_duration=LONG_TIMEOUT
            )
        if "post_install" in install_configs:
            self.logger.info("Running post-install commands...")
            for post_install_cmd in install_configs["post_install"]:
                self.communicate_with_handling(
                    post_install_cmd,
                    error_msg="Post-install commands failed to execute successfully",
                )

    def add_commands(self, commands: list[dict]) -> None:
        """
        Adds custom commands to container
        """
        for command in commands:
            name = command["name"]
            contents = command["contents"]
            copy_file_to_container(self.container_obj, contents, f"/root/commands/{name}")
            if command['type'] == "source_file":
                self.communicate_with_handling(
                    f"source /root/commands/{name}",
                    error_msg=(
                        f"Failed to source {name}. If you meant to make a script,"
                        " start the file with a shebang (e.g. #!/usr/bin/env python)."
                        )
                )
            elif command['type'] == "script":
                self.communicate_with_handling(
                    f"chmod +x /root/commands/{name}",
                    error_msg=f"Failed to chmod {name}",
                )
            elif command['type'] == "utility":
                # nothing to do for utility scripts
                pass
            else:
                raise ValueError(f"Invalid command type: {command['type']}")

    def interrupt(self):
        """
        Send interrupt signal to container and exhaust stdout buffer with a communicate call
        """
        pids = self.get_pids()
        for pid, cmd in pids:
            if pid not in self.parent_pids and cmd != "ps":
                self.container_obj.exec_run(f"kill -9 {pid}")
        try:
            _ = read_with_timeout(self.container, self.get_pids, 20)
        except TimeoutError:
            pass
        try:
            output = self.communicate(input="echo 'interrupted'", timeout_duration=5)
            assert output.strip().endswith("interrupted"), "container health check failed"
        except TimeoutError:
            raise RuntimeError("Failed to interrupt container")