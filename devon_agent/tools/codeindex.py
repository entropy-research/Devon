import os
from dataclasses import dataclass

from devon_agent.retrieval.code_index import CodeIndex
from devon_agent.tool import Tool


def setup_code_index(ctx, **kwargs):
    if ctx["state"].code_index:
        return ctx["state"].code_index
    else:
        if "cache_path" in kwargs and os.path.exists(kwargs["cache_path"]):
            return CodeIndex.load_from_json(kwargs["cache_path"])
        else:
            codebase_path = None
            if "codebase_path" in kwargs:
                codebase_path = kwargs["codebase_path"]
            else:
                codebase_path = ctx["session"].base_path
            if codebase_path is None:
                raise ValueError("Codebase path is required")

            code_index = CodeIndex(codebase_path)
            code_index.initialize()
            if "cache_path" in kwargs:
                code_index.save_as_json(kwargs["cache_path"])
            return code_index


def cleanup_code_index(ctx, code_index, **kwargs):
    if "cache_path" in kwargs:
        if not os.path.exists(kwargs["cache_path"]):
            code_index.save_as_json(kwargs["cache_path"])


class FindFunctionTool(Tool):
    @property
    def name(self):
        return "create_file"

    def setup(self, ctx, **kwargs):
        self.code_index = setup_code_index(ctx, **kwargs)

    def cleanup(self, ctx):
        cleanup_code_index(ctx, self.code_index, **self.kwargs)

    def supported_formats(self):
        return ["docstring", "manpage"]

    def documentation(self, format="docstring"):
        match format:
            case "docstring":
                return self.function.__doc__
            case "manpage":
                return """NAME 
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
            case _:
                raise ValueError(f"Unsupported format: {format}")

    def function(self, ctx, function_name: str, **kwargs):
        """
        find_function [function_name] - Find the location of a function in the codebase.
        """
        return self.code_index.function_table.get_function_with_location(function_name)


class FindClassTool(Tool):
    @property
    def name(self):
        return "find_class"

    def setup(self, ctx, **kwargs):
        self.code_index = setup_code_index(ctx, **kwargs)

    def cleanup(self, ctx):
        cleanup_code_index(ctx, self.code_index, **self.kwargs)

    def supported_formats(self):
        return ["docstring", "manpage"]

    def documentation(self, format="docstring"):
        match format:
            case "docstring":
                return self.function.__doc__
            case "manpage":
                return """NAME
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
            case _:
                raise ValueError(f"Unsupported format: {format}")

    def function(self, ctx, class_name: str, **kwargs):
        """
        find_class [class_name] - Find the location of a class in the codebase.
        """
        return self.code_index.class_table.get_class_with_location(class_name)
