// Unit tests for skills/lets-look-back/scripts/search.mjs. Run: npm test
import { test } from "node:test";
import assert from "node:assert/strict";
import {
  mkdtempSync,
  mkdirSync,
  writeFileSync,
  chmodSync,
  rmSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { join, dirname } from "node:path";
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import {
  encodeProjectPath,
  search,
  show,
} from "../skills/lets-look-back/scripts/search.mjs";

const SCRIPT = join(
  dirname(fileURLToPath(import.meta.url)),
  "../skills/lets-look-back/scripts/search.mjs",
);

// ---------- fixtures: session files the way Claude Code writes them ----------
const PROJECT = "/tmp/notes-app";
const OTHER = "/tmp/garden-plan";
const ID = {
  plan: "aaaaaaaa-0000-4000-8000-000000000001",
  search: "aaaaaaaa-0000-4000-8000-000000000002",
  followup: "aaaaaaaa-0000-4000-8000-000000000003",
  now: "aaaaaaaa-0000-4000-8000-000000000004",
  garden: "bbbbbbbb-0000-4000-8000-000000000001",
};

const user = (sessionId, at, content, extra = {}) => ({
  type: "user",
  sessionId,
  timestamp: at,
  cwd: PROJECT,
  gitBranch: "main",
  message: { role: "user", content },
  ...extra,
});
const agent = (sessionId, at, blocks) => ({
  type: "assistant",
  sessionId,
  timestamp: at,
  cwd: PROJECT,
  gitBranch: "main",
  message: { role: "assistant", content: blocks },
});
const text = (t) => ({ type: "text", text: t });

const sessions = {
  [ID.plan]: [
    user(
      ID.plan,
      "2026-09-20T10:00:00Z",
      "Let's decide the sign-up method for the notes app.",
    ),
    agent(ID.plan, "2026-09-20T10:01:00Z", [
      { type: "thinking", thinking: "secret reasoning about passwords" },
      text(
        "Three options for the sign-up method: an email link, a password, or a Google account.",
      ),
      {
        type: "tool_use",
        id: "t1",
        name: "Read",
        input: { file_path: "PLAN.md" },
      },
    ]),
    user(ID.plan, "2026-09-20T10:01:30Z", [
      {
        type: "tool_result",
        tool_use_id: "t1",
        content: "PLAN.md mentions zebra-sign-up in a tool output",
      },
    ]),
    user(
      ID.plan,
      "2026-09-20T10:04:00Z",
      "Go with the email link for the sign-up method. No passwords to reset.",
    ),
    agent(ID.plan, "2026-09-20T10:05:00Z", [
      text(
        "Recorded in DECISIONS.md: the sign-up method is an email link, because there are no passwords to reset.",
      ),
    ]),
    {
      type: "ai-title",
      sessionId: ID.plan,
      aiTitle: "Planning the sign-up page",
    },
    {
      type: "custom-title",
      sessionId: ID.plan,
      customTitle: "sign-up page planning",
    },
  ],
  [ID.search]: [
    user(
      ID.search,
      "2026-09-28T09:00:00Z",
      "Add a search filter to the notes list.",
    ),
    agent(ID.search, "2026-09-28T09:02:00Z", [
      text("Done: a text filter. The signal is the input event."),
    ]),
    user(
      ID.search,
      "2026-09-28T09:03:00Z",
      "<system-reminder>The sign-up method is a hidden reminder, not the user's words.</system-reminder>Thanks.",
    ),
    user(
      ID.search,
      "2026-09-28T09:03:10Z",
      "<local-command-caveat>Caveat: the sign-up method</local-command-caveat>",
      { isMeta: true },
    ),
    {
      type: "ai-title",
      sessionId: ID.search,
      aiTitle: "Search filter for notes",
    },
  ],
  [ID.followup]: [
    user(
      ID.followup,
      "2026-10-05T15:00:00Z",
      "Should we revisit the sign-up method? People asked for Google sign-in.",
    ),
    agent(ID.followup, "2026-10-05T15:02:00Z", [
      text(
        "We keep the email link as the sign-up method for now, and add Google sign-in after the launch.",
      ),
    ]),
  ],
  [ID.now]: [
    user(
      ID.now,
      "2026-10-11T08:00:00Z",
      "What did we decide about the sign-up method?",
    ),
  ],
};
const gardenSession = [
  {
    ...user(
      ID.garden,
      "2026-10-01T12:00:00Z",
      "The sign-up method for the garden club newsletter is a paper form.",
    ),
    cwd: OTHER,
  },
];

function makeRoot() {
  const root = mkdtempSync(join(tmpdir(), "look-back-test-"));
  const dir = join(root, encodeProjectPath(PROJECT));
  mkdirSync(dir);
  for (const [id, lines] of Object.entries(sessions))
    writeFileSync(
      join(dir, `${id}.jsonl`),
      lines.map((l) => JSON.stringify(l)).join("\n") + "\n",
    );
  const other = join(root, encodeProjectPath(OTHER));
  mkdirSync(other);
  writeFileSync(
    join(other, `${ID.garden}.jsonl`),
    gardenSession.map((l) => JSON.stringify(l)).join("\n") + "\n",
  );
  return root;
}

const opts = (root, extra = {}) => ({
  roots: [root],
  projectPaths: [PROJECT],
  now: new Date("2026-10-11T09:00:00Z"),
  ...extra,
});

// ---------- tests ----------
test("encodes a project path the way Claude Code names its session folder", () => {
  assert.equal(
    encodeProjectPath("/Users/a/Code/my_app.v2"),
    "-Users-a-Code-my-app-v2",
  );
  assert.equal(
    encodeProjectPath("/private/tmp/e-1/home/cwd"),
    "-private-tmp-e-1-home-cwd",
  );
});

test("finds the session where the decision was made, with quotes and the resume command", () => {
  const root = makeRoot();
  const r = search(["sign-up", "method"], opts(root, { exclude: ID.now }));
  const ids = r.matches.map((m) => m.sessionId);
  assert.equal(
    ids[0],
    ID.plan,
    "the session with the most matches comes first",
  );
  assert.ok(ids.includes(ID.followup), "the follow-up session is found too");
  const best = r.matches[0];
  assert.equal(
    best.title,
    "sign-up page planning",
    "the user's own name wins over the generated title",
  );
  assert.equal(best.resume, `claude --resume ${ID.plan}`);
  assert.ok(
    best.quotes.some((q) => q.role === "you" && q.text.includes("email link")),
    "quotes the user's words",
  );
  assert.ok(
    best.quotes.every((q) => q.text.length <= 240),
    "quotes are short",
  );
  rmSync(root, { recursive: true, force: true });
});

test("ignores tool output, hidden reasoning, system reminders and command notes", () => {
  const root = makeRoot();
  assert.equal(
    search(["zebra-sign-up"], opts(root)).matches.length,
    0,
    "tool output",
  );
  assert.equal(
    search(["secret", "reasoning"], opts(root)).matches.length,
    0,
    "hidden reasoning",
  );
  const r = search(["sign-up", "method"], opts(root, { exclude: ID.now }));
  assert.ok(
    !r.matches.some((m) => m.sessionId === ID.search),
    "system reminders and command notes",
  );
  rmSync(root, { recursive: true, force: true });
});

test("skips the current session", () => {
  const root = makeRoot();
  const r = search(["sign-up", "method"], opts(root, { exclude: ID.now }));
  assert.ok(!r.matches.some((m) => m.sessionId === ID.now));
  rmSync(root, { recursive: true, force: true });
});

test("searches only this project by default, and all projects on request", () => {
  const root = makeRoot();
  const here = search(["paper", "form"], opts(root));
  assert.equal(here.matches.length, 0);
  const all = search(["paper", "form"], opts(root, { all: true }));
  assert.equal(all.matches[0]?.sessionId, ID.garden);
  assert.equal(all.matches[0]?.cwd, OTHER);
  rmSync(root, { recursive: true, force: true });
});

test("falls back to some of the words when no message has all of them, and says so", () => {
  const root = makeRoot();
  const r = search(
    ["email", "nonexistentword"],
    opts(root, { exclude: ID.now }),
  );
  assert.equal(r.mode, "some");
  assert.ok(r.matches.length > 0);
  rmSync(root, { recursive: true, force: true });
});

test("limits the search to recent days", () => {
  const root = makeRoot();
  const r = search(
    ["sign-up", "method"],
    opts(root, { exclude: ID.now, days: 10 }),
  );
  assert.deepEqual(
    r.matches.map((m) => m.sessionId),
    [ID.followup],
  );
  rmSync(root, { recursive: true, force: true });
});

test("reports what it searched: the number of sessions and the date range", () => {
  const root = makeRoot();
  const r = search(["sign-up"], opts(root, { exclude: ID.now }));
  assert.equal(r.searched.sessions, 3);
  assert.equal(r.searched.from, "2026-09-20");
  assert.equal(r.searched.to, "2026-10-05");
  rmSync(root, { recursive: true, force: true });
});

test(
  "names a folder it cannot read, and goes on",
  { skip: process.getuid?.() === 0 },
  () => {
    const root = makeRoot();
    const locked = mkdtempSync(join(tmpdir(), "look-back-locked-"));
    chmodSync(locked, 0o000);
    const r = search(["sign-up", "method"], {
      ...opts(root, { exclude: ID.now }),
      roots: [locked, root],
    });
    assert.ok(r.searched.unreadable.includes(locked));
    assert.equal(r.matches[0]?.sessionId, ID.plan);
    chmodSync(locked, 0o700);
    rmSync(locked, { recursive: true, force: true });
    rmSync(root, { recursive: true, force: true });
  },
);

test("show prints the messages around the matches in one session", () => {
  const root = makeRoot();
  const out = show(ID.plan, ["email", "link"], opts(root, { around: 1 }));
  assert.match(out, /Go with the email link/);
  assert.match(out, /Recorded in DECISIONS\.md/);
  assert.doesNotMatch(out, /secret reasoning/);
  rmSync(root, { recursive: true, force: true });
});

test("the command line prints a readable list", () => {
  const root = makeRoot();
  const out = execFileSync(
    process.execPath,
    [
      SCRIPT,
      "sign-up",
      "method",
      "--root",
      root,
      "--cwd",
      PROJECT,
      "--exclude",
      ID.now,
    ],
    { encoding: "utf8" },
  );
  assert.match(out, /sign-up page planning/);
  assert.match(out, new RegExp(`claude --resume ${ID.plan}`));
  assert.match(out, /2026-09-20/);
  rmSync(root, { recursive: true, force: true });
});
