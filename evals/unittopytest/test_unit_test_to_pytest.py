







def test_change():

    import subprocess

    process = subprocess.run(["pytest"], cwd="../agent/teststest", capture_output=True, text=True)

    assert process.returncode == 0, "Pytest did not run successfully"
    assert "collected 0 items" not in process.stdout, "No tests were collected"



