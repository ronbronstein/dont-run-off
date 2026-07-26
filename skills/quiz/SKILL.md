---
name: quiz
description: Use after a non-trivial change to verify the user actually understands what landed — explain it in plain language, then quiz them until they do. Especially important when the user can't or won't read the diff themselves. Trigger when a change has landed and the user wants to understand or verify it, before accepting or merging, or when the user asks to be quizzed.
---

# Quiz

**This is a verification tool, not a teaching exercise.** For someone who can't audit the code directly, understanding the change *is* their review. If they can't explain what happened and why, they can't catch it when it's wrong — and the quiz is how that gets discovered before it ships rather than after.

## 1. Plain-language report

What changed, why, how it fits the paths that already existed, the intuition behind the approach, and anything that needs verifying by hand. At the user's altitude — the executive version, not a diff dump.

Name the trade-off you made and what it rules out. If you chose between real options, say which ones lost and why.

## 2. Then quiz

One question at a time. Wait for each answer.

Cover:
- **What** changed — do they know which parts of the system are now different?
- **Why** — the reasoning, not just the choice. At least two questions here; this is where misunderstanding hides.
- **What would break it** — what input, state, or edge case would make this go wrong?
- **How they'd know** — what would they observe if this were subtly broken in production?

Say when an answer is wrong, and why. Don't accept a vague answer as a pass.

## 3. Call it

Don't go easy. A pass should mean genuine understanding — that's the bar before accepting the work.

If the user *can't* pass after a fair attempt, that's a real signal, not a failure on their part. It usually means one of three things, and you should say which you think it is:

- The change is more complex than it needs to be → offer to simplify it.
- The explanation was bad → try again differently.
- There's a concept gap → teach it (2–4 plain sentences), then re-ask.
