#!/usr/bin/env bash
# A notes app after a lets-align review page round: the page and its data are
# in .review/notes-export/ (out of git), and the user pastes the exported
# answers. Two answered (one changed from the agent's pick, with a note), one
# not sure, one with no answer.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"

git init -q -b main
git config user.name "Eval User"
git config user.email "eval-user"

mkdir -p src .review/notes-export/data
printf '# Notes app\n\nA small app for notes.\n' > README.md
printf 'export const notes = [];\n' > src/notes.js
printf '# Plan: export notes\n\nLet users download their notes. Open decisions are on the review page.\n' > PLAN.md
printf '# Decisions\n\n## 2026-10-01 — Storage\nNotes live in memory for now.\n' > DECISIONS.md
printf '# Current state\n\nWorking on: export. Waiting for the answers on the review page.\n' > current-state.md
printf '.review/\n' >> .git/info/exclude
cp "$here/../../skills/lets-align/assets/review.html" .review/notes-export/index.html
cp "$here/review-data.js" .review/notes-export/data/current.js
git add . && git commit -q -m "feat: notes, and a plan for export"
