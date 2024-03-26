import requests

from pydantic import BaseModel, Field
from typing import List

from gilfoyle.agent.clients.tool_utils.tools import tool

class GitHubTool(BaseModel):
    token: str = Field(..., description="The GitHub access token")

    @tool(
        name="github_search_repositories",
        description="Search for repositories",
    )
    def search_repositories(self, query: str = Field(..., description="The search query")) -> List[str]:
        print(query)
        headers = {"Authorization": f"token {self.token}"}
        response = requests.get(f"https://api.github.com/search/repositories?q={query.replace(" ", "&")}", headers=headers)
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