# GitHub Issues

Tasks are issues in the repo's GitHub project, through the `gh` command. The store is remote and shared, so parallel copies of the repo see the same list. It needs `gh` and a network.

## Before the first command

- `command -v gh`: when it finds nothing, `gh` is not installed. Tell the user how to install it (https://cli.github.com) and stop; do not ask them to log in yet.
- `gh auth status`: when it fails, tell the user to run `gh auth login` themselves (type `! gh auth login` in Claude Code). Do not try to log in for them.
- The repo: `gh repo view --json nameWithOwner` from the repo folder. A repo whose `TASKS.md` names another repo: pass `--repo owner/name` on every command.

## The stable ID: the issue number

An issue number (`#12`) never changes. Cite it with the title, for example "#12 Fix the crash on an empty note".

## The seven steps

| Step | Command |
|---|---|
| next | `gh issue list --label next --state open --json number,title`, else the oldest open issue assigned to the user |
| list | `gh issue list --state open --json number,title,labels,assignees` |
| add | `gh issue create --title '<title>' --body '<one or two lines of context>'` |
| start | `gh issue edit <n> --add-assignee @me --add-label 'in progress'`, then `gh issue comment <n> --body 'Started on branch <branch>'` |
| note | `gh issue comment <n> --body '<text>'` |
| park | `gh issue edit <n> --remove-label 'in progress' --add-label parked`, then `gh issue comment <n> --body 'Parked: <reason>'` |
| done | `gh issue close <n> --comment '<what was done>'`, or let the merged pull request close it ("Fixes #<n>") |

Create a label the first time you need it only after the user says yes: labels are visible to everyone on the repo. Without a network or a login, the command fails: say so, and give the user the exact command and the issue text.

## Connect a repo

Write `TASKS.md`: "Tool: GitHub Issues in `<owner/repo>`", and the labels this repo uses.
