"""
def tool(..., context):
# doctsring here
...

context:
    - environment
    - session
    - state
    - logger
    - task_agent
"""

import io
import json
import logging
import os
import re
import tarfile
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Protocol, TypedDict
from devon_agent.utils import DotDict

from devon_swe_bench_experimental.retrieval.main import (
    get_class_defn,
    get_function_defn,
    initialize_repository,
)
from devon_agent.udiff import (
    Hallucination,
    apply_file_context_diffs,
    extract_all_diffs,
    log_failed_diff,
    log_successful_diff,
)

if TYPE_CHECKING:
    from devon_agent.environment import EnvironmentModule
    from devon_agent.agent import Agent


# class ToolContext(TypedDict):
#     environment: EnvironmentModule
#     add_event: Callable
#     logger: logging.Logger
#     task_agent: Agent
#     state: DotDict


# class ToolModule(Protocol):

#     def setup(self, ctx : ToolContext):
#         pass

#     def __call__(self, ctx : ToolContext, **kwargs):
#         pass

#     def cleanup(self, ctx : ToolContext):
#         pass


ToolContext = Any


def normalize_path(path, specified_path):
    if path == os.sep:
        return specified_path
    elif os.path.isabs(path):
        if path.startswith(specified_path):
            path = Path(path)
            return path.absolute().as_posix()
        else:
            path_components = path.strip(os.sep).split(os.sep)
            path_components[0] = specified_path.strip(os.sep)
            path = os.sep + os.path.join(*path_components)
            path = Path(path)
            return path.absolute().as_posix()
    else:
        path = Path(specified_path) / Path(path)
        return path.absolute().as_posix()


def make_abs_path(ctx, fpath: str) -> str:
    """
    Converts relative paths to absolute paths based on the container's root directory.

    Args:
        fpath (str): The file path to convert.

    Returns:
        str: The absolute path of the file.
    """

    return normalize_path(fpath, ctx.base_path)


def load_file_to_editor(ctx, file_path):
    """
    Loads the given file path into the editor.
    """
    abs_path = make_abs_path(ctx, file_path)
    contents = read_file(ctx, abs_path)
    ctx.state.editor[abs_path]["lines"] = contents


def refresh_editor(ctx):
    if ctx.state.editor is None:
        raise ValueError("Editor is not set")
    for path in list(ctx.state.editor.keys()):
        load_file_to_editor(ctx, path)


def cwd_normalize_path(ctx, path):
    if os.path.isabs(path):
        return make_abs_path(ctx, path)
    else:
        print(get_cwd(ctx), path)
        return make_abs_path(ctx, os.path.join(get_cwd(ctx), path))


def file_exists(ctx, fpath):
    abs_path = make_abs_path(ctx, fpath)
    return ctx.environment.execute(f"test -f {abs_path}")[1] == 0


def read_file(ctx, file_path: str) -> str:
    """
    Reads the content of a specific file from the docker container.

    Args:
        file_path (str): The path of the file within the system to read.

    Returns:
        str: The content of the file.
    """
    result, _ = ctx.environment.communicate(f"cat '{file_path}'")
    return result


def _list_files_recursive(ctx, files: list[str]) -> dict:
    result = ctx.environment.execute(f"find /{ctx.base_path} -type f")
    all_files = result[0].split("\n") if result[0] else []

    # Generate file tree as a nested dictionary and read specified files
    def add_to_tree(path, tree):
        parts = path.strip("/").split("/")
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
            result = ctx.environment.execute(f"cat '{file_path}'")
            files_content[file_path] = result

    return {
        "directory_tree": directory_tree,
        "file_tree": file_tree,
        "files_content": files_content,
    }


