import os
from pathlib import Path
from typing import Literal

from devon.agent.evaluate import evaluate
from devon.agent.kernel.state_machine.states.evaluate import EvaluateState
from devon.agent.kernel.state_machine.states.execute import ExecuteState
from devon.agent.kernel.state_machine.states.reason import ReasonState
from devon.agent.kernel.state_machine.states.terminate import TerminateState
from devon.agent.kernel.state_machine.states.write import WriteState
from devon.agent.kernel.state_machine.states.evaluate import EvaluateState
from devon.agent.tools.unified_diff.create_diff import generate_unified_diff2
from devon.agent.tools.unified_diff.prompts.udiff_prompts import UnifiedDiffPrompts
from devon.agent.tools.unified_diff.utils import apply_diff2
from devon.sandbox.environments import EnvironmentProtocol
from devon.format import reformat_code
from devon.agent.reasoning.reason import ReasoningPrompts
from agent.evaluate.evaluate import EvaluatePrompts
from anthropic import Anthropic
from devon.agent.clients.client import ClaudeHaiku, ClaudeOpus, ClaudeSonnet, Message
import json
import traceback
import xmltodict
from .state_machine.state_machine import StateMachine
from .state_machine.state_types import StateType

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
        
        self.state_machine = StateMachine(initial_state="reason")
        self.state_machine.add_state("reason", ReasonState())
        self.state_machine.add_state("write", WriteState())
        self.state_machine.add_state("execute", ExecuteState())
        self.state_machine.add_state("evaluate", EvaluateState())
        self.state_machine.add_state("terminate", TerminateState())
        self.context = {}

    def run(self):

        with self.env as env:
            success = False
            failure_context = []
            file_system = env.tools.file_system(path=os.getcwd())

            plan = None
            create = None
            modify = None
            delete = None

            repo_data = file_system.glob_repo_code(os.getcwd())
            file_tree = file_system.list_directory_recursive(path=os.getcwd())

            ast_data = {path: data.code for path, data in repo_data.items()}

            print("Reasoning")
            r2 = self.reasoning_model.chat([
                Message(role="user", content=ReasoningPrompts.user_msg(goal=self.task, file_tree=str(file_tree), code=json.dumps(ast_data)))
            ])

            plan, create, modify, delete, files_to_change, read_only = ReasoningPrompts.parse_msg(r2)

            modify += [p for p in create if os.path.exists(p)]
            files_to_change = [os.path.join(os.getcwd(), path.strip()) for path in files_to_change if path != '']

            print("Read Only: ", read_only)
            print("To Change: ", files_to_change)

            read_code_w_line_numbers = {path: data.code for path, data in repo_data.items() if path in read_only}
            edit_code_w_line_numbers = {path: data.code for path, data in repo_data.items() if path in files_to_change + read_only}

            try:
                out = generate_unified_diff2(
                        client=self.diff_model,
                        goal=self.task,
                        original_code=json.dumps(edit_code_w_line_numbers), 
                        plan=plan,
                        create=create,
                        modify=modify,
                        delete=delete,
                        failure_context=failure_context,
                        file_tree=file_tree
                    )

            except Exception as e:
                error = traceback.format_exc()
                print(error)
                failure_context.append(error)
            
            file_code_mapping = {path: data.code for path, data in repo_data.items()}


            apply_diff2(out)

            # # Evaluate the changes
            # print("Evaluating code")
            # eval_result = self.critic.chat(messages=[
            #     Message(
            #         role="user",
            #         content=EvaluatePrompts.user_msg(
            #             goal=self.task,
            #             requirements=r2,
            #             old_code=json.dumps(repo_data),
            #             new_code=json.dumps(file_system.glob_repo_code(os.getcwd()))
            #         )
            #     )
            # ])

            # success = EvaluatePrompts.parse_success(eval_result)

            # if success:
            #     print("Requirements met successfully!")
            # else:
            #     print("Requirements not met, trying again...")
