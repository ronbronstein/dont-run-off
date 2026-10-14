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
- Language: English, strict STE. *(The language first, then the level: "80% STE",
  "plain", or "technical". The two STE levels are for English only. The method
  says what each one means. STE is ASD-STE100 Simplified Technical English: short,
  plain sentences with one meaning each.)*
- Stop level: standard — stop before anything multi-step, unclear, or hard to
  undo. *(Or "careful — stop and show the plan before any change to files, even
  a small one." Or "fast — stop only before steps that are hard to undo or that
  other people see, or when the goal is unclear.")*
- Version control: Git. Commit as you go, one logical change per commit. *(Or "none":
  then the agent stops before file changes even at the fast level, because nothing can undo them.)*
- Work branch: the repo's default branch. Parallel copies: off.
