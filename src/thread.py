import os
from sandbox.shell import Shell
from state_functions import get_code_from_file, parse_ast, serialize_ast, reason, fix2, apply_diff, reformat_code, evaluate
from anthropic import Anthropic

class Thread:
    def __init__(self, repo_url: str, task: str, file_path: str):
        self.repo_url = repo_url
        self.task = task
        self.file_path = file_path
        self.client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    def run(self):
        with Shell(repo_url=self.repo_url) as shell:
            code, code_w_line_numbers = get_code_from_file(shell, self.file_path)
            a = parse_ast(str(code))
            ast_string = serialize_ast(a)

            print("Reasoning")
            r2 = reason(client=self.client, input=ast_string, goal=self.task)

            print("Fixing code")
            out = fix2(client=self.client, original_code=code_w_line_numbers, input=r2)

            print("Applying diffs")
            new = apply_diff(original_lines=code, diff=out)
            formatted_new = reformat_code(new)

            print(formatted_new)

            print("Evaluating code")
            eval = evaluate(client=self.client, goal=self.task, requrements=r2, old_code=code, new_code=formatted_new)
            print(eval)

