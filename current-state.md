# Current state

**Next session starts here → install it on Ron's machine and run it for real: `/plugin marketplace add ./`, `/plugin install dont-run-off@ronbronstein`, then `/dont-run-off:setup`.**

*Keep this file true. If it describes a plan rather than reality, it will
mislead the next session confidently. Rewrite it, don't just append.*

---

## Where we are

The repo is publication-ready but still **private**, and **nothing is installed anywhere**. Eleven skills, a Claude Code plugin manifest, and a self-hosted marketplace. `npm test` and `claude plugin validate .` both pass. All work is committed and pushed to `main`.

The harness targets Claude Code only. `AGENTS.md` and its one-line `CLAUDE.md` stub are gone; the method lives in `skills/setup/method.md` and is written into the user's `CLAUDE.md` by the `setup` skill, inside markers so an upgrade replaces the method and leaves personalization alone. The always-on layer is 100 of its 200-line budget.

Two skills are new and neither has ever been executed: `setup` (installs and personalizes the method — detects what it can, interviews for altitude and frictions, merges with any existing `CLAUDE.md`, backs it up) and `checkup` (audits everything that loads: rules, skills, commands, hooks, agents, MCP servers, plugins, memory). `checkup` ships `usage.mjs`, which counts real invocations from local history and session transcripts. That script *has* been run repeatedly against Ron's live setup and works.

## In progress

Nothing mid-flight. The tree is clean.

## Not started

1. **Install and run it** — the first real execution of `setup` and `checkup`. Expect to find bugs in the procedures; that is the point. Deferred because Ron was on his phone.
2. **Flip the repo public** — Ron's call, the one irreversible step.
3. **Verify the `npx skills add` line** — documented in the README but never executed, because the CLI fetches from GitHub and the repo is private. Run it once public; cut the section if it fails rather than leave a broken command in the README.
4. **Decide how the work project consumes it** — pinned marketplace in that repo's `.claude/settings.json`, or vendored skills. Leaning vendored for a work codebase.

## Explicitly not doing

- **Cross-tool support** (Cursor, Codex). Dropped when the target narrowed to Claude Code. The skills stay format-compatible, but nothing here is built or tested for it.
- **`npx skills add` as the primary path.** It stays documented as an alternative; the plugin is primary because it is the only route that auto-updates.
- **A shell or Node install wizard.** The wizard is a skill on purpose — it has to read an existing `CLAUDE.md` and propose a merge, which a script cannot do.
- **Shipping engineering opinions in the shared method** (stack, coverage bar, error envelope, model routing). Those belong in the user's own profile block.