def check_lint(ctx, code_string: str, file_path: str):
    """
    Checks the given code string for linting errors.
    """

    # example json
    # [{'type': 'error', 'module': 'tmp5cpif150', 'obj': 'ModelFormMetaclass.__new__', 'line': 224, 'column': 20, 'endLine': 224, 'endColumn': 60, 'path': '/tmp/tmp5cpif150', 'symbol': 'too-many-function-args', 'message': 'Too many positional arguments for classmethod call', 'message-id': 'E1121'}, {'type': 'error', 'module': 'tmp5cpif150', 'obj': 'ModelForm', 'line': 477, 'column': 0, 'endLine': 477, 'endColumn': 15, 'path': '/tmp/tmp5cpif150', 'symbol': 'invalid-metaclass', 'message': "Invalid metaclass 'ModelFormMetaclass' used", 'message-id': 'E1139'}, {'type': 'error', 'module': 'tmp5cpif150', 'obj': 'ModelChoiceField.__deepcopy__', 'line': 1250, 'column': 17, 'endLine': 1250, 'endColumn': 41, 'path': '/tmp/tmp5cpif150', 'symbol': 'bad-super-call', 'message': "Bad first argument 'ChoiceField' given to super()", 'message-id': 'E1003'}]

    from pylint.lint import Run
    from pylint.reporters.json_reporter import JSONReporter

    pylint_output = io.StringIO()  # Custom open stream
    reporter = JSONReporter(pylint_output)

    with tempfile.NamedTemporaryFile(mode="w+") as f:
        f.write(code_string)
        f.seek(0)
        Run(
            args=["--disable=all", "--enable=E0602,E1101", f.name],
            reporter=reporter,
            exit=False,
        )

    results = json.loads(pylint_output.getvalue())

    return results


def list_dirs_recursive(ctx, file_path: str) -> dict:
    """
    Returns the entire directory tree in its entirety from the file system.

    Args:
        path: the path to list the folder subtree from.

    Returns:
        dict: A dictionary with two keys: 'file_tree' containing a list of all files in the tree,
            and 'files_content' containing a dictionary of specified files and their content.
    """

    abs_path = make_abs_path(ctx, file_path)

    return json.dumps(_list_files_recursive(ctx, [abs_path])["directory_tree"])


def open_file(ctx, file_path: str):
    """
    Opens a file, and displays it in the editor..

    Args:
        file_path (str): The path of the file to open.
    """
    try:
        abs_path = make_abs_path(ctx, file_path)

        if abs_path in ctx.state.editor:
            raise Exception(f"File {abs_path} already open in editor")
        exists = file_exists(ctx, abs_path)
        if not exists:
            raise Exception(f"Could not open file, file does not exist: {abs_path}")

        file_contents = read_file(ctx, file_path=abs_path)
        ctx.state.editor[abs_path] = {}
        ctx.state.editor[abs_path]["lines"] = file_contents
        ctx.state.editor[abs_path]["page"] = 0

        return f"File {abs_path} opened in editor"

    except Exception as e:
        ctx.logger.error(f"Failed to open file: {abs_path}. Error: {str(e)}")
        return f"Failed to open file: {abs_path}. Error: {str(e)}"


# TOOL FUNCTIONS


def scroll_down(ctx, file_path: str):
    """
    SCROLL_DOWN(1)        General Commands Manual        SCROLL_DOWN(1)

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

    SCROLL_DOWN(1)         April 2024         SCROLL_DOWN(1)
    """

    abs_path = make_abs_path(ctx, file_path)

    exists = file_exists(ctx, abs_path)
    if not exists:
        raise Exception(f"Could not scroll in file, file does not exist: {abs_path}")

    if abs_path not in ctx.state.editor:
        raise Exception(f"Could not scroll in file, file is not open: {abs_path}")

    lines = ctx.state.editor[abs_path]["lines"].splitlines()

    last_page_idx = len(lines) // ctx.state.PAGE_SIZE

    old_page_number = ctx.state.editor[abs_path]["page"]

    if old_page_number == last_page_idx:
        new_page_number = last_page_idx
    else:
        new_page_number = old_page_number + 1

    ctx.state.editor[abs_path]["page"] = new_page_number

    return f"Scrolled down in file {abs_path} to line {ctx.state.PAGE_SIZE * new_page_number}"


