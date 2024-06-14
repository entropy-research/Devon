# file_discovery.py

import os


def discover_python_files(root_dir, ignore_dirs=None):
    """
    Discovers all Python files in the given directory and its subdirectories,
    excluding the specified ignore directories.
    Args:
        root_dir (str): The root directory to start the search from.
        ignore_dirs (list): A list of directory names to ignore (default: None).
    Returns:
        list: The list of discovered Python file paths.
    """
    if ignore_dirs is None:
        ignore_dirs = []

    python_files = []
    for root, dirs, files in os.walk(root_dir):
        # Remove ignored directories from the dirs list
        dirs[:] = [d for d in dirs if d not in ignore_dirs]

        for file in files:
            if file.endswith(".py"):
                print(f"discovered {os.path.join(root, file)}")
                python_files.append(os.path.join(root, file))

    return python_files
