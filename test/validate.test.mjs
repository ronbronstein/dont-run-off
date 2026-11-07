// Tests for scripts/validate.mjs: the leak check reaches every public text file. Run: npm test
import { test } from "node:test";
import assert from "node:assert/strict";
import {
  appendFileSync,
  cpSync,
  mkdirSync,
  mkdtempSync,
  writeFileSync,
} from "node:fs";
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

// A copy that git tracks, for the checks that read `git ls-files` and `git log`.
function repo(email = "someone@public.test") {
  const dir = copy();
  const git = (...args) =>
    spawnSync(
      "git",
      ["-c", `user.email=${email}`, "-c", "user.name=T", ...args],
      {
        cwd: dir,
        encoding: "utf8",
      },
    );
  git("init", "-q");
  git("add", "-A");
  git("commit", "-qm", "base");
  return { dir, git };
}

test("a leak in a tracked file at the top of the repo fails", () => {
  const { dir, git } = repo();
  writeFileSync(join(dir, "NOTES.md"), "Mail someone@example.com\n");
  git("add", "NOTES.md");
  const r = run(dir);
  assert.equal(r.status, 1);
  assert.match(r.stderr, /NOTES\.md: email address/);
});

test("a leak in a tracked Python file fails", () => {
  const { dir, git } = repo();
  writeFileSync(join(dir, "skills/lets-check/x.py"), '# "/Users/someone/x/"\n');
  git("add", "skills/lets-check/x.py");
  const r = run(dir);
  assert.equal(r.status, 1);
  assert.match(r.stderr, /skills\/lets-check\/x\.py: absolute home path/);
});

test("a leak in a tracked dotfile fails", () => {
  const { dir, git } = repo();
  writeFileSync(join(dir, ".somerc"), "# someone@example.com\n");
  git("add", ".somerc");
  const r = run(dir);
  assert.equal(r.status, 1);
  assert.match(r.stderr, /\.somerc: email address/);
});

test("the fake leaks in test files do not fail", () => {
  const { dir, git } = repo();
  mkdirSync(join(dir, "test"));
  writeFileSync(join(dir, "test/x.test.mjs"), "// someone@example.com\n");
  git("add", "test/x.test.mjs");
  const r = run(dir);
  assert.equal(r.status, 0, r.stderr);
});

test("a commit from a blocked author address fails", () => {
  const { dir } = repo("me@work.test");
  writeFileSync(join(dir, "blocklist.local.txt"), "author:work.test\n");
  const r = run(dir);
  assert.equal(r.status, 1);
  assert.match(r.stderr, /commit author or committer: private term/);
});

test("an author term passes other addresses and does not scan files", () => {
  const { dir, git } = repo();
  writeFileSync(join(dir, "NOTES.md"), "work.test is only an author term\n");
  git("add", "NOTES.md");
  writeFileSync(join(dir, "blocklist.local.txt"), "author:work.test\n");
  const r = run(dir);
  assert.equal(r.status, 0, r.stderr);
});