def scroll_up(ctx, file_path: str):
    """
    SCROLL_UP(1)        General Commands Manual        SCROLL_UP(1)

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

    SEE ALSO
        scroll_down(1), open_file(1), close_file(1)

    SCROLL_UP(1)         April 2024         SCROLL_UP(1)
    """
    abs_path = make_abs_path(ctx, file_path)

    exists = file_exists(ctx, abs_path)
    if not exists:
        raise Exception(f"Could not scroll in file, file does not exist: {abs_path}")

    if abs_path not in ctx.state.editor:
        raise Exception(f"Could not scroll in file, file is not open: {abs_path}")

    # lines = ctx.state.editor[abs_path]["lines"].splitlines()

    old_page_number = ctx.state.editor[abs_path]["page"]

    if old_page_number == 0:
        new_page_number = 0
    else:
        new_page_number = old_page_number - 1

    ctx.state.editor[abs_path]["page"] = new_page_number

    return f"Scrolled up in file {abs_path} to line {ctx.state.PAGE_SIZE * new_page_number}"


def scroll_to_line(ctx, file_path: str, line_number: str):
    """
    SCROLL_TO_LINE(1)        General Commands Manual        SCROLL_TO_LINE(1)

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

    SCROLL_TO_LINE(1)         April 2024         SCROLL_TO_LINE(1)
    """
    abs_path = make_abs_path(ctx, file_path)

    exists = file_exists(ctx, abs_path)
    if not exists:
        raise Exception(f"Could not scroll in file, file does not exist: {abs_path}")

    if abs_path not in ctx.state.editor:
        raise Exception(f"Could not scroll in file, file is not open: {abs_path}")

    lines = ctx.state.editor[abs_path]["lines"].splitlines()
    total_lines = len(lines)
    line_number = int(line_number)

    if line_number < 0 or line_number > total_lines:
        raise Exception(
            f"Invalid line number: {line_number}. Line number should be between 1 and {total_lines}."
        )

    window_number = (line_number) // ctx.state.PAGE_SIZE
    ctx.state.editor[abs_path]["page"] = window_number

    window_start_line = window_number * ctx.state.PAGE_SIZE + 1
    return f"Scrolled to window containing line {line_number} in file {abs_path}. Window starts at line {window_start_line}."


def close_file(ctx, file_path: str) -> bool:
    """
    Removes the target file from the editor.

    Args:
        file_path (str): The path of the file to delete from the editor.

    Returns:
        bool: True if the file was successfully deleted, False otherwise.
    """

    abs_path = make_abs_path(ctx, file_path)

    if abs_path in ctx.state.editor:
        del ctx.state.editor[abs_path]
        return "Successfully closed file!"

    return "False, file not open in editor"


def write_file(ctx, file_path: str, content: str = "") -> str:
    """
    Writes the given content to the given file path.
    """

    try:
        # Check if file doesnt already exists to avoid overwriting
        abs_path = make_abs_path(ctx, file_path)

        exists = file_exists(ctx, abs_path)
        if not exists:
            raise Exception(f"Could not write to file, file does not exist: {abs_path}")

        create_command = f"cat << 'DELIM' > {abs_path} \n" + content + "\nDELIM"
        result = ctx.environment.execute(create_command)

        if result[1] == 1:
            raise Exception(result)

        ctx.state.editor[abs_path]["lines"] = content
        msg = f"Successfully wrote to file {abs_path}"
        ctx.logger.info(msg)

        return msg

    except Exception as e:
        ctx.logger.error(f"Failed to write to file: {abs_path}. Error: {str(e)}")
        raise Exception(f"Failed to write to file: {abs_path}. Error: {str(e)}")


def delete_file(ctx, file_path: str) -> bool:
    try:
        # Check if file already exists to avoid overwriting
        abs_path = make_abs_path(file_path)

        exists = ctx.file_exists(abs_path)
        if not exists:
            raise Exception(f"Could not delete file, file does not exist: {abs_path}")

        # Creating the file with initial content
        ctx.environment.execute(f"rm -f {abs_path}")

        if abs_path in ctx.state.editor:
            del ctx.state.editor[abs_path]
        return f"Successfully deleted file {abs_path}"

    except Exception as e:
        ctx.logger.error(f"Failed to delete file: {abs_path}. Error: {str(e)}")
        return f"Failed to delete file: {abs_path}. Error: {str(e)}"


