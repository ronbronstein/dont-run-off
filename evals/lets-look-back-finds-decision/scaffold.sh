#!/usr/bin/env bash
# A notes app repo with no decisions file. The sign-up decision lives only in
# two earlier Claude Code sessions, stored where Claude Code keeps them:
# ~/.claude/projects/<this folder's path, with every non-letter-or-digit as "-">/
set -euo pipefail

git init -q -b main
git config user.name "Eval User"
git config user.email "eval-user"
printf '# Notes app\n\nA small notes app.\n' > README.md
printf 'export const notes = [];\n' > app.js
git add . && git commit -q -m "feat: first version"

HERE=$(pwd -P)
DIR="$HOME/.claude/projects/$(printf '%s' "$HERE" | sed 's/[^a-zA-Z0-9]/-/g')"
mkdir -p "$DIR"

line() { # type session time role text
  printf '{"type":"%s","sessionId":"%s","timestamp":"%s","cwd":"%s","gitBranch":"main","message":{"role":"%s","content":%s}}\n' \
    "$1" "$2" "$3" "$HERE" "$4" "$5"
}
A=aaaaaaaa-0000-4000-8000-000000000001
B=aaaaaaaa-0000-4000-8000-000000000002
C=aaaaaaaa-0000-4000-8000-000000000003
{
  line user "$A" 2026-09-20T10:00:00Z user '"Let'"'"'s decide the sign-up method for the notes app."'
  line assistant "$A" 2026-09-20T10:01:00Z assistant '[{"type":"text","text":"Three options for the sign-up method: an email link, a password, or a Google account."}]'
  line user "$A" 2026-09-20T10:04:00Z user '"Go with the email link for the sign-up method. No passwords to reset."'
  line assistant "$A" 2026-09-20T10:05:00Z assistant '[{"type":"text","text":"Agreed: the sign-up method is an email link, because there are no passwords to reset."}]'
  printf '{"type":"custom-title","sessionId":"%s","customTitle":"sign-up page planning"}\n' "$A"
} > "$DIR/$A.jsonl"
{
  line user "$B" 2026-09-28T09:00:00Z user '"Add a search filter to the notes list."'
  line assistant "$B" 2026-09-28T09:02:00Z assistant '[{"type":"text","text":"Done: a text filter on the notes list."}]'
} > "$DIR/$B.jsonl"
{
  line user "$C" 2026-10-05T15:00:00Z user '"Should we revisit the sign-up method? People asked for Google sign-in."'
  line assistant "$C" 2026-10-05T15:02:00Z assistant '[{"type":"text","text":"We keep the email link as the sign-up method for now, and add Google sign-in after the launch."}]'
} > "$DIR/$C.jsonl"
