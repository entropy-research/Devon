from devon_agent.tool import Tool, ToolContext


class AskUserTool(Tool):

    @property
    def name(self):
        return "AskUserTool"
    
    @property
    def supported_formats(self):
        return ["docstring", "manpage"]

    def setup(self, context: ToolContext):
        pass

    def cleanup(self, context: ToolContext):
        pass

    def documentation(self, format = "docstring"): 
        
        match format:
            case "docstring":
                return """
                Asks the user for their input
                """
            case "manpage":
                return """
                NAME
                    ask_user - ask the user for their input

                SYNOPSIS
                    ask_user

                DESCRIPTION
                    The ask_user command asks the user for their input

                RETURN VALUE
                    The ask_user command returns a string indicating the user's input.

                EXAMPLES
                    To ask the user for their input, run the following command:

                        ask_user
                """
            case _:
                raise ValueError(f"Invalid format: {format}")

    def function(self, context : ToolContext, question: str, **kwargs):
        """
        Excutes the tool and returns the response.
        """
        return context["environment"].execute(input=question)
