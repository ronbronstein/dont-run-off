---
name: checkup
description: Use to audit a Claude Code setup for context-engineering problems — what actually loads, what shadows what, what silently never fires, and what contradicts what. Covers rules (CLAUDE.md), skills, slash commands, and hooks. Trigger on "check my setup," "audit my config," "what's actually loaded," "why isn't my skill firing," "checkup," or right after installing or upgrading the harness.
---

# Checkup

Audit everything that loads: **rules, skills, commands, hooks, agents, MCP servers, plugins, memory.**

The thing people miss is that the always-on cost is not just `CLAUDE.md`. Every skill's description, every agent's description, and every connected MCP server's full tool schemas ride along on *every request* so the model can decide what to reach for. MCP tools are usually the single largest block, and a server you never call is the most expensive dead weight you can own. `/context all` shows the breakdown by source — start there when the budget looks wrong.

The built-ins each show one surface: `/doctor` finds installation and invalid-settings problems, `/context all` inventories what loaded this session, `/skills` lists skills by source, `/hooks` lists hooks by event, `/status` shows which settings files were read. Use them to gather — they're faster and more accurate than guessing.

What none of them answers is what *wins* when two sources disagree. That's the failure people actually hit, and it's silent: nothing errors, a skill just never fires, or a stale copy runs instead of the one you installed.

Report first, fix second. Never delete or rewrite anything before showing the finding and getting a yes.

## 1. Gather

Read what's on disk. Don't infer it.

| Surface | Where |
|---|---|
| Rules | `~/.claude/CLAUDE.md`, `./CLAUDE.md`, `./.claude/CLAUDE.md`, any `CLAUDE.md` in parent directories, plus `~/.claude/rules/` and `./.claude/rules/` |
| Skills | `~/.claude/skills/`, `./.claude/skills/`, plugin skills under `~/.claude/plugins/` |
| Commands | `~/.claude/commands/`, `./.claude/commands/` |
| Hooks | `hooks` in `~/.claude/settings.json`, `./.claude/settings.json`, `./.claude/settings.local.json` |
| Agents | `~/.claude/agents/`, `./.claude/agents/`, plus any shipped by plugins |
| MCP servers | `mcpServers` in `~/.claude.json` (global and per-project) — **names only, these files hold tokens** — plus `/mcp` for account connectors, which live in your claude.ai settings and appear nowhere on disk |
| Plugins | `enabledPlugins` in settings, and `/plugin` for what each one contributes |
| Memory | `MEMORY.md` and the memory directory for this project |

Expand `@` imports and follow them. An import pointing at a directory pulls in every file inside it — count them all. Watch for imports that loop back on themselves, targets that don't exist, and the same file pulled in twice by different paths.

## 2. Measure what actually gets used

Run the script next to this skill:

```bash
node <path-to-this-skill>/usage.mjs --days 90
```

It counts real invocations from local data — `~/.claude/history.jsonl` for slash commands, session transcripts for `Skill` and MCP tool calls — and joins them against what's installed, so every skill, command and MCP server comes back with a use count and a last-used date. `--json` gives the same thing machine-readable. It reads names and counts only, never message content.

This is what turns "probably dead" into a measurement. Nothing else here can tell you a skill has sat untouched for three months.

Read the result with judgment. Zero uses is a prompt to look, not a verdict: a skill for a rare moment is doing its job by staying quiet, and something installed last week hasn't had a chance. What *is* damning is a skill that's been installed for months, covers something the person does constantly, and has never once fired — that's a description problem, not a taste problem.

## 3. Check

**Rules.** Total the lines actually loaded, imports included, against the 200-line ceiling — past it adherence drops. Flag unresolved imports: a broken `@path` loads nothing and says nothing. Flag two sources instructing differently on the same topic — the docs are explicit that Claude may pick one arbitrarily, and that is what "my instructions are being ignored" almost always is. Flag instructions that restate default behavior; they cost budget and change nothing.

The one people get wrong: a `CLAUDE.md` in a **subdirectory** doesn't load with the session. It's read on demand, if something opens it. Anyone who put project rules three levels down and assumed they were in force is running without them.

