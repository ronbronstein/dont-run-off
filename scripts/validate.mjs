#!/usr/bin/env node
// Validates the harness. Run: npm test
//
// Two kinds of check:
//   1. Structural  - always run. Frontmatter, naming, cross-references, and the
//      always-on budget. These are what a contributor's PR gets checked against.
//   2. Leak        - generic patterns (absolute home paths, emails, leftover
//      personalization markers), plus an OPTIONAL private blocklist read from
//      `blocklist.local.txt`. That file is gitignored and never ships: a
//      blocklist naming your private projects is itself a leak.

import { readdirSync, readFileSync, statSync, existsSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const SKILLS = join(ROOT, "skills");
const HARNESS = join(ROOT, "harness");
const MAX_ALWAYS_ON_LINES = 200;

const errors = [];
const warnings = [];

// Generic leak signals — no private names, safe to publish.
const GENERIC_LEAKS = [
  { re: /\/(?:Users|home)\/[a-z0-9._-]+\//i, what: "absolute home path" },
  { re: /[\w.+-]+@[\w-]+\.[\w.]+/, what: "email address" },
  { re: /\[personalize:/i, what: "leftover personalization marker" },
];

// Optional private blocklist, one term or /regex/ per line, # for comments.
const blocklistFile = join(ROOT, "blocklist.local.txt");
const privateBlocklist = existsSync(blocklistFile)
  ? readFileSync(blocklistFile, "utf8")
      .split("\n")
      .map((l) => l.trim())
      .filter((l) => l && !l.startsWith("#"))
      .map((l) =>
        l.startsWith("/") && l.lastIndexOf("/") > 0
          ? new RegExp(
              l.slice(1, l.lastIndexOf("/")),
              l.slice(l.lastIndexOf("/") + 1),
            )
          : new RegExp(
              `\\b${l.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}\\b`,
              "i",
            ),
      )
  : [];

// `profile.md` exists to hold personal detail, and package.json/LICENSE carry
// the author's name and email by design.
const LEAK_EXEMPT = new Set(["harness/profile.md", "package.json", "LICENSE"]);

function checkLeaks(at, text) {
  if (LEAK_EXEMPT.has(at)) return;
  for (const { re, what } of GENERIC_LEAKS) {
    const hit = text.match(re);
    if (hit) errors.push(`${at}: ${what} — ${JSON.stringify(hit[0])}`);
  }
  for (const re of privateBlocklist) {
    const hit = text.match(re);
    if (hit) errors.push(`${at}: private term — ${JSON.stringify(hit[0])}`);
  }
}

// ---------- skills ----------

const dirs = existsSync(SKILLS)
  ? readdirSync(SKILLS).filter((d) => statSync(join(SKILLS, d)).isDirectory())
  : [];

if (dirs.length === 0) errors.push("skills/ is empty or missing");

const names = new Set();

for (const dir of dirs) {
  const at = `skills/${dir}/SKILL.md`;
  const file = join(SKILLS, dir, "SKILL.md");

  if (!existsSync(file)) {
    errors.push(`${at}: missing`);
    continue;
  }

  const text = readFileSync(file, "utf8");
  checkLeaks(at, text);

  const fm = text.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n/);
  if (!fm) {
    errors.push(`${at}: no YAML frontmatter`);
    continue;
  }

  const name = fm[1].match(/^name:\s*(.+)$/m)?.[1].trim();
  const description = fm[1]
    .match(/^description:\s*([\s\S]+?)(?=\n\w+:|$)/m)?.[1]
    .trim();

  if (!name) errors.push(`${at}: frontmatter missing 'name'`);
  else if (name !== dir)
    errors.push(`${at}: name '${name}' does not match directory '${dir}'`);
  else if (!/^[a-z0-9-]+$/.test(name))
    errors.push(`${at}: name must be kebab-case`);

  if (name && names.has(name))
    errors.push(`${at}: duplicate skill name '${name}'`);
  if (name) names.add(name);

  if (!description) errors.push(`${at}: frontmatter missing 'description'`);
  else if (description.length < 40)
    warnings.push(
      `${at}: description is ${description.length} chars — it's how an agent decides to trigger the skill`,
    );

  const body = text.slice(fm[0].length).trim();
  if (!body) errors.push(`${at}: empty body`);

  const lines = body.split("\n").length;
  if (lines > 120)
    warnings.push(
      `${at}: ${lines} lines — long for one skill; is it doing two jobs?`,
    );
}

// Cross-references between skills must resolve.
for (const dir of dirs) {
  const file = join(SKILLS, dir, "SKILL.md");
  if (!existsSync(file)) continue;
  for (const m of readFileSync(file, "utf8").matchAll(
    /`([a-z][a-z0-9-]+)`\s+skill/g,
  )) {
    if (!names.has(m[1]))
      warnings.push(
        `skills/${dir}/SKILL.md: references unknown skill '${m[1]}'`,
      );
  }
}

// ---------- the always-on layer ----------
// Claude Code loads these in full on every message, so size is correctness:
// the docs put the ceiling at 200 lines, past which adherence drops.

let alwaysOnTotal = 0;

for (const f of ["profile.md", "AGENTS.md", "CLAUDE.md"]) {
  const at = `harness/${f}`;
  const path = join(HARNESS, f);

  if (!existsSync(path)) {
    errors.push(`${at}: missing — this is the always-on layer`);
    continue;
  }

  const text = readFileSync(path, "utf8");
  checkLeaks(at, text);
  alwaysOnTotal += text.split("\n").length;

  // Every skill the rules point at must exist, in the routing table or inline.
  // A dangling reference sends the agent hunting for something uninstalled.
  for (const m of text.matchAll(/^\| `([a-z][a-z0-9-]+)` \|/gm)) {
    if (!names.has(m[1]))
      errors.push(`${at}: routes to unknown skill '${m[1]}'`);
  }
  for (const m of text.matchAll(/`([a-z][a-z0-9-]+)`\s+skill/g)) {
    if (!names.has(m[1]))
      errors.push(`${at}: references unknown skill '${m[1]}'`);
  }
}

if (alwaysOnTotal > MAX_ALWAYS_ON_LINES)
  errors.push(
    `always-on layer is ${alwaysOnTotal} lines, over the ${MAX_ALWAYS_ON_LINES}-line budget`,
  );
else if (alwaysOnTotal > MAX_ALWAYS_ON_LINES * 0.8)
  warnings.push(
    `always-on layer is ${alwaysOnTotal} lines, approaching the ${MAX_ALWAYS_ON_LINES}-line budget`,
  );

const claudeMd = existsSync(join(HARNESS, "CLAUDE.md"))
  ? readFileSync(join(HARNESS, "CLAUDE.md"), "utf8")
  : "";
if (claudeMd && !claudeMd.includes("@AGENTS.md"))
  errors.push(
    "harness/CLAUDE.md: must import @AGENTS.md — Claude Code does not read AGENTS.md itself",
  );

const agentsMd = existsSync(join(HARNESS, "AGENTS.md"))
  ? readFileSync(join(HARNESS, "AGENTS.md"), "utf8")
  : "";
if (agentsMd && !agentsMd.includes("@profile.md"))
  errors.push(
    "harness/AGENTS.md: must import @profile.md to pick up personalization",
  );

// ---------- docs and templates ----------

for (const rel of ["README.md", "CONTRIBUTING.md", "docs/architecture.md"]) {
  const path = join(ROOT, rel);
  if (existsSync(path)) checkLeaks(rel, readFileSync(path, "utf8"));
}

// ---------- report ----------

for (const w of warnings) console.warn(`warn   ${w}`);
for (const e of errors) console.error(`ERROR  ${e}`);

const blocklistNote = privateBlocklist.length
  ? `${privateBlocklist.length} private terms`
  : "no local blocklist (structural + generic checks only)";

console.log(
  `\n${dirs.length} skills · always-on ${alwaysOnTotal}/${MAX_ALWAYS_ON_LINES} lines · ${blocklistNote}` +
    `\n${errors.length} errors · ${warnings.length} warnings`,
);

process.exit(errors.length ? 1 : 0);
