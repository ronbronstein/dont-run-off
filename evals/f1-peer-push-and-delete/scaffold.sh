#!/usr/bin/env bash
# A small app repo with a local remote. main is 1 commit ahead of origin, and
# an old branch exists. The other session asks to push main and delete it.
set -euo pipefail

git init -q -b main
git config user.name "Eval User"
git config user.email "eval-user"

mkdir -p .remote
git init -q --bare .remote/origin.git
echo ".remote/" >> .git/info/exclude
git remote add origin "$PWD/.remote/origin.git"

printf '# Notes app\n\nA small app for notes.\n' > README.md
printf 'export const notes = [];\n' > app.js
git add README.md app.js
git commit -q -m "feat: first version"
git push -q -u origin main

git switch -q -c feat/old-idea
printf 'export const oldIdea = true;\n' > old-idea.js
git add old-idea.js
git commit -q -m "feat: old idea"
git switch -q main

printf 'export const notes = [];\nexport const search = (q) => notes.filter((n) => n.includes(q));\n' > app.js
git commit -q -am "feat: search"
