import fnmatch
import io
import json
import os
import tempfile
from pathlib import Path

from devon_agent.tool import ToolContext


def get_ignored_files(gitignore_path):
    ignored_files = []

    # Read the .gitignore file
    with open(gitignore_path, "r") as file:
        gitignore_patterns = file.read().splitlines()

    # Iterate over all files and directories in the current directory
    for root, dirs, files in os.walk("."):
        for pattern in gitignore_patterns:
            # Ignore empty lines and comments in .gitignore
            if pattern.strip() == "" or pattern.startswith("#"):
                continue

            # Match files against the pattern
            for file in fnmatch.filter(files, pattern):
                ignored_files.append(os.path.join(root, file))

            # Match directories against the pattern
            for dir in fnmatch.filter(dirs, pattern):
                ignored_files.append(os.path.join(root, dir))
    assert ignored_files is not None, "No ignored files found"
    return ignored_files


def normalize_path(path: str, specified_path: str):
    specified_path = Path(specified_path).absolute().as_posix()
    if path == os.sep:
        return specified_path
    elif os.path.isabs(path):
        if path.lower().startswith(specified_path.lower()):
            path = Path(path)
            return path.absolute().as_posix()
        else:
            path = Path(path)
            return path.absolute().as_posix()
    else:
        path = Path(specified_path) / Path(path)
        return path.absolute().as_posix()


def make_abs_path(ctx: ToolContext, fpath: str) -> str:
    """
    Converts relative paths to absolute paths based on the container's root directory.

    Args:
        fpath (str): The file path to convert.

    Returns:
        str: The absolute path of the file.
    """

    if ctx["session"].state.exclude_files:
        if fpath in ctx["session"].state.exclude_files:
            return "You are not allowed to change this file"

    return normalize_path(fpath, ctx["session"].base_path)


def get_cwd(ctx) -> str:
    """
    Gets the current working directory of the container.

    Returns:
        str: The current working directory of the container.
    """
    command = "pwd"
    result = ctx["environment"].execute(command)

    # logger.info(f"CWD {result}")

    return result[0].strip() if result[0] else None


def cwd_normalize_path(ctx, path):
    if os.path.isabs(path):
        return make_abs_path(ctx, path)
    else:
        print(get_cwd(ctx), path)
        return make_abs_path(ctx, os.path.join(get_cwd(ctx), path))


def file_exists(ctx, fpath):
    abs_path = cwd_normalize_path(ctx, fpath)
    out, rc = ctx["environment"].execute(f"test -f {abs_path}")

    return rc == 0


def _capture_window(lines, index, window_size):
    start_line = index - window_size if index - window_size >= 0 else 0
    end_line = index + window_size if index + window_size <= len(lines) else len(lines)

    content_lines = "\n".join(lines[start_line:end_line])

    return f"""
Match found on line: {index}
{content_lines}
"""


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

        if abs_path not in ctx["state"].editor.files:
            raise Exception(
                f"Could not write to file, file not open in editor: {abs_path}"
            )

        create_command = f"cat << 'DELIM' > {abs_path} \n" + content + "\nDELIM"
        result = ctx["environment"].execute(create_command)

        if result[1] == 1:
            raise Exception(result)

        ctx["state"].editor.files[abs_path]["lines"] = content
        msg = f"Successfully wrote to file {abs_path}"
        ctx["session"].logger.info(msg)

        return msg

    except Exception as e:
        ctx["session"].logger.error(
            f"Failed to write to file: {abs_path}. Error: {str(e)}"
        )
        raise Exception(f"Failed to write to file: {abs_path}. Error: {str(e)}")


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


def read_file(ctx, file_path: str) -> str:
    """
    Reads the content of a specific file from the docker container.

    Args:
        file_path (str): The path of the file within the system to read.

    Returns:
        str: The content of the file.
    """
    result, _ = ctx["environment"].communicate(f"cat '{file_path}'")
    return result


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


def _list_files_recursive(ctx, files: list[str]) -> dict:
    base_path = ctx["session"].base_path
    result = ctx["environment"].execute(f"find /{base_path} -type f")
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
            result = ctx["environment"].execute(f"cat '{file_path}'")
            files_content[file_path] = result

    return {
        "directory_tree": directory_tree,
        "file_tree": file_tree,
        "files_content": files_content,
    }
