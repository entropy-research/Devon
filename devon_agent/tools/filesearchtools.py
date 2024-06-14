import json
import os

from devon_agent.tool import Tool, ToolContext
from devon_agent.tools.utils import (_list_files_recursive, cwd_normalize_path,
                                     get_cwd, make_abs_path)


class SearchDirTool(Tool):
    @property
    def name(self):
        return "search_dir"

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
            case _:
                raise ValueError(f"Invalid format: {format}")

    def function(self, ctx: ToolContext, search_term: str, dir: str = "./"):
        """
        command_name: search_dir
        description: Searches for the term in all files in the specified directory.
        signature: search_dir [SEARCH_TERM] [SEARCH_DIR]
        example: `search_dir "hello" ./docs`
        """
        if search_term.startswith("--"):
            search_term = '"' + search_term + '"'

        abs_path = cwd_normalize_path(ctx, dir)

        command = f"find {abs_path} -type f ! -path '*/.*' -exec grep -nIH '{search_term}' {{}} + | cut -d: -f1 | sort | uniq -c"
        result = ctx["environment"].execute(command)

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


class FindFileTool(Tool):
    @property
    def name(self):
        return "find_file"

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
                return """FIND_FILE(1)        General Commands Manual        FIND_FILE(1)

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

    FIND_FILE(1)         April 2024         FIND_FILE(1)"""
            case _:
                raise ValueError(f"Invalid format: {format}")

    def function(self, ctx: ToolContext, file_path: str):
        """
        command_name: find_file
        description: Finds a file by its name within the file system.
        signature: find_file [FILE_NAME]
        example: `find_file README.md`
        """
        filename = os.path.basename(file_path)
        base_path = get_cwd(ctx)
        command = f"find {base_path} -type f -name '{filename}'"
        result = ctx["environment"].execute(command)
        if result[0] is None:
            return "No such file. Make sure the file exists"
        return result[0]


class ListDirsRecursiveTool(Tool):
    @property
    def name(self):
        return "list_dirs_recursive"

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
                return """LIST_DIRS_RECURSIVE(1)        General Commands Manual        LIST_DIRS_RECURSIVE(1)

    NAME
        list_dirs_recursive - lists out the directory tree starting at FILE_PATH

    SYNOPSIS
        list_dirs_recursive FILE_PATH

    DESCRIPTION
        The list_dirs_recursive command lists out the directory tree starting from FILE_PATH

    OPTIONS
        FILE_PATH
            The path of the file to search for.

    RETURN VALUE
        It returns the directory tree in JSON format.

    EXAMPLES
        To list out the tree from cwd within the file system:

            list_recursive_dirs "."

    SEE ALSO
        ls(1), locate(1)

    LIST_DIRS_RECURSIVE(1)         April 2024         LIST_DIRS_RECURSIVE(1)"""
            case _:
                raise ValueError(f"Invalid format: {format}")

    def function(self, ctx: ToolContext, file_path: str):
        """
        command_name: list_recursive_dirs
        description: Returns the entire directory tree in its entirety from the file system.
        signature: list_recursive_dirs [DIR_PATH]
        example: `list_recursive_dirs .`
        """

        abs_path = make_abs_path(ctx, file_path)

        return json.dumps(_list_files_recursive(ctx, [abs_path])["directory_tree"])


class GetCwdTool(Tool):
    @property
    def name(self):
        return "get_cwd"

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
            get_cwd - get the current working directory

    SYNOPSIS
            get_cwd

    DESCRIPTION
            The get_cwd command returns the current working directory.

    RETURN VALUE
            The get_cwd command returns the current working directory as a string.

    EXAMPLES
            To get the current working directory:

                    get_cwd
                    """
            case _:
                raise ValueError(f"Invalid format: {format}")

    def function(self, ctx: ToolContext):
        """
        get_cwd
        Returns the current working directory.
        """

        return get_cwd(ctx)
