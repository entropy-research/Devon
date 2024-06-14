from devon_agent.tool import PreTool, Tool, ToolContext
from devon_agent.tools.utils import (cwd_normalize_path, file_exists,
                                     make_abs_path, read_file)
from devon_agent.utils import DotDict
from devon_agent.vgit import (commit_files, simple_stash_and_commit_changes,
                              stash_and_commit_changes)


def load_file_to_editor(ctx, file_path):
    """
    Loads the given file path into the editor.
    """
    abs_path = make_abs_path(ctx, file_path)
    contents = read_file(ctx, abs_path)
    ctx["state"].editor.files[abs_path]["lines"] = contents


def refresh_editor(ctx):
    if ctx["state"].editor is None:
        raise ValueError("Editor is not set")
    for path in list(ctx["state"].editor.files.keys()):
        load_file_to_editor(ctx, path)


PAGE_SIZE = 200


class OpenFileTool(Tool):
    @property
    def supported_formats(self):
        return ["docstring", "manpage"]

    @property
    def name(self):
        return "open_file"

    def setup(self, ctx: ToolContext):
        ctx["state"].editor = DotDict({})
        ctx["state"].editor.files = {}
        ctx["state"].editor.PAGE_SIZE = PAGE_SIZE

    def cleanup(self, ctx: ToolContext):
        del ctx["state"].editor

    def documentation(self, format="docstring"):
        match format:
            case "docstring":
                return self.function.__doc__
            case "manpage":
                return """
    OPEN_FILE(1)                   General Commands Manual                  OPEN_FILE(1)

    NAME
            open_file - open a new file at the target path

    SYNOPSIS
            open_file FILE_PATH

    DESCRIPTION
            The open_file command opens a new file at the specified FILE_PATH within the
            file system.

    OPTIONS
            FILE_PATH
                    The path of the file to create within the system.

    RETURN VALUE
            The open_file command returns a boolean value:

            True  If the file was successfully opened.

            False If opening the file failed.

    EXAMPLES
            To open aa file at "/path/to/file.txt":

                    open_file "/path/to/file.txt"

    SEE ALSO
            cat(1), echo(1)

    OPEN_FILE(1)                        April 2024                         OPEN_FILE(1)
    """
            case _:
                raise ValueError(f"Invalid format: {format}")

    def function(self, ctx, file_path):
        """
        command_name: open_file
        description: opens a file in your editor interface so you can see it
        signature: open_file [FILE_PATH]
        example: `open_file ./README.md`
        """
        try:
            abs_path = cwd_normalize_path(ctx, file_path)

            if abs_path in ctx["state"].editor.files:
                raise Exception(f"File {abs_path} already open in editor")

            exists = file_exists(ctx, abs_path)
            if not exists:
                raise Exception(f"Could not open file, file does not exist: {abs_path}")

            file_contents = read_file(ctx, file_path=abs_path)
            ctx["state"].editor.files[abs_path] = {}
            ctx["state"].editor.files[abs_path]["lines"] = file_contents
            ctx["state"].editor.files[abs_path]["page"] = 0

            return f"File {abs_path} opened in editor"

        except Exception as e:
            ctx["session"].logger.error(
                f"Failed to open file: {file_path}. Error: {str(e)}"
            )
            return f"Failed to open file: {file_path}. Error: {str(e)}"


