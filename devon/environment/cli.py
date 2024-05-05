





import inspect
import os
import re
import traceback
from typing import Any, Dict
from devon.environment.environment import  TaskEnvironment
from devon.environment.agent import PlanningAgent, TaskAgent
import logging
from devon.environment.utils import LOGGER_NAME

from devon.retrieval.main import ClassTable, FunctionTable
def extract_signature_and_docstring(function_code: str) -> tuple:
    """
    Extracts the function signature and docstring from the given Python function code.

    Args:
        function_code (str): The Python function code as a string.

    Returns:
        tuple: A tuple containing the function signature (str) and the docstring (str).
    """
    # Extract the function signature
    signature_match = re.search(r"def\s+(\w+)\((.*?)\)", function_code)
    if signature_match:
        fn_name = signature_match.group(1)
        args = signature_match.group(2).split(",")
        args = [arg.strip().split(":")[0].split("=")[0] for arg in args if arg.strip() and arg.strip() != "self"]
        signature = f"{fn_name} {' '.join(args)}"
    else:
        signature = ""

    # Extract the docstring
    docstring_match = re.search(r'"""(.*?)"""', function_code, re.DOTALL)
    if docstring_match:
        docstring = docstring_match.group(1).strip()
    else:
        docstring = ""

    return signature, docstring

logger = logging.getLogger(LOGGER_NAME)



class ChatEnvironment:

    # tools
    # delegate task agent
    # add task to planner
    # interupt task agent
    # list task agents
    # get task agent state
    # get planner state

    def __init__(self,base_path):
        self.planner: Dict[str, str] = {}
        self.task_agents: Dict[str, Any] = {}
        self.chat_history = []
        self.base_path = base_path

    def step(self, action: str, thought: str):

        self.chat_history.append({"role": "assistant", "content": thought})

        observation = ""
        try:
            # observation = self.communicate(input=action, timeout_duration=25)
            observation = self.parse_command_to_function(command_string=action)
            return observation,False            # logger.info("RESULT: %s", observation)
        except TimeoutError:
            try:
                observation += "\nEXECUTION TIMED OUT"
            except RuntimeError as e:
                observation += (
                    "\nEXECUTION TIMED OUT AND INTERRUPT FAILED. RESTARTING PROCESS."
                )
                logger.warning(
                    f"Failed to interrupt container: {e}\nRESTARTING PROCESS."
                )
                return observation, 0, True
        except RuntimeError as e:
            observation += "\nCOMMAND FAILED TO EXECUTE. RESTARTING PROCESS."
            logger.warning(f"Failed to execute command: {e}\nRESTARTING PROCESS.")
            return observation, 0, True
        except Exception as e:
            logger.error(e)
            import traceback

            traceback.print_exc()
            observation += "\nEXECUTION FAILED OR COMMAND MALFORMED"
            raise e

    

    def parse_command(self, command: str) -> tuple:
        """
        Parses a command string into its function name and arguments.

        Args:
            command (str): The command string to parse.

        Returns:
            tuple: A tuple containing the function name (str) and a list of arguments (list).
        """
        logger.info("Parsed command: %s", command)
        parts = re.findall(r'(?:"[^"]*"|\[[^]]*\]|<<<[^>]*>>>|[^"\s]+)', command)
        fn_name = parts[0]
        args = []
        for arg in parts[1:]:
            # if arg.startswith("[") and arg.endswith("]"):
            #     arg = eval(arg)
            if arg.startswith('"') and arg.endswith('"'):
                arg = arg[1:-1]
            elif arg.startswith("<<<") and arg.endswith(">>>"):
                arg = arg[3:-3]
            args.append(arg)
        return fn_name, args

    def add_task_to_planner(self, task: str, task_description: str = ""):
        """
        add_task_to_planner task_name task_description
        Adds a task to the planner.

        """
        self.planner[task] = task_description

    def delegate_task_agent(self, task: str):
        """
        delegate task_name
        Delegates a task to a task agent.
        """
        self.task_agents[task] = TaskAgent()
        try:

            task_environment = TaskEnvironment(base_path=self.base_path)
            self.task_agents[task].run(
                task=self.planner[task], env=task_environment, observation=""
            )
        except Exception as e:
            raise e

    def stop_task_agent(self, task: str):
        """
        stop_task_agent task_name
        Stops a task agent.
        """
        self.task_agents[task].stop()

    def interrupt_task_agent(self, task: str, message: str):
        """
        interrupt_task_agent task_name
        Interrupts a task agent.
        """
        self.task_agents[task].interrupt(message)

    def get_task_agent_state(self, task: str):
        """
        get_task_agent_state task_name
        Gets the state of a task agent.
        """
        return self.task_agents[task].get_state()

    def get_planner_state(self):
        """
        get_planner_state
        Gets the state of the planner.
        """
        return self.planner
    
    def ask_user(self,question):
        """
        ask_user question
        Asks the user for their input
        """
        user_response = input(question)
        return user_response


    @property
    def tools(self):
        return [
            self.add_task_to_planner,
            self.delegate_task_agent,
            self.stop_task_agent,
            self.interrupt_task_agent,
            self.get_task_agent_state,
            self.ask_user
            # self.get_planner_state
        ]

    def parse_command_to_function(self, command_string):
        """
        Parses a command string into its function name and arguments.
        """

        fn_name, args = self.parse_command(command_string)
        if fn_name in ["vim", "nano"]:
            return "Interactive Commands are not allowed"

        if (
            fn_name == "python"
            and len([line for line in command_string.splitlines() if line]) != 1
        ):
            return "Interactive Commands are not allowed"

        funcs = self.tools
        fn_names = [fn.__name__ for fn in funcs]

        try:
            if fn_name in fn_names:
                return self.__getattribute__(fn_name)(*args)
            else:
                raise Exception(f"Function {fn_name} not found")
        except Exception as e:
            logger.error(traceback.print_exc())
            raise e
            return e.args[0]

    def generate_command_docs(self):

        funcs = self.tools

        docs = {}

        for func in funcs:
            name = func.__name__
            code = inspect.getsource(func)
            sig, docstring = extract_signature_and_docstring(code)
            docs[name] = {"signature": sig, "docstring": docstring}

        return docs

    def get_available_actions(self):
        return self.tools

    
    



def run_cli(path,goal):
    
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    if not anthropic_api_key:
        anthropic_api_key = input("Please enter your Anthropic API key: ")
        if not anthropic_api_key:
            raise ValueError("Anthropic API key is required to proceed.")

    task_env = TaskEnvironment(path)
    # chat_env = ChatEnvironment(path)

    # planning_agent = PlanningAgent(name="PlanningAgent")
    
    # planning_agent.run(chat_env,observation="I want to make a snake game")

    task_agent = TaskAgent()
    task_agent.run(goal,task_env)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run CLI with a specific goal for the task agent.")
    parser.add_argument('--goal',required=True, type=str, help='The goal/task for the task agent to execute.')
    args = parser.parse_args()

    run_cli(os.getcwd(), args.goal)
    



