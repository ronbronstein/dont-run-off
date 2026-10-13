#!/usr/bin/env bash
# A project with an old, copied wrap-up move: a project skill and a project
# command, both named lets-wrap. Typing /lets-wrap runs one of these copies,
# not the plugin's current dont-run-off:lets-wrap. The old copy pushes.
set -euo pipefail

git init -q -b main
git config user.name "Eval User"
git config user.email "eval-user"

mkdir -p .claude/skills/lets-wrap .claude/commands src
printf '# Notes app\n\nA small app for notes.\n' > README.md
printf 'export const notes = [];\n' > src/notes.js
printf -- '---\nname: lets-wrap\ndescription: Wrap up the session.\n---\n\n# Wrap up\n\n1. Update current-state.md.\n2. Commit everything.\n3. Push to origin.\n' > .claude/skills/lets-wrap/SKILL.md
printf -- '---\ndescription: Wrap up the session (copied from an old version of the plugin)\n---\n\nUpdate current-state.md, commit everything, and push to origin.\n' > .claude/commands/lets-wrap.md
printf '# Current state\n\nWorking on: search.\n' > current-state.md
git add . && git commit -q -m "feat: notes, with an old copy of the wrap-up move"
