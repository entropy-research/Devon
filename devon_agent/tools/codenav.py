import os

from devon_agent.tool import Tool, ToolContext
import code_nav_devon
import tempfile


class CodeSearch(Tool):
    def __init__(self):
        self.temp_file_path = None

    @property
    def name(self):
        return "code_search"

    @property
    def supported_formats(self):
        return ["docstring", "manpage"]

    def setup(self, ctx):
        self.base_path = ctx["session"].base_path

        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_dir_path = self.temp_dir.name

    def cleanup(self, ctx):
        # Clean up the temporary directory
        if self.temp_dir:
            self.temp_dir.cleanup()
            self.temp_dir = None

    def documentation(self, format="docstring"):
        match format:
            case "docstring":
                return self.function.__doc__
            case "manpage":
                return """
    CODE_SEARCH(1)                   General Commands Manual                  CODE_SEARCH(1)

    NAME
            code_search - case-sensitive search for text within all the project files

    SYNOPSIS
            code_search TEXT

    DESCRIPTION
            The code_search command does case-sensitive search for the specified text within all the project files.

    OPTIONS
            TEXT
                    The text to search within the project files.

    RETURN VALUE
.

    EXAMPLES
            To search for the text "def my_function":

                    code_search "def my_function"
    """
            case _:
                raise ValueError(f"Invalid format: {format}")

    def function(self, ctx: ToolContext, text: str) -> str:
        """
        command_name: code_search
        description: Searches for the specified text within the code base.
        signature: code_search [TEXT]
        example: `code_search "def my_function"`
        """
        try:
            # Run the text_search function
            output = code_nav_devon.text_search(self.base_path, self.temp_dir_path, text, True)
            return output
        except Exception as e:
            ctx["session"].logger.error(f"Search failed for text: {text}. Error: {str(e)}")
            return f"Search failed for text: {text}. Error: {str(e)}"
        


class CodeGoTo(Tool):
    def __init__(self):
        self.temp_file_path = None

    @property
    def name(self):
        return "code_goto"

    @property
    def supported_formats(self):
        return ["docstring", "manpage"]

    def setup(self, ctx):
        self.base_path = ctx["session"].base_path

        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_dir_path = self.temp_dir.name

    def cleanup(self, ctx):
        # Clean up the temporary directory
        if self.temp_dir:
            self.temp_dir.cleanup()
            self.temp_dir = None


    def documentation(self, format="docstring"):
        match format:
            case "docstring":
                return self.function.__doc__
            case "manpage":
                return """
    CODE_GOTO(1)                   General Commands Manual                  CODE_GOTO(1)

    NAME
            code_goto - find symbol's definition or all references and get a list of all the positions within the codebase

    SYNOPSIS
            code_goto FILE_PATH LINE_NUMBER SYMBOL_STRING

    DESCRIPTION
            The code_goto command navigates to the specified symbol's definition or reference within the project files by using ast tree
            and returns a lists all positions of the symbol in the rest of the codebase. To find reference, use it on a definition. To find definition, use it on reference.
            This is not a simple sting matching

    OPTIONS
            FILE_PATH
                    The path of the file containing the symbol.

            LINE_NUMBER
                    The line number where the symbol is located.

            SYMBOL_STRING
                    The symbol string to navigate to and search for within the project files.

    RETURN VALUE
            The code_goto command returns a string of all positions of the symbol in the rest of the codebase.

    EXAMPLES
            To navigate to a symbol "my_function" in file "example.py" at line 42 and find its positions:

                    code_goto "example.py" 42 "my_function"
    """
            case _:
                raise ValueError(f"Invalid format: {format}")

    def function(self, ctx: ToolContext, file_path: str, line_number: int, symbol_string: str) -> str:
        """
        command_name: code_goto
        description: Navigates to the specified symbol's definition or reference within the code base
                    and lists all positions of the symbol in the rest of the codebase.
        signature: code_goto [FILE_PATH] [LINE_NUMBER] [SYMBOL_STRING]
        example: `code_goto "example.py" 42 "my_function"`
        """
        try:


            # to tell the agent whether fuzzy search was enabled
            fuzzy_search_text = ""

            line_number = int(line_number)
            abs_file_path = os.path.abspath(os.path.normpath(file_path))
            with open(abs_file_path, 'r') as file:
                lines = file.readlines()

            if int(line_number) - 1 >= len(lines):
                raise ValueError(f"Line number {line_number} is out of range in file {file_path}")
            
            base_path = ctx["session"].base_path

            # Check the specified line for the symbol
            line_content = lines[line_number - 1]
            start_index = line_content.find(symbol_string)
            if start_index != -1:
                end_index = start_index + len(symbol_string)
            else:
                # Perform fuzzy search within ±2 lines if symbol is not found in the specified line
                start_line = max(0, line_number - 3)  # 1 lines above
                end_line = min(len(lines), line_number + 2)  # 2 lines below

                old_line_number = line_number

                # Initialize variables for line content and symbol indices
                line_content = None
                start_index = -1
                end_index = -1

                # Search for the symbol in the lines within ±2 lines
                for i in range(start_line, end_line):
                    line_content = lines[i]
                    start_index = line_content.find(symbol_string)
                    if start_index != -1:
                        line_number = i + 1  # Adjust line number to the found line
                        end_index = start_index + len(symbol_string)
                        break

                fuzzy_search_text = f"{symbol_string} is not found in line number {old_line_number} but found in line number {line_number} \n\n"

                # If symbol is not found, raise an error
                if start_index == -1:
                    raise ValueError(f"Symbol '{symbol_string}' not found in line {line_number} or within ±2 lines of it in file {file_path}")

            # Run the go_to function
            output = code_nav_devon.go_to(base_path, self.temp_dir_path, abs_file_path, line_number, start_index, end_index)
            return fuzzy_search_text + output
        except Exception as e:
            ctx["session"].logger.error(f"Navigation failed for symbol: {symbol_string} at line: {line_number} in file: {file_path}. Error: {str(e)}")
            return f"Navigation failed for symbol: {symbol_string} at line: {line_number} in file: {file_path}. Error: {str(e)}"



# Create a temporary directory
# temp_dir = tempfile.TemporaryDirectory()
# temp_file_dir = temp_dir.name
# print(f"Temporary directory created at: {temp_dir}")

# try:
#     # Use the temporary directory with the package function
#     result = code_nav_devon.go_to("/Users/arnav/Desktop/devon/Devon", temp_file_dir, "/Users/arnav/Desktop/devon/Devon/devon_agent/session.py", 34, 6, 22)
#     print(result)
# except Exception as e:
#     print(f"Error: {e}")
# finally:
#     # Manually delete the temporary directory and its contents
#     temp_dir.cleanup()
#     temp_dir = None
    
