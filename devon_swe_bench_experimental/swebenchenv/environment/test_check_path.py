def check_path_for_tests(file_path):
    if "/tests/" in file_path:
        return True
    else:
        return False

if __name__ == "__main__":
    assert check_path_for_tests("/django__django/tests/epic") == True