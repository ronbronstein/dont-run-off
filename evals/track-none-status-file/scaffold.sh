#!/usr/bin/env bash
# A notes app with no task tool: the status file lists what is next.
set -euo pipefail

git init -q -b main
git config user.name "Eval User"
git config user.email "eval-user"
printf '# Notes app\n\nA small notes app.\n' > README.md
cat > current-state.md <<'STATE'
# Current state

Working on: search.

## Next

- Tests for search
STATE
git add . && git commit -q -m "feat: first version"
