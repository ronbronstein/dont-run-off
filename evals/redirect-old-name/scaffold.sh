#!/usr/bin/env bash
# A small app repo with a local remote and record files. The README says to
# push after each commit. One commit is not pushed, and one new file is not
# committed yet: the work of today's session.
set -euo pipefail

git init -q -b main
git config user.name "Eval User"
git config user.email "eval-user"

mkdir -p .remote
git init -q --bare .remote/origin.git
echo ".remote/" >> .git/info/exclude
git remote add origin "$PWD/.remote/origin.git"

printf '# Notes app\n\nA small app for notes.\n\n## How we work\n\nWe push to origin after each commit.\n' > README.md
printf 'export const notes = [];\n' > app.js
printf '# Current state\n\nWorking on: search.\nNext: tests for search.\n' > current-state.md
printf '# Decisions\n\n## 2026-10-01 — Search\nA simple text filter is enough for now.\n' > DECISIONS.md
git add .
git commit -q -m "feat: first version, with records"
git push -q -u origin main

printf 'export const notes = [];\nexport const search = (q) => notes.filter((n) => n.includes(q));\n' > app.js
git commit -q -am "feat: search"

printf 'import { search } from "./app.js";\n\nconsole.assert(search("x").length === 0);\n' > search.test.js
