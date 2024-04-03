import pytest
from subprocess import run, PIPE

def test_valid_addition():
    # Test valid addition operation
    result = run(["python", "fixed_cli_app.py", "add", "5", "3"], stdout=PIPE, stderr=PIPE, text=True)
    assert result.returncode == 0
    assert result.stdout.strip() == "Result: 8"

def test_valid_multiplication():
    # Test valid multiplication operation 
    result = run(["python", "fixed_cli_app.py", "multiply", "4", "6"], stdout=PIPE, stderr=PIPE, text=True)
    assert result.returncode == 0
    assert result.stdout.strip() == "Result: 24"

def test_invalid_operation():
    # Test invalid operation
    result = run(["python", "fixed_cli_app.py", "divide", "10", "2"], stdout=PIPE, stderr=PIPE, text=True)
    assert result.returncode != 0

def test_missing_arguments():
    # Test missing arguments
    result = run(["python", "fixed_cli_app.py", "add", "7"], stdout=PIPE, stderr=PIPE, text=True)
    assert result.returncode != 0

def test_non_integer_arguments():
    # Test non-integer arguments
    result = run(["python", "fixed_cli_app.py", "multiply", "3.14", "2"], stdout=PIPE, stderr=PIPE, text=True)
    assert result.returncode != 0

def test_zero_argument():
    # Test zero as an argument
    result = run(["python", "fixed_cli_app.py", "multiply", "0", "5"], stdout=PIPE, stderr=PIPE, text=True)
    assert result.returncode == 0
    assert result.stdout.strip() == "Result: 0"

def test_large_numbers():
    # Test large numbers
    result = run(["python", "fixed_cli_app.py", "add", "999999999", "1"], stdout=PIPE, stderr=PIPE, text=True)
    assert result.returncode == 0
    assert result.stdout.strip() == "Result: 1000000000"