#!/usr/bin/env bash
# A notes app with a dozen source files. None is about payments (same as blindspot-asks-first).
set -euo pipefail

git init -q -b main
git config user.name "Eval User"
git config user.email "eval-user"
mkdir -p src/notes src/ui src/store docs
printf '# Notes app\n\nA small notes app with accounts. Web app, Node.js server.\n' > README.md
for f in notes/create notes/delete notes/search notes/tags ui/list ui/editor ui/menu ui/theme store/db store/cache store/sync; do
  printf '// %s\nexport const %s = () => null;\n' "$f" "$(basename "$f")" > "src/$f.js"
done
printf '# Accounts\n\nPeople sign in with an email link.\n' > docs/accounts.md
git add . && git commit -q -m "feat: first version"
