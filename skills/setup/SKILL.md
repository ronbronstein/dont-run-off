---
name: setup
description: Use to install, personalize, upgrade, or repair the Don't Run Off harness — writing the method and the user's profile into their CLAUDE.md. Trigger on "set up the harness," "install don't run off," "personalize my CLAUDE.md," "upgrade the harness," or the first run after installing the plugin.
---

# Set Up the Harness

Install the always-on method into `CLAUDE.md` and personalize it. A plugin can ship skills but cannot write `CLAUDE.md` — that's this skill's job.

Two files sit next to this one: `method.md` (the method, same for everyone) and `profile.md` (the personalization template).

**Never overwrite a `CLAUDE.md` wholesale.** Someone's existing instructions are the most expensive thing in the room.

## 1. Pick the target

Ask which, unless it's obvious from what they said:

- **Global** — `~/.claude/CLAUDE.md`. How they want to be worked with everywhere. The default.
- **Project** — `./CLAUDE.md` in the current repo. Facts about *this* codebase, for everyone on it.

## 2. Read what's already there

Read the target file if it exists. Then check for `<!-- dont-run-off:method` — if present this is an **upgrade**: replace only the text between that marker and `<!-- /dont-run-off:method -->`, leave everything else exactly as it is, and skip to step 5.

Otherwise it's a fresh install. Read their existing content properly and note anything that overlaps the method — a section on how they want to be talked to, rules about planning, testing, or commits. You'll reconcile these in step 4, not silently duplicate them.

## 3. Detect, then ask only what's left

Detect from the machine — don't ask what you can check:

| Field | How to detect |
|---|---|
| Task tool | `task` on PATH → Taskwarrior. A connected Jira/Linear MCP. `TASKS.md` in the repo. Else GitHub Issues if it's a GitHub remote. |
| Version control | `git rev-parse` succeeds → Git. |
| Record files | `DECISIONS.md` / `current-state.md` already present in the repo. |
| Conventions | For a project target: the actual stack, test command, and lint setup. |

Report what you found and let them correct it: *"I see Taskwarrior and git, and no record files yet. Right?"*

Then ask what detection can't answer — **one question at a time**, not a form:

1. **Altitude.** How do they want to be talked to? Offer the examples from `profile.md` as concrete choices rather than asking an open question.
2. **Frictions.** What usually goes wrong when they work with an agent? This is the highest-value line in the whole harness and the one people skip. Don't accept a blank — offer the common ones ("it runs off before I've agreed to anything," "I can't tell what it actually did," "I lose the thread between sessions") and let them pick or add their own.
3. **Conventions.** Only if detection left it empty and they seem to have opinions. Blank is a fine answer.

Fill the `profile.md` template with their answers. Delete the italic guidance text as you go — none of it should survive into the final file.

## 4. Reconcile, don't append

If their existing content overlaps the method, say so plainly and propose the merge before writing:

> *"Your 'Role & altitude' section says the same thing as the method's 'How to talk to me.' I'd fold your version into the profile block and drop the duplicate — two sets of instructions saying it differently is how rules start getting ignored. Sound right?"*

Keep anything of theirs the method doesn't cover — move it below the two blocks, untouched.

## 5. Write it

Back up first: copy the existing file to `CLAUDE.md.bak` and tell them where it is.

Then write the target as:

```markdown
<!-- dont-run-off:method — managed, replaced on upgrade. Edit below this block. -->
...contents of method.md...
<!-- /dont-run-off:method -->

...their filled-in profile...

...anything of theirs you kept...
```

For a **project** target, cut the method down to project facts — stack, commands, conventions, gotchas. The full method belongs in the global file; repeating it per project burns the always-on budget for no gain.

## 6. Verify, then hand back

Check the total line count. Over 200 and adherence drops — if it's close, say so and offer to trim.

Tell them to run **`/context`** and confirm the file is listed. An install you haven't verified isn't finished. Then recap in plain language: what you wrote, what you merged or dropped and why, where the backup is, and that `profile.md`'s content is theirs to edit freely — upgrades only touch the marked block.
