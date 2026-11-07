---
name: lets-statusline
description: Install, update, or undo a rich status line for Claude Code — where you are in git, how long the session can go on, and how much usage is left. It shows a preview and asks before it changes anything. For when the user types this command to get or update the line.
argument-hint: "[undo]"
disable-model-invocation: true
---

# Status line

A plugin cannot set a status line by itself, so this skill copies the code to `~/.claude/statusline/` and writes `statusLine` in `~/.claude/settings.json`. It copies because the plugin folder changes at each update. Nothing changes before the user says yes.

If the user passed `undo`, go to "Undo".

## 1. See what is there

```bash
python3 "${CLAUDE_SKILL_DIR}/install.py" status
```

- **The command fails, or a dialog opens to install developer tools:** Python 3 is not ready. Tell the user to install Python 3, and stop.
- **`platform` starts with `win`:** the line is not tested on Windows. Say so, and stop unless the user wants to try it.

## 2. Tell the user what the line needs

- **Required:** Python 3 and git. Tested on macOS with Python 3.9; say so if `python` is older. If `tools.git` is false, stop.
- **Optional:** `gh` adds merged and closed PRs, checks, and conflicts. Taskwarrior adds a task chip. Name the ones that `tools` shows as missing, and say that those items do not show. Do not offer to install them unless asked.
- **Usage row:** Claude Code gives the 5-hour and 7-day numbers to subscribers. With an API key, this row can stay empty.

## 3. Show the preview

The colors need the user's own terminal. Ask them to run this, with the real path of this skill's folder:

```
! python3 "${CLAUDE_SKILL_DIR}/statusline/preview.py" 140
```

Ask: "Can you read it? Do the colors and the symbols show correctly?"

The colors assume a dark terminal. The line cannot detect a light one, so if `theme` is `light`, or is unset or `auto` and you do not know, ask about this first. On a light terminal the band keeps its own dark background, so look at the edges and at any text outside the band. If the user cannot read it, do not install. Offer to change `sl/theme.py` first, or stop.

## 4. Say what will change, and get a yes

Use `state`:

- **`not-installed`:** a new install.
- **`up-to-date`:** say so. Stop unless the user wants to install it again.
- **`update-available`:** a new version is ready.
- **`not-active`:** the code is current, but `settings.json` runs another line, for example after an undo. Installing makes this line active again.
- **`no-record`:** code is in the folder, but this skill did not install it.

If `changed_by_user` has files, name them. **Warning:** the update replaces those files. The old folder stays as a backup, and the user can copy their changes back from it.

If `current_status_line` holds a line that is not this one, show its command, and say that this replaces it and that `/lets-statusline undo` brings it back.

Say what changes: the code folder, and the `statusLine` key with a 10-second refresh in `settings.json`. All other settings stay the same, and a backup comes first. Ask for a clear yes, and wait for it.

## 5. Install

```bash
python3 "${CLAUDE_SKILL_DIR}/install.py" install
```

If it fails, show the message. It stops before it changes settings that it cannot read.

Report the backup paths from the output, and say that the line shows after the next reply. If it does not, start a new session.

## 6. Tell the user that the line is theirs

Say this in your own words: "You can customize this line however you like: colors, icons, rows, and what each row shows. Ask me to change it, or edit the files yourself. `~/.claude/statusline/README.md` says which file holds what. `python3 ~/.claude/statusline/preview.py` shows the result. To get a new version later, run `/lets-statusline` again; it names the files that you changed and keeps a backup."

## Undo

```bash
python3 "${CLAUDE_SKILL_DIR}/install.py" undo
```

This puts the earlier `statusLine` back, or removes the key if there was none. It keeps all other settings and makes a backup. The code stays in `~/.claude/statusline/`; the user can delete that folder. Ask before you delete it.
