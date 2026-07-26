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

- **`DECISIONS.md`** — append what was decided and why, any deviations from the plan (with the reason), and any open questions. Deviations especially: an undocumented deviation is how a project quietly becomes something nobody chose.
- **`current-state.md`** — rewrite it so it describes reality *now*, not the plan from three sessions ago. If a phase finished, say so. If something was abandoned, remove it rather than leaving it looking active.
- **Task tool** — close what's done, add what surfaced.

Don't just append. Read what's there and correct anything that's now false.

## 3. Check the always-on layer didn't go stale

If this session changed how the project works — a new convention, a renamed directory, a build command that's different now — then the project's `AGENTS.md` / `CLAUDE.md` may now be lying to every future session. Flag it, and offer to fix it.

Cheap here, expensive later: wrong always-on instructions are worse than none, because they get confidently applied to everything.

## 4. Capture open threads

List what's unfinished, and name the single best **next step** — specific enough that a future session (or the `catchup` skill) can resume without re-deriving context.

## 5. Save the work

Commit if in a repo, or save/export for knowledge work, following the user's convention. Say what you committed.

## 6. Leave a breadcrumb

One line at the top of `current-state.md`: **"Next session starts here → …"**

Keep the whole thing tight. The user should be able to walk away and come back in two weeks without losing the thread.
