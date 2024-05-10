import os
from devon_agent.agent.clients.client import GPT4, Message

def test_add_valid_integers():
    """
    Verify that the application can add two valid integers.
    """
    result = run(["python", "evalmath.py", "add", "5", "3"], stdout=PIPE, stderr=PIPE, universal_newlines=True)