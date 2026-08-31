---
name: wrap-session
description: Use when ending or pausing a work session — "let's wrap up," "I'm stopping for today," "end the session," "save where we are," "that's it for now." Closes a session cleanly so nothing is lost, and leaves the project's record files accurate so the next session starts instantly. The bookend to starting a session.
---

# Wrap Session

Close a session so nothing evaporates and the next start is instant. Do this in order.

## 1. Recap

In plain language: what got done this session, and the key decisions made — with the reason for each, not just the choice.

## 2. Leave the record true

This is the part that matters most, and the part most often skipped. **A session that ends with a stale `current-state.md` breaks the next session before it starts.**

**One fact, one home.** Writing the same session into two files is how records rot: each copy then
goes stale on its own schedule, and a future session can't tell which one is lying.

| File | What it holds | How it's written |
|---|---|---|
| `current-state.md` | **Only what is true right now** — where we are, the next action, open blockers | **Rewritten** each session. Capped. |
| `DECISIONS.md` | What was decided and why, deviations with their reason, session narrative | **Appended**, newest first. Never rewritten. |
| Task tool | Tasks, defects, open questions, backlog | Updated in place |

- **`DECISIONS.md`** — append what was decided and why, any deviations from the plan (with the reason), and any open questions. Deviations especially: an undocumented deviation is how a project quietly becomes something nobody chose. **This is where narrative goes.** If you want to tell the story of the session, tell it here and nowhere else.
- **`current-state.md`** — rewrite it so it describes reality *now*, not the plan from three sessions ago. If a phase finished, say so. If something was abandoned, remove it rather than leaving it looking active.
- **Task tool** — close what's done, add what surfaced.

Don't just append. Read what's there and correct anything that's now false.

### Keep the snapshot small, on purpose

`current-state.md` is a snapshot, not a journal. **It has a size cap** — the project's own
always-on file should state it; if it doesn't, use ~150 lines and say so.

**Before you finish, check the length.** If it's over the cap, you must prune it, not extend it:

1. Anything that is narrative — what happened, in what order, who said what — **belongs in
   `DECISIONS.md`.** Move it, or simply delete it if that session already has an entry there.
2. Anything that is a timeless constraint — a gotcha, a landmine, "never do X" — belongs in the
   project's constraints file (`traps.md`, `gotchas.md`, whatever it's called), not here.
3. What's left should be: current position, next action, open blockers, and pointers.

**A snapshot nobody prunes stops being a snapshot.** It becomes an append-only log with the newest
entry on top, and every session pays to read the whole thing — while the older layers quietly start
contradicting the newer ones inside the same file. Pruning is part of wrapping, not a separate
cleanup task for later.

## 3. Check the always-on layer didn't go stale

If this session changed how the project works — a new convention, a renamed directory, a build command that's different now — then the project's `AGENTS.md` / `CLAUDE.md` may now be lying to every future session. Flag it, and offer to fix it.

Cheap here, expensive later: wrong always-on instructions are worse than none, because they get confidently applied to everything.

## 4. Capture open threads

List what's unfinished, and name the single best **next step** — specific enough that a future session (or the `catchup` skill) can resume without re-deriving context.

## 5. Save the work

Commit if in a repo, or save/export for knowledge work, following the user's convention. Say what you committed.

## 6. Leave a breadcrumb

One line at the top of `current-state.md`: **"Next session starts here → …"**

**Replace the old breadcrumb. Do not stack a new one above it.** Stacked breadcrumbs are how a
one-line pointer becomes a thousand-line archive — each one was true when written, so nobody ever
deletes one, and the file grows forever. There is exactly one breadcrumb, and it is about this
moment.

Keep the whole thing tight. The user should be able to walk away and come back in two weeks without losing the thread.
