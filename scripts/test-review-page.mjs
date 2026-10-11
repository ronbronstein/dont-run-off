#!/usr/bin/env node
// Browser test of the lets-align review page (skills/lets-align/assets/review.html).
// Run: npm run test:page. Needs Playwright: `import("playwright")`, or set PLAYWRIGHT to the
// path of a playwright package folder. Uses the installed Chrome when it can, else Chromium.

import { createServer } from "node:http";
import { createRequire } from "node:module";
import {
  mkdtempSync,
  readFileSync,
  writeFileSync,
  mkdirSync,
  rmSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { join, dirname, extname } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const PAGE = join(ROOT, "skills/lets-align/assets/review.html");

async function loadPlaywright() {
  const path = process.env.PLAYWRIGHT;
  if (path) return createRequire(import.meta.url)(path);
  return import("playwright");
}

let pw;
try {
  pw = await loadPlaywright();
} catch (e) {
  console.error(
    `Playwright not found (${e.message}).\nInstall it, or set PLAYWRIGHT to a playwright package folder, then run again.`,
  );
  process.exit(2);
}

// ---------- fixtures ----------
const choice = (id, title, q) => ({
  id,
  title,
  q,
  rec: 0,
  options: [
    { label: `${title}: first`, pro: "The first choice." },
    { label: `${title}: second`, con: "The second choice." },
  ],
});
const Q1 = choice("Q1", "Sign-in method", "How should people sign in?");
const Q2 = choice(
  "Q2",
  "Stay signed in",
  "How long should people stay signed in?",
);
const Q3 = choice(
  "Q3",
  "Sign-out button",
  "Where should the sign-out button be?",
);

const base = {
  id: "t-review",
  project: "Notes app",
  title: "sign-in review",
  context: "A test review for the page test.",
};
const round1Open = {
  ...base,
  rounds: [
    {
      id: "r1",
      title: "Round 1: now",
      needed_by: "the build",
      status: "open",
      groups: [{ id: "g1", title: "Now", items: [Q1, Q2] }],
    },
    {
      id: "r2",
      title: "Round 2: later",
      needed_by: "launch",
      status: "closed",
      groups: [
        {
          id: "g2",
          title: "Later",
          items: [{ id: "Q3", title: Q3.title, q: Q3.q }],
        },
      ],
    },
  ],
};
// Round 1 is done. Q2 was "not sure", so it moved into round 2 with the same id.
const round2Open = {
  ...base,
  rounds: [
    {
      id: "r1",
      title: "Round 1: now",
      needed_by: "the build",
      status: "done",
      groups: [{ id: "g1", title: "Now", items: [Q1] }],
    },
    {
      id: "r2",
      title: "Round 2: later",
      needed_by: "launch",
      status: "open",
      groups: [{ id: "g2", title: "Later", items: [Q2, Q3] }],
    },
  ],
};
const { project: _drop, ...noProject } = round1Open;
// The schema lets a note-only item leave out `options`.
const noteOnly = {
  ...base,
  rounds: [
    {
      id: "r1",
      title: "Round 1: now",
      needed_by: "the build",
      status: "open",
      groups: [
        {
          id: "g1",
          title: "Now",
          items: [
            Q1,
            { id: "Q4", title: "Anything to avoid", q: "What must we avoid?" },
          ],
        },
      ],
    },
  ],
};

// ---------- server ----------
const dir = mkdtempSync(join(tmpdir(), "review-page-test-"));
mkdirSync(join(dir, "data"));
writeFileSync(join(dir, "index.html"), readFileSync(PAGE));
const setData = (review) =>
  writeFileSync(
    join(dir, "data/current.js"),
    `window.REVIEW = ${JSON.stringify(review, null, 2)};\n`,
  );

const TYPES = { ".html": "text/html", ".js": "text/javascript" };
const server = createServer((req, res) => {
  const path = new URL(req.url, "http://x").pathname;
  if (path === "/favicon.ico") return res.writeHead(204).end();
  try {
    const body = readFileSync(join(dir, path === "/" ? "index.html" : path));
    res
      .writeHead(200, {
        "content-type": TYPES[extname(path)] ?? "text/plain",
        "cache-control": "no-store",
      })
      .end(body);
  } catch {
    res.writeHead(404).end();
  }
});
await new Promise((ok) => server.listen(0, "127.0.0.1", ok));
const URL_ = `http://127.0.0.1:${server.address().port}/index.html`;

// ---------- browser ----------
const browser = await pw.chromium
  .launch({ channel: "chrome", headless: true })
  .catch(() => pw.chromium.launch({ headless: true }));
const consoleErrors = [];
async function freshPage() {
  const ctx = await browser.newContext({
    permissions: ["clipboard-read", "clipboard-write"],
  });
  const page = await ctx.newPage();
  page.on(
    "console",
    (m) => m.type() === "error" && consoleErrors.push(m.text()),
  );
  page.on("pageerror", (e) => consoleErrors.push(e.message));
  return page;
}
async function show(page, review) {
  setData(review);
  await page.goto(URL_, { waitUntil: "networkidle" });
}
const pill = (page, id) =>
  page.locator(`.card[data-id="${id}"] .pill`).innerText();
const progress = (page) => page.locator("#p").innerText();
const OLD_KEY = "review:t-review";

// ---------- tests ----------
const results = [];
async function test(name, fn) {
  try {
    await fn();
    results.push({ name, ok: true });
  } catch (e) {
    results.push({ name, ok: false, why: e.message });
  }
}
function expectEqual(actual, expected, what) {
  if (actual !== expected)
    throw new Error(
      `${what}: expected ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}`,
    );
}

await test("the tab title is 'project | title'", async () => {
  const page = await freshPage();
  await show(page, round1Open);
  expectEqual(await page.title(), "Notes app | sign-in review", "tab title");
});

await test("without a project, the tab title is the review title", async () => {
  const page = await freshPage();
  await show(page, noProject);
  expectEqual(await page.title(), "sign-in review", "tab title");
});

await test("a new round starts with a clear page", async () => {
  const page = await freshPage();
  await show(page, round1Open);
  await page.locator('.card[data-id="Q1"] .opt').first().click();
  await page.locator('.card[data-id="Q2"] [data-act="unsure"]').click();
  await page
    .locator('.card[data-id="NOTE"] textarea')
    .fill("a note from round 1");
  expectEqual(await progress(page), "1 of 2 answered", "round 1 progress");

  await show(page, round2Open);
  expectEqual(
    await pill(page, "Q2"),
    "Open",
    "Q2 (moved from round 1) in round 2",
  );
  expectEqual(
    await page.locator('.card[data-id="NOTE"] textarea').inputValue(),
    "",
    "the 'Anything else' note in round 2",
  );
  expectEqual(await progress(page), "0 of 2 answered", "round 2 progress");
});

await test("a page copied over an older one keeps answers when no round is done", async () => {
  const page = await freshPage();
  await show(page, round1Open);
  await page.evaluate(
    ([key]) =>
      localStorage.setItem(
        key,
        JSON.stringify({
          Q1: {
            pick: [1],
            note: "",
            files: [],
            unsure: false,
            at: new Date().toISOString(),
          },
        }),
      ),
    [OLD_KEY],
  );
  await page.reload({ waitUntil: "networkidle" });
  if (!(await pill(page, "Q1")).startsWith("Answered"))
    throw new Error("Q1 lost its answer from the older page");
});

await test("an older page's answers do not leak into a later round", async () => {
  const page = await freshPage();
  await show(page, round2Open);
  await page.evaluate(
    ([key]) =>
      localStorage.setItem(
        key,
        JSON.stringify({
          Q2: {
            pick: [],
            note: "",
            files: [],
            unsure: true,
            at: new Date().toISOString(),
          },
        }),
      ),
    [OLD_KEY],
  );
  await page.reload({ waitUntil: "networkidle" });
  expectEqual(
    await pill(page, "Q2"),
    "Open",
    "Q2 in round 2 after an older page saved it as not sure",
  );
});

await test("Copy Markdown names the project and the title", async () => {
  const page = await freshPage();
  await show(page, round1Open);
  await page.locator('.card[data-id="Q1"] .opt').first().click();
  await page.locator('footer [data-f="md"]').click();
  const md = await page.evaluate(() => navigator.clipboard.readText());
  const first = md.split("\n")[0];
  expectEqual(
    first,
    "# Review answers: Notes app | sign-in review",
    "first line of the export",
  );
});

await test("a note-only item with no options key shows as an open card", async () => {
  const page = await freshPage();
  await show(page, noteOnly);
  expectEqual(
    await page.locator('.card[data-id="Q4"]').count(),
    1,
    "cards for Q4",
  );
  expectEqual(await pill(page, "Q4"), "Open", "Q4 status");
  expectEqual(await progress(page), "0 of 2 answered", "progress");
});

await test("no console errors", async () => {
  if (consoleErrors.length) throw new Error(consoleErrors.join(" | "));
});

await browser.close();
server.close();
rmSync(dir, { recursive: true, force: true });

for (const r of results)
  console.log(
    `${r.ok ? "PASS" : "FAIL"}  ${r.name}${r.ok ? "" : `\n      ${r.why}`}`,
  );
const failed = results.filter((r) => !r.ok).length;
console.log(`\n${results.length - failed} passed · ${failed} failed`);
process.exit(failed ? 1 : 0);
