---
name: taskwarrior
description: Use for ALL Taskwarrior work in any repo — adding, listing, completing, or editing tasks, "what's next here," "add a task," "mark X done" — AND for first-time setup or binding a repo to a namespace ("set up taskwarrior here," "track this project"). Also use to explain what Taskwarrior is and whether it's worth adopting. Resolves the project namespace from the repo and scopes every command explicitly.
---

# Taskwarrior

## What it is (explain this before recommending it)

Taskwarrior is a free, open-source task manager that lives entirely on the command line. There's no account, no web app, and no server — your tasks are a local file on your own machine, and nothing leaves it.

**Why it suits agents better than Jira or Linear:** an agent can query it directly from the shell and get back stable JSON. That means the agent reasons over your *actual* task list instead of guessing, scraping a web UI, or needing an API token. It's fast, scriptable, and it works offline.

**When not to use it:** if you work with a team that already lives in a shared tracker, use that instead — a private local list nobody else can see is worse than a clunky shared one. Taskwarrior is for solo work and personal project tracking.

Install: `brew install task` (macOS) or `apt install taskwarrior` (Debian/Ubuntu).

## The model

One global store at `~/.task`. Projects are isolated by **namespace**, not by separate data files: `project:<ns>`. This gives you a single inbox and lets tasks relate across projects, while every command stays scoped to one project.

## 1. Resolve the namespace first — every invocation

```bash
ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
```

1. `$ROOT/TASKS.md` exists → read it. If it maps several sub-folders to namespaces, pick the one for the folder you're actually working in.
2. Else `$ROOT/.taskproject` → first line is the namespace.
3. Else the repo is unbound → derive a candidate (`basename $ROOT`, lowercased), tell the user, and offer setup (§4).

**Never invent a namespace and start writing tasks into it.**

## 2. The iron rule: scope explicitly

Every read and every write passes `project:<ns>` on the command line. Do **not** rely on `task context` — that's a human convenience, and it's ambient state you can't see. Being explicit is what makes one shared store safe.

## 3. Daily operations

Always scope with `project:<ns>`. **Reason over `export` JSON, not the pretty table** — the table truncates and reorders.

```bash
task project:<ns> +next next                  # what's next here
task project:<ns> status:pending export       # full open list, as JSON
task add project:<ns> "description" +next due:fri priority:H
task <id> modify due:mon +blocked
task <id> annotate "ref: <url>"
task <id> done
task <uuidA> modify depends:<uuidB>           # relate tasks, even across projects
```

**IDs renumber.** Before any `done`, `modify`, or `delete`, confirm the ID resolves to the task you mean — verify by description or UUID first.

`task <project>` lists from pending by default, so a project whose tasks are all complete looks like it doesn't exist. For a true inventory use `task project:<ns> status.any: export`.

### Naming and tags

A namespace is a dotted path: `<area>.<project>[.<sub>]`. Areas are yours to choose — pick a handful and keep them stable. Common starting sets: `work` / `personal` / `learning`, or `client` / `internal` / `side`.

Universal tags: `+next` (queued to do now), `+blocked`, `+waiting` (on someone else), `+backlog` (deferred — don't invent a second "deferred" tag or a backlog namespace). Project-specific tags get declared in that repo's `TASKS.md`.

## 4. Setup / bind a new repo

```bash
echo "<area>.<slug>" > "$ROOT/.taskproject"
```

Then write `$ROOT/TASKS.md` so a future session — or a different agent — can resolve the namespace without asking:

```markdown
# Tasks — <project name>

**Namespace:** `<area>.<slug>`

Scope every command explicitly: `task project:<area>.<slug> ...`

## Local tags
- `+<tag>` — what it means here
```

For a repo holding several projects, use a table instead:

| folder | namespace | notes |
|---|---|---|

## 5. Safety

- **Never** run `delete`, `purge`, or a bulk `modify` without first showing exactly which tasks change and getting confirmation **in this turn**.
- Don't edit `~/.taskrc` or contexts without asking.
- Never set a per-repo `data.location` or `$TASKDATA`. One store, always.

## Quick reference

| Want | Command |
|---|---|
| Next here | `task project:<ns> +next next` |
| Open here (parseable) | `task project:<ns> status:pending export` |
| Add | `task add project:<ns> "…" +next` |
| Complete | `task <id> done` |
| Relate | `task <uuidA> modify depends:<uuidB>` |
| True inventory | `task project:<ns> status.any: export` |
