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
                return """NAME
            submit - submit your solution once you think you have resolved the issue
        
        SYNOPSIS
            submit
        
        DESCRIPTION
            The submit command submits your solution. It is used to indicate that you have resolved the issue and are ready to submit your
            solution.
        """
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
    
    def function(self, ctx : ToolContext):
        ctx["session"].event_log.append({
            "type": "Stop",
            "content": "Submit",
            "producer": "devon",
            "consumer": "user",
        })

        command = """submit() {
    cd $ROOT

    # Check if the patch file exists and is non-empty
    if [ -s "/root/test.patch" ]; then
        # Apply the patch in reverse
        git apply -R < "/root/test.patch"
    fi

    echo "\nbuild" >> .gitignore
    git add -A
    git diff --cached > model.patch
    echo "<<SUBMISSION||"
    cat model.patch
    echo "||SUBMISSION>>"
}
submit"""

        output, rc =  ctx["environment"].execute(command)

        return output

    def cleanup(self, ctx):
        pass

