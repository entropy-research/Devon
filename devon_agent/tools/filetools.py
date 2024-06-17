import os

from devon_agent.tool import Tool, ToolContext
from devon_agent.tools.utils import _capture_window, cwd_normalize_path, make_abs_path, file_exists
from devon_agent.retrieval.file_tree.file_tree_tool import FileTreeTool


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
        description: Deletes a file at the specified file path.
        signature: delete_file [FILE_PATH]
        example: `delete_file ./README.md`
        """

        try:
            # Check if file already exists to avoid overwriting
            abs_path = make_abs_path(ctx, file_path)

            exists = file_exists(ctx, abs_path)
            if not exists:
                raise Exception(
                    f"Could not delete file, file does not exist: {abs_path}"
                )

            # Creating the file with initial content
            ctx["environment"].execute(f"rm -f {abs_path}")

            return f"Successfully deleted file {abs_path}"

        except Exception as e:
            ctx["session"].logger.error(
                f"Failed to delete file: {abs_path}. Error: {str(e)}"
            )
            return f"Failed to delete file: {abs_path}. Error: {str(e)}"


class CreateFileTool(Tool):
    @property
    def name(self):
        return "create_file"

    @property
    def supported_formats(self):
        return ["docstring", "manpage"]

    def setup(self, ctx):
        pass

    def cleanup(self, ctx):
        pass

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

                    

    SEE ALSO
            touch(1), echo(1)

    CREATE_FILE(1)                        April 2024                         CREATE_FILE(1)
    """
            case _:
                raise ValueError(f"Invalid format: {format}")

    def function(self, ctx: ToolContext, file_path: str, content: str = "") -> str:
        """
                command_name: create_file
                description: Creates a new file at the specified file path with optional initial content.
                signature: create_file [FILE_PATH] <<<CONTENT>>>
                example: `create_file "/path/to/script.py" <<<
        import os
        import asyncio
        >>>`
        """
        try:
            # Check if file already exists to avoid overwriting
            abs_path = make_abs_path(ctx, file_path)

            exists = file_exists(ctx, abs_path)
            if exists:
                raise Exception(
                    f"Could not create file, file already exists: {abs_path}"
                )

            create_command = (
                f"mkdir -p $(dirname '{abs_path}') && cat << 'DELIM' > '{abs_path}' \n"
                + content
                + "\nDELIM"
            )
            ctx["environment"].execute(create_command)

            exists = file_exists(ctx, abs_path)
            if not exists:
                raise Exception(
                    f"Could not create file, file does not exist: {abs_path}"
                )

            return f"Successfully created file {abs_path}"
        except Exception as e:
            ctx["logger"].error(f"Failed to create file: {file_path}. Error: {str(e)}")
            # traceback.print_exc()
            # raise e
            return f"Failed to create file: {file_path}. Error: {str(e)}"


