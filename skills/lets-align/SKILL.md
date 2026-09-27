---
name: lets-align
description: Use whenever you need answers or decisions from the user before or during work — pinning down a fuzzy ask, collecting the open decisions of a plan or spec, or confirming many small choices at once. It asks in chat when there are only a few quick questions; otherwise it builds a small local review page (plain questions, options with pros and cons, your recommended pick, notes and files, saved in the browser) and reads the pasted answers back. Trigger on "interview me", "what do you need from me", "give me all the decisions", "open questions", "let's align", "too many questions at once", "make me a page to answer", or before any plan that has open decisions, even when the user does not name this skill.
---

# Let's align

Get the answers the work needs, with the least effort for the user, in a form you can act on. Asking well is part of the work: a vague question gets a vague answer, and twenty questions at once get none.

## 1. Collect before you ask

- List every open question the work depends on: from the request, plans and specs, the decision log, the code.
- Settle what you can from evidence yourself. Ask only what is the user's to decide: taste, priorities, money, risk, and facts only they know.
- For each question, note what it blocks and when it is needed.

## 2. Pick the medium

| Situation | Medium |
|---|---|
| 1–3 questions, each answerable in a line, no pictures or files | **Chat.** |
| The goal itself is fuzzy | **Chat, one question at a time.** Each answer changes the next question, so they cannot be batched. Start with the question that changes the most, usually the problem behind the request. Then, one per message: for whom, how you will know it worked, scope in and out, hard limits, edge cases, and examples they like. After about 5–8 answers in total, write a short spec for a nod, and move any remaining concrete choices to a page. |
| 4 or more questions ready at once; options whose effects need spelling out, a picture, or a file; or the user asks for a page | **Review page** (steps 3–5). |

In chat, send one question per message and wait for the answer. A question tool may show up to 4 short questions at once. Never send a numbered list of questions as text: if you are about to, you have a page's worth, so build the page.

## 3. Write questions that are easy to answer

- One decision per question. If a plan line holds two choices, make two questions; if the honest answer would be "it depends", ask about what it depends on.
- One plain sentence per question, in simple words (about A2 English). One line of background at most.
- Write for the person who decides, not for the builder. Leave out builder terms (API, webhook, endpoint, schema, data model, job, component, deploy) unless the user uses them; say what the user will notice instead. "Needs a webhook" becomes "needs a link so the app hears when a payment arrives".
- 2–4 real options. Each one says what happens if it is picked: a `pro`, a `con`, or both. Write concrete results, not adjectives.
- Recommend one option when you have a view, and put the reason in its `pro`. Do not pre-select it: the user picks.
- Add an example when the effect is easy to misread.
- Add a picture only when the choice is about how something looks or where it sits: order, color, logo, direction, layout. Never for process, timing, or cost.

## 4. Build the page

- Copy `assets/review.html` from this skill into the project as `<folder>/index.html`: `docs/review/` when the project has a `docs/` folder, otherwise a folder you and the user agree on. Put everything project-specific in `<folder>/data/current.js`; never edit the page per project. Start from `assets/example-data.js`. The schema is in `references/schema.md`.
- Group the questions into rounds by deadline:
  - The open round holds only what is needed now: at most 7 questions that need the user.
  - Choices with a safe default go into one `defaults` group: collapsed rows, accepted with one click. A default is safe when it is cheap to change later and you would pick it for almost any user in this situation. A choice that changes money, stored data, legal duties, or what people see first is not a default.
  - Later questions go into closed rounds, by the milestone that needs them, with a title and the question only.
- Set `accent` to the project's brand color if it has one (look in its styles or tokens). Otherwise leave it out: the page uses violet on paper.
- Run `node scripts/check.mjs <folder>/data/current.js` from this skill. Fix every error and read every warning.
- Open the page and use it yourself before you hand it over: it loads with no console errors, a pick saves, and Copy Markdown copies. If your preview opens local files as `data:` URLs, serve the folder over http instead. If you cannot open a browser, say so.
- Hand it over in a few lines: the path and the command to open it, how many questions there are and when they are needed, and "click Copy Markdown and paste it here when you are done". Say what you will do with the answers (record them, then propose the next step), not that you will start building. Do not publish, upload, or share the page.

## 5. Read the answers back

- The export says how to read it. Act on `answered` items; for a note-only item, the note is the answer. Ask again about `open` items. When `matches_recommendation` is false, read the note before you act. Search the project for `name_only` files.
- Move each `not_sure` item into the next round with its full content and the same id, in a group of that round (a new group id if needed: group ids are unique across the review).
- Record each decision and its reason in the project's decision log, if it has one.
- Set the answered round to `done`, run the checker again, and keep the page: the user reloads it when the next round opens.
- Reply with a short summary of what you recorded and what you propose next. Then continue under the project's normal rules: a plan still needs its nod.

## Limits

- At most 7 questions for the user in one open round. More means step 1 was skipped, or a `defaults` group is missing.
- Every option on the page has a what-happens line, and no page goes to the user while the checker fails.
- The page is local and private, and it saves only in that one browser. Put no secrets in the data file.
- Change the page itself only here, in this skill's `assets/review.html`, never in a project. That is what makes every project get the same result.

## Hand-offs

- The user wants to see options before any questions: `directions`.
- The decisions are in and the work needs sizing: `shaping`.
- The area is new to the user: `blindspot` first.
