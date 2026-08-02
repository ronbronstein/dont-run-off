# Decisions

Why things are the way they are. Append as you go — the reason matters more than
the choice, because the reason is what tells a future reader whether the decision
still holds.

---

## 2026-08-02 — Prepare for publication: distribution, install, and the always-on layer

The repo was feature-complete but unpublishable: private, with a README promising
a one-command install that didn't exist. This slice decided how it ships.

### Decisions

| Decision | Why | What it rules out |
|---|---|---|
| Target Claude Code only | The install path, the visibility commands (`/context`, `/doctor`), and the plugin system are all Claude Code's. Supporting three tools meant plumbing that served none of them well. | Cursor and Codex as first-class targets. The skills still follow the Agent Skills format, so they'd work there — but nothing here is built or tested for it. |
| Drop `AGENTS.md` and its one-line `CLAUDE.md` stub | That indirection existed *only* so non-Claude tools could read the same method. Once the target narrowed, it was pure overhead. | The single-source-of-truth-across-tools property. Irrelevant now. |
| One `CLAUDE.md`, method inside marker comments | Personalization has to survive an upgrade. Markers give the upgrade a deterministic target without an import or a second file. | Two files with `@profile.md` (safest, but keeps an import) and no-markers-at-all (cleanest, but every upgrade depends on the agent merging correctly with no guardrail — unacceptable when strangers run it against config we've never seen). |
| The wizard is a skill, not a script | A plugin cannot write `CLAUDE.md`, so *something* must. A skill can read the user's existing file, recognize overlaps, and propose a merge — a script can only append blindly. Install becomes a conversation, which is the product's own thesis applied to onboarding. | A `curl \| bash` or `npx` installer. Also flagged in research as an anti-pattern users increasingly distrust. |
| Detect first, ask only what's left | A six-field form is the lazy version and gets abandoned. Task tool, VCS, and record files are all detectable. | Nothing — this is strictly better UX. |
| Never accept a blank "frictions" | It's the highest-leverage line in the harness and the one everyone skips. Naming what usually goes wrong is what makes the agent watch for it. | A fully silent/unattended install. |
| Merge with backup, never overwrite | Most installers will meet an existing `CLAUDE.md`. Two sets of instructions saying the same thing differently is the documented cause of "my rules are being ignored." | Append-only install. |
| Method gains a "Working on code" section | The harness was all interaction discipline and said nothing about code — a hole, since that's where the damage happens. Six lines: stay in scope, reuse before creating, read before editing, verify before claiming, don't swallow errors, small commits. | Shipping engineering *opinions* (stack, coverage bar, error envelope, model routing) in the shared method. Those went to the profile's new `Conventions` field — true for one person, not for everyone. |
| Ship as a Claude Code plugin, repo as its own marketplace | Two commands to install, and the only route with real auto-updates. Costs one small JSON file. | `npx skills add` (Vercel's cross-tool CLI) — ruled out by the Claude-Code-only call, though the repo layout stays compatible with it if that reverses. |
| Marketplace named `ronbronstein`, not `dont-run-off` | Reads correctly at the install line (`dont-run-off@ronbronstein`) and lets a second plugin join later without a second marketplace. | Nothing meaningful. |
| Document `npx skills add` as a second install path | A genuine one-liner for people who don't want the plugin system, at the cost of a few README lines and no structural change — the repo's `skills/<name>/SKILL.md` layout is already what that CLI expects. | Nothing. The plugin stays primary because it's the only path that auto-updates. |

Note on the second install path: no mechanism can be *fully* one-command, because
installing is two jobs — get the files, then write `CLAUDE.md`. Only the first
compresses; the second is a conversation by design.

### Deviations

- None. The slice ran as planned: manifests, setup skill, method relocation,
  validator, docs.

### Open questions

- **The repo is still private.** Flipping it public is Ron's call and the one
  genuinely irreversible step — assume anything published is cached the moment
  it lands.
- **Not yet dogfooded.** Ron's own `~/.claude/CLAUDE.md` is the *ancestor* of
  this harness, not this harness: no method block, the moves live as slash
  commands in `~/.claude/commands/`, and every shared skill has drifted from the
  repo version. Publishing without migrating means the published version stops
  reflecting what actually works. Running `/dont-run-off:setup` on his own
  machine is the natural first test.
- **How the work project consumes it** — pinned marketplace in the project's
  `.claude/settings.json` (auto-prompts colleagues on folder trust) versus
  vendoring the skills into the repo (nothing to install, reviewed like code).
  Decide when that repo is open.
- **`setup` has never been run end-to-end.** It's a procedure written for an
  agent, not code with tests. The first real run is the verification.
- **The `npx skills add` line is docs-verified, not run.** The CLI's documented
  layout matches this repo's, but it fetches from GitHub, so it can't be tested
  against a private repo. Run it for real immediately after the repo goes
  public; if it fails, cut the section rather than leaving a broken command in
  the README.
