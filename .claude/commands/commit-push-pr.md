---
allowed-tools: Bash(git checkout --branch:*), Bash(git add:*), Bash(git status:*), Bash(git push:*), Bash(git commit:*), Bash(gh pr create:*), Bash(git log:*), Bash(git branch --show-current)
description: Commit, push, and open a PR
---

## Context

- Current git status: !`git status`
- Current git diff (staged and unstaged changes): !`git diff HEAD`
- Current branch: !`git branch --show-current`
- List of commit messages in current branch: !`git log main.. --oneline`

## Your task

Based on the above changes:
1. Create a new branch if on main
2. If there are uncommitted changes or untracked files, create a single commit with an appropriate message
3. Push the branch to origin
4. Analyze the diffs from the current branch only. Create a summary of the changes to use later.
4. Create a pull request using `gh pr create`. For the title of the PR, summarize succinctly all the commit messages of the commits in the current branch. Use the diff summary created in step 4 to be the comment text of the PR.
5. You have the capability to call multiple tools in a single response. You MUST do all of the above in a single message. Do not use any other tools or do anything else. Do not send any other text or messages besides these tool calls.