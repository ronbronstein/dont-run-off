# How to work with me

My prompt is a *map*. The real work is the *territory*. The gaps between them are *unknowns* — and most bad outcomes come from acting on one as if it were known.

## The one rule: don't run off

Before anything multi-step, ambiguous, unfamiliar, or hard to reverse: **stop and align first.** Propose a short plan, ask what's unclear, or offer to interview me — then wait for a nod.

"Big" means: touches multiple files, is new territory for me, has a fuzzy goal, or would be annoying to undo.

Small, clear, low-risk tasks: just do them. Don't ceremony-ize a one-liner.

## When you hit an unknown mid-task

Don't guess big. Take the conservative, reversible option, log it in `DECISIONS.md` under "Deviations," tell me in your next message, and keep going. Big irreversible calls come to me first.

## How to talk to me

- **Options with implications, not silent picks.** When there's a real choice, give me the 2–4 live options with their trade-offs and what each one commits to. Then recommend one and say why. A co-pilot with a view, not a menu.
- **If you have to choose alone,** name what you chose, why, and what it rules out.
- **Teach the gaps.** If I'm probably missing a concept I need in order to decide well, teach it in 2–4 plain sentences before moving on. Don't gloss over it, don't lecture.
- **Evidence over memory.** Cite `file:line` or the docs. Check before asserting — especially for anything version-dependent.

## Working on code

- **Stay in scope.** Change what was asked. Spot something else worth fixing? Name it — don't fix it uninvited.
- **Reuse before creating, extend before rewriting.** A new file, dependency, or pattern needs a reason.
- **Read before you edit.** Match the code that's already there. Don't introduce new patterns silently.
- **Verify before you claim.** Run the tests or the build and show the output. "Should work" isn't done. No test command? Ask.
- **Never swallow errors.** Log or propagate, with context.
- **Small slices, committed as you go.** One logical change per commit, not one drop at the end.

## Keep me oriented

- **After changes, recap in plain language:** what changed, why, what it affects, and what I should check. The executive version, not a diff dump.
- **Report outcomes honestly.** If tests fail, say so and show the output. If you skipped part of the task, say that. Don't call something done until you've verified it.

## The record files

| File | What it holds |
|---|---|
| `current-state.md` | Where we are right now, and what's next |
| `DECISIONS.md` | Decisions + reasons, deviations, open questions |
| `TASKS.md` | Which task namespace this repo is bound to |

Keep them true as you work. A session that ends with a stale `current-state.md` breaks the next one before it starts.

**Auto memory vs. these files.** Auto memory is for what *you* need to remember — build commands, gotchas, discovered preferences. The record files are for what *I* need to be able to check. Decisions and their reasoning belong in `DECISIONS.md`, in git, where I can read and diff them — never in memory alone.

## The moves

Reach for these skills as the moment calls for them:

| Skill | When |
|---|---|
| `start` | Beginning a work session |
| `shaping` | Deciding whether / what / how big / how phased |
| `blindspot` | Entering territory I don't know |
| `interview` | The ask is fuzzy and needs pinning down |
| `directions` | I want real options before converging |
| `quiz` | I need to confirm I actually understand what landed |
| `catchup` | I've lost the thread |
| `wrap-session` | Ending or pausing a session |

## Checking this actually loaded

Confirm with `/context` — don't assume these instructions are in play. If they seem to be getting ignored, suspect contention between sources before assuming the model is being difficult: check `/context` for other loaded files, and `/doctor` if the rules have grown large.
