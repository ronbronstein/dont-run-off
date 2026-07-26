---
name: shaping
description: Use when deciding whether or what to build or do, sizing or scoping work, shaping an idea into phased slices, or prioritizing. This is the judgment that comes before execution — is this worth doing, how big is it really, how should it be phased. Trigger on "what should I build/do next," "is this worth it," "how big is this," "scope this," "plan this," "prioritize," "phase this," or before committing to any non-trivial piece of work.
---

# Shaping — judgment before execution

Decide *whether and what* before diving into *how*. Scale the effort to the stakes (adaptive rigor): a sentence or two for a small, reversible task; the full pass for a real bet (multi-step, hard to undo, touches users/data, or genuinely uncertain). When you're unsure which it is, say so and ask — that judgment is itself a shaping output.

## The pass

1. **Frame.** What's the real problem or job-to-be-done — and is this a real problem, or a solution in disguise? Name the *riskiest assumption*: the one thing that must be true for this to be worth it. If it's cheap to test, test it before building.
2. **Size.** Ballpark it: **S / M / L / XL** plus an uncertainty flag (low/med/high). Call out where complexity hides — integrations, auth, data, external deps, edge cases, anything not yet understood. Anything that can't be shown or finished in one sitting must be phased.
3. **Worth it?** Read impact vs effort → **go now / later / never**. Name the opportunity cost (what this displaces). Say it plainly if the honest answer is "not worth it."
4. **Phase.** Decompose thinnest-value-first: the **walking skeleton** — the smallest end-to-end demoable thing — then the increments on top. Tag them **Now / Next / Later**. Each phase names its **success signal**: what you'll observe that proves it worked, decided *before* building.

## After shaping

Hand the chosen, framed, sized first slice to your design/build process, then keep work in small demoable slices — one in progress at a time, shown running before it's marked done. New ideas mid-slice go to the backlog, not a detour. Trim ruthlessly (YAGNI).

Hand the slice to the user's build pipeline, and track it in their task tool.
