import os
from sandbox.shell import Shell
from state_functions import glob_repo_code, parse_ast, serialize_ast, reason, fix2, apply_diff, reformat_code, evaluate
from anthropic import Anthropic
import json

class Thread:
    def __init__(self, repo_url: str, task: str):
        self.repo_url = repo_url
        self.task = task
        self.client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    def run(self):
        with Shell(repo_url=self.repo_url) as shell:
            repo_data = glob_repo_code(shell)

            ast_data = {path: data.serialized_ast for path, data in repo_data.items()}

            print("Reasoning")
            r2 = reason(client=self.client, input=json.dumps(ast_data), goal=self.task)

            code_w_line_numbers = {path: data.code_with_lines for path, data in repo_data.items()}
            print("Fixing code")
            out = fix2(client=self.client, original_code=json.dumps(code_w_line_numbers), input=r2)

            file_code_mapping = {path: data.code for path, data in repo_data.items()}

            print("Applying diffs")
            new, touched_files = apply_diff(file_code_mapping=file_code_mapping, diff=out)
            formatted_new = {path: reformat_code(code) for path, code in new.items()}

            for file in touched_files:
                print(f"{file}:\n\n {json.dumps(formatted_new[file])}\n\n")

            print("Evaluating code")
            eval = evaluate(client=self.client, goal=self.task, requrements=r2, old_code=json.dumps(file_code_mapping), new_code=json.dumps(formatted_new))
            print(eval)