def create_file(ctx, file_path: str, content: str = "") -> bool:
    """
    CREATE_FILE(1)                   General Commands Manual                  CREATE_FILE(1)

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

    SEE ALSO
            touch(1), echo(1)

    CREATE_FILE(1)                        April 2024                         CREATE_FILE(1)
    """
    try:
        # Check if file already exists to avoid overwriting
        abs_path = make_abs_path(ctx, file_path)

        exists = file_exists(ctx, abs_path)
        if exists:
            raise Exception(f"Could not create file, file already exists: {abs_path}")

        # Creating the file with initial content

        create_command = (
            f"mkdir -p $(dirname '{abs_path}') && cat << 'DELIM' > '{abs_path}' \n"
            + content
            + "\nDELIM"
        )
        ctx.environment.execute(create_command)

        # copy_file_to_container(self.container_obj, contents=content, container_path=file_path)

        exists = file_exists(ctx, abs_path)

        # Verify file creation
        if not exists:
            raise Exception(f"Command failed to create file: {abs_path}")

        ctx.state.editor[abs_path] = {}
        ctx.state.editor[abs_path]["lines"] = content
        ctx.state.editor[abs_path]["page"] = 0
        return f"Successfully created file {abs_path}"

    except Exception as e:
        ctx.logger.error(f"Failed to create file: {file_path}. Error: {str(e)}")
        # traceback.print_exc()
        # raise e
        return f"Failed to create file: {file_path}. Error: {str(e)}"


def view_open_files(ctx) -> dict:
    """
    Returns the current state of the open files.

    Returns:
        dict: A dictionary representing the open files
    """
    return json.dumps(ctx.state.editor)


def edit_file(ctx, diff: str) -> dict:
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


def apply_diff(ctx, multi_file_diffs):
    """
    Applies the given diffs to the codebase.
    """

    results = []

    for file_diff in multi_file_diffs:
        src_file = file_diff.src_file
        tgt_file = file_diff.tgt_file

        # diff_logger.debug(src_file + " " + tgt_file)
        if not (src_file or tgt_file):
            raise Hallucination(
                "Could not apply changes, missing source or target file."
            )

        # diff_logger.debug("Applying diff to: %s, %s", src_file, tgt_file)

        # Ensure src_file and tgt_file are valid paths, if not, make them absolute paths from file_tree_root
        src_file_abs = make_abs_path(ctx, src_file)
        tgt_file_abs = make_abs_path(ctx, tgt_file)

        src_file_exists = (
            ctx.environment.execute(f"test -e {src_file_abs} && echo 'exists'")[
                0
            ].strip()
            == "exists"
        )

        # diff_logger.debug("Applying diff to: %s, %s", src_file_abs, tgt_file_abs)
        cwd = ctx.environment.get_cwd().strip()

        if tgt_file_abs.startswith(cwd):
            tgt_file_abs = make_abs_path(ctx, tgt_file_abs)
        else:
            tgt_file_abs = make_abs_path(ctx, os.path.join(cwd, tgt_file_abs))

        if src_file_abs.startswith(cwd):
            src_file_abs = make_abs_path(ctx, src_file_abs)
        else:
            src_file_abs = make_abs_path(ctx, os.path.join(cwd, src_file_abs))

        if not src_file_exists:
            raise Exception(
                f"Failed to write diff with source file: {src_file}, {src_file_abs} not open"
            )

        # Modifying an existing file
        src_content = read_file(ctx, file_path=src_file_abs)
        # diff_logger.debug("source content: %s", src_content)

        file_diff.src_file = src_file_abs
        file_diff.tgt_file = tgt_file_abs

        apply_result = apply_file_context_diffs(src_content, [file_diff])
        results.append(apply_result)

    return results


def check_lint_entry_equal(a, b):
    """
    Checks if two lint entries are equal.
    """
    if (
        a["obj"] == b["obj"]
        and a["column"] == b["column"]
        and a["endColumn"] == b["endColumn"]
        and a["message"] == b["message"]
        and a["message-id"] == b["message-id"]
    ):
        print("Success, these are equal")
        return True
    return False


def check_lint_entry_in_list(a, b_set):
    """
    Checks if a lint entry is in a list of lint entries.
    """

    return any(check_lint_entry_equal(a, entry) for entry in b_set)


