import subprocess
import os
import sys
import platform

class GitVersioning:
    def __init__(self, project_path):
        self.project_path = project_path

    def check_git_installation(self):
        try:
            subprocess.run(['git', '--version'], capture_output=True, check=True)
            return True
        except FileNotFoundError:
            return False

    def install_git(self):
        system = platform.system().lower()
        if system == 'linux':
            subprocess.run(['sudo', 'apt-get', 'update'], check=True)
            subprocess.run(['sudo', 'apt-get', 'install', '-y', 'git'], check=True)
        elif system == 'darwin':  # macOS
            subprocess.run(['brew', 'install', 'git'], check=True)
        elif system == 'windows':
            print("Please download and install Git from https://git-scm.com/downloads")
            sys.exit(1)
        else:
            print(f"Unsupported operating system: {system}")
            sys.exit(1)

    def initialize_git(self):
        if not self.check_git_installation():
            print("Git is not installed. Attempting to install...")
            self.install_git()
        
        # Check if the current directory is already a Git repository
        try:
            subprocess.run(['git', 'rev-parse', '--is-inside-work-tree'], cwd=self.project_path, check=True, capture_output=True, text=True)
            print("This directory is already a Git repository. Skipping initialization.")
            return
        except subprocess.CalledProcessError:
            # If the command fails, it means this is not a Git repository
            subprocess.run(['git', 'init'], cwd=self.project_path, check=True)
            print("Git repository initialized successfully.")

    def commit_all_files(self, message="Initial commit"):
        subprocess.run(['git', 'add', '.'], cwd=self.project_path, check=True)
        subprocess.run(['git', 'commit', '-m', message], cwd=self.project_path, check=True)

    def commit_changes(self, message):
        subprocess.run(['git', 'commit', '-am', message], cwd=self.project_path, check=True)

    def list_commits(self):
        result = subprocess.run(['git', 'log', '--oneline'], cwd=self.project_path, capture_output=True, text=True, check=True)
        return result.stdout

    def revert_to_commit(self, commit_hash):
        subprocess.run(['git', 'checkout', commit_hash], cwd=self.project_path, check=True)

    def create_branch(self, branch_name):
        subprocess.run(['git', 'checkout', '-b', branch_name], cwd=self.project_path, check=True)

    def switch_branch(self, branch_name):
        subprocess.run(['git', 'checkout', branch_name], cwd=self.project_path, check=True)

    def merge_branch(self, branch_name):
        subprocess.run(['git', 'merge', branch_name], cwd=self.project_path, check=True)

    def create_and_checkout_branch(self, branch_name):
        subprocess.run(['git', 'checkout', '-b', branch_name], cwd=self.project_path, check=True)
        print(f"Created and checked out new branch: {branch_name}")

# Example usage:
# gv = GitVersioning('/path/to/your/project')
# gv.initialize_git()
# gv.commit_all_files("Initial commit")
# gv.commit_changes("Made some changes")
# print(gv.list_commits())
# gv.revert_to_commit("abc123")
# gv.create_branch("feature-branch")
# gv.switch_branch("main")
# gv.merge_branch("feature-branch")
