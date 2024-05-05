import argparse
import threading
from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.layout import Layout
from rich.text import Text
from rich.align import Align
from rich.prompt import Prompt
from devon.environment.agent import TaskAgent

from devon.environment.environment import TaskEnvironment

def read_user_input(revisions):
    while True:
        revision = Prompt.ask(":")
        revisions.append(revision)

        

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("task", help="Task for the coding agent")
    args = parser.parse_args()

    revisions = []
    task = args.task
    revision = Text()

    # Create a Rich console
    console = Console()

    # Create a layout with a main panel and an input bar
    layout = Layout()
    layout.split_column(
        Layout(name="main"),
        # Layout(name="input", size=3)
    )

    # Create a text input field for user revision
    # textinput = Prompt.ask(":")
    # layout["input"].update(Align.center(textinput))

    # Start a separate thread to read user input
    input_thread = threading.Thread(target=read_user_input, args=(revisions,))
    input_thread.daemon = True
    input_thread.start()

    # Create a Live context for updating the UI
    with Live(layout, console=console, screen=True, auto_refresh=True) as live:
        while True:
            # Create a panel for displaying the task and user input
            task_panel = Panel(
                f"[bold]Task:[/bold]\n{task}\n\n[bold]User Revision:[/bold]\n{revision}",
                title="Coding Agent",
                expand=True
            )
            layout["main"].update(task_panel)

            task_env = TaskEnvironment(path)
    # chat_env = ChatEnvironment(path)

    # planning_agent = PlanningAgent(name="PlanningAgent")
    
    # planning_agent.run(chat_env,observation="I want to make a snake game")

            task_agent = TaskAgent()
            task_agent.run(goal,task_env)


            # Check if there is any revision from the user
            # if textinput:
            #     revision.append(textinput.value + "\n")
            #     console.print(f"[yellow]User revision:[/yellow] {textinput.value}")
            #     textinput.value = ""  # Clear the input field
                # Process the revised task
                # ...

            # Execute the coding agent's commands
            # ...

            # Display the agent's step
            # agent_step = "Agent step: ..."  # Replace with the actual step taken by the agent
            # console.print(f"[green]Agent step:[/green] {agent_step}")

            # Check if the task is complete or if there are more steps
            # ...

if __name__ == "__main__":
    main()