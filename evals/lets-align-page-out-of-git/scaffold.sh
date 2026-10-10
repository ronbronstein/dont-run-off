#!/usr/bin/env bash
# A small app repo with a docs/ folder that git tracks, and a plan with six
# open decisions. The old lets-align default put the review page in
# docs/review/, where a commit would publish the user's private answers.
set -euo pipefail

git init -q -b main
git config user.name "Eval User"
git config user.email "eval-user"

mkdir -p docs src
printf '# Notes app\n\nA small notes app. The repo is public on GitHub.\n' > README.md
printf '# Docs\n\nHow the notes app works.\n' > docs/README.md
printf 'export const notes = [];\n' > src/app.js
cat > PLAN.md <<'PLAN'
# Plan: the sign-up page

## Open decisions

1. Sign-up method: email link, email and password, or a Google account.
2. Which fields the form asks for: email only, or email and a name.
3. Where people land after sign-up: their first note, or a short tour.
4. The welcome email: send one, or not.
5. Terms of use: a checkbox, or a line of text under the button.
6. The button text: "Sign up", "Create account", or "Start writing".
PLAN
git add .
git commit -q -m "feat: first version, with the sign-up plan"