def real_write_diff(ctx, diff):
    """
    Writes the given diff to the codebase.
    """

    diff_code = diff

    all_diffs, _ = extract_all_diffs(diff_code)
    results = apply_diff(ctx, all_diffs)
    # print("diff applied")
    failures = []
    successes = []
    for result in results:
        if len(result["fail"]) > 0:
            failures.extend(result["fail"])
            for failure in result["fail"]:
                log_failed_diff(
                    diff=diff_code,
                    file_content=failure[2],
                    src_file=failure[0],
                    tgt_file=failure[0],
                )
        if len(result["success"]) > 0:
            successes.extend(result["success"])
            for success in result["success"]:
                log_successful_diff(
                    diff=diff_code,
                    file_content=success[2],
                    src_file=success[0],
                    tgt_file=success[0],
                )

    if len(failures) == 0:
        file_paths = []
        diff_results = []
        for result in successes:
            # This will overwrite if the tgt files are the same, but doesnt really matter in this case because its usually only one diff

            target_path = result[0]

            if target_path.endswith(".py"):
                try:
                    compile(result[1], "<string>", "exec")
                    before_results = check_lint(
                        ctx, read_file(ctx, target_path), target_path
                    )
                except Exception as e:
                    return "Error applying diff: \n" + repr(e)

            old_editor_code = "\n".join(ctx.state.editor[target_path]["lines"])

            write_file(ctx, file_path=target_path, content=result[1])
            file_paths.append(target_path)

            new_editor_code = "\n".join(ctx.state.editor[target_path]["lines"])

            assert old_editor_code != new_editor_code

            if target_path.endswith(".py"):
                after_results = check_lint(ctx, result[1], target_path)

                diff_results = [
                    x
                    for x in after_results
                    if not check_lint_entry_in_list(x, before_results)
                ]

        paths = ", ".join(file_paths)

        if diff_results:
            lint_error_message = ""
            for rst in diff_results:
                lint_error_message += f"{rst['type']}: {rst['message']} on line {rst['line']} column {rst['column']}. Line {result[1].splitlines()[int(rst['line'])-1]} \n"

            return f"Successfully edited file(s): {paths}. Please review the new contents of the files. Your change introduced the following linting errors. Please address them before you submit. \n{lint_error_message}"

        return f"Successfully edited file(s): {paths}. Please review the new contents of the files."

    return "\n".join(["Failed to edit file"] + [f[1].args[0] for f in failures])


def create_tar(file_path):
    """
    Creates a tar file from the given file path.
    """

    # Create a tar file in memory
    tar_stream = io.BytesIO()
    with tarfile.open(fileobj=tar_stream, mode="w") as tar:
        tar.add(file_path, arcname=os.path.basename(file_path))

    # Seek to the beginning of the stream
    tar_stream.seek(0)
    tar_data = tar_stream.read()

    return tar_data


def build_index(ctx, file_path):
    """
    Builds the code index from the given file path.
    """

    tar_data = create_tar(file_path)
    # logger.debug(tar_data)

    with tempfile.NamedTemporaryFile() as temp_file:
        temp_file.write(tar_data)
        temp_file.flush()
        # print(temp_file.read())
        temp_file.seek(0)

        temp_dir = tempfile.mkdtemp()
        ctx.state.code_index.class_table.temp_dir = temp_dir
        ctx.state.code_index.function_table.temp_dir = temp_dir

        # save archive to file
        with tarfile.open(fileobj=temp_file, mode="r") as tar:
            tar.extractall(path=temp_dir)

        code_graph = initialize_repository(
            temp_dir,
            ctx.state.code_index.class_table,
            ctx.state.code_index.function_table,
        )

        # os.remove(temp_file)

    return code_graph


def find_function(ctx, function_name):
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

    return str(get_function_defn(function_name, ctx.state.code_index.function_table))


def find_class(ctx, class_name):
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

    class_defns = get_class_defn(class_name, ctx.state.code_index.class_table)
    if len(class_defns) > 1:
        if len(str(class_defns)) > 4000:
            for class_defn in class_defns:
                del class_defn["code"]

    return str(get_class_defn(class_name, ctx.state.code_index.class_table))


## END DIFF CODE


