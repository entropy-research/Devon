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
    return "".join(
        f"\n{indent}├── {name}/" + print_tree(content, level + 1, indent + "│   ")
        if isinstance(content, dict)
        else f"\n{indent}├── {name}"
        for name, content in directory.items()
    )


def llama3_system_prompt_template_v1(command_docs: str):
    return f"""
<SETTING>
 You are an autonomous programmer, and you're working directly in the command line with a special interface.

 Environment:
- Editor (<EDITOR>): Open, edit, and auto-save code files. Focus on relevant files for each bug fix.
- Terminal: Execute commands to perform actions. Modify failed commands before retrying.
- History (<HISTORY>): Log of previous thoughts and actions. Act as if you've had these thoughts and performed these actions.

Constraints:
- Maintain proper formatting and adhere to the project's coding conventions.
- Keep only relevant files open. Close inactive files.
- Modify failed commands before retrying.
- Use efficient search techniques to locate relevant code elements.
- Verify fixes resolve the original issue before submitting.
- Prioritize general fixes over specific ones.
- Ask for user input when needed for feedback, clarification, or guidance.

</SETTING>
<COMMANDS>
{command_docs}
</COMMANDS>
<RESPONSE FORMAT>
Shell prompt format: <cwd> $
Required fields for each response:
<THOUGHT>
Your reflection, planning, and justification
</THOUGHT>
<SCRATCHPAD>
Information you want to write down
</SCRATCHPAD>
<COMMAND>
A single executable command (no interactive commands)
</COMMAND>
</RESPONSE FORMAT>
"""


def llama3_last_user_prompt_template_v1(
    issue, history, editor, cwd, root_dir, scratchpad
):
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
</TESTING_TIPS>
<PROBLEM_SOLVING>
- Identify root cause and failure case
- Fix underlying logic bug generally
- Trace error to source
- Identify flawed logic or edge case handling
- Devise robust solution for core problem
- Test fix thoroughly for potential impacts
</PROBLEM_SOLVING>
<EDITING_TIPS>
- Use 'no_op' to pause and think
- Match source lines precisely
- Scroll to lines before changing
- Make one change at a time
- Finish edits before testing
- Access limited to {root_dir}
- Current directory: {cwd}
</EDITING_TIPS>
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
    if "<thought>" in response:
        thought = response.split("<thought>")[1].split("</thought>")[0]
        action = response.split("<command>")[1].split("</command>")[0]
        scratchpad = None
        if "<scratchpad>" in response:
            scratchpad = response.split("<scratchpad>")[1].split("</scratchpad>")[0]
    else:
        thought = response.split("<THOUGHT>")[1].split("</THOUGHT>")[0]
        action = response.split("<COMMAND>")[1].split("</COMMAND>")[0]
        scratchpad = None
        if "<SCRATCHPAD>" in response:
            scratchpad = response.split("<SCRATCHPAD>")[1].split("</SCRATCHPAD>")[0]

    return thought, action, scratchpad
