---
name: lets-set-up
description: Use to install, personalize, upgrade, or repair the Don't Run Off harness — writing the method and the user's profile into their CLAUDE.md. Trigger on "set up the harness," "install don't run off," "personalize my CLAUDE.md," "upgrade the harness," or the first run after installing the plugin.
---

# Set Up the Harness

Install the always-on method into `CLAUDE.md` and personalize it. A plugin can ship skills but cannot write `CLAUDE.md` — that's this skill's job.

Two files sit next to this one: `method.md` (the method, same for everyone) and `profile.md` (the personalization template).

**Never overwrite a `CLAUDE.md` as a whole.** The user's own lines took them time to write, and a lost line is hard to notice.

## 1. Pick the target

Ask which, unless it's obvious from what they said:

- **Global** — `~/.claude/CLAUDE.md`. How they want to be worked with everywhere. The default.
- **Project** — `./CLAUDE.md` in the current repo. Facts about *this* codebase, for everyone on it.

A project's `CLAUDE.md` can be shared with a team or be theirs alone, and the files cannot tell you which. When they pick Project, ask once, with a hint from git (`git shortlog -sn HEAD` counts the authors): *"I see 3 people in the git history. Do others use this CLAUDE.md, or only you?"* Ask it with the step 3 facts, not as an extra stop.

- **Only them:** the project file can hold the method and My setup.
- **Shared:** the method and My setup describe one person. Recommend the global file for them, with only project facts in `./CLAUDE.md`. The runner-up is `./CLAUDE.local.md`, which only they load (check that git ignores it, or add it to the file that `git rev-parse --git-path info/exclude` names).

If `~/.claude/CLAUDE.md` has no `<!-- dont-run-off:method` block, say so: a project file with only project facts leaves the method loaded nowhere.

## 2. Read what's already there

Read the target file if it exists. Then check for `<!-- dont-run-off:method` — if present this is an **upgrade**: replace only the text between that marker and `<!-- /dont-run-off:method -->`, leave everything else exactly as it is, and skip to step 5.

An upgrade of a file with no `## My setup` section (set up before My setup existed) adds it first, because the method reads the stop level, the language, and the record files from it. Detect every My setup line with the table in step 3 and confirm them in one message. Then ask only the Language and Stop level questions from step 3, one at a time; if their file already has a rule about how to write replies, propose the Language line that matches it. Write the My setup block from `profile.md` directly below the method block, then go to step 5.

Otherwise it's a fresh install. Read their existing content properly and note anything that overlaps the method — a section on how they want to be talked to, rules about planning, testing, or commits. You'll reconcile these in step 4, not silently duplicate them.

## 3. Detect, then ask only what's left

Detect from the machine — don't ask what you can check:

| Field | How to detect |
|---|---|
| Task tool | `TASKS.md` in the repo says. Else look for each: `task _version` succeeds → Taskwarrior (another tool, go-task, also installs `task`, so `task` on PATH alone is not proof); Linear or Jira tools in your tool list → that tool; a GitHub remote → GitHub Issues. When you find more than one, do not pick: name them and ask which one this work uses. A tool that the `lets-track` skill has no guide for: follow its "your tool" guide with the user. |
| Version control | `git rev-parse` succeeds → Git. Else ask how they keep and undo their work; with nothing, write the full "none" line from `profile.md`, as plain text: it carries the rules for work that nothing can undo. |
| Work branch | `git symbolic-ref --short refs/remotes/origin/HEAD` (strip `origin/`). When that fails (no `origin`, or no HEAD set for it), do not take the current branch, which can be a feature branch: suggest `main` or `master` if one exists, and confirm. |
| Status file | The name the project already uses: `current-state.md`, `STATUS.md`, `docs/status.md`, `PROGRESS.md`, or a similar file that says where things stand. |
| Decision log | The name the project already uses: `DECISIONS.md`, `docs/decisions/`, `docs/adr/`, or similar. |
| Conventions | For a project target: the actual stack, test command, and lint setup. |

Use the names the project already has. A user who keeps `STATUS.md` should not get a second status file because the default is `current-state.md`.

Report what you found and let them correct it: *"I see Taskwarrior, git with `main` as the work branch, a status file at `docs/STATUS.md`, and no decision log. Right?"*

Then ask what detection can't answer — **one question at a time**, not a form:

