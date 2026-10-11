#!/usr/bin/env bash
# A tiny single-user notes app with no storage yet.
set -euo pipefail

git init -q -b main
git config user.name "Eval User"
git config user.email "eval-user"
printf '# Notes app\n\nA small notes app for one person, on one computer. Node.js, no server yet.\n' > README.md
printf 'export const notes = [];\nexport const add = (text) => notes.push(text);\n' > app.js
printf '# Current state\n\nWorking on: saving notes between runs.\n' > current-state.md
git add . && git commit -q -m "feat: first version"
