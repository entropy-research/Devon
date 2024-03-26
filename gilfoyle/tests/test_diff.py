import os
from anthropic import Anthropic

from gilfoyle.agent.clients.client import ClaudeOpus
from gilfoyle.agent.tools.unified_diff.create_diff import generate_unified_diff
from gilfoyle.agent.tools.unified_diff.prompts.udiff_prompts import UnifiedDiffPrompts
from gilfoyle.agent.tools.unified_diff.utils import apply_diff_to_file

import ast

def get_file(file_path):
    try:
        with open(file=file_path) as f:
            code_lines = f.readlines()
        numbered_lines = []
        for i, line in enumerate(code_lines, start=1):
            numbered_lines.append(f"{i}: {line}")
        return os.path.abspath(file_path), "".join(code_lines), "".join(numbered_lines)
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return None
    except IOError as e:
        print(f"Error reading file: {e}")
        return None

def test_diff_creation():
    abs_path, _, numbered_lines = get_file("./state_functions.py")
    diff_code = "\n".join([abs_path, numbered_lines])

    claude = ClaudeOpus(os.getenv("ANTHROPIC_API_KEY"), system_message=UnifiedDiffPrompts.main_system + UnifiedDiffPrompts.system_reminder, max_tokens=4096)

    diff = generate_unified_diff(claude, diff_code, "modify this code so that it doesnt use the parse and serialize ast functions", [])

def test_diff_apply():
    abs_path, old_code, numbered_lines = get_file("./state_functions.py")

    diff_code = "\n".join([abs_path, numbered_lines])

    print(diff_code)
    print(old_code)

    claude = ClaudeOpus(os.getenv("ANTHROPIC_API_KEY"), system_message=UnifiedDiffPrompts.main_system + UnifiedDiffPrompts.system_reminder, max_tokens=4096)

    diff = generate_unified_diff(claude, diff_code, "remove the parse and serialize ast functions", [])

    file = diff.files[0]

    new_code = apply_diff_to_file(old_code, file)

    print(new_code)

    ast.parse(new_code)
