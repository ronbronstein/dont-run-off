---
name: lets-shape
description: Use when deciding whether or what to build or do, sizing or scoping work, shaping an idea into phased slices, or prioritizing. This is the judgment that comes before execution — is this worth doing, how big is it really, how should it be phased. Trigger on "what should I build/do next," "is this worth it," "how big is this," "scope this," "plan this," "prioritize," "phase this," or before committing to any non-trivial piece of work.
---

# Shape — judgment before execution

Shape the work the way one team in one head would: the PM decides whether and what, the architect decides how, the developer cuts it into slices, and QA decides how we will know that it works. The result is a first slice that is ready to build.

Scale the pass to the stakes. A small, reversible task gets three lines: the plan, the size, and the check. A real bet (days of work, hard to undo, touches users or stored data, or truly uncertain) gets the full pass. When you are not sure which one it is, say so: that is a shaping result too.

Read what the shaping needs, and no more: the request, the status file and the decision log, and the code that the work touches.

## 1. Frame (PM)

What is the real problem, and for whom? Check that it is a problem and not a solution that someone already picked. Say what "done" looks like for the user. Name the *riskiest assumption*: the one thing that must be true for this to be worth it. When it is cheap to test, test it before anything else.

## 2. Size and verdict (PM)

- **Size:** S / M / L / XL, with how sure you are (low / medium / high). Say where the size comes from: integrations, sign-in, stored data, outside services, edge cases, and the parts that nobody understands yet.
- **Verdict:** go now / later / never, with the reason and what it pushes aside. When the honest answer is "not worth it", say so plainly.

## 3. Design (architect)

The simplest design that solves the problem now:

- The parts that it adds or changes, and how they connect: a few lines, or a small diagram when there are more than three parts.
- What it reuses from the code that is there.
- The choices that are hard to change later: the shape of stored data, interfaces that others call, outside services, security. These are direction choices. Give your pick and the runner-up for each, and bring them to the user.
- What you leave out on purpose, and what would make you add it later.

Design for the needs that exist, not for ones that might come. When two designs are close and the difference matters, `lets-explore` shows them side by side.

## 4. Slices (developer)

Thinnest value first. Start with the *walking skeleton*: the smallest end-to-end thing that you can show running. Then add the increments on top. Tag each slice **Now / Next / Later**. Each slice is small enough to build, show, and check in one sitting.

## 5. Check plan (QA)

For each slice, decide before you build it how you will know that it works: what you will run or show, and what the user will see. Name the one or two edge cases that matter here (the ones that touch stored data, money, or other people), not every case you can think of. Fit the tests to the risk.

## Hand off

Give the result in one short block: the frame, the size and verdict, the design and its open choices, and the slices with their checks. Ask for the nod once. It covers the whole plan, so build the slices after it without asking again; come back only when what you find changes the plan.

Build one slice at a time, and show each one working before you call it done. A new idea in the middle of a slice goes to the task list, not into the slice.

**Next move:** build the first slice and track it with `lets-track`. When the open choices need many answers, `lets-align`.
