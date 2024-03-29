import os
from pathlib import Path
from typing import Literal

from devon.agent.evaluate import evaluate
from devon.agent.kernel.state_machine.state_machine import StateMachine
from devon.agent.kernel.state_machine.state_types import State
from devon.agent.tools.unified_diff.create_diff import generate_unified_diff, generate_unified_diff2
from devon.agent.tools.unified_diff.prompts.udiff_prompts import UnifiedDiffPrompts
<<<<<<< HEAD
from devon.agent.tools.unified_diff.utils import apply_diff, apply_diff_to_file_map
=======
from devon.agent.tools.unified_diff.utils import apply_diff, apply_diff2, apply_diff_to_file_map
>>>>>>> 0f6851b (new coding)
from devon.sandbox.environments import EnvironmentProtocol
from devon.format import reformat_code
from devon.agent.reasoning.reason import ReasoningPrompts
from agent.evaluate.evaluate import EvaluatePrompts
from anthropic import Anthropic
from devon.agent.clients.client import ClaudeHaiku, ClaudeOpus, ClaudeSonnet, Message
import json
import traceback
import xmltodict

class Thread:
    def __init__(self,
        task: str,
        environment : EnvironmentProtocol,
        mode : Literal["Container"] | Literal["Local"] = Literal["Local"]
    ):
        self.task = task
        api_key=os.environ.get("ANTHROPIC_API_KEY")
        self.env: EnvironmentProtocol = environment

        anthrpoic_client = Anthropic(api_key=api_key)

        self.reasoning_model = ClaudeSonnet(client=anthrpoic_client, system_message=ReasoningPrompts.system, max_tokens=1024,temperature=0.5)
        self.diff_model = ClaudeSonnet(client=anthrpoic_client, system_message=UnifiedDiffPrompts.main_system, max_tokens=4096)
        self.critic = ClaudeOpus(client=anthrpoic_client, system_message=EvaluatePrompts.system, max_tokens=1024)
        self.mode = mode

    def run(self):

        with self.env as env:
            success = False
            failure_context = []
            state_manager = StateMachine(state="reason")
            file_system = env.tools.file_system(path=os.getcwd())

            plan = None
            create = None
            modify = None
            delete = None

            # while not state_manager.state == "success":

                #Define run context
            repo_data = file_system.glob_repo_code(os.getcwd())
            file_tree = file_system.list_directory_recursive(path=os.getcwd())

            ast_data = {path: data.code for path, data in repo_data.items()}

            print("Reasoning")
            r2 = self.reasoning_model.chat([
                Message(role="user", content=ReasoningPrompts.user_msg(goal=self.task, file_tree=str(file_tree), code=json.dumps(ast_data)))
            ])

            plan, create, modify, delete, files_to_change = ReasoningPrompts.parse_msg(r2)

            modify += [p for p in create if os.path.exists(p)]
            files_to_change = [os.path.join(os.getcwd(), path.strip()) for path in files_to_change if path != '']

<<<<<<< HEAD
            code_w_line_numbers = {path: data.code_with_lines for path, data in repo_data.items() if path in files_to_change}

            print(code_w_line_numbers.keys())
            try:
                out = generate_unified_diff(
=======
            code_w_line_numbers = {path: data.code for path, data in repo_data.items() if path in files_to_change}

            print(code_w_line_numbers.keys())
            try:
                out = generate_unified_diff2(
>>>>>>> 0f6851b (new coding)
                        client=self.diff_model,
                        goal=self.task,
                        original_code=json.dumps(code_w_line_numbers), 
                        plan=plan,
                        create=create,
                        modify=modify,
                        delete=delete,
<<<<<<< HEAD
                        failure_context=failure_context
=======
                        failure_context=failure_context,
                        file_tree=file_tree
>>>>>>> 0f6851b (new coding)
                    )

                print(out)
            except Exception as e:
                error = traceback.format_exc()
                print(error)
                failure_context.append(error)
                # continue

            file_code_mapping = {path: data.code for path, data in repo_data.items()}

            # print("Applying diffs")
            # new, touched_files = apply_diff_to_file_map(file_code_mapping=file_code_mapping, diff=out)
<<<<<<< HEAD
            apply_diff(out)
=======
            apply_diff2(out)
>>>>>>> 0f6851b (new coding)

            # print(new, touched_files)

            # file_code_mapping = {path: data.code for path, data in repo_data.items()}

    #         match state_manager.state:
    #             case "reason":
    #                 print("Reasoning")
    #                 r2 = self.reasoning_model.chat([
    #                     Message(role="user", content=ReasoningPrompts.user_msg(goal=self.task, file_tree=str(file_tree), code=json.dumps(ast_data)))
    #                 ])

    #                 plan, create, modify, delete = ReasoningPrompts.parse_msg(r2)

    #                 state_manager.state = "write"

    #             case "write":
    #                 print("Fixing code")
    #                 code_w_line_numbers = {path: data.code_with_lines for path, data in repo_data.items() if path in create + modify + delete}

    #                 try:
    #                     out = generate_unified_diff(
    #                             client=self.diff_model,
    #                             original_code=json.dumps(code_w_line_numbers), 
    #                             input=plan,
    #                             failure_context=failure_context
    #                         )
                        
    #                     print(out)
    #                 except Exception as e:
    #                     error = traceback.format_exc()
    #                     print(error)
    #                     failure_context.append(error)
    #                     # continue

    #                 file_code_mapping = {path: data.code for path, data in repo_data.items()}

    #                 state_manager.state = "execute"

    #             case "execute":
    #                 print("Applying diffs")
    #                 new, touched_files = apply_diff_to_file_map(file_code_mapping=file_code_mapping, diff=out)
    #                 formatted_new = {path: reformat_code(code) for path, code in new.items()}

    #                 state_manager.state = "evaluate"
                
    #             case "evaluate":

    #                 print("Evaluating code")
    #                 eval = self.critic.chat(messages=[
    #                     Message(
    #                         role="user",
    #                         content=EvaluatePrompts.user_msg(goal=self.task, requirements=r2, old_code=json.dumps(file_code_mapping), new_code=json.dumps(formatted_new))
    #                     )
    #                 ])

    #                 success_status = self.critic.chat(messages=[
    #                     Message(
    #                         role="user",
    #                         content=eval + "\n" + """If you think the requirements have been met reply with
    # <SUCCESS>
    # True
    # </SUCCESS>
    # If you think the requirements have not been met reply with
    # <SUCCESS>
    # False
    # </SUCCESS>.
    # Do not reply with anything else. Your response will be parsed as is. Thank you."""
    #                     ),
    #                     Message(
    #                         role="assistant",
    #                         content=EvaluatePrompts.success
    #                     )
    #                 ],stop_sequences=["</SUCCESS>"])

    #                 result = xmltodict.parse("<SUCCESS>" + success_status + "</SUCCESS>")

    #                 # result = json.loads("{\n" + success_status)
    #                 success = result["SUCCESS"]

    #                 if success == "True":
    #                     state_manager.state = "success"
    #                 else:
    #                     state_manager.state = "reason"


            # for path, code in file_code_mapping.items():
            #     path = shell.container.cwd + "/" + path
            #     os.makedirs(os.path.dirname(path), exist_ok=True)
            #     with open(path, "w") as f:
            #         f.write(code)
