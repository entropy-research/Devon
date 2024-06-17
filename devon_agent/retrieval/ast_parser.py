import ast


def parse_python_file(file_path):
    """
    Parses a Python file and returns its Abstract Syntax Tree (AST).
    Args:
        file_path (str): The path to the Python file.
    Returns:
        ast.AST: The AST representation of the Python file.
    """
    try:
        with open(file_path, "r") as file:
            source_code = file.read()

        return ast.parse(source_code)
    except SyntaxError:
        print(f"SyntaxError: {file_path}")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None