**Skills.** For every name, list every scope it exists in. Precedence runs **personal → project → plugin → bundled**, so a stale `~/.claude/skills/x` silently beats the plugin's current `x`. That's the one people never catch: they install an upgrade and keep running the old copy. Then check each skill can actually fire — a `description` that lists topics instead of naming triggers and phrases means a skill that sits there forever. Flag two skills whose descriptions claim the same moment; that's contention with extra steps. Flag bodies over ~120 lines as probably two skills.

**Commands.** A command and a skill sharing a name is the trap: typing `/x` runs the command, while the model invokes the skill. Two different instruction sets behind one name, usually because one was copied from the other and then drifted. Diff them and say which is stale.

**Hooks.** Hooks are the only deterministic layer — they run whether or not the model cooperates — so a broken one fails silently in the worst direction. Check each event name is real, each matcher compiles, and each command actually exists and is executable. Flag the same event configured in more than one settings file, and overlapping matchers within an event, where firing order decides the outcome. Flag anything slow enough to tax every tool call. If a rule says something must happen *every time*, say so: that's a hook's job, and a rule is the wrong tool for it.

**Settings themselves.** A settings file with a JSON syntax error doesn't announce itself — it just doesn't load, taking its hooks and permissions with it. Parse every one you found. `/debug settings` and `/debug hooks` show the live resolution if something still doesn't add up.

**Memory.** Auto memory loads its index every session, so it's part of the always-on cost. Check the index hasn't grown past its limits, and flag entries that contradict the rules or record decisions that belong in `DECISIONS.md` where they can be diffed.

**MCP servers.** The expensive one. Every connected server's tool schemas load on every request whether or not you ever call them, so rank by cost-per-use: a server with a large tool surface and a handful of calls in three months is costing you context on every message you send. Say where each one lives, because that determines how to remove it — servers in `~/.claude.json` come out locally, but account connectors have to be disconnected in claude.ai settings and will otherwise reappear on every machine you log into.

**Agents.** Subagent descriptions load so the model can route to them. An agent nobody routes to is paying rent. Check whether it's genuinely unused or just badly described — same diagnosis as skills, since routing works the same way.

**Plugins.** Judge a plugin by everything it contributes: skills, agents, commands, hooks, MCP servers. A plugin whose every surface is unused is a clean uninstall. A plugin where one skill carries it and the rest never fire is worth keeping and worth saying so.

## 4. Report

Lead with the gap between what they think is in force and what actually is. Group findings so the worst are first:

1. **Shadowed** — installed but never used. Name the winner and the loser, with paths.
2. **Never fires** — present but untriggerable: weak descriptions, broken hooks, dead imports.
3. **Contradictions** — two sources steering the same behavior.
4. **Over budget** — always-on total against the ceiling.
5. **Dead weight** — restates defaults, duplicates another source, or hasn't changed behavior since it was written.

Every finding needs a path, the consequence in plain language, and a specific fix. "Skills may conflict" is not a finding. "`~/.claude/skills/wrap-session/` (16 lines) shadows the plugin's current 42-line version — delete yours and the upgrade takes effect" is.

If nothing is wrong, say so plainly and give the counts. A clean report is a result.

## 5. Tune the descriptions that aren't firing

A skill's `description` is the whole trigger mechanism — it's the only part the agent reads before deciding whether to load it. Usage data makes this measurable: a skill with a real audience and zero invocations almost always has a description problem, not a value problem.

Compare a skill's invocation count against how often its *moment* actually came up in recent sessions. When something should have fired and didn't, rewrite the description to include:

- **the phrases a person actually types** — "this is fuzzy," "I've lost the thread," "what should I build" — not the topic it covers
- **the situation**, stated as a condition rather than a category: "when the ask is ambiguous and needs pinning down" beats "requirements gathering"
- **a boundary**, if it's near a neighbour, so two skills stop competing for the same moment

Rewriting a description changes when the skill fires, so show the before and after and get a yes on each one. Don't batch-edit descriptions.

## 6. Fix

Offer the safe fixes as a numbered list and apply only what's picked. Back up anything you edit. Deleting a shadowing copy, removing a drifted duplicate command, and repairing a broken hook path are safe. Merging rules files changes behavior — propose those, don't perform them.

Finish by having them run `/context` to confirm the result, and recap what changed.
