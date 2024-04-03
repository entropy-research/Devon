import requests

from pydantic import BaseModel, Field
from typing import List

from devon.agent.clients.tool_utils.tools import tool

class GitHubTool(BaseModel):
    token: str = Field(..., description="The GitHub access token")

    @tool(
        name="github_search_repositories",
        description="Search for repositories",
    )
    def search_repositories(self, query: str = Field(..., description="The search query")) -> List[str]:
        print(query)
        headers = {"Authorization": f"token {self.token}"}
        response = requests.get(f"https://api.github.com/search/repositories?q={query.replace(' ', '&')}", headers=headers)
        response.raise_for_status()
        return [repo["full_name"] for repo in response.json()["items"]]

    @tool(
        name="list_directory",
        description="List the contents of a directory",
    )
    def list_user_repositories(self) -> List[str]:
        headers = {"Authorization": f"token {self.token}"}
        response = requests.get("https://api.github.com/user/repos", headers=headers)
        response.raise_for_status()
        return [repo["full_name"] for repo in response.json()]

    @tool(
        name="create_pull_request",
        description="Create a pull request",
    )
    def create_pull_request(self, repo: str = Field(..., description="The repository name"),
                            title: str = Field(..., description="The title of the pull request"),
                            body: str = Field(..., description="The body of the pull request"),
                            head: str = Field(..., description="The name of the branch where your changes are implemented"),
                            base: str = Field(..., description="The name of the branch you want the changes pulled into")) -> str:
        headers = {"Authorization": f"token {self.token}"}
        data = {
            "title": title,
            "body": body,
            "head": head,
            "base": base
        }
        response = requests.post(f"https://api.github.com/repos/{repo}/pulls", json=data, headers=headers)
        response.raise_for_status()
        return response.json()["html_url"]
    
    @tool(
        name="create_repository",
        description="Create a new repository",
    )
    def create_repository(
        self,
        name: str = Field(..., description="The name of the repository"),
        description: str = Field(None, description="The description of the repository")
    ) -> str:
        headers = {"Authorization": f"token {self.token}"}
        data = {
            "name": name,
            "description": description
        }
        try:
            response = requests.post("https://api.github.com/user/repos", json=data, headers=headers)
            response.raise_for_status()
            return response.json()["html_url"]
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                raise ValueError("Insufficient permissions to create a repository. Please check your access token.")
            else:
                raise e
    
    @tool(
        name="enable_github_pages",
        description="Enable GitHub Pages for a repository",
    )
    def enable_github_pages(
        self,
        owner: str = Field(..., description="The user/owner name"),
        repo: str = Field(..., description="The repository name"),
        branch: str = Field("main", description="The branch to use for GitHub Pages"),
        path: str = Field("/", description="The path to the GitHub Pages files")
    ) -> None:
        headers = {"Authorization": f"token {self.token}"}
        data = {
            "source": {
                "branch": branch,
                "path": path
            }
        }
        try:
            response = requests.post(f"https://api.github.com/repos/{owner}/{repo}/pages", json=data, headers=headers)
            response.raise_for_status()
            print(f"GitHub Pages enabled for repository: {repo}")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                raise ValueError("Insufficient permissions to enable GitHub Pages. Please check your access token.")
            else:
                return {"result": e.response.reason}
