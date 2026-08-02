---
name: checkup
description: Use to audit a Claude Code setup for context-engineering problems — what actually loads, what shadows what, what silently never fires, and what contradicts what. Covers rules (CLAUDE.md), skills, slash commands, and hooks. Trigger on "check my setup," "audit my config," "what's actually loaded," "why isn't my skill firing," "checkup," or right after installing or upgrading the harness.
---

# Checkup

Audit the four surfaces that decide agent behavior: **rules, skills, commands, hooks.**

`/doctor` checks whether Claude Code is healthy. `/context` shows what loaded this session. Neither tells you what *wins* when two sources disagree — which is the failure people actually hit, because it's silent. Nothing errors. A skill just never fires, or the wrong copy runs.

Report first, fix second. Never delete or rewrite anything before showing the finding and getting a yes.

## 1. Gather

Read what's on disk. Don't infer it.

| Surface | Where |
|---|---|
| Rules | `~/.claude/CLAUDE.md`, `./CLAUDE.md`, `./.claude/CLAUDE.md`, and any `CLAUDE.md` in parent directories |
| Skills | `~/.claude/skills/`, `./.claude/skills/`, plugin skills under `~/.claude/plugins/` |
| Commands | `~/.claude/commands/`, `./.claude/commands/` |
| Hooks | `hooks` in `~/.claude/settings.json`, `./.claude/settings.json`, `./.claude/settings.local.json` |

Expand `@` imports in rules files and follow them. An import pointing at a directory pulls in every file inside it — count them all.

## 2. Check

**Rules.** Total the lines actually loaded, imports included, against the 200-line ceiling — past it adherence drops. Flag unresolved imports (a broken `@path` loads nothing and says nothing). Flag two sources instructing differently on the same topic: the docs are explicit that Claude may pick one arbitrarily, and that is what "my instructions are being ignored" almost always is. Flag instructions that restate default behavior — they cost budget and change nothing.

**Skills.** For every name, list every scope it exists in. Precedence runs **personal → project → plugin → bundled**, so a stale `~/.claude/skills/x` silently beats the plugin's current `x`. That's the one people never catch: they install an upgrade and keep running the old copy. Then check each skill can actually fire — a `description` that lists topics instead of naming triggers and phrases means a skill that sits there forever. Flag two skills whose descriptions claim the same moment; that's contention with extra steps. Flag bodies over ~120 lines as probably two skills.

**Commands.** A command and a skill sharing a name is the trap: typing `/x` runs the command, while the model invokes the skill. Two different instruction sets behind one name, usually because one was copied from the other and then drifted. Diff them and say which is stale.

**Hooks.** Hooks are the only deterministic layer — they run whether or not the model cooperates — so a broken one fails silently in the worst direction. Check each event name is real, each matcher compiles, and each command actually exists and is executable. Flag overlapping matchers on the same event, where firing order decides the outcome. If a rule says something must happen *every time*, say so: that's a hook's job, and a rule is the wrong tool for it.

## 3. Report

Lead with the gap between what they think is in force and what actually is. Group findings so the worst are first:

1. **Shadowed** — installed but never used. Name the winner and the loser, with paths.
2. **Never fires** — present but untriggerable: weak descriptions, broken hooks, dead imports.
3. **Contradictions** — two sources steering the same behavior.
4. **Over budget** — always-on total against the ceiling.
5. **Dead weight** — restates defaults, duplicates another source, or hasn't changed behavior since it was written.

Every finding needs a path, the consequence in plain language, and a specific fix. "Skills may conflict" is not a finding. "`~/.claude/skills/wrap-session/` (16 lines) shadows the plugin's current 42-line version — delete yours and the upgrade takes effect" is.

If nothing is wrong, say so plainly and give the counts. A clean report is a result.

## 4. Fix

Offer the safe fixes as a numbered list and apply only what's picked. Back up anything you edit. Deleting a shadowing copy, removing a drifted duplicate command, and repairing a broken hook path are safe. Merging rules files or rewriting descriptions changes behavior — propose those, don't perform them.

Finish by having them run `/context` to confirm the result, and recap what changed.
