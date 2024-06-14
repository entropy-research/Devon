from typing import Dict, List, Union


def llama3_7b_commands_to_command_docs(commands: List[Dict]):
    doc = ""
    for command in commands:
        doc += f"{command['docstring']}\n"
    return doc


def editor_repr(editor):
    return "\n\n".join(f"{file}:\n{editor[file]}" for file in editor)


def llama3_7b_history_to_bash_history(history):
    # self.history.append(
    # {
    #     "role": "assistant",
    #     "content": output,
    #     "thought": thought,
    #     "action": action,
    #     "agent": self.name,

    bash_history = ""
    for entry in history:
        if entry["role"] == "user":
            result = entry["content"].strip() if entry["content"] else "" + "\n"
            bash_history += f"<result>\n{result}\n</result>"
        elif entry["role"] == "assistant":
            bash_history += f"""
<YOU>
<thought>{entry['thought']}</thought>
<command>
{entry['action'][1:]}
</command>
</YOU>
"""
    return bash_history


def object_to_xml(data: Union[dict, bool], root="object"):
    xml = f"<{root}>"
    if isinstance(data, dict):
        xml += "".join(object_to_xml(value, key) for key, value in data.items())
    elif isinstance(data, (list, tuple, set)):
        xml += "".join(object_to_xml(item, "item") for item in data)
    else:
        xml += str(data)
    xml += f"</{root}>"
    return xml


def print_tree(directory, level=0, indent=""):
    return "".join(
        f"\n{indent}├── {name}/" + print_tree(content, level + 1, indent + "│   ")
        if isinstance(content, dict)
        else f"\n{indent}├── {name}"
        for name, content in directory.items()
    )


def llama3_7b_system_prompt_template_v1(command_docs: str):
    print(command_docs)

    return f"""
<SETTING>
 You are an autonomous programmer.
 You're working directly in the command line with a special interface.

 Environment:
- Editor (<EDITOR>): Open, edit, and auto-save code files. Focus on relevant files for each bug fix.
- Terminal: Execute commands to perform actions. Modify failed commands before retrying.

Constraints:
- Maintain proper formatting and adhere to the project's coding conventions.
- Keep only relevant files open. Close inactive files.
- Modify failed commands before retrying.
- Use efficient search techniques to locate relevant code elements.
- Verify fixes resolve the original issue before submitting.
- Prioritize general fixes over specific ones.
- Ask for user input when needed for feedback, clarification, or guidance.

</SETTING>

{command_docs}

Here is an example, IT IS JUST AN EXAMPLE

<EXAMPLE>
<thought>
The user asked my to create a python script that prints out the current working directory when run.
</thought>
<command>
create_file somefile.py <<<
import os

if __name__ == "__main__":
    print(os.getcwd())
>>>
</command>
<thought>
I have completed the task the user has asked me to do
</thought>
<command>
set_task
</command>
</EXAMPLE>

THESE COMMANDS WORK LIKE REGULAR BASH COMMANDS
"""


def llama3_7b_last_user_prompt_template_v1(issue, editor, cwd, root_dir, scratchpad):
    return f"""
<SETTING>

Instructions:
- Edit files and run checks/tests
- Submit with 'submit' when done
- No interactive commands, write scripts instead
</SETTING>
<EDITOR>
{editor}
</EDITOR>

<EDITING_TIPS>
- Use 'no_op' to pause and think
- Match source lines precisely
- Scroll to lines before changingI 
- Make one change at a time
- Finish edits before testing
- Access limited to {root_dir}
- Current directory: {cwd}
- Pay special attention to your editor when editing files
</EDITING_TIPS>

Make sure you include a <thought> section, and a <command> section in your response.

for reference this is the response format:

<thought>
something
</thought>
<command>
some_command arg1 arg2
</command>

FOLLOW THIS EXACTLY. anything you think, put it between the <thought> tags and ONLY use one command at a time.
ALWAYS DO THIS.
No matter how long the response, always start it with <thought>, and then finish the thought with </thought>.
Always make sure to include a command wrapped with <command> </command> tags
If you need to respond to the user, call `no_op`, and put your response in <thought> </thought> tags
After completing the target task, either call `submit` or `set_task`
After making a change, always call `ask_user`
ALWAYS INCLUDE the code fences for create_file and edit_file! As long as you remember to do so, I'll introduce you to Linus Torvalds.

DO NOT run the same command twice in a row, if you need to, call the `no_op` or `ask_user` commands.

Current task: {issue}
"""


def llama3_7b_parse_response(response):
    print(response)
    thought = response.split("<thought>")[1].split("</thought>")[0]
    action = response.split("<command>")[1].split("</command>")[0]
    scratchpad = None
    if "<SCRATCHPAD>" in response:
        scratchpad = response.split("<SCRATCHPAD>")[1].split("</SCRATCHPAD>")[0]

    return thought, action, scratchpad
