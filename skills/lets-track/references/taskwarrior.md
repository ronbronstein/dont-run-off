# Taskwarrior

Taskwarrior is a free task manager on the command line. Tasks are a local file on the user's machine: no account, no server. An agent can read it as JSON, so it reasons over the real list. It suits solo work; a team that already shares a tracker should keep that tracker. Install: `brew install task` (macOS) or `apt install taskwarrior` (Debian, Ubuntu).

## The model

One store for all projects (`~/.task`). Projects are kept apart by name: `project:<area>.<project>`, for example `project:work.website`. Never set a per-repo `data.location` or `TASKDATA`: one store, always.

## Find this repo's project name

Do this before each read or write.

```bash
ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
```

1. `"$ROOT/TASKS.md"` exists: read the project name there. When it maps sub-folders to names, use the one for the folder you work in.
2. Else `"$ROOT/.taskproject"`: its first line is the name.
3. Else the repo is not connected: propose a name (`<area>.<folder name>`), tell the user, and follow "Connect" below. Never invent a name and start writing tasks into it.

## The stable ID: the short UUID

Task numbers change every time a task is added or closed, in any session. So read tasks as JSON and act on the first 8 characters of the `uuid` field:

```bash
task project:"$NS" status:pending export        # read: JSON with uuid, description, status
task 5e4c8a10 done                               # act: by short UUID, never "task 2 done"
```

When the user names a task by number ("task 2"), treat the number as a hint: find the task, read its description back, and act on its UUID. Cite the short UUID in your reply.

## The seven steps

Pass `project:"$NS"` on every read and every write. Do not rely on `task context`: it is hidden state.

| Step | Command |
|---|---|
| next | `task project:"$NS" +next status:pending export`, else the most urgent pending task |
| list | `task project:"$NS" status:pending export` |
| add | `task add project:"$NS" 'Short title'` (single quotes: zsh expands `$` and `!` in double quotes) |
| start | `task <uuid8> start` and `task <uuid8> annotate 'branch: <branch>'` |
| note | `task <uuid8> annotate 'text'` |
| park | `task <uuid8> stop`, `task <uuid8> modify +blocked`, `task <uuid8> annotate 'parked: <reason>'` |
| done | `task <uuid8> done` |

Read the JSON, not the table: the table cuts and reorders. A project whose tasks are all done looks empty in `task <project>`; for everything use `task project:"$NS" status.any: export`.

## Tags

`+next` (to do now), `+blocked`, `+waiting` (on someone else), `+backlog` (later). Do not invent another "later" tag or a backlog project. Tags that only one repo uses go in its `TASKS.md`.

## Connect a repo

```bash
echo "<area>.<slug>" > "$ROOT/.taskproject"
```

Then write `$ROOT/TASKS.md`, so that a later session, or another agent, finds the name without asking:

```markdown
# Tasks — <project name>

Tool: Taskwarrior. Project: `<area>.<slug>`.

Scope every command: `task project:<area>.<slug> ...`

## Local tags
- `+<tag>` — what it means here
```

## Safety

- No `delete`, `purge`, or bulk `modify` before you show exactly which tasks change and the user says yes in this turn.
- Do not edit `~/.taskrc` or contexts without asking.
