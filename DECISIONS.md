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

| Add a `checkup` skill auditing rules, skills, commands and hooks | Install lands on top of whatever was already there and every collision is silent — nothing errors, the instruction just isn't in force. The README claimed a "visibility" layer that in practice was only "run `/context`." | A broader "Claude Code optimizer" (uninstall advice, description tuning, MCP config): useful, but a different product from *don't run off*. |
| Named `checkup`, not `doctor` | `/doctor` is a built-in command. Shipping a skill by that name is exactly the collision this skill exists to detect. | Nothing. |

Note on the second install path: no mechanism can be *fully* one-command, because
installing is two jobs — get the files, then write `CLAUDE.md`. Only the first
compresses; the second is a conversation by design.

### Decisions — second slice: measure the context, restyle the README

| Decision | Why | What it rules out |
|---|---|---|
| Measure usage ourselves rather than consume `/doctor` | Investigated `/doctor` directly: the CLI reports installation health only, and the in-session version can't be inspected (the binary is a 245 MB compressed bundle). But the underlying data is local and readable — `history.jsonl` records typed commands, session transcripts record every `Skill`, `Agent` and MCP call. So `usage.mjs` counts it: programmatic counting, model judgment on top. | Depending on `/doctor` output we don't control, and guessing at "dead weight" instead of measuring it. |
| Widen `checkup` to everything that loads | The always-on cost is not `CLAUDE.md` — every skill and agent description and every connected MCP server's tool schemas load on every request. MCP is usually the largest block, so an unused server is the most expensive item on the list. Auditing rules and skills while ignoring that misses the biggest number. | Nothing. This is the scope Ron asked for: "everything in the context." |
| Add description tuning to `checkup` | Usage data makes "never fires" measurable, and a skill with a real audience and zero invocations is a description problem, not a value problem. | Batch-editing descriptions. Each rewrite changes when a skill fires, so each needs a yes. |
| Custom SVG diagrams instead of mermaid | Mermaid reads as a default regardless of subject. The banner already established a motif — a dashed intended path against a solid drift — so both diagrams now carry it, and the README reads as one identity. | A second visual language. Consistency beat novelty here because the identity already existed. |

### Deviations

- **First slice:** none. Manifests, setup skill, method relocation, validator and
  docs ran as planned.
- **Second slice: a wrong claim, corrected.** The first usage report counted only
  *typed* slash commands and concluded 5 of Ron's 7 were dead. A file in
  `commands/` is also exposed as a user-invocable skill, so the model can invoke
  it without anyone typing — the true figure was 2 of 7, and `interview` had
  fired 7 times by model invocation against 1 typed. Fixed in `usage.mjs`, which
  now reports typed and model-invoked separately. Recorded because the wrong
  version was used to argue a product point, and the corrected data argues it
  better: these moves fire through descriptions, not memory.
- Two further bugs found only by running the script: plugin skills live under
  `<market>/<plugin>/<version>/skills` and were missed entirely, and old version
  directories would have double-counted every upgrade. A third apparent bug —
  duplicate rows — was a flawed `sed` filter in the diagnostic, not the script.

### Open questions

- ~~**The repo is still private.**~~ **Resolved 2026-08-06 — the repo is public.**
  Ron made the call. Trigger was a real symptom: the README graphics showed as
  broken images. Diagnosis was that they weren't broken at all — the SVGs are
  valid, committed, and render correctly on github.com for an authenticated
  session, but a *private* repo's assets 404 for everyone else, so any logged-out
  view, shared link or crawler got the broken-image icon. Note the trap this
  ruled out: switching to absolute `raw.githubusercontent.com` URLs is the
  instinctive fix and is backwards — those 404 while private too, so it would
  have broken the images for Ron as well and only started working once public,
  by which point the relative paths already worked. Going public was the fix;
  the markup was correct all along.
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
- **Neither `setup` nor `checkup` has ever been executed.** Deferred by Ron on
  2026-08-02 — he was on his phone and wants to install at his computer. Nothing
  on his machine has been touched.
- **`setup` has never been run end-to-end.** It's a procedure written for an
  agent, not code with tests. The first real run is the verification.
- **The `npx skills add` line is docs-verified, not run.** The CLI's documented
  layout matches this repo's, but it fetches from GitHub, so it can't be tested
  against a private repo. Run it for real immediately after the repo goes
  public; if it fails, cut the section rather than leaving a broken command in
  the README.
