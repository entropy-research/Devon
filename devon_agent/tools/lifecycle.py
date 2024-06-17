from devon_agent.tool import Tool, ToolContext


class SubmitTool(Tool):
    @property
    def name(self):
        return "submit"

    def supported_formats(self):
        return ["docstring", "manpage"]

    def documentation(self, format="docstring"):
        match format:
            case "docstring":
                return self.function.__doc__
            case "manpage":
                return """NAME
            submit - submit your solution once you think you have resolved the issue
        
        SYNOPSIS
            submit
        
        DESCRIPTION
            The submit command submits your solution. It is used to indicate that you have resolved the issue and are ready to submit your
            solution.
        """
            case _:
                return "Unknown format"

    def setup(self, ctx):
        pass

    def function(self, ctx: ToolContext):
        """
        command_name: submit
        description:The submit command submits your solution. It is used to indicate that you are done making or are stuck while making changes.
        signature: submit
        example: `submit`
        """
        ctx["session"].event_log.append(
            {
                "type": "Stop",
                "content": "Submit",
                "producer": "devon",
                "consumer": "user",
            }
        )
        return "Submitted"

    def cleanup(self, ctx):
        pass


class NoOpTool(Tool):
    @property
    def name(self):
        return "no_op"

    def supported_formats(self):
        return ["docstring", "manpage"]

    def documentation(self, format="docstring"):
        match format:
            case "docstring":
                return self.function.__doc__
            case "manpage":
                return """NAME
            no_op - no op
        
        SYNOPSIS
            no_op
        
        DESCRIPTION
            The no_op command does nothing. It is used to indicate that you are not ready to submit your solution.
        """
            case _:
                return "Unknown format"

    def setup(self, ctx):
        pass

    def function(self, ctx):
        """
        command_name: no_op
        description: This allows you to take a brief moment to think and synthesize what you know about the current state of the system.
        signature: no_op
        example: no_op
        """
        return "No Op"

    def cleanup(self, ctx):
        pass
