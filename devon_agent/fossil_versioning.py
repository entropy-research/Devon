import subprocess
import os
import sys
import requests
import platform

class FossilVersioning:
    def __init__(self, project_path, fossil_dir):
        self.project_path = project_path
        self.fossil_dir = fossil_dir

    def revert_to_initial_commit(self):
        subprocess.run(['fossil', 'update', '0'], cwd=self.project_path, check=True)

    def check_fossil_installation(self):
        try:
            subprocess.run(['fossil', '--version'], capture_output=True, check=True)
            return True
        except FileNotFoundError:
            return False

    def install_fossil(self):
        system = platform.system().lower()
        if system == 'linux':
            subprocess.run(['sudo', 'apt-get', 'update'], check=True)
            subprocess.run(['sudo', 'apt-get', 'install', '-y', 'fossil'], check=True)
        elif system == 'darwin':  # macOS
            subprocess.run(['brew', 'install', 'fossil'], check=True)
        elif system == 'windows':
            print("Please download and install Fossil from https://fossil-scm.org/home/uv/download.html")
            sys.exit(1)
        else:
            print(f"Unsupported operating system: {system}")
            sys.exit(1)

    def initialize_fossil(self):
        if not self.check_fossil_installation():
            print("Fossil is not installed. Attempting to install...")
            self.install_fossil()

        if not os.path.exists(self.fossil_dir):
            os.makedirs(self.fossil_dir)
        
        fossil_file = os.path.join(self.fossil_dir, 'repo.fossil')
        subprocess.run(['fossil', 'init', fossil_file], check=True)
        subprocess.run(['fossil', 'open', fossil_file], cwd=self.project_path, check=True)

    def commit_all_files(self, message="Initial commit"):
        subprocess.run(['fossil', 'add', '.'], cwd=self.project_path, check=True)
        subprocess.run(['fossil', 'commit', '-m', message], cwd=self.project_path, check=True)

    def commit_changes(self, message):
        subprocess.run(['fossil', 'commit', '-m', message], cwd=self.project_path, check=True)

    def list_commits(self):
        result = subprocess.run(['fossil', 'timeline'], cwd=self.project_path, capture_output=True, text=True, check=True)
        return result.stdout

    def revert_to_commit(self, commit_hash):
        subprocess.run(['fossil', 'update', commit_hash], cwd=self.project_path, check=True)

    def create_git_commit(self, message):
        # This function assumes git is initialized in the project directory
        subprocess.run(['git', 'add', '.'], cwd=self.project_path, check=True)
        subprocess.run(['git', 'commit', '-m', message], cwd=self.project_path, check=True)

# Example usage:
# fv = FossilVersioning('/path/to/your/project', github_token='your_github_token')
# fv.initialize_fossil()
# fv.commit_all_files("Initial commit")
# fv.commit_changes("Agent made some changes")
# print(fv.list_commits())
# fv.revert_to_commit("abc123")
# fv.create_git_commit("Integrate agent changes")
# fv.create_git_pr("agent-changes", "Integrate latest agent changes", "This PR integrates the latest changes made by the agent.", "repo_owner", "repo_name")
