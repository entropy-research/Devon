import ast
import os
from typing import Optional, Any

from pydantic import BaseModel, Field

from sandbox.shell import Shell

class CodeFile(BaseModel):
    filepath: str
    code: str
    code_with_lines: str
    ast: Optional[Any] = Field(default=None, description="An abstract syntax tree represented as a generic Python object.")
    raw: Optional[str] = None

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

def glob_repo_code(shell: Shell):
    files = {}
    def extract_code_recursive(shell: Shell, path: str):
        dirs, file_paths = shell.list_directory_contents(path)
        for file_path in file_paths:
            if not file_path.startswith('.') and file_path.endswith(".py"):  # Avoid hidden directories and files
                full_path = os.path.join(path, file_path)
                code, code_with_lines = get_code_from_file(shell, full_path)
                if code is not None and code != "":
                    parsed_ast = parse_ast(code)
                    files[full_path] = CodeFile(filepath=full_path, code=code, code_with_lines=code_with_lines, ast=parsed_ast, raw=code)
        for directory in dirs:
            if not directory.startswith('.'):  # Avoid hidden directories
                extract_code_recursive(shell, os.path.join(path, directory))

    extract_code_recursive(shell, ".")
    return files

def get_code_from_file(shell: Shell, file_path):
    try:
        code_lines = shell.read_file(file_path).split('\n')
        numbered_lines = []
        for i, line in enumerate(code_lines, start=1):
            numbered_lines.append(f"{i}: {line}")
        return "\n".join(code_lines), "\n".join(numbered_lines)
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return None
    except IOError as e:
        print(f"Error reading file: {e}")
        return None