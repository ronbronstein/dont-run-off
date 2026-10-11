# A to-do file, or none

No task tool. My setup says where the list lives: a section of the status file (for example "Next"), or a to-do file. Use that place, and create no other task file.

## The stable ID: the item's words

A line in a file has no ID, so use its words: quote the item when you change it. When two items are alike, ask which one.

## The seven steps

| Step | What to do |
|---|---|
| next | The first open item of the list |
| list | The open items |
| add | A new line at the end of the list: `- <title>` (or `- [ ] <title>` when the list uses boxes) |
| start | Add `(in progress, branch <branch>)` to the line |
| note | Add ` — <note>` to the line, or an indented line under it |
| park | Move the line to a "Parked" section, with ` — parked: <reason>` |
| done | Remove the line, or mark it `[x]` when the list keeps finished items |

Keep the list short: a finished item belongs in the status file's story or in the decision log, not in the list forever.

## Parallel copies

Each git branch has its own copy of a file. Two copies that both change the list clash at the merge. When the user works in parallel copies (My setup), change the list only on the work branch, or record the change in your recap and let the merge write it.
