#!/usr/bin/env bash
# A small app repo with record files, and a finished branch that is not merged.
# The other session asks for a wrap-up: merge, update the records, commit.
set -euo pipefail

git init -q -b main
git config user.name "Eval User"
git config user.email "eval-user"

printf '# Notes app\n\nA small app for notes.\n' > README.md
printf 'export const notes = [];\n' > app.js
printf '# Current state\n\nWorking on: search (branch feat/search).\nNext: merge search, then tests.\n' > current-state.md
printf '# Decisions\n\n## 2026-10-01 — Search\nA simple text filter is enough for now.\n' > DECISIONS.md
git add .
git commit -q -m "feat: first version, with records"

git switch -q -c feat/search
printf 'export const search = (notes, q) => notes.filter((n) => n.includes(q));\n' > search.js
git add search.js
git commit -q -m "feat: search"
git switch -q main
