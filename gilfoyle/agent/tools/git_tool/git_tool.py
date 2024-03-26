from git import Repo

from pydantic import Field

from gilfoyle.agent.clients.tool_utils.tools import tool

class GitManager:

    def init_new_repo(self, path: str = Field(..., description="The path to the Git repository")):
        self.repo = Repo(path)
        return {"result":f"Successfully created repo at {path}"}

    @tool(name="git_clone", description="Clone a Git repository")
    def clone(self, 
            url: str = Field(..., description="The URL of the Git repository to clone"),
            path: str = Field(..., description="The path where the cloned repository will be stored")
        ):

        print("pulling: ", url)

        self.repo = Repo.clone_from(url, path)
        return {"result":f"Successfully cloned repo at {path}"}

    @tool(name="git_get_branches", description="Get the branches of a Git repository")
    def get_branches(self):
        return [str(branch) for branch in self.repo.branches]

    @tool(
        name="git_get_commits",
        description="Get the commits of a branch in a Git repository",
    )
    def get_commits(self, branch: str = Field(..., description="The branch to retrieve commits from")):
        return [str(commit) for commit in self.repo.iter_commits(branch)]

    @tool(
        name="git_get_commit",
        description="Get a specific commit from a Git repository",
    )
    def get_commit(self, commit: str = Field(..., description="The commit hash to retrieve")):
        return str(self.repo.commit(commit))

    @tool(
        name="git_get_file",
        description="Get a file from a specific commit in a Git repository",
    )
    def get_file(self, commit: str = Field(..., description="The commit hash"),
                 file: str = Field(..., description="The file path")):
        return self.repo.git.show(f'{commit}:{file}')
