from os import getcwd, path
from git import Repo
from typing import List
from pydantic import Field
from devon.agent.clients.tool_utils.tools import tool

class GitTool:

    def __init__(self, path="."):
        self.repo = Repo(path=path)

    @tool(name="git_create_repo", description="Clone a Git repository")
    def init_new_repo(self, path: str = Field(..., description="The path to the Git repository")):
        self.repo = Repo(path)
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