class CloseFileTool(Tool):
    @property
    def supported_formats(self):
        return ["docstring", "manpage"]

    @property
    def name(self):
        return "close_file"

    def setup(self, ctx: ToolContext):
        ctx["state"].editor = {}
        ctx["state"].editor.files = {}
        ctx["state"].editor.PAGE_SIZE = PAGE_SIZE

    def cleanup(self, ctx: ToolContext):
        del ctx["state"].editor

    def documentation(self, format="docstring"):
        match format:
            case "docstring":
                return self.function.__doc__
            case "manpage":
                return """
    CLOSE_FILE(1)                   General Commands Manual                  CLOSE_FILE(1)

    NAME
            close_file - close a new file at the target path

    SYNOPSIS
            close_file FILE_PATH

    DESCRIPTION
            The close_file command closes a new file at the specified FILE_PATH within the
            file system.

    OPTIONS
            FILE_PATH
                    The path of the file to create within the system.

    RETURN VALUE
            The close_file command returns a boolean value:

            True  If the file was successfully opened.

            False If opening the file failed.

    EXAMPLES
            To close a file at "/path/to/file.txt":

                close_file "/path/to/file.txt"

    SEE ALSO
            cat(1), echo(1)

    CLOSE_FILE(1)                        April 2024                         CLOSE_FILE(1)
    """
            case _:
                raise ValueError(f"Invalid format: {format}")

    def function(self, ctx, file_path):
        """
        command_name: close_file
        description: closes a file in your editor interface
        signature: close_file [FILE_PATH]
        example: `close_file ./README.md`
        """

        abs_path = cwd_normalize_path(ctx, file_path)

        if abs_path not in ctx["state"].editor.files:
            raise Exception(f"File {abs_path} not open in editor")

        del ctx["state"].editor.files[abs_path]
        return "Successfully closed file!"


class DeleteFileTool(Tool):
    @property
    def name(self):
        return "delete_file"

    @property
    def supported_formats(self):
        return ["docstring", "manpage"]

    def setup(self, ctx):
        pass

    def cleanup(self, ctx):
        pass

    def supported_formats(self):
        return ["docstring", "manpage"]

    def documentation(self, format="docstring"):
        match format:
            case "docstring":
                return self.function.__doc__
            case "manpage":
                return """
    DELETE_FILE(1)                   General Commands Manual                  DELETE_FILE(1)

    NAME
            delete_file - delete a file at the target path

    SYNOPSIS
            delete_file FILE_PATH

    DESCRIPTION
            The delete_file command deletes a file at the specified FILE_PATH within the
            file system.

    OPTIONS
            FILE_PATH
                    The path of the file to delete within the system.

    RETURN VALUE
            The delete_file command returns a boolean value:

            True  If the file was successfully deleted.

            False If the file deletion failed.

    EXAMPLES
            To delete a file at "/path/to/file.txt":

                    delete_file "/path/to/file.txt" 
    """
            case _:
                raise ValueError(f"Invalid format: {format}")

    def function(self, ctx: ToolContext, file_path: str) -> str:
        """
        command_name: delete_file
        description: deletes a file
        signature: delete_file [FILE_PATH]
        example: `delete_file ./README.md`
        """

        try:
            # Check if file already exists to avoid overwriting
            abs_path = cwd_normalize_path(file_path)

            exists = file_exists(ctx, abs_path)
            if not exists:
                raise Exception(
                    f"Could not delete file, file does not exist: {abs_path}"
                )

            # Creating the file with initial content
            ctx["environment"].execute(f"rm -f {abs_path}")

            if abs_path in ctx["state"].editor.files:
                del ctx["state"].editor.files[abs_path]

            return f"Successfully deleted file {abs_path}"

        except Exception as e:
            ctx["session"].logger.error(
                f"Failed to delete file: {file_path}. Error: {str(e)}"
            )
            return f"Failed to delete file: {file_path}. Error: {str(e)}"