def submit(ctx):
    """NAME
            submit - submit your solution once you think you have resolved the issue

    SYNOPSIS
            submit

    DESCRIPTION
            The submit command submits your solution. It is used to indicate that you have resolved the issue and are ready to submit your
            solution.
    """
    #     command = (
    #         """submit() {
    # cd"""
    #         + ctx.base_path
    #         + """
    # git add -A
    # git diff --cached > model.patch
    # echo "<<SUBMISSION||"
    # cat model.patch
    # echo "||SUBMISSION>>"
    # }
    # submit"""
    #     )
    #     return ctx.environment.communicate(command)
    return "Submitted"


def find_file(ctx, file_path: str):
    """
    FIND_FILE(1)        General Commands Manual        FIND_FILE(1)

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

    SEE ALSO
        ls(1), locate(1)

    FIND_FILE(1)         April 2024         FIND_FILE(1)
    """
    filename = os.path.basename(file_path)
    command = f"find {ctx.base_path} -type f -name '{filename}'"
    result = ctx.environment.execute(command)
    if result[0] is None:
        return "No such file. Make sure the file exists"
    return result[0]


def search_dir(ctx, search_term: str, dir: str = "./"):
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
        search_term = '"' + search_term + '"'

    abs_path = cwd_normalize_path(ctx, dir)

    command = f"find {abs_path} -type f ! -path '*/.*' -exec grep -nIH '{search_term}' {{}} + | cut -d: -f1 | sort | uniq -c"
    result = ctx.environment.execute(command)

    matches = result[0].strip()
    if not matches:
        return f'No matches found for "{search_term}" in {abs_path}'
    # print(matches)
    try:
        num_matches = sum(int(line.split()[0]) for line in matches.split("\n"))
    except Exception:
        raise Exception(
            "Command not formed well. Make sure the term you are searching for is in quotes and you are providing the correct directory."
            + matches
        )
    num_files = matches.count("\n") + 1

    if num_files > 100:
        return f'More than {num_files} files matched for "{search_term}" in {abs_path}. Please narrow your search.'

    result = (
        f'Found {num_matches} matches for "{search_term}" in {abs_path}:\n{matches}'
    )
    return result.replace("\n", "\n    ")


def _capture_window(lines, index, window_size):
    start_line = index - window_size if index - window_size >= 0 else 0
    end_line = index + window_size if index + window_size <= len(lines) else len(lines)

    content_lines = "\n".join(lines[start_line:end_line])

    return f"""
Match found on line: {index}
{content_lines}
"""


def search_file(ctx, search_term: str, file_path: str = None):
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

    abs_path = cwd_normalize_path(ctx, file_path)

    if abs_path not in ctx.state.editor:
        raise Exception(f"Could not find in file, file is not open: {abs_path}")

    content_lines = ctx.state.editor[abs_path]["lines"].splitlines()

    matches = []
    tolerance = 10
    for i, line in enumerate(content_lines):
        if search_term in line:
            matches.append(_capture_window(content_lines, i, tolerance))

    if not matches:
        return f'No matches found for "{search_term}" in {abs_path}'

    num_matches = len(matches)

    if num_matches > 10:
        return f'More than {10} lines matched for "{search_term}" in {abs_path}. Please narrow your search.'

    matches = "\n".join(matches)
    result = (
        f'Found {num_matches} matches for "{search_term}" in {abs_path}:\n {matches}'
    )
    return result


#     def search_files(self, file_name: str, dir: str = "./"):
#         """
#         NAME
#       search_files - find all files with a given name in a directory

# SYNOPSIS
#       search_files [FILE_NAME] [DIR]

# DESCRIPTION
#       The search_files command finds all files with the given FILE_NAME in the specified
#       DIR. If DIR is not provided, it searches in the current directory.

# OPTIONS
#       FILE_NAME
#              The name of the file to search for.

#       DIR   The directory to search in. If not provided, the command searches in the
#              current directory ("./").

# RETURN VALUE
#       The search_files command returns a summary of the search results as a string.

# EXAMPLES
#       To find all files named "example.txt" in the current directory:

#              search_files "example.txt"

#       To find all files named "data.csv" in the "/path/to/directory" directory:

