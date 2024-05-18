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

    """),
    # add mistral, llama3, gemma etc.
}


# command docs is generated in agent.py and has the following format
# command["signature"]
# command["docstring"]
# Example:
# NAME
#     search_dir - search for a term in all files in a directory
#
#     SYNOPSIS
#             search_dir [SEARCH_TERM] [DIR]
#
#     DESCRIPTION
#             The search_dir command searches for SEARCH_TERM in all files in the specified DIR.
#             If DIR is not provided, it searches in the current directory.
#             Does not search for files but for the content of the files.
#
#     OPTIONS
#             ...
#     RETURN VALUE
#             ...
#     EXAMPLES
#             ...


def ollama_system_prompt_template(model: str,
                                  command_docs: str):
    """"""
    return system_prompts[model].format(command_docs=command_docs)


def ollama_user_prompt_template(model: str,
                                issue: str, editor: str, cwd: str, root_dir: str, scratchpad: str):
    """"""
    return user_prompts[model]


# TODO:
#   the following commands are common to all prompt classes,
#   could be abstracted with a Prompt class in future
def parse_response(response):
    thought = response.split("<THOUGHT>")[1].split("</THOUGHT>")[0]
    action = response.split("<COMMAND>")[1].split("</COMMAND>")[0]
    scratchpad = None
    if "<SCRATCHPAD>" in response:
        scratchpad = response.split("<SCRATCHPAD>")[1].split("</SCRATCHPAD>")[0]

    return thought, action, scratchpad


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


# TODO: make test
if __name__ == "__main__":
    from devon_agent.agents.default.agent import TaskAgent
    from devon_agent.session import SessionArguments, Session
    from devon_agent.agents.model import ModelArguments, OllamaModel

    # --- Setup
    # the agent is created only to have the command_docs, so gpt4-o was arbitrary 
    agent = TaskAgent(model='gpt4-o', name='test_agent') 

    se_args = SessionArguments(
        name='test_session',
        path='../../../../',
        user_input='Hello World'
    )
    session = Session(se_args, agent)

    command_docs = list(session.generate_command_docs().values())
    command_docs = (
            "Custom Commands Documentation:\n"
            + ollama_commands_to_command_docs(command_docs)
            + "\n"
    )
    sys_prompt = ollama_system_prompt_template('phi3', command_docs)
    # print(sys_prompt)

    # --- Model
    model_args = ModelArguments(
        model_name='phi3',
        temperature=0.1
    )
    model = OllamaModel(model_args)

    # --- TEST
    # response = model.query(
    #     system_message=sys_prompt,
    #     messages=[
    #         {'role': 'user', 'message': 'search the file test.txt'}
    #     ]
    # )
    # print(response)
