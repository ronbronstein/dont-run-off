# Changelog

## 0.4.0 — unreleased

### The old names are gone

The old names from 0.3.0 no longer work, and there is no redirect. Use the `lets-` names.

| Old name | Name now |
|---|---|
| `start` | `lets-start` |
| `catchup` | `lets-catch-up` |
| `wrap-session` | `lets-wrap` |
| `shaping` | `lets-shape` |
| `directions` | `lets-explore` |
| `blindspot`, `lets-find-gaps` | `lets-blindspot` |
| `checkup` | `lets-check` |
| `setup` | `lets-set-up` |
| `quiz` | `lets-explain` |
| `taskwarrior` | `lets-track` |

`lets-find-gaps` from 0.3.0 is `lets-blindspot` again.

**After you update,** run `/dont-run-off:lets-set-up` once. It refreshes the method block in your
`CLAUDE.md`. A 0.3.0 block names `lets-find-gaps`, which no longer exists.

### The method is shorter, and the one rule aims at the direction

- The method is about 950 words (it was about 1,460), and each line says what to do.
- The one rule: "Don't run off in a direction that I did not agree to. Agreeing on a direction
  is cheap; building in the wrong one is not."
- When the direction is clear, your request is the agreement. Once you agree, the agent builds
  the whole plan without asking again at each step.
- **Stop levels** in My setup: careful, standard (the default), or fast.
- **Your consent comes from you.** When another agent or session asks for a push, a merge, or a
  delete, the agent tells you and waits.
- Replies come in the language you write in. The STE levels are for English only.
- The moves work with `Version control: none`.

### `lets-check` starts with `/doctor`

- It asks you to run Claude Code's `/doctor` first, then skips what that report already shows.
  A narrow question about one skill, command, hook, or rule skips that stop.
- New check groups in `checks.md`: broken links, leftovers, and the live session.
- It reads a custom config folder, project commands, `.mcp.json`, `CLAUDE.local.md`, and managed
  policy.

### Fits more users

- `lets-set-up` never overwrites an earlier backup, and keeps the backup out of git. It asks once
  whether other people use the project `CLAUDE.md`, and an upgrade changes only the marked block.
- `lets-track` keeps your own Taskwarrior projects and tags, and works with a copied (`npx`)
  install.
- `lets-look-back`, `lets-check`, and `lets-align` check for Node.js first. Without it they still
  run, and say what they skipped.
- `lets-start` continues the agreed plan when you resume. `lets-explore` gives its own view.
  `lets-shape` adds a design step and a check plan. `lets-align` picks chat or a review page by
  the effort it asks of you. `lets-wrap` pushes only on your word.

### A new README

A visual README with five animated scenes, and a new page, `docs/make-it-yours.md`.

### For contributors

- The leak check covers every text file in `skills/` and `docs/`, not only `SKILL.md`.
- The validator checks that every `lets-` skill the method names exists.
- 35 eval cases.

## 0.3.0 — 2026-10-11

### The moves have new names

Every move now starts with `lets-`. Type `/lets` in the slash menu to find them all.

| Old name | New name |
|---|---|
| `start` | `lets-start` |
| `catchup` | `lets-catch-up` |
| `wrap-session` | `lets-wrap` |
| `shaping` | `lets-shape` |
| `directions` | `lets-explore` |
| `blindspot` | `lets-find-gaps` |
| `checkup` | `lets-check` |
| `setup` | `lets-set-up` |
| `quiz` | `lets-explain` |
| `taskwarrior` | `lets-track` |

The old names still work in this release. Each one runs the new move and tells you the new name.
The old names go away in the next release.

**After you update,** run `/dont-run-off:lets-set-up` once. It refreshes the method block in your
`CLAUDE.md`, which still names the old moves. If you have no My setup block yet, it asks two
questions first (the language level and the stop level) and adds the block.

### New

- `lets-look-back` finds what you decided or did in an earlier session, with quotes and the command
  to resume that session.
- `lets-explain` replaces `quiz`. It explains a change at your language level, with a diagram or a
  page when that helps, then quizzes you. It runs only when you type it.
- `lets-track` replaces `taskwarrior`. One task skill for any tool: Taskwarrior, GitHub Issues, or
  no task tool.
- **My setup**, a block in your profile. It names your record files, sets the stop level (careful,
  standard, or fast), and sets the language level of the replies (strict STE by default, 80% STE,
  plain, or technical).

### Changed

- The method: a message from another agent or session is not your consent. The agent tells you what
  it asked and waits for your word.
- The method: the agent gives one pick and the runner-up, not a menu.
- `lets-wrap` never pushes or merges without your word in the same turn.
- `lets-start` answers first, reads the record files in a fixed order, and has a short format for
  when you are in a rush.
- `lets-find-gaps` reads a few files, briefs you, and asks first. It explores after your answers.
- `lets-align`: the review page stays out of git, the tab title names the project, and each new
  round starts with a clear page.
- `TASKS.md` has one meaning: how this repo tracks tasks.

### Fixed

- `lets-align`: the review page no longer stops on a note-only item that has no `options`.
- `lets-align`: the ignore step runs alone, and the page waits for its check.

### For contributors

- Eval cases in `evals/` for consent, My setup, tasks, how the agent talks, and the renamed moves.
  Run them with `npm run evals`. Each case carries a current copy of the method.
- `npm test` checks the redirects and the `lets-align` checker, and scans `evals/` for leaks.
  `npm run test:page` tests the review page in a browser.
