# Status line

A status line for Claude Code. It uses Python 3 and only its standard library.

This copy is yours. Change anything: the colors, the icons, the rows, what each row shows.
If you run `/lets-statusline` again to update, the skill names the files that you changed, makes a
backup, and asks before it replaces them.

## What the rows show

All rows sit on one slate band of one width. A thin `│` separates the items. Each bar has its own
design, so that a bar shows what it measures.

1. **Where am I?**
   - The repo, any worktree, and the branch.
   - Uncommitted work (`3 changed · last commit 2h ago`, or `✓ clean`).
   - Commits only when they differ from "in sync": `↑2 not pushed`, `↓3 to pull`,
     `5 ahead of main`, `2 behind main`, `branch not pushed`, `≡1 stashed`.
   - The PR: draft, open, merged, or closed, with its checks, conflicts, and review. A pushed branch
     with no PR shows `no PR`. The base branch shows no PR chip.
   - Last, the session name and age. On a full line, the name goes first and the age stays.
2. **How long can this session go on?**
   - First, the model and the effort: an icon and a color per model, and 5 dots for the effort
     (`◆ Opus 5.5 ●●○○○ medium`). A short line drops the effort word and keeps the dots.
   - The context as a tank that fills (`ctx ▰▰▱▱▱▱▱▱▱▱ 120k`), with `wrap soon` and `wrap now`.
   - The cache countdown: an hourglass, sand that runs down, and the time (`⏳ cache ⣿⣿⣿⣿⣿⣀ 53:12`), or
     `⌛ cache cold · next reply re-reads 295k`. The hourglass turns at each refresh.
   - The active task, and overdue or due-today tasks, when Taskwarrior is in use.
   - Last, the coins `⛁ $7.78`: the session cost at API prices that Claude Code estimates. A
     subscriber does not pay it, so it stays white.
3. **How much usage is left?** Claude Code gives the limits to subscribers. With an API key, this row
   does not show.
   - The 5-hour limit: a meter, the pace, and a countdown (`5h ▮▮▮▯▯▯▯▯▯▯ 26%  ↯ ~6h38m  ◷ 𝟮𝗵𝟰𝟬𝗺`).
     The digits are heavy Unicode digits, because a terminal has one font size.
   - The 7-day limit: one square per day, the pace, and the reset day and time
     (`7d ■□□□□□□ 8%  ↯ ~11d12h  ▦ Fri 00:18`).
   - The pace `↯` (burn rate) says how long the limit lasts at your current speed: `↯ ~6h38m`. It is a
     nudge to use the limit before it resets: amber means much of it will go unused, green means good
     use, and red means you run out before the reset. It shows after the first 10% of a window;
     before that, the speed is noise.

A banner line goes above these rows at a high context level.

## What it needs

- **Required:** Python 3 and git. Tested on macOS with Python 3.9.
- **Optional:** `gh` adds merged and closed PRs, checks, and conflicts. Taskwarrior adds the task chip,
  when a repo names its project in `TASKS.md` or `.taskproject`. Without them, these items do not show.
- **Terminal:** one that shows 24-bit color and these symbols. The colors assume a dark terminal. The
  band has its own dark background, so preview it on a light terminal before you keep it.

## Colors

| Color | Meaning |
|---|---|
| Solid red chip | Act now |
| Solid amber chip | Act soon |
| Slate band | Nothing to do |
| Teal name | The base branch |
| Blue name | Another branch |
| Magenta name | A worktree |
| Amber name | A detached HEAD |
| Green, gray, purple, red PR tag | Open, draft, merged, closed (GitHub's colors) |
| Green, lime, amber, red limit | Percent used: under 50, under 70, under 90, 90 and up. Share of the window left to wait: under 25%, under 50%, under 75%, 75% and up |
| Amber, lime, green, red pace | Projected use at the reset: under 60%, under 85%, under 100%, 100% and up (runs out) |
| Rose `❦`, violet `◆`, sky blue `♪`, mint `✿` | Fable, Opus, Sonnet, Haiku. White `◇`: any other model |

## Refresh and speed

- `refreshInterval` in `~/.claude/settings.json` is 10 seconds, so the countdown moves in 10-second
  steps. `TICK_S` in `sl/seg_context.py` must match it. Claude Code also re-runs the line after a reply
  and when the cache expires.
- Git data comes from a cache, read inline with a 0.5 s limit. A slow repo shows the last good state
  and refreshes in a background job.
- PR data comes from `gh` in a background job only. The line never waits for `gh`.

## Commands

| To do this | Run this |
|---|---|
| See every state in your terminal | `python3 ~/.claude/statusline/preview.py` |
| See only some states | `python3 ~/.claude/statusline/preview.py pr` |
| Run the tests | `cd ~/.claude/statusline && python3 -m unittest discover -s tests -t .` |
| Read the errors | `cat ~/.claude/cache/statusline/errors.log` |

## Where to change what

- `sl/theme.py`: every color.
- `sl/bars.py`: the bar designs.
- `sl/seg_session.py`: the model icons, and the session and task chips.
- `sl/seg_place.py`, `sl/seg_pr.py`, `sl/seg_context.py`, `sl/seg_budget.py`: the items in each row.
- `sl/ladder.py`: the context warning levels and banners.
- `sl/render.py`: which item goes in which row.
- `sl/layout.py`, `sl/fmt.py`: the band and the text formats.
- `sl/payload.py`: reads the JSON from Claude Code.
- `sl/gitstate.py`, `sl/gitcache.py`, `sl/prstate.py`, `sl/tasks.py`: the data sources.
- `sl/background.py`: starts a detached refresh job. `sl/errlog.py`: the error log.
- `statusline.py`: the entry point. It always exits 0.
- `preview.py`: the gallery. `tests/`: the unit tests.
