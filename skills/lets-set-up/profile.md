## Who you're working with

**Altitude.** Explain at a normal technical level. Lead with the decision and the
trade-offs, then the detail if asked.

*Swap in what fits you: "product director — I care about the decision and the
'so what,' not line-by-line mechanics." / "staff engineer — go deep, skip the
hand-holding." / "learning as I go — teach me the concept before using it."*

**Build pipeline.** Shape the work, design it, then implement in small demoable
slices, testing as you go.

**Conventions.** *Your stack, testing bar, and house style — the opinions that
are true for you but not for everyone. Leave blank if you have none yet.
Examples: "Python for scripts, plain HTML/JS for small web tools." / "TDD:
failing test first, 80%+ coverage." / "API responses use `{ success, data,
error }`." / "Immutable — return new objects, never mutate in place."*

**My frictions.** *None recorded yet — this is the highest-value line to fill in.
Naming what usually goes wrong makes the agent watch for it. Common ones: "it
runs off before I've agreed to anything" / "I can't tell what it actually did" /
"I lose the thread between sessions."*

## My setup

The moves read these lines. Change any of them in plain words. A project's
`CLAUDE.md` can repeat a line to change it for that project.

- Status file: `current-state.md`
- Decision log: `DECISIONS.md`
- Tasks: *the tool and where. For example: "Taskwarrior; each repo names its
  project in `TASKS.md`" / "GitHub Issues in this repo" / "none: the status
  file lists what is next."*
- Language: English, strict STE: ASD-STE100 Simplified Technical English. One
  instruction per sentence. Procedural sentences of 20 words or fewer, descriptive
  sentences of 25 or fewer. Active voice, simple tenses, one word for one meaning,
  and the articles "a" and "the". No idioms, slang, or metaphors. A vertical list
  for more than 3 items. You cannot check words against the official STE word
  list, so never claim strict compliance. *(The language first, then the level
  and its text: `lets-set-up` offers strict STE, 80% STE, plain, and technical.
  The two STE levels are for English only.)*
- Stop level: standard — agree on the direction before new work; a nod covers
  the plan. *(Or "careful — show the plan and wait before any change to files,
  even a small one." Or "fast — make the choices that are easy to change
  yourself, and stop only before hard-to-undo steps or when the goal is unclear.")*
- Version control: Git. Commit as you go, one logical change per commit. *(Or "none —
  nothing can undo a change, so the fast stop level works like standard.")*
- Work branch: the repo's default branch. Parallel copies: off.
