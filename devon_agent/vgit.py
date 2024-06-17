"""
When the agent makes changes to the codebase, all changes should be commited to a branch that only the agent should use. This will allow the diffs to be separated while user will not notice any changes. Another important thing is it allows from the agent to be restarted without it being confused by changes made after the previous session and before the restarted session.
Some Invariants:
- The users branch/workspace should remain unchanged at all times. No files should be added, removed, staged or committed.
- Any changes added to the agent branch should not deleted or affect the agent branche's history, any commits added to it from its existing state to the new backup state the diffs should be re computed


Algorithm (w git commands [will look different with PyGit])
- Agent writes diff
- create agent branch if doesnt exist or reuse old one
- stash push changes (git stash -u we want to stash untracked files possible even --keep-index )
- checkout branch
- stash apply
- commit
- checkout to original branch
- stash pop

GitPython Algorithm
TBD ...

agent branch naming convention: [agent-name]-[original-branch]-[base-commit-hash]

Lifecycle

Setup
- If there is no history stored, proceed
- checkout base commit
- recreate branch
- apply all diffs
- compute diff between user branch and and applied diffs
- give the agent the computed diff as an interrupt

Teardown
- get all the diffs involved in the branch (w commit information ideally)
- store branch name, base commit, base branch
"""

import fnmatch
import os

from devon_agent.environment import EnvironmentModule, LocalEnvironment
from devon_agent.tool import ToolContext


def get_git_root(ctx: ToolContext):
    output, rc = ctx["environment"].execute("git rev-parse --show-toplevel")
    if rc != 0:
        raise Exception("Failed to get git root")
    return output.strip()


def find_gitignore_files(ctx: ToolContext):
    gitignore_paths = []
    git_root = get_git_root(ctx)

    if git_root:
        current_dir = ctx["environment"].execute("pwd")[0].strip()

        while current_dir.startswith(git_root):
            gitignore_path = os.path.join(current_dir, ".gitignore")
            if os.path.isfile(gitignore_path):
                gitignore_paths.append(gitignore_path)
            current_dir = os.path.dirname(current_dir)

    return gitignore_paths


def get_or_create_repo(env: EnvironmentModule, repo_path):
    """
    Get the existing git repository at the given path or initialize a new one if it doesn't exist, using the provided environment module.

    Args:
    env (EnvironmentModule): The environment module to execute git commands.
    repo_path (str): The file system path to the repository.
    """

    # Check if the directory at repo_path is a git repository using the environment module
    result = env.execute(f"cd {repo_path} && git rev-parse --is-inside-work-tree")[0]
    if "true" in result.strip():
        print("Repository found at:", repo_path)
    else:
        print("No git repository at:", repo_path)
        # env.execute(f'mkdir -p {repo_path}')
        env.execute(f"cd {repo_path} && git init")
        print("Initialized a new git repository at:", repo_path)


def simple_stash_and_commit_changes(
    env: EnvironmentModule, branch_name, commit_message
):
    current_branch = env.execute("git rev-parse --abbrev-ref HEAD")[0].strip()
    branch_name = f"{branch_name}"

    # Stash changes (including untracked files)
    _, rc = env.execute("git stash push")
    if rc != 0:
        raise Exception("Failed to stash changes")

    commit_hash = None

    try:
        # Checkout the specified branch
        # check if branch exists
        _, rc = env.execute(f"git rev-parse --verify {branch_name}")
        if rc == 0:
            _, rc = env.execute(f"git checkout {branch_name}")
        else:
            _, rc = env.execute(f"git checkout -b {branch_name}")
        if rc != 0:
            raise Exception("Failed to checkout branch")

        # Apply the stashed changes
        _, rc = env.execute("git stash apply")
        if rc != 0:
            raise Exception("Failed to apply stashed changes")

        # Stage all files
        _, rc = env.execute("git add $(git rev-parse --show-toplevel)")
        if rc != 0:
            raise Exception("Failed to stage all files")

        # Commit the changes
        _, rc = env.execute(f"git commit -m '{commit_message}'")
        if rc != 0:
            raise Exception("Failed to commit changes")

        # Get the commit hash
        commit_hash = env.execute("git rev-parse HEAD")[0].strip()

    finally:
        # Checkout the original branch
        _, rc = env.execute(f"git checkout {current_branch}")
        if rc != 0:
            raise Exception("Failed to checkout original branch")

        # Pop the stash
        _, rc = env.execute("git stash pop")
        if rc != 0:
            raise Exception("Failed to pop stash")

    return commit_hash


