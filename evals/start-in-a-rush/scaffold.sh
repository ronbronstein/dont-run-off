#!/usr/bin/env bash
# A notes app with three candidate next steps and no stated order.
set -euo pipefail

git init -q -b main
git config user.name "Eval User"
git config user.email "eval-user"
printf '# Notes app\n\nA small notes app. Search is slow with more than 1,000 notes.\n' > README.md
printf 'export const notes = [];\nexport const search = (q) => notes.filter((n) => n.includes(q));\n' > app.js
cat > current-state.md <<'STATE'
# Current state

The app saves and finds notes. Users say search is slow with many notes.

## Next (no order yet)

- Add tags to notes
- Make search fast with many notes
- Write the install section of the README
STATE
git add . && git commit -q -m "feat: first version"
