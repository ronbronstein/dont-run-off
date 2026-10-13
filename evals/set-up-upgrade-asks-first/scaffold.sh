#!/usr/bin/env bash
# A notes app whose CLAUDE.md has the OLD method block (August 2026: it names
# `interview`), no My setup section, and the user's own lines below the block,
# including a rule about how to write replies. Records and Taskwarrior-free.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"

git init -q -b main
git config user.name "Eval User"
git config user.email "eval-user"

printf '# Notes app\n\nA small app for notes.\n' > README.md
printf 'export const notes = [];\n' > app.js
printf '# Current state\n\nWorking on: search.\nNext: tests for search.\n' > current-state.md
printf '# Decisions\n\n## 2026-10-01 — Search\nA simple text filter is enough for now.\n' > DECISIONS.md
{
  cat "$here/old-claude-md-method.md"
  printf '\n## About this project\n\nA notes app in plain JavaScript. Run it with `node app.js`.\n'
  printf '\n## How to write replies\n\nKeep replies short and plain. Explain any technical word in one line.\n'
} > CLAUDE.md
git add . && git commit -q -m "feat: first version, with records"