def stash_and_commit_changes(env: EnvironmentModule, branch_name, commit_message):
    # Get the current branch
    current_branch = env.execute("git rev-parse --abbrev-ref HEAD")[0].strip()
    branch_name = f"{branch_name}"

    # Stash changes (including untracked files)
    _, rc = env.execute("git stash push --include-untracked")
    if rc != 0:
        raise Exception("Failed to stash changes")

    commit_hash = None

    try:
        # Checkout the specified branch
        # check if branch exists
        _, rc = env.execute(f"git rev-parse --verify {branch_name}")
        if rc == 0:
            _, rc = env.execute(f"git checkout {branch_name}")
        else:
            _, rc = env.execute(f"git checkout -b {branch_name}")
        if rc != 0:
            raise Exception("Failed to checkout branch")

        # Apply the stashed changes
        _, rc = env.execute("git stash apply")
        if rc != 0:
            raise Exception("Failed to apply stashed changes")

        # Stage all files
        _, rc = env.execute("git add $(git rev-parse --show-toplevel)")
        if rc != 0:
            raise Exception("Failed to stage all files")

        # Commit the changes
        _, rc = env.execute(f"git commit -m '{commit_message}'")
        if rc != 0:
            raise Exception("Failed to commit changes")

        # Get the commit hash
        commit_hash = env.execute("git rev-parse HEAD")[0].strip()

    finally:
        # Checkout the original branch
        _, rc = env.execute(f"git checkout {current_branch}")
        if rc != 0:
            raise Exception("Failed to checkout original branch")

        # Pop the stash
        _, rc = env.execute("git stash pop")
        if rc != 0:
            raise Exception("Failed to pop stash")

    return commit_hash


# Function to get all commits in a specified branch using environment module
def get_all_commits_in_branch(env: EnvironmentModule, repo_path: str, branch_name: str):
    """
    Retrieve all commits from a specified branch in the repository using the environment module.

    Args:
    env (EnvironmentModule): The environment module to execute git commands.
    repo_path (str): The file system path to the repository.
    branch_name (str): The name of the branch to retrieve commits from.

    Returns:
    list: A list of commit hashes from the specified branch.
    """
    # Navigate to the repository path and list all commits in the branch
    original_path = env.execute("pwd")[0].strip()
    env.execute(f"cd {repo_path}")
    commit_list = env.execute(f'git log {branch_name} --pretty=format:"%H"')[
        0
    ].splitlines()
    env.execute(f"cd {original_path}")
    return commit_list


def get_commit_diffs_in_udiff_format(env: EnvironmentModule, commit_sha: str):
    """
    Retrieve the diffs for a specific commit in unified diff format.

    Args:
    repo (git.Repo): The repository object.
    commit_sha (str): The SHA of the commit to retrieve diffs for.

    Returns:
    str: A string containing the unified diff of the specified commit.
    """
    # Navigate to the repository path and retrieve the unified diff for the specified commit
    # original_path = env.execute('pwd')[0].strip()
    # env.execute(f'cd {repo_path}')
    diff_output = env.execute(f"git diff {commit_sha}^ {commit_sha} --unified")[0]
    # env.execute(f'cd {original_path}')
    return diff_output


def make_new_branch(env: EnvironmentModule, branch_name):
    output, rc = env.execute(f"git checkout -b {branch_name}")
    if rc != 0:
        raise Exception("Failed to create new branch", output)
    return branch_name


def get_current_diff(env: EnvironmentModule):
    """
    Retrieve the diffs for a specific commit in unified diff format.
    """
    # Get the current commit hash
    current_branch = env.execute("git rev-parse --abbrev-ref HEAD")[0].strip()

    env.execute(f"git branch -D agent-commit-{current_branch}")
    commit = stash_and_commit_changes(env, "agent-commit", "agent commit")
    diff = get_commit_diffs_in_udiff_format(env, commit)
    # delete branch agent-commit
    env.execute(f"git branch -D agent-commit-{current_branch}")
    return diff