class CreateFileTool(Tool):
    @property
    def name(self):
        return "create_file"

    def setup(self, ctx):
        pass

    def cleanup(self, ctx):
        pass

    def supported_formats(self):
        return ["docstring", "manpage"]

    def documentation(self, format="docstring"):
        match format:
            case "docstring":
                return self.function.__doc__
            case "manpage":
                return """
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
            case _:
                raise ValueError(f"Invalid format: {format}")

    def function(self, ctx: ToolContext, file_path: str, content: str = "") -> str:
        """
        command_name: create_file
        description: creates a file in your editor interface and file system
        signature: create_file file_path <<<content>>>
        example: `create_file README.md <<<
        # HEADER 1
        This is a good readme
        >>>`
        """
        try:
            # Check if file already exists to avoid overwriting
            abs_path = cwd_normalize_path(ctx, file_path)

            exists = file_exists(ctx, abs_path)
            if exists:
                raise Exception(
                    f"Could not create file, file already exists: {file_path}"
                )

            # Creating the file with initial content

            create_command = (
                f"mkdir -p $(dirname '{abs_path}') && cat << 'DELIM' > '{abs_path}' \n"
                + content
                + "\nDELIM"
            )
            ctx["environment"].execute(create_command)

            # copy_file_to_container(self.container_obj, contents=content, container_path=file_path)

            exists = file_exists(ctx, abs_path)

            # Verify file creation
            if not exists:
                raise Exception(f"Command failed to create file: {file_path}")

            ctx["state"].editor.files[abs_path] = {}
            ctx["state"].editor.files[abs_path]["lines"] = content
            ctx["state"].editor.files[abs_path]["page"] = 0
            return f"Successfully created file {file_path}"

        except Exception as e:
            ctx["session"].logger.error(
                f"Failed to create file: {file_path}. Error: {str(e)}"
            )
            # traceback.print_exc()
            # raise e
            return f"Failed to create file: {file_path}. Error: {str(e)}"


class ScrollUpTool(Tool):
    @property
    def supported_formats(self):
        return ["docstring", "manpage"]

    @property
    def name(self):
        return "scroll_up_in_editor"

    def setup(self, ctx: ToolContext):
        ctx["state"].editor.files = {}
        ctx["state"].editor.PAGE_SIZE = PAGE_SIZE

    def cleanup(self, ctx: ToolContext):
        del ctx["state"].editor

    def documentation(self, format="docstring"):
        match format:
            case "docstring":
                return self.function.__doc__
            case "manpage":
                return """
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
            case _:
                raise ValueError(f"Invalid format: {format}")

    def function(self, ctx, file_path):
        """
        command_name: scroll_up
        description: scroll up by one page in the specified file in the editor
        signature: scroll_up [FILE_PATH]
        example: `scroll_up ./README.md`
        """

        abs_path = cwd_normalize_path(ctx, file_path)

        exists = file_exists(ctx, abs_path)
        if not exists:
            raise Exception(
                f"Could not scroll in file, file does not exist: {abs_path}"
            )

        if abs_path not in ctx["state"].editor.files:
            raise Exception(f"Could not scroll in file, file is not open: {abs_path}")

        # lines = ctx["state"]editor[abs_path]["lines"].splitlines()

        old_page_number = ctx["state"].editor.files[abs_path]["page"]

        if old_page_number == 0:
            new_page_number = 0
        else:
            new_page_number = old_page_number - 1

        ctx["state"].editor.files[abs_path]["page"] = new_page_number

        return f"Scrolled up in file {abs_path} to line {ctx['state'].editor.PAGE_SIZE * new_page_number}"


