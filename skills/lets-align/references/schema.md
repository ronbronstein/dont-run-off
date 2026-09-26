# lets-align — the data file

The page (`assets/review.html`) is the same in every project. Everything the user sees comes from one
data file, `data/current.js`, in a `data/` folder next to the page. It is plain JavaScript that sets
`window.REVIEW`, so it can use small helper functions for pictures. `assets/example-data.js` shows
every feature; copy it and replace the content.

## Shape

```
REVIEW
  id        letters, digits, - and _. The browser saves answers under this id: keep it the same
            for the whole review; a new review gets a new id.
  title     shown at the top: "<project> · <topic> review"
  context   2–3 sentences for the agent that reads the export: the project, the work, why now
  source?   the files the questions come from (plans, specs, issues)
  page?     the page's path in the repo, repeated in the export (default: the browser's path)
  agent?    the name in "<agent>’s pick" (default "Claude")
  accent?   #RRGGBB, the project's brand color (default violet). The page derives a readable
            text shade and a button text color from it.
  terms?    technical words the user already uses (["API", "webhook"]); the checker then
            does not flag them as builder words
  rounds    Round[]

Round
  id, title ("Round 1: before we build X"), needed_by (the milestone), status: open | closed | done
  groups    Group[]

Group
  id, title, intro?
  defaults? true = collapsed rows with the pick shown, plus one "accept all" button
  items     Item[]

Item
  id        unique in the whole review ("D1", "P3"). Never reuse an id for a different question:
            saved answers are matched by id.
  title     2–4 words (sidebar, rows, export)
  q         one plain sentence
  why?      one line of background
  example?  a concrete case, when the effect is easy to misread
  visual?   HTML picture of the question (see Pictures)
  multi?    true when the user may pick more than one option
  rec?      index of your recommended option (required in a defaults group)
  options   none = a note-only item; otherwise 2–5 Options

Option
  label     the choice, in a few words
  pro?      what gets better if the user picks it
  con?      what it costs; every option has a pro, a con, or both
  visual?   HTML picture of this option
```

Items in closed rounds need only `id`, `title`, and `q`: the page lists them under "What I will ask
later". Fill in their options when the round opens.

## What the page adds by itself

- On every item: "Not sure yet" (the item moves to the next round), a note, and files.
- One "Anything else?" item at the end of the last open round, for a general note and files.
- Reserved: item id `NOTE`, group id `general`.
- Number keys 1–9 pick an option in the card the user is on; "Next open" jumps to the next question
  without an answer; the footer shows the progress, the last save time, and the copy buttons.

## Pictures

Only when the choice is about how something looks or where it sits: order, color, logo, direction,
layout. Never for process, timing, or cost. Keep each one tiny: inline HTML or SVG, no image files,
no scripts, no event handlers (the checker rejects them). Classes the page styles for you:

- `.nv`: a row of parts that wraps on small screens (a menu, a toolbar, a screen outline)
- `.pill`: a solid, button-like chip inside `.nv`
- `.sw`: a color swatch; set its `background` inline

## Files the user attaches

A browser never gives a page the full path of a chosen file, only its name. So the page takes files
in two ways, and the export marks each one:

- a pasted path (`kind: path`, full path; on macOS, ⌥⌘C in Finder copies it)
- a chosen or dropped file (`kind: name_only`: search the project for the name, or ask)

## The export

Markdown or JSON, only for open rounds, with a `how_to_read` line for you. Per item: `id`, `group`,
`title`, `question`, `context`, `status` (`answered` | `not_sure` | `open`), `note_only`, `answer`
(`[{label, pro, con}]`), `recommended`, `matches_recommendation`, `note`, `files`
(`[{name, path, kind}]`), `saved_at`.

## Round lifecycle

1. The open round holds what is needed now. Closed rounds hold later questions, by deadline.
2. When the answers come back, set the round to `done`. Move each `not_sure` item into the next round
   with its full content and the same id, inside a group of that round. Group ids are unique across
   the whole review, so a moved item may need a new group (for example `session-2`).
3. Between rounds there is no open round; the checker notes it, and the page lists only what comes
   later. When the next round is due, fill in its items and set it to `open`. The user reloads the
   same page.
4. To keep a finished review, rename `data/current.js` to `data/<id>.js`. Open it again with
   `index.html?r=<id>`.

## Opening the page

- From disk: open `<folder>/index.html` in a browser. It loads the data file with a script tag, which
  works from disk.
- Some embedded previews open local files as `data:` URLs, which cannot load the data file. Serve the
  folder instead, for example `python3 -m http.server 4330 --directory <folder>`.
