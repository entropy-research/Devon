import re

import pytest
from pytest import raises

from devon_agent.tools import parse_commands


def test_1():
    # Test case 1: Single command without arguments
    commands = "ls"
    expected_output = [("ls", [])]
    assert parse_commands(commands) == expected_output


def test_2():
    # Test case 2: Single command with single-line arguments
    commands = 'grep -rl "hello world"'
    expected_output = [("grep", ["-rl", "hello world"])]
    assert parse_commands(commands) == expected_output


def test_3():
    # Test case 3: Single command with multiline arguments
    commands = """
    create_file ./test.txt <<<
This is a test file.
It contains multiple lines.
>>>
    """
    expected_output = [
        (
            "create_file",
            ["./test.txt", "This is a test file.\nIt contains multiple lines."],
        )
    ]
    assert parse_commands(commands) == expected_output


# Test case 4: Multiple commands with single-line and multiline arguments
def test_4():
    commands = """
    grep -rl "hello"
    create_file ./example.txt <<<
This is an example file.
It has two lines.
>>>
    ls -l
    """
    expected_output = [
        ("grep", ["-rl", "hello"]),
        (
            "create_file",
            ["./example.txt", "This is an example file.\nIt has two lines."],
        ),
        ("ls", ["-l"]),
    ]
    output = parse_commands(commands)
    assert output == expected_output


# Test case 5: Multiple commands with missing closing fence


def test_5():
    commands = """
    grep -rl "hello"
    create_file ./example.txt <<<
    This is an example file.
    It has two lines.
    ls -l
    """
    with pytest.raises(ValueError):
        parse_commands(commands)


def test_6():
    # Test case 6: Empty command string
    commands = ""
    expected_output = []
    actual_output = parse_commands(commands)
    assert actual_output == expected_output


def test_7():
    # Test case 7: Command string with only whitespace
    commands = "   \n   \t   "
    expected_output = []
    actual_output = parse_commands(commands)
    assert actual_output == expected_output
