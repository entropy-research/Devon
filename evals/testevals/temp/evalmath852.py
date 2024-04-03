from evalmath import main

def test_add_valid_integers():
    """
    Verify that the application can add two valid integers.
    """
    args = ["add", "5", "3"]
    assert main(args) == "Result: 8"

def test_multiply_valid_integers():
    """
    Verify that the application can multiply two valid integers.
    """
    args = ["multiply", "4", "6"]
    assert main(args) == "Result: 24"

def test_invalid_operation():
    """
    Verify that the application handles an invalid operation gracefully.
    """
    args = ["subtract", "2", "3"]
    with pytest.raises(Exception):
        main(args)

def test_non_integer_arguments():
    """
    Verify that the application handles non-integer arguments gracefully.
    """
    args = ["add", "2.5", "3"]
    with pytest.raises(Exception):
        main(args)

def test_missing_arguments():
    """
    Verify that the application handles missing arguments gracefully.
    """
    args = ["add", "5"]
    with pytest.raises(Exception):
        main(args)

def test_extra_arguments():
    """
    Verify that the application handles extra arguments gracefully.
    """
    args = ["add", "5", "3", "extra"]
    with pytest.raises(Exception):