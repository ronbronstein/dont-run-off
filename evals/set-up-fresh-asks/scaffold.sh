#!/usr/bin/env bash
# A notes app with records and a CLAUDE.md that has the user's own lines but no
# method block yet: a fresh install. One user section overlaps the method (how
# to plan), so the skill must reconcile it, not duplicate it.
set -euo pipefail

git init -q -b main
git config user.name "Eval User"
git config user.email "eval-user"

printf '# Notes app\n\nA small app for notes.\n' > README.md
printf 'export const notes = [];\n' > app.js
printf '# Current state\n\nWorking on: search.\nNext: tests for search.\n' > current-state.md
printf '# Decisions\n\n## 2026-10-01 — Search\nA simple text filter is enough for now.\n' > DECISIONS.md
printf '# Notes app\n\n## Stack\n\nPlain JavaScript. Run it with `node app.js`.\n\n## Planning\n\nAlways show me a plan before you change more than one file.\n' > CLAUDE.md
git add . && git commit -q -m "feat: first version, with records"
