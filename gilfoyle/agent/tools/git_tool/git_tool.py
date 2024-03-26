from git import Repo

from pydantic import Field

class GitManager:

    def init_new_repo(self, path: str = Field(..., description="The path to the Git repository")):
        self.repo = Repo(path)
        return self.repo

    def clone(self, 
            url: str = Field(..., description="The URL of the Git repository to clone"),
            path: str = Field(..., description="The path where the cloned repository will be stored")
        ):

        print("pulling: ", url)

        self.repo = Repo.clone_from(url, path)
        return self.repo

    def get_branches(self):
        return [str(branch) for branch in self.repo.branches]

    def get_commits(self, branch: str = Field(..., description="The branch to retrieve commits from")):
        return [str(commit) for commit in self.repo.iter_commits(branch)]

    def get_commit(self, commit: str = Field(..., description="The commit hash to retrieve")):
        return str(self.repo.commit(commit))

    def get_file(self, commit: str = Field(..., description="The commit hash"),
                 file: str = Field(..., description="The file path")):
        return self.repo.git.show(f'{commit}:{file}')
