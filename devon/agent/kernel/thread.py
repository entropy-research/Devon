import os
from pathlib import Path
from typing import Literal

from devon.agent.evaluate import evaluate
from devon.agent.kernel.state_machine.state_types import State
from devon.agent.tools.unified_diff.create_diff import generate_unified_diff
from devon.agent.tools.unified_diff.prompts.udiff_prompts import UnifiedDiffPrompts
from devon.agent.tools.unified_diff.utils import apply_diff_to_file_map
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

        self.reasoning_model = ClaudeOpus(client=anthrpoic_client, system_message=ReasoningPrompts.system, max_tokens=1024,temperature=0.5)
        self.diff_model = ClaudeSonnet(client=anthrpoic_client, system_message=UnifiedDiffPrompts.main_system, max_tokens=4096)
        self.critic = ClaudeOpus(client=anthrpoic_client, system_message=EvaluatePrompts.system, max_tokens=1024)
        self.mode = mode

    def run(self):

        with self.env as env:
            success = False
            failure_context = []
            state_manager: State = State(state="reason")
            file_system = env.tools.file_system(path=os.getcwd())
            while not state_manager.state == "success":

                #Define run context
                repo_data = file_system.glob_repo_code(os.getcwd())
                ast_data = {path: data.code for path, data in repo_data.items()}

                match state_manager.state:
                    case "reason":
                        print("Reasoning")
                        r2 = self.reasoning_model.chat([
                            Message(role="user", content=ReasoningPrompts.user_msg(goal=self.task, code=json.dumps(ast_data)))
                        ])

                        state_manager.state = "write"

                    case "write":
                        print("Fixing code")
                        code_w_line_numbers = {path: data.code_with_lines for path, data in repo_data.items()}

                        try:
                            out = generate_unified_diff(client=self.diff_model, original_code=json.dumps(code_w_line_numbers), input=r2, failure_context=failure_context)
                            print(out)
                        except Exception as e:
                            error = traceback.format_exc()
                            print(error)
                            failure_context.append(error)
                            continue

                        file_code_mapping = {path: data.code for path, data in repo_data.items()}

                        state_manager.state = "execute"

                    case "execute":
                        print("Applying diffs")
                        new, touched_files = apply_diff_to_file_map(file_code_mapping=file_code_mapping, diff=out)
                        formatted_new = {path: reformat_code(code) for path, code in new.items()}

                        state_manager.state = "evaluate"
                    
                    case "evaluate":

                        print("Evaluating code")
                        eval = self.critic.chat(messages=[
                            Message(
                                role="user",
                                content=EvaluatePrompts.user_msg(goal=self.task, requirements=r2, old_code=json.dumps(file_code_mapping), new_code=json.dumps(formatted_new))
                            )
                        ])

                        success_status = self.critic.chat(messages=[
                            Message(
                                role="user",
                                content=eval + "\n" + """If you think the requirements have been met reply with
    <SUCCESS>
    True
    </SUCCESS>
    If you think the requirements have not been met reply with
    <SUCCESS>
    False
    </SUCCESS>.
    Do not reply with anything else. Your response will be parsed as is. Thank you."""
                            ),
                            Message(
                                role="assistant",
                                content=EvaluatePrompts.success
                            )
                        ],stop_sequences=["</SUCCESS>"])

                        result = xmltodict.parse("<SUCCESS>" + success_status + "</SUCCESS>")

                        # result = json.loads("{\n" + success_status)
                        success = result["SUCCESS"]

                        if success == "True":
                            state_manager.state = "success"
                        else:
                            state_manager.state = "reason"


            # for path, code in file_code_mapping.items():
            #     path = shell.container.cwd + "/" + path
            #     os.makedirs(os.path.dirname(path), exist_ok=True)
            #     with open(path, "w") as f:
            #         f.write(code)
