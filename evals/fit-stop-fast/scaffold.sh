#!/usr/bin/env bash
# A small app in git where getNotes is defined in one file and used in another.
# The rename is clear and git can undo it.
set -euo pipefail

git init -q -b main
git config user.name "Eval User"
git config user.email "eval-user"

mkdir -p src
printf '# Notes app\n\nA small notes app.\n' > README.md
printf 'const notes = [];\n\nexport function getNotes() {\n  return [...notes];\n}\n' > src/notes.js
printf 'import { getNotes } from "./notes.js";\n\nexport function render() {\n  return getNotes().join("\\n");\n}\n' > src/ui.js
git add . && git commit -q -m "feat: notes and ui"
