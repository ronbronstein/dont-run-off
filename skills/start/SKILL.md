---
name: start
description: Use at the very start of a work session to orient and route before doing anything. Reads where things stand — recent history, open tasks, project status — names the session type, and picks the right next move. Trigger on "let's start," "begin," "what should we do today," or the first substantive message of a session on a new or existing project.
---

# Start a Session

Orient first, then route — don't dive into building.

## 0. Answer first

If the user's first message holds a question, answer it in the first lines. Then give the frame. A user who asked something and got a status report feels unheard.

## 1. Orient

Read in this order, and stop when you know enough to name the next move:

1. **The status file** (My setup names it; default `current-state.md`): the live north star and "what's next."
2. **The last entry of the decision log:** what was decided most recently, and anything left open.
3. **Open tasks** in the task tool that My setup names: what is queued as next.
4. **Recent history:** `git log --oneline -10`, the current branch, and uncommitted work.

A new or empty project has none of these: say so, and route to "New".

## 2. Name the session type

- **New** — no north star yet → shape it first (the `shaping` skill), or go straight to design if the goal is already clear.
- **Existing · pick work** → recommend one next move, with its reason, and name the runner-up and why it lost. Show only those two; the user can ask for the rest.
- **Existing · resume** → a slice is mid-flight → catch up: where we are, what's in progress, next step.
- **Fuzzy · explore** → offer `blindspot`, `lets-align`, or `directions`.

## 3. State the frame and wait

One tight paragraph: the project, the session type, the current slice/goal, what "done" looks like, and what's NOT in scope. Propose the first move and **wait for a nod** before executing.

**In a rush:** when the user says they are short of time and names a target, do not interview them. State your assumptions in 1–3 lines, propose the first move, and ask only for a yes. A list of questions costs the time they do not have.
