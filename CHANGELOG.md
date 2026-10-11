# Changelog

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
`CLAUDE.md`, which still names the old moves.

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
