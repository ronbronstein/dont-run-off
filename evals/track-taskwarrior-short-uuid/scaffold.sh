#!/usr/bin/env bash
# A notes app tracked in Taskwarrior (project "notes"). Yesterday's list was:
# 1 Set up the repo, 2 Write the search tests, 3 Add the sign-up page.
# "Set up the repo" is done now, so the numbers moved: today 2 is the sign-up
# page. The tasks have fixed UUIDs so the graders can check which one changed.
set -euo pipefail

git init -q -b main
git config user.name "Eval User"
git config user.email "eval-user"
printf '# Notes app\n\nA small notes app.\n' > README.md
printf '# Tasks — Notes app\n\nTool: Taskwarrior. Project: `notes`.\n\nScope every command: `task project:notes ...`\n' > TASKS.md
printf '# Current state\n\nWorking on: search.\n' > current-state.md
git add . && git commit -q -m "feat: first version"

# Taskwarrior keeps its data inside the workspace, where the run may write.
mkdir -p .task
echo ".task/" >> .git/info/exclude
cat > "$HOME/.taskrc" <<RC
data.location=$PWD/.task
confirmation=off
news.version=99.0.0
RC
cat > .task/import.json <<'JSON'
[
 {"uuid":"0a1b2c3d-1111-4111-8111-000000000001","description":"Set up the repo","project":"notes","status":"pending","entry":"20261001T090000Z"},
 {"uuid":"5e4c8a10-2222-4222-8222-000000000002","description":"Write the search tests","project":"notes","status":"pending","entry":"20261001T090100Z"},
 {"uuid":"9f8e7d6c-3333-4333-8333-000000000003","description":"Add the sign-up page","project":"notes","status":"pending","entry":"20261001T090200Z"},
 {"uuid":"77aa66bb-4444-4444-8444-000000000004","description":"Plan the garden beds","project":"garden","status":"pending","entry":"20261001T090300Z"}
]
JSON
task import .task/import.json >/dev/null 2>&1
rm -f .task/import.json
task 0a1b2c3d done >/dev/null 2>&1
task project:notes list >/dev/null 2>&1 || true
