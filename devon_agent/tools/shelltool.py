import os
from typing import List

from devon_agent.tool import Tool, ToolContext
from devon_agent.tools.utils import (_capture_window, cwd_normalize_path,
                                     file_exists, make_abs_path)


class ShellTool(Tool):
    @property
    def name(self):
        return "shell_tool"

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
                return """NA/NOT USED"""
            case _:
                raise ValueError(f"Invalid format: {format}")

    def function(self, ctx: ToolContext, fn_name, args: List[str]) -> str:
        """
        Default tool for shell environments to execute in the environment
        """
        output, rc = ctx["environment"].communicate(fn_name + " " + " ".join(args))
        if rc != 0:
            raise Exception(output)
        return output
