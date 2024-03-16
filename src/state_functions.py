import ast
import os
import json
import xmltodict
from typing import List, Literal, Optional, Union

from anthropic import Anthropic
from pydantic import BaseModel
from parsing import parse_code, end_json_symbol, begin_xml
import dotenv

from format import reformat_code

dotenv.load_dotenv()

def get_code_from_file(file_path):
    try:
        with open(file_path, 'r') as file:
            code_lines = file.readlines()
            numbered_lines = []
            for i, line in enumerate(code_lines, start=1):
                numbered_lines.append(f"{i}: {line}")
            return "".join(code_lines), "".join(numbered_lines)
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return None
    except IOError as e:
        print(f"Error reading file: {e}")
        return None

def ask(prompt):
    return input(prompt)

def parse_ast(code):
    try:
        return ast.parse(code)
    except SyntaxError as e:
        print(f"SyntaxError: {e}")
        return None

def serialize_ast(tree):
    if tree is None:
        return ""
    return ast.unparse(tree)

def reason(client, input, goal):
    message = client.messages.create(
        max_tokens=1024,
        system="You're a helpful assistant who is incredibly good at understanding what the user wants, the user will provide an AST and you need to reason about what needs to change for the code to be correct, do NOT update the code. ONLY describe the required changes",
        messages=[
            {
                "role": "user",
                "content": f"{goal}\n <AST>{input}</AST>",
            }
        ],
        model="claude-3-opus-20240229",
    )
    return message.content[0].text

class LineDiff(BaseModel):
    line_number: int
    indent_level: int
    new_code: Optional[str] = None
    action: Literal['delete', 'insert', 'modify']

class GitDiff(BaseModel):
    line_diffs: List[LineDiff]

def xml_to_git_diff(xml_data):
    # Parse the XML data into a dictionary
    data_dict = xmltodict.parse(xml_data)

    # Extract the line_diffs from the dictionary
    line_diffs_data = data_dict['root']['line_diffs']['LineDiff']

    # Create LineDiff objects from the parsed data
    line_diffs = []
    for line_diff_data in line_diffs_data:
        line_number = int(line_diff_data['line_number'])
        indent_level = line_diff_data['indent_level']
        action = line_diff_data['action']
        new_code = None
        if "new_code" in line_diff_data:
            new_code = line_diff_data['new_code']
        else:
            action = "delete"
        line_diff = LineDiff(line_number=line_number, new_code=new_code, indent_level=indent_level, action=action)
        line_diffs.append(line_diff)

    # Create a GitDiff object with the line_diffs
    git_diff = GitDiff(line_diffs=line_diffs)

    return git_diff

def fix2(client, original_code, input):

    model = GitDiff.model_json_schema()
    data_model = str(xmltodict.unparse({"root": GitDiff.model_json_schema()}, pretty=True))

    message = client.messages.create(
        max_tokens=4096,
        system="""
You're a helpful assistant who is incredibly good at understanding what the user wants, the user will provide code and what needs to change.
Your job is to help them! Given code + a set of modifications, generate a new version of the code that meets the requirements. Make sure to update all relevant references when changing the code.
Use XML format with the following pydantic basemodel to specify the code diff (the base model is the schema dump in XML, make sure to only use field names): """+ data_model +f"""
You have 4096 tokens to use for each diff, if you cannot complete the task make sure to not leave any un-closed tags without introducing syntax erros.
Make sure to delete lines that you aren't using and will result in syntax errors. Pay special attention to indentation. M
ake sure you are actively considering this as you generate code.
If you update the indentation level of some code, make sure you consider the indentation of the code that follows.
If new_code is not present, the diff is automatically turned into a delete.
Line numbers are provided for reference, BUT DO NOT OUTPUT LINE NUMBERS.
If you need to add information, add it as comments in the code itself. use the {end_json_symbol} after the XML section but before any following text.

DO NOT make syntax errors.

""",
        messages=[
            {
                "role": "user",
                "content": input + "\n" + original_code,
            },
            {
                "role": "assistant",
                "content": begin_xml,
            },
        ],
        model="claude-3-opus-20240229",
    )
    content = begin_xml + "\n" + message.content[0].text.split(end_json_symbol)[0]
    out = xml_to_git_diff(content)

    return out

def evaluate(client, goal, requrements, old_code, new_code):
    message = client.messages.create(
        max_tokens=1024,
        system="You're a helpful assistant who is incredibly good at understanding what the user wants, the user will provide code and what needs to change. Your job is to help them! Also think about yourself, take some time to just slow down and think through it. Using a set of change requriements, given original code and modified code, validate whether or not the new code matches the requirements",
        messages=[
            {
                "role": "user",
                "content": f"Goal:{goal}\n Requirements: {requrements} \n<OLD_CODE>{input}<OLD_CODE>\n<NEW_CODE>{input}<NEW_CODE>",
            }
        ],
        model="claude-3-opus-20240229",
    )
    return message.content[0].text

def apply_diffs(original_text, diff: GitDiff):
    lines = original_text.split('\n')
    
    # Create a list to store the modified lines
    modified_lines = []
    
    # Iterate over the lines and apply the differences
    i = 0
    while i < len(lines):
        line_number = i + 1
        
        print(line_number)

        # Check if the current line has a corresponding line difference
        line_diff = next((diff for diff in diff.line_diffs if diff.line_number == line_number), None)
        
        if line_diff:
            if line_diff.action == 'delete':
                # Skip the current line if the action is 'delete'
                i += 1
                continue
            elif line_diff.action == 'insert':
                # Insert the new line if the action is 'insert'
                indent = line_diff.indent_level * "    "
                modified_lines.append(indent + line_diff.new_code)
                i += 1
            elif line_diff.action == 'modify':
                # Modify the current line if the action is 'modify'
                indent = line_diff.indent_level * "    "
                modified_lines.append(indent + line_diff.new_code)
                i += 1
        else:
            # Keep the original line if there is no corresponding line difference
            modified_lines.append(lines[i])
            i += 1
    
    # Join the modified lines back into a single string
    modified_text = '\n'.join(modified_lines)
    
    return modified_text

def ast_to_dict(node):
    if isinstance(node, ast.AST):
        # Convert the node fields to a dictionary
        node_dict = {}
        for key, value in ast.iter_fields(node):
            node_dict[key] = ast_to_dict(value)
        
        # Add the node type as a special key
        node_dict['_type'] = type(node).__name__
        
        return node_dict
    elif isinstance(node, list):
        # Convert each item in the list recursively
        return [ast_to_dict(item) for item in node]
    else:
        # Return the value as is for primitive types
        return node

def main():
    client = Anthropic(
        api_key = os.environ.get("ANTHROPIC_API_KEY"),
    )

    path = ask("Please enter your file path: ")
    goal = ask("Please enter your goal: ")
    code, code_w_line_numbers = get_code_from_file(path)
    a = parse_ast(str(code))
    ast_string = serialize_ast(a)

    print("Reasoning")
    r2 = reason(client=client, input=ast_string, goal=goal)

    print("Fixing code")
    out = fix2(client=client, original_code=code_w_line_numbers, input=r2)

    print("Applying diffs")
    new = apply_diffs(original_text=code, diff=out)
    formatted_new = reformat_code(new)

    print(formatted_new)

    # print("Evaluating code")
    # eval = evaluate(client=client, goal=goal, requrements=r, old_code=code, new_code=new)
    # print(eval)

if __name__ == "__main__":
    main()
