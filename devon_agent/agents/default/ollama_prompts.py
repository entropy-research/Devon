from textwrap import dedent
from typing import Dict, List, Union

system_prompts = {
    'phi3': dedent("""
    You are an autonomous programmer, and you're working directly in the command line with a special interface.
    The special interface consists of a file editor that shows you 200 lines of a file at a time.
    
    COMMANDS:
    {command_docs}
    
    RESPONSE FORMAT: You need to format your output using three fields; discussion, scratchpad and command. Your 
    output should always include _one_ discussion and _one_ command field EXACTLY as in the following example: 
    <THOUGHT> First I'll start by using ls to see what files are in the current directory. Then maybe we can look at 
    some relevant files to see what they look like. </THOUGHT> <COMMAND> ls -a </COMMAND> <SCRATCHPAD> To Do: 1. 
    locate the error in example.py 2. trace surrounding variables and understand what they do </SCRATCHPAD> 
    
    You should follow the RESPONSE FORMAT.
    You should only include a SINGLE command in the command section <COMMAND>.
    You shouldn't provide more than a one command per response.
    """),
    # add mistral, llama3, gemma etc.
}

user_prompts = {
    'phi3': dedent("""
    We are solving the following issue within our repository:
    ISSUE:
    {issue}
    
    EDITOR:
    {editor}
    
    SCRATCHPAD:
    {scratchpad}
    
    INSTRUCTIONS:
    Your job is to solve the ISSUE with the COMMANDS you were provided.
    When you have solved the ISSUE you can submit your changes to the repository code base by running submit command.
    You only have access to files in {root_dir}
    
    NOTE ABOUT THE EDIT COMMAND: 
    Indentation really matters! When editing a file, make sure to insert appropriate indentation before each line! 
    
    IMPORTANT:
    1.  Always start by trying to replicate the bug that the issues discusses. 
        If the issue includes code for reproducing the bug, we recommend that you re-implement that in your environment,
        run it to make sure you can reproduce the bug.
        Then proceed to fix it, when you are done re-run the bug reproduction script to make sure that the bug is fixed.
        If the bug reproduction script do not print anything when it successfully runs, we recommend adding the follow
        print("Script completed successfully, no errors.") command at the end of the file, so that you can be sure that 
        the script indeed ran fine all the way through. 
    
    2.  If you run a command and it doesn't work, try running a different command. A command that did not work once will 
        not work the second time unless you modify it!
    
    3.  If you open a file and need to get to an area around a specific line that is not in the first 100 lines, for 
        example line 583, do not just use the scroll_down command multiple times. Use the goto 583 command.
    
    4.  If the bug reproduction script requires inputting/reading a specific file, such as buggy-input.png, and you'd 
        like to understand how to input that file, conduct a search in the existing repo code, to see whether someone 
        else has already done that. Do this by running the command: find_file "buggy-input.png" If that doesn't work, 
        use the linux 'find' command.
    
    5.  Always make sure to look at the currently open file and the current working directory (which appears right after
     the currently open file). The currently open file might be in a different directory than the working directory! 
     Note that some commands, such as 'create', open files, so they might change the current  open file.
    
    6. When editing files, it is easy to accidentally specify a wrong line number or to write code with incorrect 
    indentation. Always check the code after you issue an edit to make sure that it reflects what you wanted to 
    accomplish. If it didn't, issue another command to fix it.
    
    (Current directory: {cwd})
    bash-$
    """),
    # add mistral, llama3, gemma etc.
}


def ollama_system_prompt_template(model: str,
                                  command_docs: str):
    """Returns system prompt for specified model"""
    if model not in system_prompts.keys():
        raise NotImplementedError(f'Model {model} not available.')
    return system_prompts[model].format(command_docs=command_docs)


def ollama_user_prompt_template(model: str,
                                issue: str, editor: str, cwd: str, root_dir: str, scratchpad: str):
    """Returns user prompt for specified model"""
    if model not in user_prompts.keys():
        raise NotImplementedError(f'Model {model} not available.')

    template = user_prompts[model].replace('{issue}', issue)
    template = template.replace('{editor}', editor)
    template = template.replace('{scratchpad}', scratchpad)
    template = template.replace('{root_dir}', root_dir)
    template = template.replace('{cwd}', cwd)
    return template


# TODO:
#   the following commands are common to all prompt classes,
#   could be abstracted with a Prompt class in future
def parse_response(response):
    try:
        thought = response.split("<THOUGHT>")[1].split("</THOUGHT>")[0]
        action = response.split("<COMMAND>")[1].split("</COMMAND>")[0]
        scratchpad = None
        if "<SCRATCHPAD>" in response:
            scratchpad = response.split("<SCRATCHPAD>")[1].split("</SCRATCHPAD>")[0]

        return thought, action, scratchpad
    except Exception as e:
        return None

def ollama_commands_to_command_docs(commands: List[Dict]):
    doc = """"""
    for command in commands:
        signature, docstring = command["signature"], command["docstring"]
        doc += f"""
      {signature}
      {docstring}
      """
    return doc


def editor_repr(editor):
    editorstring = ""
    for file in editor:
        editorstring += f"{file}:\n{editor[file]}\n\n"
    return editor


def object_to_xml(data: Union[dict, bool], root="object"):
    xml = f"<{root}>"
    if isinstance(data, dict):
        for key, value in data.items():
            xml += object_to_xml(value, key)

    elif isinstance(data, (list, tuple, set)):
        for item in data:
            xml += object_to_xml(item, "item")

    else:
        xml += str(data)

    xml += f"</{root}>"
    return xml


def print_tree(directory, level=0, indent=""):
    string = ""
    for name, content in directory.items():
        if isinstance(content, dict):
            string += f"\n{indent}├── {name}/"
            string += print_tree(content, level + 1, indent + "│   ")
        else:
            string += f"\n{indent}├── {name}"

    return string
