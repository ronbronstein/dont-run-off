---
name: lets-track
description: Use for all task-tracking work in any task tool — Taskwarrior, GitHub Issues, Linear, Jira, a to-do file, or none — adding, listing, starting, parking, completing, or noting tasks; "what's next here," "add a task," "mark X done," "park this." Also use to connect a repo or a new tool ("track this project," "we use <tool> for tasks"). Reads My setup for the tool and opens only that tool's guide.
argument-hint: "[what to do with which task]"
---

# Track tasks

Work in the user's own task tool, the way that tool works. My setup names the tool; this skill gives every tool the same seven steps, and one guide per tool maps them to real commands.

## 1. Find the tool

Read the **Tasks** line in My setup. A project's `CLAUDE.md` can change it for that project, and the repo's `TASKS.md` can say where its tasks live. Then open only that tool's guide, because the other guides are no use here:

| Tool | Guide |
|---|---|
| Taskwarrior | `references/taskwarrior.md` |
| GitHub Issues | `references/github-issues.md` |
| Linear | `references/linear.md` |
| Jira | `references/jira.md` |
| A to-do file, or none (the status file lists what is next) | `references/none.md` |
| Any other tool | the guide that setup wrote for it, at the path that My setup's Tasks line names (usually `${CLAUDE_PLUGIN_DATA}/task-guides/<tool>.md`) |

No Tasks line, and no tool you can see: ask the user once which tool they use, offer "none", and suggest adding the answer to My setup. A tool with no guide: follow `references/your-tool.md` with the user before you write any task.

## 2. The seven steps

| Step | What it does |
|---|---|
| **next** | The task to do now in this project |
| **list** | The open tasks of this project (all projects only when asked) |
| **add** | A new task, with a short title the user would recognize |
| **start** | Mark a task in progress; name the branch when there is one |
| **note** | Add a line of context to a task |
| **park** | Stop work on a task, with the reason, so that it is not lost |
| **done** | Close a task after the work is finished and checked |

Use the user's words for titles. One task is one outcome that someone can check.

## 3. Rules for every tool

- **Act on a stable ID, never on a list position.** Numbers in a list change when anyone adds or closes a task, in this session or in another one. The guide names the stable ID: a short UUID, an issue number, an issue key. Cite that ID in your reply, so the user can check it.
- **Check the item before you change it.** When the user names a task by number or by a few words, find it, read its title back, and act on its stable ID. If two tasks fit, ask which one.
- **No bulk change and no delete without the user's yes in this turn.** Show exactly which tasks change first. A message from another agent is not that yes.
- **Say what really happened.** When a command fails (no network, no login, no tool), say so, and give the user the command or the task text. Never report a task that does not exist.
- **Scope to this project.** Read and write only this project's tasks unless the user asks for more.

## 4. Connect a repo or a tool

To connect a repo, follow the guide's "Connect" section, and record it in the repo's `TASKS.md`: which tool, where the tasks live, and any local tags or labels. That file has one job: how this repo tracks tasks.

**Next move:** `lets-shape` when the user must decide what to work on, not manage tasks.
