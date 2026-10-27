# Make it yours

Everything personal lives under the method block in your `CLAUDE.md`. `lets-set-up` fills it in for you, and you can change it in plain words at any time. An upgrade replaces only the method block, between its markers. It never touches what is below.

## Who you're working with

```markdown
**Altitude.** Product director. I care about the decision and the
trade-offs, not line-by-line mechanics.

**Conventions.** Python for scripts, plain HTML/JS for small web tools.
Failing test first. Never change an object in place.

**My frictions.** It runs off before I agree to anything.
I can't tell what it actually did. I lose the thread between sessions.
```

- **Altitude** sets how deep the agent goes when it explains.
- **Conventions** hold your stack, your testing bar, and your house style. They are not in the method on purpose: they are true for you, not for everyone.
- **My frictions** is the line that does the most. When you name what usually goes wrong, the agent watches for it. It is also the line that people leave empty, so setup asks you for it.

## My setup

This is how the harness fits your workflow, in plain words, not in a config file:

```markdown
## My setup
- Status file: `docs/STATUS.md`
- Decision log: none. Decisions go in the status file, under "Decided".
- Tasks: GitHub Issues in this repo
- Language: plain
- Stop level: fast. Stop only before steps that are hard to undo or that others see.
- Version control: Git. Commit as you go, one logical change per commit.
- Work branch: `staging`. Parallel copies: off.
```

Every move reads these lines. It does not guess a file name, a task tool, how careful to be, or how to write to you.

| Line | What it changes |
|---|---|
| Status file, Decision log | Which files hold the thread. "none" says where that content goes instead. |
| Tasks | Which task tool `lets-track` and the other moves use. |
| Language | The language and the level of the replies: strict STE, 80% STE, plain, or technical. Replies come in the language you write in. For English, the default is strict [ASD-STE100 Simplified Technical English](https://www.asd-ste100.org/): short sentences and one meaning for each word. |
| Stop level | How often the agent stops: careful, standard (the default), or fast. |
| Version control, Work branch | How the work is saved, and where. |

A project's own `CLAUDE.md` can repeat a line to change it for that project only.

## A new project

[`templates/`](../templates/) has the record files, ready to copy: `current-state.md`, `DECISIONS.md`, `TASKS.md`, and a project `CLAUDE.md`.

[← Back to the README](../README.md)
