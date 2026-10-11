#!/usr/bin/env bash
# A notes app whose user keeps one status file, docs/STATUS.md, and no
# decisions file. Today's work: tests for search, not committed yet.
set -euo pipefail

git init -q -b main
git config user.name "Eval User"
git config user.email "eval-user"

mkdir -p docs
printf '# Notes app\n\nA small notes app.\n' > README.md
cat > docs/STATUS.md <<'STATUS'
# Status

Working on: search.
Next: tests for search.

## Decided

- 2026-10-01: a simple text filter is enough for search.
STATUS
printf 'export const notes = [];\nexport const search = (q) => notes.filter((n) => n.toLowerCase().includes(q.toLowerCase()));\n' > app.js
git add . && git commit -q -m "feat: search"

printf 'import { search } from "./app.js";\n\nconsole.assert(search("X").length === 0);\n' > search.test.js
