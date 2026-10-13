#!/usr/bin/env bash
# A notes app with a PLAN.md that holds two open decisions, each answerable in
# one line. lets-align must use chat (one question at a time), not a page.
set -euo pipefail

git init -q -b main
git config user.name "Eval User"
git config user.email "eval-user"

mkdir -p src
printf '# Notes app\n\nA small app for notes.\n' > README.md
printf 'export const notes = [];\n' > src/notes.js
printf '# Plan: export notes\n\nLet users download their notes.\n\n## Open decisions\n\n1. File format: Markdown or plain text?\n2. One file with all notes, or one file per note?\n' > PLAN.md
printf '# Decisions\n\n(none yet)\n' > DECISIONS.md
git add . && git commit -q -m "feat: notes, and a plan for export"
