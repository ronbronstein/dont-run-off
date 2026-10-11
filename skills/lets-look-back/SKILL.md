---
name: lets-look-back
description: Use to find and recall what happened in earlier Claude Code sessions of this project — what was decided, said, or tried, and when — and to reopen the right session. Trigger on "what did we decide about X," "when did we…," "find the session where…," "we talked about this before," "look back," or when the user refers to earlier work that the project's records do not explain.
argument-hint: "[what to look for]"
---

# Look back

Find what happened in earlier sessions, and answer from what was actually said. Claude Code keeps each session as a file on this machine, but `/resume` searches only session names and first prompts. A decision made in the middle of a long session is hard to find without this skill.

## 1. Search

Run the search script that sits next to this file, with 2–4 words that matter. Use the user's own words first.

```bash
node "${CLAUDE_SKILL_DIR}/scripts/search.mjs" <words> --exclude ${CLAUDE_SESSION_ID}
```

- `--exclude` skips this session, because it holds the question itself.
- Add `--days N` when the user names a time ("last week"). Add `--all` when the user asks about another project, or when this project has no match and the topic can live elsewhere.
- No match: try a synonym or fewer words once or twice before you say that it is not there.

## 2. Read before you answer

A match on the words is not yet the answer. For the 1–3 best matches, read what was said around them:

```bash
node "${CLAUDE_SKILL_DIR}/scripts/search.mjs" --show <session id> <words>
```

A later session can change an earlier decision, so always read the newest match too.

## 3. Answer

- Lead with the answer: what was decided or done, and the date.
- Support it with 1–3 short quotes. Give each its date and who said it: "you" or "the agent". Quote the words; do not turn a suggestion into a decision.
- When sessions disagree, say which one is newest and what changed.
- Give the command that reopens the most useful session: `claude --resume <session id>`.
- When the sessions do not hold the answer, say so plainly, with what you searched: the words, the number of sessions, and the date range.

## 4. Say what the search cannot see

- It covers only the sessions still on disk, and the script prints how long Claude Code keeps them. When the user needs older history and the period is the default 30 days, say that the setting `cleanupPeriodDays` in `~/.claude/settings.json` keeps sessions longer. Change it only after the user says yes.
- When the script says it could not read a folder, name that folder.
- Session files are private. Quote only what the answer needs.

## 5. Keep it found

When the answer is a decision that the project's decision log does not hold, offer to add it, with its date and the session id. Then the next person who asks finds it without a search.

**Next move:** `lets-catch-up` when the user wants where things stand now, not history.