#              search_files "data.csv" "/path/to/directory"
#         """

#         command = f"grep -rl '{file_name}' {dir}"
#         result = self.communicate(command)

#         matches = result
#         if not matches:
#             return f"No matches found for \"{file_name}\" in {dir}"

#         num_matches = matches.count('\n') + 1
#         result = f"Found {num_matches} matches for \"{file_name}\" in {dir}:\n{matches}"
#         return result.replace('\n', '\n    ')


def list_files(ctx, folder_path: str = ".") -> list:
    """NAME
            list_files - list all files in a specific folder

    SYNOPSIS
            list_files [FOLDER_PATH]

    DESCRIPTION
            The list_files command lists all files in the specified FOLDER_PATH. If no
            FOLDER_PATH is provided, it lists files in the current directory.

    OPTIONS
            FOLDER_PATH
                    The path of the folder to list files from. If not specified, the command
                    lists files in the current directory (".").

    RETURN VALUE
            The list_files command returns a list of file paths within the specified folder.

    EXAMPLES
            To list all files in the current directory:

                    list_files

            To list all files in the "/path/to/directory" directory:

                    list_files "/path/to/directory"
    """

    abs_path = cwd_normalize_path(ctx, folder_path)

    command = f"grep -rl '' {abs_path}"
    result = ctx.environment.execute(command)

    return result


def get_cwd(ctx) -> str:
    """
    Gets the current working directory of the container.

    Returns:
        str: The current working directory of the container.
    """
    command = "pwd"
    result = ctx.environment.execute(command)

    # logger.info(f"CWD {result}")

    return result[0].strip() if result[0] else None


def no_op(ctx) -> str:
    """
    Lets you think! This allows you to take a brief moment to think and synthesize what you know about the current state of the system.

    Make sure you think step by step!
    """

    return "No Action Taken"


def extract_signature_and_docstring(function_code: str) -> tuple:
    """
    Extracts the function signature and docstring from the given Python function code.

    Args:
        function_code (str): The Python function code as a string.

    Returns:
        tuple: A tuple containing the function signature (str) and the docstring (str).
    """
    # Extract the function signature
    signature_match = re.search(r"def\s+(\w+)\((.*?)\)", function_code)
    if signature_match:
        fn_name = signature_match.group(1)
        args = signature_match.group(2).split(",")
        args = [
            arg.strip().split(":")[0].split("=")[0]
            for arg in args
            if arg.strip() and arg.strip() != "self"
        ]
        signature = f"{fn_name} {' '.join(args)}"
    else:
        signature = ""

    # Extract the docstring
    docstring_match = re.search(r'"""(.*?)"""', function_code, re.DOTALL)
    if docstring_match:
        docstring = docstring_match.group(1).strip()
    else:
        docstring = ""

    return signature, docstring


def parse_command(ctx, command: str) -> tuple:
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
                args.extend(
                    [arg.strip('"').strip("'") for arg in after_multiline.split()]
                )
        else:
            # Handle single line arguments
            temp_pre = re.findall(r'(?:[^\s"]+|"[^"]*")+', arg_string)
            args = [arg.strip('"').strip("'") for arg in temp_pre]

    return fn_name, args


def ask_user(ctx, question):
    """
    ask_user "question"
    Asks the user for their input
    """
    pass
    # user_response = input(question)
    # return user_response


# Output is the submission observation?
def get_submission(ctx, output: str) -> str:
    """
    Function for extracting diff patch submission at the end of an episode.

    Args:
        output (`str`) - `submit` observation
    Returns:
        submission (`str`) - diff patch submission
    """
    if output is None:
        output = ""
    print(output)
    assert isinstance(output, str), "Output must be a string"
    ctx.logger.info(output)
    pattern = r"\<\<SUBMISSION\|\|(.*)\|\|SUBMISSION\>\>"
    match = re.search(pattern, output, re.DOTALL)
    if match is None:
        return None
    return match.group(1)


def exit(ctx):
    """
    NAME
        exit - exit the current task

    SYNOPSIS
        exit
    """
    pass


def set_task(ctx: ToolContext, task):
    """
    NAME
        set_task - set the current task

    SYNOPSIS
        set_task TASK
    """
    pass
