import pytest
from subprocess import run, PIPE

def test_valid_addition():
    # Test valid addition operation
    result = run(["python", "evalmath.py", "add", "5", "3"], stdout=PIPE)
    assert result.stdout.decode().strip() == "Result: 8"

def test_valid_multiplication():
    # Test valid multiplication operation  
    result = run(["python", "evalmath.py", "multiply", "4", "7"], stdout=PIPE)
    assert result.stdout.decode().strip() == "Result: 28"

def test_invalid_operation():
    # Test invalid operation
    with pytest.raises(Exception):
        run(["python", "evalmath.py", "subtract", "10", "6"], check=True)

def test_non_integer_argument():
    # Test non-integer argument
    with pytest.raises(Exception):
        run(["python", "evalmath.py", "add", "2.5", "8"], check=True)

def test_missing_argument():
    # Test missing argument
    with pytest.raises(Exception):
        run(["python", "evalmath.py", "multiply", "9"], check=True)