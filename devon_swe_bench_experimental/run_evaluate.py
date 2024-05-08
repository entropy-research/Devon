from fabric import Connection

# Set the local folder path
local_folder = "/Users/mihirchintawar/agent/devon/trajectories"

# Set the remote server details
remote_user = "root"
remote_server = "5.78.117.161"
remote_directory = "/root/SWE-agent/trajectories"

eval_dir = "/root/SWE-agent/evaluation"

private_key_path= "/Users/mihirchintawar/.ssh/hetzner"

# Create a connection to the remote server
with Connection(host=remote_server, user=remote_user,connect_kwargs={"key_filename": private_key_path},
) as c:
    
    # if directory exists remotely, delete it
    c.run("rm -rf " + remote_directory)
    
    # Copy the folder to the remote server using put()
    local_tar_path = "/tmp/trajectories.tar.gz"
    remote_tar_path = "/root/SWE-agent/trajectories.tar.gz"
    c.local(f"tar -czf {local_tar_path} -C {local_folder} .")
    c.put(local_tar_path, remote=remote_tar_path)
    c.run(f"mkdir -p {remote_directory}")
    c.run(f"tar -xzf {remote_tar_path} -C {remote_directory}")




    with c.cd(eval_dir):
        c.run("source ~/.bashrc")
        c.run("conda activate swe-agent")
        c.run("sh run_eval.sh " + remote_directory)

    c.get(remote_directory + "/results.json", local_folder + "/results.json")
    c.get(remote_directory + "/scorecards.json", local_folder + "/scorecards.json")


    # # Execute bash commands on the remote server and save the output to a file
    # with c.cd(remote_directory):
    #     output = c.run("ls -l", hide=True).stdout

    # # Save the output to a file
    # with open("output.txt", "w") as file:
    #     file.write(output)

# print("Script execution completed. Output saved to output.txt.")