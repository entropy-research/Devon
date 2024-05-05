
from rich.console import Console
from rich.layout import Layout
from rich.text import Text
from rich.text import TextInput
from rich.align import Align

class TerminalUI:

    def __init__(self):
        revision = Text()

        # Create a Rich console
        console = Console()

        # Create a layout with a main panel and an input bar
        layout = Layout()
        layout.split_column(
            Layout(name="main"),
            Layout(name="input", size=3)
        )

        textinput = TextInput(multiline=False, password=False)
        layout["input"].update(Align.center(textinput))