def combine_diffs(env: EnvironmentModule, diff1_path, diff2_path, output_path):
    env.execute(f"combinediff {diff1_path} {diff2_path} > {output_path}")


def subtract_diffs(env: EnvironmentModule, diff1_path, diff2_path, output_path):
    env.execute(f"interdiff {diff1_path} {diff2_path} > {output_path}")


def safely_revert_to_commit(
    env: EnvironmentModule, commit_to_revert: str, commit_to_go_to: str
):
    # get the diff between the two commits
    # get temp file
    temp_file = env.execute("mktemp")[0].strip()
    env.execute(f"git diff {commit_to_revert} {commit_to_go_to} > {temp_file}")
    files = env.execute(f"git diff {commit_to_revert} {commit_to_go_to} --name-only")[
        0
    ].splitlines()
    print(env.execute(f"cat {temp_file}"))
    env.execute(f"git apply {temp_file}")

    env.execute(f"rm {temp_file}")

    env.execute(f"git reset --soft {commit_to_go_to}")

    # add all files to working tree
    print(files)
    git_root = get_git_root()
    files = [os.path.join(git_root, f) for f in files]
    env.execute(f"git add {' '.join(files)}")
    print(f"git add {' '.join(files)}")


def get_last_commit(env: EnvironmentModule):
    return env.execute("git rev-parse HEAD")[0].strip()


def commit_files(env: EnvironmentModule, files, commit_message):
    _, rc = env.execute(f"git add {' '.join(files)}")
    if rc != 0:
        raise Exception("Failed to add files")
    _, rc = env.execute(f"git commit -m '{commit_message}'")
    if rc != 0:
        raise Exception("Failed to commit files")

    commit_hash = env.execute("git rev-parse HEAD")[0].strip()
    return commit_hash


def delete_last_commit(env: EnvironmentModule):
    # soft reset latest commit
    env.execute(f"git reset --soft HEAD~1")


def get_diff_last_commit(env: EnvironmentModule, files):
    return env.execute(f"git diff HEAD --" + " ".join(files))[0]


# import difflib

# def parse_diff(diff_text):
#     """ Parse a unified diff text into a structured format """
#     # This function will need to parse the diff and extract changes
#     # For simplicity, using difflib.unified_diff is a starting point
#     diff_lines = diff_text.splitlines()
#     parsed_diff = list(difflib.unified_diff(diff_lines))
#     return parsed_diff

# def combine_diffs(diff1, diff2):
#     """ Combine two diffs """
#     # This is a simplified example. Real implementation would need conflict resolution
#     combined_diff = parse_diff(diff1) + parse_diff(diff2)
#     return '\n'.join(combined_diff)

# def reverse_diff(diff):
#     """ Reverse the changes in a diff """
#     # This function should reverse the additions and deletions
#     reversed_diff = []
#     for line in diff.splitlines():
#         if line.startswith('+'):
#             reversed_diff.append('-' + line[1:])
#         elif line.startswith('-'):
#             reversed_diff.append('+' + line[1:])
#         else:
#             reversed_diff.append(line)
#     return '\n'.join(reversed_diff)

# def subtract_diffs(diff1, diff2):
#     """ Subtract diff2 from diff1 """
#     reversed_diff2 = reverse_diff(diff2)
#     return combine_diffs(diff1, reversed_diff2)


if __name__ == "__main__":
    import os

    from devon_agent.session import Session, SessionArguments

    session = Session(
        args=SessionArguments(path=os.getcwd(), user_input=None, name="dummy"),
        agent=None,
    )
    # env = LocalEnvironment(os.getcwd())
    # session.default_environment.session = session
    session.default_environment.setup(session)
    safely_revert_to_commit(
        session.default_environment,
        "415cc8021ba520bff77144e018346cce25e09d4e",
        "fae10f9c98d2eaf16ba7704418ce59a7de40b4ae",
    )
