#!/usr/bin/env bash
# A notes app mid-way through a slice, with records (the same project as the
# catch-up-where-were-we case, smaller).
set -euo pipefail

git init -q -b main
git config user.name "Eval User"
git config user.email "eval-user"

mkdir -p src
printf '# Notes app\n\nA small app for notes.\n' > README.md
printf 'const notes = [];\n\nexport function listNotes() {\n  return [...notes];\n}\n' > src/notes.js
printf '# Decisions\n\n## 2026-10-05 — Tags are free text\nNo fixed tag list: users asked for their own words.\n\n## Open\n- Should tags be case-insensitive? Not decided.\n' > DECISIONS.md
printf '# Current state\n\nWorking on: tags (slice 1 of 2).\nDone: tagNote adds a tag to a note.\nNext: filter notes by tag, then its test.\n' > current-state.md
git add . && git commit -q -m "feat: notes, tags slice 1"
