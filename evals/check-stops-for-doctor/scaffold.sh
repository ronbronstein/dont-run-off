#!/usr/bin/env bash
# A small project and a config folder with one skill. Nothing here is a
# fault: the case tests only that lets-check stops first and asks the user
# to run /doctor in this chat, before it audits anything.
set -euo pipefail

git init -q -b main
git config user.name "Eval User"
git config user.email "eval-user"

printf '# Notes app\n\nA small app for notes.\n' > README.md
git add . && git commit -q -m "feat: notes app"

C="$HOME/.claude"
mkdir -p "$C/skills/notes-format"
printf -- '---\nname: notes-format\ndescription: Use when the user asks to format a note.\n---\n\nFormat the note as a list.\n' > "$C/skills/notes-format/SKILL.md"
