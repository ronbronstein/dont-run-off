# How the harness works

Written for someone who directs an AI agent competently but doesn't spend their day in a codebase. If you understand this page, you can debug your own setup — which is most of the value.

## The core problem: context is a budget

Everything you tell an agent has to fit in its context window alongside your actual conversation. Some of what you write is loaded into **every single message**; some is loaded **only when it's relevant**. Getting a thing into the wrong category is the most common way a setup goes bad.

Too much always-on context and the agent starts skimming — the docs are explicit that longer instruction files "reduce adherence." Too little and it doesn't know your conventions. The whole design of this harness is about putting each piece in the right place.

## The four layers

### 1. Always-on — the rules

Loaded at the start of every session, in full, forever. This is where the *method* lives: how the agent should behave before it knows anything about the task.

| File | Scope |
|---|---|
| `~/.claude/CLAUDE.md` | How you want to be worked with, everywhere |
| `./CLAUDE.md` | Facts about this project, for everyone on it |

**Budget: keep each under 200 lines.** This layer costs tokens on every message you ever send.

Claude Code reads `CLAUDE.md` and nothing else at this layer, so that's the only file the harness writes. No imports, no stubs.

**The global file has two halves**, separated by marker comments:

- **The method block** — the rules of engagement. Identical for everyone. Replaced wholesale on upgrade, which is what the markers are for.
- **Your profile** — altitude, task tool, conventions, frictions. Yours. Never touched by an upgrade.

The split exists entirely so that shipping you a new method doesn't cost you your personalization. Nothing else depends on it.

**The project file gets facts, not method** — stack, commands, gotchas. Repeating the method in every repo pays for it twice out of the same budget.

**Nothing installs this layer automatically.** A Claude Code plugin can ship skills, agents, hooks and MCP servers, but it cannot write your `CLAUDE.md`. That's why the `setup` skill exists: it's the only path from an installed plugin to a working always-on layer, and it's why installing is a short conversation rather than a copy command.

### 2. On-demand — the skills

A skill is a folder with a `SKILL.md` inside. The agent reads only the *descriptions* up front; it loads the full skill **only when the description matches what you're doing.**

That's the key property: **skills are free until they fire.** You can have fifty of them and pay almost nothing. This is why the harness puts every specific procedure in a skill instead of in the rules.

### The heuristic that decides which layer

> **If it must be true before the agent decides anything, it's a rule.**
> **If it's a move you take at a moment, it's a skill.**

"Don't run off" has to be a rule. A skill only loads once its description matches something — and by then the agent has already decided what it's doing. Too late.

"Interview me about this fuzzy task" is a skill. It's a specific move for a specific moment, and it costs nothing the rest of the time.

### 3. State — the record files

Never loaded automatically. Skills read and write them when relevant.

| File | Answers |
|---|---|
| `current-state.md` | Where are we right now? |
| `DECISIONS.md` | Why did we choose this? What did we rule out? |
| `TASKS.md` | What's tracked, and where? |

These exist so **you** can check the work without reading code. They're in git, so they're diffable and they survive. Treat a stale `current-state.md` as a bug — it will mislead the next session confidently.

### 4. Visibility — how you check it's working

The layer people skip, and the one that matters most if you can't read the diff.

| Question | How to answer it |
|---|---|
| What instructions actually loaded? | `/context` |
| Are my rules too big to be followed? | `/doctor` |
| Which instruction files loaded, and when? | the `InstructionsLoaded` hook |
| What did it just do? | the recap rule in the method block |
| Do I actually understand the change? | the `quiz` skill |
| Where are we, and why did we choose this? | `current-state.md`, `DECISIONS.md` |

**Run `/context` after any setup change.** It's the difference between believing your rules are loaded and knowing it.

## Auto memory — the other thing writing to your context

Claude Code keeps its own memory at `~/.claude/projects/<project>/memory/`, which it writes itself and loads every session. It's useful, but it overlaps the record files, and two systems recording project knowledge is how setups start contradicting themselves.

The division this harness uses:

- **Auto memory** is what *the agent* needs to remember — build commands, gotchas, discovered preferences. Machine-local, disposable.
- **The record files** are what *you* need to be able to check — decisions, reasons, current state. In git, permanent, reviewable.

Decisions belong in `DECISIONS.md`, not in memory alone. If it only exists in the agent's memory, you can't audit it and it doesn't survive a new machine.

## When instructions seem ignored

Almost always **contention**, not disobedience. If several sources are steering behavior at once — your rules, a plugin's hooks, another CLAUDE.md up the directory tree, a stale rule contradicting a new one — the agent picks one arbitrarily, and your instruction looks ignored.

The docs say it plainly: "if two rules contradict each other, Claude may pick one arbitrarily."

Debug it in this order:

1. `/context` — did your file even load? If it's not listed, nothing else matters.
2. Look for contradictions across all loaded sources, including CLAUDE.md files in parent directories.
3. Check size — over 200 lines and adherence drops.
4. Make the instruction more specific. "Use 2-space indentation" beats "format code properly."
5. If it genuinely must happen every time, a rule isn't strong enough — that's what hooks are for.

