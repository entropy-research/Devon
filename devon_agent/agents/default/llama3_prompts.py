from typing import Dict, List, Union

def llama3_commands_to_command_docs(commands: List[Dict]):
    doc = ""
    for command in commands:
        doc += f"{command['signature']}\n{command['docstring']}\n"
    return doc

def editor_repr(editor):
    return "\n\n".join(f"{file}:\n{editor[file]}" for file in editor)

def llama3_history_to_bash_history(history):
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
            bash_history += f"<RESULT>\n{result}\n</RESULT>"
        elif entry["role"] == "assistant":
            bash_history += f"""
<YOU>
<THOUGHT>{entry['thought']}</THOUGHT>
<COMMAND>
{entry['action'][1:]}
</COMMAND>
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
    return "".join(f"\n{indent}├── {name}/" + print_tree(content, level + 1, indent + "│   ") if isinstance(content, dict) else f"\n{indent}├── {name}" for name, content in directory.items())

def llama3_system_prompt_template_v3(command_docs: str):
    return f"""
<SETTING>
You are an AI programmer fixing bugs in a project.

Environment:
- Editor (<EDITOR>): Open, edit, and auto-save code files. Focus on relevant files.
- Terminal: Execute commands. Modify failed commands before retrying.
- History (<HISTORY>): Previous thoughts and actions. Roleplay as if you had these.

Key constraints:
- EDITING: Maintain formatting and conventions.
- FILE MANAGEMENT: Keep only relevant files open.
- COMMANDS: Modify failed commands before retrying.
- SEARCH: Use efficient search techniques.
- SUBMISSION: Verify fix resolves original issue.
- CODEBASE: Choose general fixes over specific ones.
- ASK_USER: Ask for input, feedback, or guidance.

You are on a branch, don't worry about changing core parts.
</SETTING>
<EDITOR>
Currently open files will be listed here. Close unused files.
</EDITOR>
<COMMANDS>
{command_docs}
</COMMANDS>
<RESPONSE FORMAT>
Shell prompt: <cwd> $
Required fields:
<THOUGHT>Your reflection and planning</THOUGHT>
<SCRATCHPAD>Information to write down</SCRATCHPAD>
<COMMAND>A single executable command, no interactive commands</COMMAND>
</RESPONSE FORMAT>
"""

def llama3_last_user_prompt_template_v3(issue, history, editor, cwd, root_dir, scratchpad):
    return f"""
<SETTING>
Objective: {issue}

Instructions:
- Edit files and run checks/tests
- Submit with 'submit' when done
- No interactive commands, write scripts instead
</SETTING>
<CONSTRAINTS>
- One command at a time
- Wait for feedback after each command
- Locate classes/functions over files
- Use 'no_op' for thinking time
- Issue title/first line describes it succinctly
</CONSTRAINTS>
<TESTING_TIPS>
- Write unit tests to verify fixes
- Run tests frequently to catch regressions 
- Test edge cases and error handling
- Manually verify UI and integration tests
- Ensure tests pass before submitting
<HISTORY>
{history}
</HISTORY>
<EDITOR>
{editor}
</EDITOR>
<SCRATCHPAD>
{scratchpad}
</SCRATCHPAD>
<DIRECTORY>
{root_dir}
</DIRECTORY>
<cwd>{cwd}</cwd> $
"""

def llama3_parse_response(response):
    thought = response.split("<THOUGHT>")[1].split("</THOUGHT>")[0]
    action = response.split("<COMMAND>")[1].split("</COMMAND>")[0]
    scratchpad = None
    if "<SCRATCHPAD>" in response:
        scratchpad = response.split("<SCRATCHPAD>")[1].split("</SCRATCHPAD>")[0]

    return thought, action, scratchpad
