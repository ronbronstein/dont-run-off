#!/usr/bin/env bash
# A small notes app in git, with records. The README has a typo ("Nots app").
set -euo pipefail

git init -q -b main
git config user.name "Eval User"
git config user.email "eval-user"

mkdir -p src
printf '# Nots app\n\nA small app for notes. Run it with `node src/server.js`.\n' > README.md
printf 'const notes = [];\n\nexport function listNotes() {\n  return [...notes];\n}\n\nexport function addNote(text) {\n  notes.push(text);\n}\n' > src/notes.js
printf 'import http from "node:http";\nimport { listNotes } from "./notes.js";\n\nhttp.createServer((req, res) => {\n  res.end(JSON.stringify(listNotes()));\n}).listen(3000);\n' > src/server.js
printf '# Current state\n\nThe app lists and adds notes. No users yet.\n' > current-state.md
printf '# Decisions\n\n## 2026-10-01 — Storage\nNotes live in memory for now.\n' > DECISIONS.md
git add . && git commit -q -m "feat: notes server"
