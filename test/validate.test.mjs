// Tests for scripts/validate.mjs: the leak check reaches every public text file. Run: npm test
import { test } from "node:test";
import assert from "node:assert/strict";
import { cpSync, mkdtempSync, writeFileSync, appendFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, dirname } from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");

// A copy of the files the validator reads, without git and without the local blocklist.
function copy() {
  const dir = mkdtempSync(join(tmpdir(), "validate-test-"));
  for (const p of [
    "scripts",
    "skills",
    "evals",
    "docs",
    ".claude-plugin",
    "README.md",
    "CONTRIBUTING.md",
  ])
    cpSync(join(ROOT, p), join(dir, p), {
      recursive: true,
      filter: (s) => !s.includes("/results"),
    });
  return dir;
}

const run = (dir) =>
  spawnSync(process.execPath, [join(dir, "scripts/validate.mjs")], {
    encoding: "utf8",
  });

test("a clean copy passes", () => {
  const r = run(copy());
  assert.equal(r.status, 0, r.stderr);
});

test("a leak in a skill's other text file fails", () => {
  const dir = copy();
  appendFileSync(
    join(dir, "skills/lets-check/checks.md"),
    "\nAsk someone@example.com\n",
  );
  const r = run(dir);
  assert.equal(r.status, 1);
  assert.match(r.stderr, /skills\/lets-check\/checks\.md: email address/);
});

test("a leak in a skill's script fails", () => {
  const dir = copy();
  appendFileSync(
    join(dir, "skills/lets-check/usage.mjs"),
    '\n// "/Users/someone/x/"\n',
  );
  const r = run(dir);
  assert.equal(r.status, 1);
  assert.match(r.stderr, /skills\/lets-check\/usage\.mjs: absolute home path/);
});

test("a leak in a docs page fails", () => {
  const dir = copy();
  writeFileSync(join(dir, "docs/extra.md"), "Mail someone@example.com\n");
  const r = run(dir);
  assert.equal(r.status, 1);
  assert.match(r.stderr, /docs\/extra\.md: email address/);
});