class ListFilesTool(Tool):
    @property
    def name(self):
        return "list_files"

    @property
    def supported_formats(self):
        return ["docstring", "manpage"]

    def setup(self, ctx):
        pass

    def cleanup(self, ctx):
        pass

    def documentation(self, format="docstring"):
        match format:
            case "docstring":
                return self.function.__doc__
            case "manpage":
                return """NAME
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
            case _:
                raise ValueError(f"Invalid format: {format}")

    def function(self, ctx: ToolContext, folder_path: str = ".") -> list:
        """
        command_name: list_files
        description: Lists all files in the specified folder.
        signature: list_files [FOLDER_PATH]
        example: `list_files .`
        """
        abs_path = cwd_normalize_path(ctx, folder_path)

        command = f"grep -rl '' {abs_path}"
        result = ctx["environment"].execute(command)

        return result


class ReadFileTool(Tool):
    @property
    def name(self):
        return "read_file"

    @property
    def supported_formats(self):
        return ["docstring", "manpage"]

    def setup(self, ctx):
        pass

    def cleanup(self, ctx):
        pass

    def documentation(self, format="docstring"):
        match format:
            case "docstring":
                return self.function.__doc__
            case "manpage":
                return """
    READ_FILE(1)                   General Commands Manual                  READ_FILE(1)

    NAME
            read_file - read a file at the target path

    SYNOPSIS
            read_file FILE_PATH

    DESCRIPTION
            The read_file command reads the contents of a file at the specified FILE_PATH   
    
    OPTIONS
            FILE_PATH
                    The path of the file to read.

    RETURN VALUE
            The read_file command returns the contents of the file at the specified FILE_PATH.

    EXAMPLES
            To read the contents of a file at "/path/to/file.txt":

                    read_file "/path/to/file.txt" 
    """
            case _:
                raise ValueError(f"Invalid format: {format}")

    def function(self, ctx: ToolContext, file_path: str) -> str:
        """
        command_name: read_file
        description: Reads the contents of a file at the specified file path.
        signature: read_file [FILE_PATH]
        example: `read_file ./README.md`
        """
        try:
            # Check if file exists to avoid reading from non-existent files
            result, _ = ctx["environment"].communicate(f"cat '{file_path}'")
            return result
        except Exception as e:
            ctx["logger"].error(f"Failed to read file: {file_path}. Error: {str(e)}")
            return f"Failed to read file: {file_path}. Error: {str(e)}"


class SearchFileTool(Tool):
    @property
    def name(self):
        return "search_file"

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
    SEARCH_FILE(1)                   General Commands Manual                  SEARCH_FILE(1)

    NAME
            search_file - search for a file by name within the file system

    SYNOPSIS
            search_file [SEARCH_TERM] [FILE]

    DESCRIPTION
            The search_file command searches for SEARCH_TERM in the specified FILE. If FILE is
            not provided, it searches in the current open file.

    OPTIONS
            SEARCH_TERM
                    The term to search for in the file.

            FILE  The file to search in. If not provided, the command searches in the
                    current open file.

    RETURN VALUE
            The search_file command returns a summary of the search results as a string.

    EXAMPLES
            To search for the term "hello" in the current open file:

                    search_file "hello"

            To search for the term "world" in the file "/path/to/file.txt":

                    search_file "world" "/path/to/file.txt"
    """
            case _:
                raise ValueError(f"Invalid format: {format}")

    def function(self, ctx: ToolContext, search_term: str, file_path: str):
        """
        command_name: search_file
        description: Searches for the term in the specified file.
        signature: search_file [SEARCH_TERM] [DIR_PATH]
        example: `search_file "Hello" .`
        """
        abs_path = cwd_normalize_path(ctx, file_path)

        try:
            # Check if file exists to avoid reading from non-existent files
            content, _ = ctx["environment"].communicate(f"cat '{file_path}'")
        except Exception as e:
            ctx["session"].logger.error(
                f"Failed to read file: {file_path}. Error: {str(e)}"
            )
            return f"Failed to read file: {file_path}. Error: {str(e)}"
        matches = []
        tolerance = 10
        content_lines = content.splitlines()
        for i, line in enumerate(content_lines):
            if search_term in line:
                matches.append(_capture_window(content_lines, i, tolerance))

        if not matches:
            return f'No matches found for "{search_term}" in {abs_path}'

        num_matches = len(matches)

        if num_matches > 10:
            return f'More than {10} lines matched for "{search_term}" in {abs_path}. Please narrow your search.'

        matches = "\n".join(matches)
        result = f'Found {num_matches} matches for "{search_term}" in {abs_path}:\n {matches}'
        return result



class FileTreeDisplay(Tool):

    @property
    def name(self):
        return "file_tree_display"
    
    @property
    def supported_formats(self):
        return ["docstring", "manpage"]
    
    def setup(self, ctx):
        root_dir = ctx["session"].base_path
        self.fileTreeTool = FileTreeTool(root_dir=root_dir)
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
    FILE_TREE_DISPLAY(1)                   General Commands Manual                  FILE_TREE_DISPLAY(1)

    NAME
            file_tree_display - display the file tree structure in YAML format

    SYNOPSIS
            file_tree_display [DIR_PATH]

    DESCRIPTION
            The file_tree_display command generates a YAML representation of the file tree 
            structure starting from the specified directory. If DIR_PATH is not provided, 
            it generates the file tree for the entire project.

    OPTIONS
            DIR_PATH
                    The path of the directory to start generating the file tree from. If not 
                    provided, the command starts from the project root directory.

    RETURN VALUE
            The file_tree_display command returns the YAML representation of the file tree 
            structure as a string.

    EXAMPLES
            To display the file tree of the current project:

                    file_tree_display

            To display the file tree starting from a specific directory:

                    file_tree_display "/path/to/directory"
    """
            case _:
                raise ValueError(f"Invalid format: {format}")

    def function(self, ctx: ToolContext, dir_path: str = None) -> str:
        """
        command_name: file_tree_display
        description: Displays the file tree structure in YAML format starting from the specified directory.
                     If no directory is specified, displays the file tree for the entire project.
        signature: file_tree_display [DIR_PATH]
        example: `file_tree_display "/path/to/directory"`
        """
        try:
            if dir_path is None:
                dir_path = self.fileTreeTool.root_dir

            result_list, result_tree = self.fileTreeTool.get_large_tree(dir_path, 500, 20)
            return result_tree
        except Exception as e:
            ctx["session"].logger.error(f"Failed to display file tree for directory: {dir_path}. Error: {str(e)}")
            return f"Failed to display file tree for directory: {dir_path}. Error: {str(e)}"