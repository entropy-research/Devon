# test_cases.py
import subprocess

def test_add_numbers():
    # Test case 1: Adding two positive numbers
    output = subprocess.check_output(["python", "fixed_cli_app.py", "add", "5", "3"], universal_newlines=True)
    assert "Result: 8" in output, "Adding two positive numbers should return the correct sum"

    # Test case 2: Adding a positive and a negative number
    output = subprocess.check_output(["python", "fixed_cli_app.py", "add", "10", "-2"], universal_newlines=True)
    assert "Result: 8" in output, "Adding a positive and a negative number should return the correct sum"

def test_multiply_numbers():
    # Test case 3: Multiplying two positive numbers
    output = subprocess.check_output(["python", "fixed_cli_app.py", "multiply", "4", "6"], universal_newlines=True)
    assert "Result: 24" in output, "Multiplying two positive numbers should return the correct product"

    # Test case 4: Multiplying a positive and a negative number
    output = subprocess.check_output(["python", "fixed_cli_app.py", "multiply", "5", "-3"], universal_newlines=True)
    assert "Result: -15" in output, "Multiplying a positive and a negative number should return the correct product"

def test_invalid_operation():
    # Test case 5: Providing an invalid operation
    try:
        subprocess.check_output(["python", "fixed_cli_app.py", "invalid", "5", "3"], universal_newlines=True)
        assert False, "Invalid operation should raise an exception"
    except subprocess.CalledProcessError as e:
        assert True
        # assert "invalid choice" in e.output, "Invalid operation should be handled properly"