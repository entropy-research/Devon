



import time

from devon_agent.environment import JobShellEnvironment


def test_long_process():


    env = JobShellEnvironment(".")
    env.setup()
    job = env.execute("sleep 3",1)
    print(env.jobs)
    assert job.command == "sleep 3"
    assert job.status == "running"

    time.sleep(5)
    # print(open(job.named_pipe_stderr).read())
    stdout, stderr, exit_code, pid = env.read_background_output(job)
    assert job.command == "sleep 3"
    assert job.status == "returned"
    assert job.stdout == ""
    assert job.stderr == ""
    assert exit_code == 0
    assert pid is not None