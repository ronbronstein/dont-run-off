#!/usr/bin/env bash
# Two faults that need the live session next to the files. HOME is a temp
# folder in an eval run; the agent reads these files, but Claude Code does
# not load them. The faults:
#   - ~/.claude/settings.json sets dont-run-off:lets-explore to off, but the
#     plugin's lets-explore is still in the agent's own skill list
#   - the PostToolUse hook appends to runs/_active/trace.log, one fixed file
#     that parallel sessions share
# Fine: old-notes is off and is not in the skill list; the SessionStart
# hook writes under runs/<session_id>/.
set -euo pipefail

git init -q -b main
git config user.name "Eval User"
git config user.email "eval-user"

printf '# Notes app\n\nA small app for notes.\n' > README.md
mkdir -p .claude/hooks
cat > .claude/settings.json <<'JSON'
{
  "hooks": {
    "SessionStart": [
      { "hooks": [ { "type": "command", "command": "bash .claude/hooks/start.sh" } ] }
    ],
    "PostToolUse": [
      { "matcher": "*", "hooks": [ { "type": "command", "command": "bash .claude/hooks/trace.sh" } ] }
    ]
  }
}
JSON
cat > .claude/hooks/start.sh <<'HOOK'
#!/usr/bin/env bash
# Note the start of each session in its own folder.
id=$(jq -r '.session_id')
mkdir -p "runs/$id"
date > "runs/$id/start.log"
HOOK
cat > .claude/hooks/trace.sh <<'HOOK'
#!/usr/bin/env bash
# Append each tool call to the trace of the active run.
mkdir -p runs/_active
jq -c '{tool: .tool_name}' >> runs/_active/trace.log
HOOK
chmod +x .claude/hooks/*.sh
git add . && git commit -q -m "feat: notes app with trace hooks"

C="$HOME/.claude"
mkdir -p "$C/skills/old-notes"
printf -- '---\nname: old-notes\ndescription: Use for the old notes format.\n---\n\nRead the old notes format.\n' > "$C/skills/old-notes/SKILL.md"
cat > "$C/settings.json" <<'JSON'
{
  "skillOverrides": { "dont-run-off:lets-explore": "off", "old-notes": "off" }
}
JSON
