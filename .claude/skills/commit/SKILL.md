---
name: commit
description: Commit only task-related changes (Claude's + user's) with repo commit conventions. Use when the user asks to commit.
user-invocable: true
disable-model-invocation: true
allowed-tools: Bash, Read, Grep, Glob
---

# Commit

Create a commit containing only the changes you made, plus any related changes the user made as part of the same task or issue. Exclude unrelated modifications in the working tree.

## Steps

1. Run `git status` (never use `-uall`) and `git diff` to see all staged and unstaged changes.
2. Run `git log --oneline -5` to see recent commit message style.
3. Identify which files are **in scope** — files you changed, plus any user-modified files that are clearly part of the same task/issue being addressed. If unsure whether a user change is related, ask.
4. Stage only in-scope files using `git add <file1> <file2> ...`. Never use `git add -A` or `git add .`.
5. Write a commit message following the repo conventions:
   - **Format**: `<type>: <Short description>`
   - **Types**: `feat` (new feature), `fix` (bug fix), `chore` (maintenance), `wip` (work in progress)
   - **Body**: If the commit touches multiple concerns, add a bullet list explaining each change.
   - Keep the title under 72 characters.
6. Commit using a HEREDOC for the message. Append `Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>`.
7. Run `git status` after committing to verify success.

## Rules

- Do NOT push unless the user explicitly asks.
- Do NOT amend existing commits unless the user explicitly asks.
- Do NOT commit files that may contain secrets (`.env`, credentials, tokens).
- If a pre-commit hook fails, fix the issue and create a NEW commit — do not amend.
