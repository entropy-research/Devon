import ast
import os
import json
import xmltodict
from typing import List, Literal, Optional, Union

from anthropic import Anthropic
from pydantic import BaseModel
from parsing import parse_code, end_json_symbol, begin_xml
from diff import UnifiedDiff, xml_to_unified_diff, apply_diff
import dotenv

from format import reformat_code
from sandbox.shell import Shell

dotenv.load_dotenv()

def get_code_from_file(shell: Shell, file_path):
    try:
        code_lines = shell.read_file(file_path).split('\n')
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

def fix2(client, original_code, input):

    model = UnifiedDiff.model_json_schema()
    data_model = str(xmltodict.unparse({"root": UnifiedDiff.model_json_schema()}, pretty=True))

    message = client.messages.create(
        max_tokens=4096,
        system="""
You're a helpful assistant who is incredibly good at understanding what the user wants, the user will provide code and what needs to change.
Your job is to help them! Given code + a set of modifications, generate a new version of the code that meets the requirements. Make sure to update all relevant references when changing the code.
Use XML format with the following pydantic basemodel to specify the code diff (the base model is the schema dump in XML, make sure to only use field names): """+ data_model +f"""
You have 4096 tokens to use for each diff, if you cannot complete the task make sure to not leave any un-closed tags without introducing syntax erros.
Follow the provided types as well.

Make sure to delete lines that you aren't using and will result in syntax errors. Pay special attention to indentation. 
Make sure you are actively considering this as you generate code.
Make sure you are considering previous lines and following lines.
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
    # print(content)
    out = xml_to_unified_diff(content)

    return out


def evaluate(client, goal, requrements, old_code, new_code):
    message = client.messages.create(
        max_tokens=1024,
        system="You're a helpful assistant who is incredibly good at understanding what the user wants, the user will provide code and what needs to change. Your job is to help them! Also think about yourself, take some time to just slow down and think through it. Using a set of change requriements, given original code and modified code, validate whether or not the new code matches the requirements",
        messages=[
            {
                "role": "user",
                "content": f"Goal:{goal}\n Requirements: {requrements} \n<OLD_CODE>{old_code}<OLD_CODE>\n<NEW_CODE>{new_code}<NEW_CODE>",
            }
        ],
        model="claude-3-opus-20240229",
    )
    return message.content[0].text


def main():
    client = Anthropic(
        api_key = os.environ.get("ANTHROPIC_API_KEY"),
    )

    repo_url = ask("Please enter your repository git url: ")
    path = ask("Please enter your file path: ")
    goal = ask("Please enter your goal: ")

    with Shell(repo_url=repo_url) as shell:
      code, code_w_line_numbers = get_code_from_file(shell, path)
      a = parse_ast(str(code))
      ast_string = serialize_ast(a)

      print("Reasoning")
      r2 = reason(client=client, input=ast_string, goal=goal)

      print("Fixing code")
      out = fix2(client=client, original_code=code_w_line_numbers, input=r2)

      print("Applying diffs")
      new = apply_diff(original_lines=code, diff=out)
      formatted_new = reformat_code(new)

      print(formatted_new)

      print("Evaluating code")
      eval = evaluate(client=client, goal=goal, requrements=r2, old_code=code, new_code=formatted_new)
      print(eval)

if __name__ == "__main__":
    main()
