from os import getcwd, path
from git import Repo
from typing import List
from pydantic import Field
from devon_agent.agent.clients.tool_utils.tools import tool

class GitTool:

    @tool(name="git_create_repo", description="Clone a Git repository")
    def init_new_repo(self, path: str = Field(..., description="The path to the Git repository")):
        self.repo = Repo.init(path)
        return {"result": f"Git repo at {path}"}

    @tool(name="git_clone", description="Clone a Git repository")
    def clone(self, url: str = Field(..., description="The URL of the Git repository to clone"),
              path: str = Field(..., description="The path where the cloned repository will be stored")):
        print("pulling: ", url)
        self.repo = Repo.clone_from(url, path)
        return {"result": f"Successfully cloned repo at {path}"}

    @tool(name="git_get_branches", description="Get the branches of a Git repository")
    def get_branches(self):
        return [str(branch) for branch in self.repo.branches]

    @tool(name="git_get_commits", description="Get the commits of a branch in a Git repository")
    def get_commits(self, branch: str = Field(..., description="The branch to retrieve commits from")):
        return [str(commit) for commit in self.repo.iter_commits(branch)]

    @tool(name="git_get_commit", description="Get a specific commit from a Git repository")
    def get_commit(self, commit: str = Field(..., description="The commit hash to retrieve")):
        return str(self.repo.commit(commit))

    @tool(name="git_get_file", description="Get a file from a specific commit in a Git repository")
    def get_file(self, commit: str = Field(..., description="The commit hash"),
                 file: str = Field(..., description="The file path")):
        return self.repo.git.show(f'{commit}:{file}')

    @tool(name="git_create_branch", description="Create a new branch in a Git repository")
    def create_branch(self, branch_name: str = Field(..., description="The name of the new branch"),
                      commit: str = Field("HEAD", description="The commit to branch from (default: HEAD)")):
        new_branch = self.repo.create_head(branch_name, commit)
        return {"result": f"Successfully created branch '{branch_name}' from commit '{commit}'"}

    @tool(name="git_checkout_branch", description="Checkout a branch in a Git repository")
    def checkout_branch(self, branch_name: str = Field(..., description="The name of the branch to checkout")):
        self.repo.git.checkout(branch_name)
        return {"result": f"Successfully checked out branch '{branch_name}'"}

    @tool(name="git_create_commit", description="Create a new commit with the specified files")
    def create_commit(self, message: str = Field(..., description="The commit message"),
                      paths: str = Field(..., description="The list of file paths to include in the commit delineated by ';'")):
        
        files = paths.split(";")

        # Stage the files
        for file_path in files:
            try:
                self.repo.index.add(file_path)
            except:
                self.repo.index.add(path.join(getcwd(),file_path))

        # Create the commit
        commit = self.repo.index.commit(message)

        return {"result": f"Successfully created commit '{commit.hexsha}' with message '{message}'"}

    @tool(name="git_add_remote", description="Add a remote to a Git repository")
    def add_remote(self, name: str = Field(..., description="The name of the remote"),
                   url: str = Field(..., description="The URL of the remote")):
        self.repo.create_remote(name, url)
        return {"result": f"Successfully added remote '{name}' with URL '{url}'"}

    @tool(name="git_remove_remote", description="Remove a remote from a Git repository")
    def remove_remote(self, name: str = Field(..., description="The name of the remote to remove")):
        remote = self.repo.remote(name)
        remote.remove(self.repo, name)
        return {"result": f"Successfully removed remote '{name}'"}

    @tool(name="git_list_remotes", description="List the remotes of a Git repository")
    def list_remotes(self):
        remotes = []
        for remote in self.repo.remotes:
            remotes.append({"name": remote.name, "url": remote.url})
        return remotes

    @tool(name="git_push", description="Push changes to a remote repository")
    def push(
            self,
            remote: str = Field(..., description="The name of the remote"),
            branch: str = Field(..., description="The branch to push")
        ):
        self.repo.remote(remote).push(branch)
        return {"result": f"Successfully pushed branch '{branch}' to remote '{remote}'"}

    @tool(name="git_pull", description="Pull changes from a remote repository")
    def pull(self, remote: str = Field(..., description="The name of the remote"),
             branch: str = Field(..., description="The branch to pull")):
        self.repo.remote(remote).pull(branch)
        return {"result": f"Successfully pulled changes from branch '{branch}' of remote '{remote}'"}
