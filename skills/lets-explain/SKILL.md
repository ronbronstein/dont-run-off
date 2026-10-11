---
name: lets-explain
description: Explain a change that landed, in the user's own language level, with a diagram or a local page when that makes it clearer, then check that the user understands it with a short quiz. For when a change is done and the user wants to understand it before they accept or merge it.
argument-hint: "[the change: a commit, a branch, or what you just did]"
disable-model-invocation: true
---

# Explain

For someone who does not read the diff, understanding the change *is* the review. If they cannot say what changed and why, they cannot catch it when it is wrong. Explain first. Then check the understanding, if the user wants that.

## 1. Read the change

Find what the user means: the last commit, a branch (`git diff <work branch>...HEAD`), or the work of this session. Read the code, the commit messages, and the decision log entry for it. Explain what is really there, not what the plan said.

## 2. Explain, at the user's altitude and in their language level

- **What changed for them:** what they will see, or what now behaves differently. Not a diff dump.
- **Why:** the problem it fixes, or the goal it serves.
- **How it fits** with what was there before.
- **The trade-off:** what you chose, what it rules out, and which real options lost and why.
- **What to check by hand:** one to three things the user can try, and what they should see.

## 3. Use the clearest format

Text is the default. Offer the next format when it helps, and build it only when the user says yes:

- **A diagram,** when the change has a structure: a flow, an order of steps, parts that talk to each other, before and after. Put a Mermaid or plain-text diagram in the reply.
- **A page,** when the change is large, or the user wants something to keep or to show others: one local HTML file with the explanation and its diagrams. Put it in a folder that git does not track, with the same rule as the `lets-align` review page, and give the path.

## 4. Offer the quiz

Ask: "Do you want a short quiz on this?" When the user says yes:

- Ask one question at a time, and wait for each answer.
- Cover what changed; why (at least two questions, because this is where a wrong idea hides); what would break it; and how the user would notice in use.
- Say when an answer is wrong, and why. A vague answer is not a pass.

## 5. Call the result

A pass means real understanding. That is the bar before the user accepts the work. When the user cannot pass after a fair attempt, say which cause you think it is:

- The change is more complex than it needs to be: offer to make it simpler.
- The explanation was not clear: explain again in another way, or in the next format.
- A concept is missing: teach it in 2–4 plain sentences, then ask again.

The user wants to know where the whole project stands, not one change: the `catchup` skill.
