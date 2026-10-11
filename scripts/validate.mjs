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

import {
  readdirSync,
  readFileSync,
  statSync,
  existsSync,
  mkdtempSync,
  writeFileSync,
  rmSync,
} from "node:fs";
import { execFileSync } from "node:child_process";
import { tmpdir } from "node:os";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { EVALS, caseFiles, withMethod } from "./eval-method.mjs";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const SKILLS = join(ROOT, "skills");
const SETUP = join(SKILLS, "lets-set-up");
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
const LEAK_EXEMPT = new Set([
  "skills/lets-set-up/profile.md",
  "package.json",
  "LICENSE",
]);

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

// Redirects: a renamed skill keeps its old name for one release as a skill
// whose description starts with "Old name of <new>". It must run only when
// typed (no always-on cost) and point to a skill that exists.
for (const dir of dirs) {
  const file = join(SKILLS, dir, "SKILL.md");
  if (!existsSync(file)) continue;
  const text = readFileSync(file, "utf8");
  const target = text.match(/^description:\s*Old name of ([a-z0-9-]+)\b/m)?.[1];
  if (!target) continue;
  if (!/^disable-model-invocation:\s*true\s*$/m.test(text))
    errors.push(
      `skills/${dir}/SKILL.md: a redirect must set disable-model-invocation: true, or its description costs context in every session`,
    );
  if (!names.has(target))
    errors.push(`skills/${dir}/SKILL.md: redirects to '${target}', which does not exist`);
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
// The `lets-set-up` skill writes these two into the user's CLAUDE.md, which Claude
// Code then loads in full on every message. Size is correctness: the docs put
// the ceiling at 200 lines, past which adherence drops.

let alwaysOnTotal = 0;

for (const f of ["method.md", "profile.md"]) {
  const at = `skills/lets-set-up/${f}`;
  const path = join(SETUP, f);

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

// The setup skill is what installs the always-on layer, so it has to be able to
// name both halves it writes.
const setupSkill = existsSync(join(SETUP, "SKILL.md"))
  ? readFileSync(join(SETUP, "SKILL.md"), "utf8")
  : "";
if (!setupSkill)
  errors.push("skills/lets-set-up/SKILL.md: missing — nothing installs the harness");
for (const f of ["method.md", "profile.md"])
  if (setupSkill && !setupSkill.includes(f))
    errors.push(`skills/lets-set-up/SKILL.md: never references ${f}`);

// An upgrade replaces the marked block in place, so the marker the skill writes
// has to match the one it looks for.
if (setupSkill && !setupSkill.includes("<!-- dont-run-off:method"))
  errors.push(
    "skills/lets-set-up/SKILL.md: missing the dont-run-off:method marker — upgrades need a target",
  );

// ---------- plugin + marketplace manifests ----------
// These are the install path. Malformed JSON here means `/plugin marketplace
// add` fails for everyone, and nothing else in this file would catch it.

function readJson(rel) {
  const path = join(ROOT, rel);
  if (!existsSync(path)) {
    errors.push(`${rel}: missing — this is how the plugin installs`);
    return null;
  }
  try {
    return JSON.parse(readFileSync(path, "utf8"));
  } catch (e) {
    errors.push(`${rel}: invalid JSON — ${e.message}`);
    return null;
  }
}

const plugin = readJson(".claude-plugin/plugin.json");
const marketplace = readJson(".claude-plugin/marketplace.json");

if (plugin && !plugin.name)
  errors.push(".claude-plugin/plugin.json: missing 'name'");
if (plugin && !plugin.version)
  warnings.push(
    ".claude-plugin/plugin.json: no 'version' — every commit then reads as a new release",
  );

if (marketplace) {
  if (!marketplace.name)
    errors.push(".claude-plugin/marketplace.json: missing 'name'");
  const listed = marketplace.plugins ?? [];
  if (!listed.length)
    errors.push(".claude-plugin/marketplace.json: lists no plugins");
  // A marketplace entry whose name doesn't match the manifest installs a
  // plugin under a name that doesn't exist.
  if (
    plugin?.name &&
    listed.length &&
    !listed.some((p) => p.name === plugin.name)
  )
    errors.push(
      `.claude-plugin/marketplace.json: no entry named '${plugin.name}' to match plugin.json`,
    );
}

// ---------- docs and templates ----------

for (const rel of ["README.md", "CONTRIBUTING.md", "docs/architecture.md"]) {
  const path = join(ROOT, rel);
  if (existsSync(path)) checkLeaks(rel, readFileSync(path, "utf8"));
}

// ---------- eval cases ----------
// The eval runs load no CLAUDE.md, so each case carries a copy of the method
// (see scripts/eval-method.mjs). A stale copy tests old rules. The cases are
// public, so every file under evals/ also gets the leak check; run results
// (evals/results/) are gitignored and skipped.

function filesUnder(dir) {
  return readdirSync(dir, { withFileTypes: true }).flatMap((d) => {
    const path = join(dir, d.name);
    if (d.isDirectory()) return d.name === "results" ? [] : filesUnder(path);
    return [path];
  });
}

const evalCases = caseFiles();

if (existsSync(EVALS)) {
  for (const path of filesUnder(EVALS))
    checkLeaks(path.slice(ROOT.length + 1), readFileSync(path, "utf8"));

  const method = existsSync(join(SETUP, "method.md"))
    ? readFileSync(join(SETUP, "method.md"), "utf8")
    : null;
  for (const { rel, path, profile } of method ? evalCases : []) {
    const text = readFileSync(path, "utf8");
    const result = withMethod(text, method, profile);
    if (result.error) errors.push(`${rel}: ${result.error}`);
    else if (result.found && result.text !== text)
      errors.push(
        `${rel}: its copy of the method is stale — run \`npm run evals:sync\``,
      );
  }
}

// ---------- lets-align data checker ----------
// Agents run this checker before a user sees a review page. The shipped example
// must pass it, and a data file with no `project` must fail it: the tab title
// "<project> | <title>" depends on that field.

const LA = join(SKILLS, "lets-align");
const CHECK = join(LA, "scripts", "check.mjs");
const EXAMPLE = join(LA, "assets", "example-data.js");

function checkerExit(file) {
  try {
    execFileSync(process.execPath, [CHECK, file], { stdio: "pipe" });
    return 0;
  } catch (e) {
    return e.status ?? 1;
  }
}

if (existsSync(CHECK) && existsSync(EXAMPLE)) {
  if (checkerExit(EXAMPLE) !== 0)
    errors.push(
      "skills/lets-align/assets/example-data.js fails skills/lets-align/scripts/check.mjs",
    );
  const tmp = mkdtempSync(join(tmpdir(), "lets-align-check-"));
  const noProject = join(tmp, "no-project.js");
  writeFileSync(
    noProject,
    readFileSync(EXAMPLE, "utf8").replace(/^\s*project:.*\n/m, ""),
  );
  if (checkerExit(noProject) !== 1)
    errors.push(
      "skills/lets-align/scripts/check.mjs accepts a data file with no 'project'",
    );
  rmSync(tmp, { recursive: true, force: true });
}

// ---------- private paths ----------
// These are gitignored on purpose. A forced `git add` would still publish them,
// so fail if git tracks any of them.

const PRIVATE_PATHS = [
  /^workshop\//,
  /^CLAUDE\.local\.md$/,
  /^\.taskproject$/,
  /^blocklist\.local\.txt$/,
];

try {
  const tracked = execFileSync("git", ["ls-files"], {
    cwd: ROOT,
    encoding: "utf8",
  });
  for (const f of tracked.split("\n"))
    if (PRIVATE_PATHS.some((re) => re.test(f)))
      errors.push(
        `${f}: private file is tracked by git — untrack it with \`git rm --cached\``,
      );
} catch {
  warnings.push("git is not available — skipped the private-path check");
}

// ---------- report ----------

for (const w of warnings) console.warn(`warn   ${w}`);
for (const e of errors) console.error(`ERROR  ${e}`);

const blocklistNote = privateBlocklist.length
  ? `${privateBlocklist.length} private terms`
  : "no local blocklist (structural + generic checks only)";

console.log(
  `\n${dirs.length} skills · ${evalCases.length} eval cases · always-on ${alwaysOnTotal}/${MAX_ALWAYS_ON_LINES} lines · ${blocklistNote}` +
    `\n${errors.length} errors · ${warnings.length} warnings`,
);

process.exit(errors.length ? 1 : 0);
