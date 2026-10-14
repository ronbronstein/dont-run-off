Done on the review page. Here are my answers:

# Review answers: Notes app | export review

- review: notes-export · round: Round 1: before we build export · exported: 2026-10-13T09:12:44.000Z
- page: .review/notes-export/index.html
- source: PLAN.md (open decisions 1–4)
- context: A small notes app. Users asked to download their notes. These are the choices the export work needs before the build starts.
- progress: 2/4 answered · 1 not sure · 1 open
- how to read: read these with the `lets-align` skill, step 5 (Read the answers back). status: answered = act on the answer. not_sure = move the item to the next round. open = no answer yet; ask again. matches_recommendation false = the user changed Claude's pick; read the note first. files: kind path = full path; kind name_only = the browser hid the folder, so search for the name.

## The downloaded file

### D1 · File format — answered
- Question: In which format should the notes download?
- Answer: Markdown (Claude's pick)
  - + Opens well in most note apps.
  - − Shows small marks like # in a plain editor.

### D2 · One file or many — answered
- Question: Should the download be one file, or one file per note?
- Answer: One file per note, in a zip (changed; Claude's pick was: One file with all notes)
  - + Each note stays separate.
  - − People must unzip it first.
- Note: Our users move single notes into other apps, so separate files matter more than one click.

### D3 · Deleted notes — not sure
- Question: Should the download include notes that the user deleted?
- Answer: —
- Note: I need to ask two users first.

### D4 · Button place — open
- Question: Where should the download button be?
- Answer: —
