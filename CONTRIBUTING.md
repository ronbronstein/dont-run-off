# Contributing

The toolkit is meant to grow *and shrink*. A skill that isn't pulling its weight should be cut, not kept out of politeness.

## The bar for a skill

A skill has to clear all five:

1. **Agnostic.** No personal names, no specific employers or clients, no one person's workflow. Anything personal belongs in the user's own profile block — the `setup` skill collects it, and skills refer to it rather than embedding it. If you can tell whose setup a skill came from, it isn't ready.
2. **Earns its keep.** It changes what the agent actually does. Restating good intentions ("be careful," "think it through") is not a skill — those get ignored. Every line should alter behavior or be cut.
3. **Small and single-purpose.** One job per skill. If it needs section headers to hold two unrelated jobs, it's two skills.
4. **Triggerable.** The `description` frontmatter is how an agent decides to load it. Write it for that job: say when to use it and include the natural phrases a user would actually type. A vague description means a skill that never fires.
5. **Composable.** It should hand off to other skills by name rather than duplicating them.

## Format

Each skill is a directory under `skills/` with a `SKILL.md`:

```markdown
---
name: kebab-case-name          # must match the directory name
description: When to use this, and the phrases that should trigger it.
---

# Title

Content — imperative, addressed to the agent.
```

Keep the body tight. Most skills here are 15–40 lines. If yours is much longer, it's probably doing two jobs, or explaining rather than instructing.

## Proposing a change

- **New skill** — open an issue first describing the gap it fills and why an existing skill can't. Cheaper to discuss than to write.
- **Editing a skill** — a PR is fine. Say what behavior changes, not just what text changes.
- **Removing a skill** — very welcome. Make the case that it's redundant, never triggers, or doesn't change behavior.

## Testing a skill

### Automated

```bash
npm test
```

Checks frontmatter validity, that each skill's `name` matches its directory, that cross-references resolve, that the always-on layer stays under its 200-line budget, that both plugin manifests parse and agree with each other, and that no absolute home paths, email addresses, or leftover personalization markers made it in. This runs on every pull request.

If you touched `.claude-plugin/`, also run the official manifest check — it validates against the current schema, which `npm test` can't:

```bash
claude plugin validate .
```

It isn't in CI because the `claude` CLI isn't available there.

### Behavioral

The automated check can't tell you whether a skill *works*. Before proposing:

1. Install it into a real agent.
2. Give it a prompt that *should* trigger it, and confirm it fires without you naming the skill.
3. Give it a nearby prompt that should *not* trigger it, and confirm it stays quiet.
4. Confirm the agent's output actually differs from what it does without the skill.

Step 4 is the one people skip. If the output is the same, the skill is decoration.

## Anti-patterns

- Cramming personal preferences into a shared skill, or into the method, instead of the profile block.
- A description that lists topics instead of triggers.
- Duplicating another skill's content instead of pointing at it.
- Long prose explaining *why* to the agent when an instruction would do.
- Skills that only fire if the user knows to ask for them by name.
