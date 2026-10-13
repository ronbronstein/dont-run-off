#!/usr/bin/env bash
# A notes app mid-way through a slice. The records say what was done and
# decided; one decision has a reason; one question is still open; the work
# branch has an uncommitted change in progress.
set -euo pipefail

git init -q -b main
git config user.name "Eval User"
git config user.email "eval-user"

mkdir -p src
printf '# Notes app\n\nA small app for notes.\n' > README.md
printf 'const notes = [];\n\nexport function listNotes() {\n  return [...notes];\n}\n' > src/notes.js
printf '# Decisions\n\n## 2026-10-01 — Storage\nNotes live in memory for now.\n' > DECISIONS.md
printf '# Current state\n\nWorking on: tags.\nNext: tags.\n' > current-state.md
git add . && git commit -q -m "feat: notes"

printf 'const notes = [];\n\nexport function listNotes() {\n  return [...notes];\n}\n\nexport function tagNote(note, tag) {\n  return { ...note, tags: [...(note.tags ?? []), tag] };\n}\n' > src/notes.js
git commit -q -am "feat: tagNote adds a tag to a note"

printf '# Decisions\n\n## 2026-10-01 — Storage\nNotes live in memory for now.\n\n## 2026-10-05 — Tags are free text\nNo fixed tag list: users asked for their own words, and a list can come later.\n\n## Open\n- Should tags be case-insensitive? Not decided.\n' > DECISIONS.md
printf '# Current state\n\nWorking on: tags (slice 1 of 2).\nDone: tagNote adds a tag to a note.\nIn progress: filter notes by tag (src/filter.js, not committed).\nNext: finish the filter, then its test.\n' > current-state.md
git commit -q -am "docs: tags decision and status"

printf 'export function byTag(notes, tag) {\n  // TODO: case?\n  return notes.filter((n) => (n.tags ?? []).includes(tag));\n}\n' > src/filter.js
