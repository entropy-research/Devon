import os
from pathlib import Path
from typing import Literal

from openai import OpenAI

from devon.agent.evaluate.evaluate import EvaluatePrompts
from devon.agent.kernel.context import BaseStateContext
from devon.agent.kernel.state_machine.states.evaluate import EvaluateContext, EvaluateParameters, EvaluateState
from devon.agent.kernel.state_machine.states.execute import ExecuteState
from devon.agent.kernel.state_machine.states.reason import ReasonState, ReasoningContext, ReasoningParameters
from devon.agent.kernel.state_machine.states.terminate import TerminateState
from devon.agent.kernel.state_machine.states.tool import ToolContext, ToolParameters, ToolState
from devon.agent.kernel.state_machine.states.write import WriteContext, WriteParameters, WriteState
from devon.agent.tools.git_tool.git_tool import GitTool
from devon.agent.tools.github.github_tool import GitHubTool
from devon.agent.tools.file_system.fs import FileSystemTool
from devon.agent.tools.tool_prompts import ToolPrompts
from devon.agent.tools.unified_diff.create_diff import generate_unified_diff2
from devon.agent.tools.unified_diff.prompts.udiff_prompts import UnifiedDiffPrompts
from devon.agent.tools.unified_diff.utils import apply_diff2
from devon.sandbox.environments import EnvironmentProtocol
from devon.format import reformat_code
from devon.agent.reasoning.reason import ReasoningPrompts
from agent.evaluate.evaluate import EvaluatePrompts
from anthropic import Anthropic
from devon.agent.clients.client import GPT4, ClaudeHaiku, ClaudeOpus, ClaudeSonnet, Message
import json
import traceback
import xmltodict
from .state_machine.state_machine import StateMachine
from .state_machine.state_types import StateType

class Thread:
    def __init__(self,
        task: str,
        qa: bool,
        environment : EnvironmentProtocol,
        mode : Literal["Container"] | Literal["Local"] = Literal["Local"],
        target_path : str = os.getcwd()
    ):
        self.task = task
        api_key=os.environ.get("ANTHROPIC_API_KEY")
        self.env: EnvironmentProtocol = environment

        anthrpoic_client = Anthropic(api_key=api_key)

        oai_api_key=os.environ.get("OPENAI_API_KEY")
        openai_client = OpenAI(api_key=oai_api_key)

        self.reasoning_model = ClaudeSonnet(client=anthrpoic_client, system_message=ReasoningPrompts.system, max_tokens=1024,temperature=0.5)
        self.diff_model = ClaudeSonnet(client=anthrpoic_client, system_message=UnifiedDiffPrompts.main_system, max_tokens=4096)
        self.critic = ClaudeOpus(client=anthrpoic_client, system_message=EvaluatePrompts.system, max_tokens=1024)
        self.tool_model = GPT4(client=openai_client, system_message=ToolPrompts.system, max_tokens=1000, tools_enabled=True)
        self.mode = mode
        
        self.state_machine = StateMachine(initial_state="reason")
        self.state_machine.add_state("reason", ReasonState(parameters=ReasoningParameters(model=self.reasoning_model)))
        self.state_machine.add_state("write", WriteState(parameters=WriteParameters(diff_model=self.diff_model)))
        self.state_machine.add_state("tools", ToolState(parameters=ToolParameters(model=self.tool_model)))
        self.state_machine.add_state("terminate", TerminateState())
        self.state_machine.add_state("evaluate", EvaluateState(parameters=EvaluateParameters(model=self.critic)))

        self.state_context = BaseStateContext(
            github_tool=GitHubTool(token=os.getenv("AGENT_GITHUB_TOKEN")),
            git_tool=GitTool(),
            file_system=self.env.tools.file_system(path=target_path),
            fs_root=target_path
        )

        # branches = self.state_context.git_tool.get_branches()
        # # print(branches)
        # commits = self.state_context.git_tool.get_commits(branch=branches[0])
        # # print(commits)

        # self.state_context.git_tool.create_branch("test", commit=commits[0])
        # self.state_context.git_tool.checkout_branch(branch_name="test")

    def run(self):

        # State machine init => reasoning
        # Capture state of filesystem should be a function
        # Capture state of code should be a function, Should read live from the files themselves each time rather than virtualize
        # Should be able to be run in a loop, and the state machine should be able to be reset and re-run
        # 
        # Context object for each state should include a fresh load of the file system, from root, not cwd
        
        # Load global context: File tree, File-Code mapping

        # 1. Reasoning
            # Identify which files are necessary for the change
            # Create a mapping on a file level of what changes need to be made to each file
            # Review plan
        # 2. Write
            # load required files based on input in the global context format
            # Identify 'n' change sets (1 to start)
            # For each
                # apply change set
                # evaluate change
        # 3. Evaluate
            # Look at edited files (This suffers from survivorship bias)
            # Evaluate the changes as to whether or not they are complete in context
                # Good eval is all you need

        success = False

        while not success:
            reasoning_result, old_code = self.state_machine.transition("reason", ReasoningContext(task=self.task, global_context=self.state_context))
            self.state_machine.transition("tools", ToolContext(task=self.task, global_context=self.state_context, plan=reasoning_result.plan))
            write_result = self.state_machine.transition("write", WriteContext(task=self.task, global_context=self.state_context, reasoning_result=reasoning_result))
            self.state_machine.transition("tools", ToolContext(task=self.task, global_context=self.state_context, plan=reasoning_result.plan))
            success = self.state_machine.transition("evaluate", context=EvaluateContext(task=self.task, global_context=self.state_context, reasoning_result=reasoning_result, old_code=old_code))

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