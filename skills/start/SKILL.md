---
name: start
description: Use at the very start of a work session to orient and route before doing anything. Reads where things stand — recent history, open tasks, project status — names the session type, and picks the right next move. Trigger on "let's start," "begin," "what should we do today," or the first substantive message of a session on a new or existing project.
---

# Start a Session

Orient first, then route — don't dive into building.

## 1. Orient
- **Read in the project's own order first.** If the always-on file (`CLAUDE.md` / `AGENTS.md`) names a
  read-first order, follow it exactly — it exists because someone learned the hard way what a cold
  start misses.
- **Project state:** established or new/empty? Look for version control, a task list, and a status / "current state" doc.
- **History:** recent changes, current branch, anything in flight.
- **Tasks:** what's queued / "next," using the user's task tool.
- **Status doc:** the live north star / "what's next."
- **Constraints:** if the project keeps a traps / gotchas file, read it **before** anything that
  spends money, pushes, or touches a recorded fixture. Those files exist because the constraint was
  not guessable from the code.

### Check the record isn't lying before you trust it

Records rot quietly, and a stale record breaks the session more thoroughly than no record. Spend
thirty seconds on these, and **say so out loud** if one trips:

- **Is the snapshot over its cap?** A `current-state.md` that has become a journal means nobody has
  pruned it, so its older layers are probably contradicting its newer ones.
- **Does it contradict itself?** Two different "last session" markers, two different test counts, two
  different next actions — take the most recent and flag the rest.
- **Does it claim something checkable?** Test counts, "everything is pushed", "X is done" — verify the
  cheap ones (`git status -sb`, run the tests) rather than inheriting them.
- **Are any advertised files dead?** A log the always-on file points at, whose last entry is weeks
  old, is worse than no log — it will be trusted.

Report what you found before proposing work. Fixing the record can be the session.

## 2. Name the session type
- **New** — no north star yet → shape it first (the `shaping` skill), or go straight to design if the goal is already clear.
- **Existing · pick work** → rank candidates, recommend one + the runner-up.
- **Existing · resume** → a slice is mid-flight → catch up: where we are, what's in progress, next step.
- **Fuzzy · explore** → offer `blindspot`, `lets-align`, or `directions`.

## 3. State the frame and wait
One tight paragraph: the project, the session type, the current slice/goal, what "done" looks like, and what's NOT in scope. Propose the first move and **wait for a nod** before executing.
