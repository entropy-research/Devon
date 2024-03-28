import subprocess

def reformat_code(code):
    try:
        # Run Ruff as a subprocess to reformat the code
        process = subprocess.Popen(
            ["ruff", "--fix", "-"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        # Pass the code to Ruff via stdin
        stdout, stderr = process.communicate(code)

        # Check the return code of the Ruff process
        if process.returncode == 0:
            # If Ruff executed successfully, return the reformatted code
            return stdout
        else:
            # If Ruff encountered an error, return the original code
            return code

    except FileNotFoundError:
        # If the Ruff command is not found, return the original code
        return code