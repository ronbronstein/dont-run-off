#!/usr/bin/env bash
# A notes app whose tasks live in GitHub Issues. The test has no network and
# no GitHub login, so the gh command can fail; the graders check the choice.
set -euo pipefail

git init -q -b main
git config user.name "Eval User"
git config user.email "eval-user"
git remote add origin https://github.com/example-org/notes-app.git
printf '# Notes app\n\nA small notes app.\n' > README.md
printf '# Current state\n\nWorking on: search.\n' > current-state.md
git add . && git commit -q -m "feat: first version"
