#!/usr/bin/env bash
# A notes app. The last commit made search ignore upper and lower case, and
# added a test for it.
set -euo pipefail

git init -q -b main
git config user.name "Eval User"
git config user.email "eval-user"
printf '# Notes app\n\nA small notes app.\n' > README.md
printf 'export const notes = [];\nexport const search = (q) => notes.filter((n) => n.includes(q));\n' > app.js
git add . && git commit -q -m "feat: search"
printf 'export const notes = [];\nexport const search = (q) =>\n  notes.filter((n) => n.toLowerCase().includes(q.toLowerCase()));\n' > app.js
printf 'import { notes, search } from "./app.js";\n\nnotes.push("Buy Milk");\nconsole.assert(search("milk").length === 1, "search ignores case");\n' > search.test.js
git add . && git commit -q -m "fix: search ignores upper and lower case; add a test"
