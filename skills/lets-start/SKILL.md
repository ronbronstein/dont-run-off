---
name: lets-start
description: Use at the very start of a work session to orient and route before doing anything. Reads where things stand — recent history, open tasks, project status — names the session type, and picks the right next move. Trigger on "let's start," "begin," "what should we do today," or the first substantive message of a session on a new or existing project.
---

# Start a Session

Orient first, then pick the move. A session that starts from the records does not repeat old work or undo old decisions.

## 0. Answer first

If the user's first message holds a question, answer it in the first lines. Then give the frame. A user who asked something and got a status report feels unheard.

## 1. Orient

Read in this order, and stop when you know enough to name the next move:

1. **The status file** (My setup names it; default `current-state.md`): the live north star and "what's next."
2. **The last entry of the decision log:** what was decided most recently, and anything left open.
3. **Open tasks** in the task tool that My setup names: what is queued as next.
4. **Recent history**, when the project uses git: `git log --oneline -10`, the current branch, and uncommitted work. With no version control, the newest changed files stand in for it.

A new or empty project has none of these: say so, and route to "New".

## 2. Name the session type

- **New** — no north star yet → shape it first (the `lets-shape` skill), or go straight to design if the goal is already clear.
- **Existing · pick work** → recommend one next move, with its reason, and name the runner-up and why it lost. Show only those two; the user can ask for the rest.
- **Existing · resume** → a slice is in progress, and its plan has the user's nod from an earlier session → say in two or three lines where we are and what comes next, then continue it. That nod still covers the plan. Stop first only when the records show that the plan changed, or that a choice is still open.
- **Rush** — the user says they are short of time and names a target → skip the frame. Reply in 5 lines or fewer: your assumptions (1–3 lines), the first move, and "Go?". No runner-up, no options, no teaching, and no other questions: a decision that can wait comes after the first move. A list of questions costs the time they do not have.
- **Fuzzy · explore** → offer `lets-blindspot`, `lets-align`, or `lets-explore`.
- **Clear ask** — the first message names the work, and there is one obvious way to do it → the request is the nod. Say in a line what you found that matters, then do the work under the one rule and the stop level in My setup.

## 3. State the frame

Not for a rush or a clear ask (above). One short paragraph: the project, the session type, the current slice or goal, what "done" looks like, and what is not in scope. For new work or a pick of work, propose the first move and wait for the nod: choosing the work is a direction choice. For a resume, the frame is the start of the work.

**Next move:** the one the frame names: `lets-shape` for new work, `lets-catch-up` to resume, `lets-blindspot`, `lets-align` or `lets-explore` when the ask is fuzzy.