class ScrollDownTool(Tool):
    @property
    def supported_formats(self):
        return ["docstring", "manpage"]

    @property
    def name(self):
        return "scroll_down"

    def setup(self, ctx: ToolContext):
        ctx["state"].editor.files = {}
        ctx["state"].editor.PAGE_SIZE = PAGE_SIZE

    def cleanup(self, ctx: ToolContext):
        del ctx["state"].editor

    def documentation(self, format="docstring"):
        match format:
            case "docstring":
                return self.function.__doc__
            case "manpage":
                return """
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
            case _:
                raise ValueError(f"Invalid format: {format}")

    def function(self, ctx, file_path):
        f"""
        command_name: scroll_down
        description: scroll down by one window of size {ctx["state"].editor.PAGE_SIZE} in the specified file
        signature: scroll_down [FILE_PATH]
        example: `scroll_down ./README.md`
        """

        abs_path = cwd_normalize_path(ctx, file_path)

        exists = file_exists(ctx, abs_path)
        if not exists:
            raise Exception(
                f"Could not scroll in file, file does not exist: {abs_path}"
            )

        if abs_path not in ctx["state"].editor.files:
            raise Exception(f"Could not scroll in file, file is not open: {abs_path}")

        lines = ctx["state"].editor.files[abs_path]["lines"].splitlines()

        last_page_idx = len(lines) // ctx["state"].editor.PAGE_SIZE

        old_page_number = ctx["state"].editor.files[abs_path]["page"]

        if old_page_number == last_page_idx:
            new_page_number = last_page_idx
        else:
            new_page_number = old_page_number + 1

        ctx["state"].editor.files[abs_path]["page"] = new_page_number

        return f"Scrolled down in file {abs_path} to line {ctx['state'].editor.PAGE_SIZE * new_page_number}"


class ScrollToLineTool(Tool):
    @property
    def supported_formats(self):
        return ["docstring", "manpage"]

    @property
    def name(self):
        return "scroll_to_line"

    def setup(self, ctx: ToolContext):
        ctx["state"].editor.files = {}
        ctx["state"].editor.PAGE_SIZE = PAGE_SIZE

    def cleanup(self, ctx: ToolContext):
        del ctx["state"].editor

    def documentation(self, format="docstring"):
        match format:
            case "docstring":
                return self.function.__doc__
            case "manpage":
                return """
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
            case _:
                raise ValueError(f"Invalid format: {format}")

    def function(self, ctx, file_path, line_number):
        """
        command_name: scroll_to_line
        description: scroll to the window containing the specified line in the file
        signature: scroll_to_line [FILE_PATH] [LINE_NO]
        example: `scroll_down ./README.md 20`
        """
        abs_path = cwd_normalize_path(ctx, file_path)

        exists = file_exists(ctx, abs_path)
        if not exists:
            raise Exception(
                f"Could not scroll in file, file does not exist: {abs_path}"
            )

        if abs_path not in ctx["state"].editor.files:
            raise Exception(f"Could not scroll in file, file is not open: {abs_path}")

        lines = ctx["state"].editor.files[abs_path]["lines"].splitlines()
        total_lines = len(lines)
        line_number = int(line_number)

        if line_number < 0 or line_number > total_lines:
            raise Exception(
                f"Invalid line number: {line_number}. Line number should be between 1 and {total_lines}."
            )

        window_number = (line_number) // ctx["state"].editor.PAGE_SIZE
        ctx["state"].editor.files[abs_path]["page"] = window_number

        window_start_line = window_number * ctx["state"].editor.PAGE_SIZE
        return f"Scrolled to window containing line {line_number} in file {abs_path}. Window starts at line {window_start_line}."


def save_create_file(ctx, response):
    """
    save_create_file - post func for create_file
    """

    if "Successfully created file " in response:
        files = response.split("Successfully created file ")[1].split(" ")
        # vgit
        # commit = commit_files(ctx["environment"], files, "created file(s) " + " ".join(files))
        # if commit:
        #     ctx["session"].event_log.append({
        #         "type": "GitEvent",
        #         "content" : {
        #             "type" : "commit",
        #             "commit" : commit,
        #             "files" : files,
        #         }
        #     })
        return f"Successfully saved file {files[0]} to git repository"


def save_delete_file(ctx, response):
    """
    save_delete_file - post func for delete_file
    """
    if "Successfully deleted file " in response:
        files = response.split("Successfully deleted file ")[1].split(" ")
        # vgit
        # commit = commit_files(ctx["environment"], files, "Deleted file(s) " + " ".join(files))
        # if commit:
        #     ctx["session"].event_log.append({
        #         "type": "GitEvent",
        #         "content" : {
        #             "type" : "commit",
        #             "commit" : commit,
        #             "files" : files,
        #         }
        #     })
        return f"Successfully saved file {files[0]} to git repository"
