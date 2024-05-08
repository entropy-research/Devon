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