1. **Altitude.** How do they want to be talked to? Offer the examples from `profile.md` as concrete choices rather than asking an open question.
2. **Language.** Which language, and which level, should the agent's replies use? First suggest the language they write to you in, and let them confirm or change it. Then offer the four levels below, with one line each and a short example sentence. Strict STE is the suggested pick because its short, single-meaning sentences are the easiest to check; a user who finds it stiff picks 80% STE. STE is a standard for English, so for another language offer plain or technical, with plain as the suggested pick. Write the language, the level's name, and the level's text into the Language line ("English, plain: short, everyday words; …"). The method only points to this line, so this line is the whole rule; with no level named, the method writes plain. When their file already has a rule about how to write replies, reconcile it in step 4 instead of adding a second one.
   - *Strict STE* (the suggested pick): ASD-STE100 Simplified Technical English. One instruction per sentence. Procedural sentences of 20 words or fewer, descriptive sentences of 25 or fewer. Active voice, simple tenses, one word for one meaning, and the articles "a" and "the". No idioms, slang, or metaphors. A vertical list for more than 3 items. You cannot check words against the official STE word list, so never claim strict compliance.
   - *80% STE*: the strict STE rules, written out, applied with judgment where a strict rule makes a sentence harder to read.
   - *Plain*: short, everyday words; explain any technical term in one line.
   - *Technical*: precise terms and dense prose, for an expert reader.
3. **Frictions.** What usually goes wrong when they work with an agent? This is the highest-value line in the whole harness and the one people skip. Don't accept a blank — offer the common ones ("it runs off before I've agreed to anything," "I can't tell what it actually did," "I lose the thread between sessions") and let them pick or add their own.
4. **Stop level.** When should the agent stop and ask? Offer the three levels from `profile.md` — careful, standard, fast — with one line each on what changes. Standard is the default: the agent agrees on the direction before new work, and then builds the agreed plan without asking again.
5. **Conventions.** Only if detection left it empty and they seem to have opinions. Blank is a fine answer.

Fill the `profile.md` template with their answers, and write the **My setup** block from what you detected and what they confirmed. A record file they do not want is "none", with where its content goes instead (for example: "Decision log: none. Decisions go in the status file, under 'Decided'."). Delete the italic guidance text as you go — none of it should survive into the final file.

## 4. Reconcile, don't append

If their existing content overlaps the method, say so plainly and propose the merge before writing:

> *"Your 'Role & altitude' section says the same thing as the method's 'How to talk to me.' I'd fold your version into the profile block and drop the duplicate — two sets of instructions saying it differently is how rules start getting ignored. Sound right?"*

Keep anything of theirs the method doesn't cover — move it below the two blocks, untouched.

## 5. Write it

Back up first: copy the existing file to `CLAUDE.md.bak` and tell them where it is. When that name is taken, add the date and time (`CLAUDE.md.2026-03-05-1412.bak`): never overwrite an earlier backup. In a repo, add the backup's name to the exclude file that `git rev-parse --git-path info/exclude` names, so `git add .` does not commit it.

Then write the target as:

```markdown
<!-- dont-run-off:method — managed, replaced on upgrade. Edit below this block. -->
...contents of method.md...
<!-- /dont-run-off:method -->

...their filled-in profile...

...anything of theirs you kept...
```

For a **shared** project file, cut the method down to project facts — stack, commands, conventions, gotchas. The full method belongs in the global file; repeating it per project burns the always-on budget for no gain. When this project differs from the global My setup (another status file, another task tool, another work branch), add a `## My setup` section with only the lines that differ.

## 6. Check what you just installed into

Run the `lets-check` skill. A fresh install lands on top of whatever was already there, and the collisions are silent — a personal skill outranks the plugin copy of the same name, and a slash command with a skill's name wins when typed. Someone can install this, see no errors, and be running none of it.

Report what it finds before offering to fix anything.

## 7. Verify, then hand back

Check the total line count. Over 200 and adherence drops — if it's close, say so and offer to trim.

Tell them to run **`/context`** and confirm the file is listed. An install you haven't verified isn't finished. Then recap in plain language: what you wrote, what you merged or dropped and why, where the backup is, anything `lets-check` flagged, and that the profile content is theirs to edit freely — upgrades only touch the marked block.

**Next move:** `lets-start` in a project.
