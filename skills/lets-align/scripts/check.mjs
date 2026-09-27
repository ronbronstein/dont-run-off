#!/usr/bin/env node
// Checks a lets-align data file against the skill's limits before the user sees the page.
// Usage: node check.mjs <path/to/data/current.js>
// Exit 1 on errors (fix them); warnings are judgment calls (read them).
import { readFileSync } from "node:fs";
import vm from "node:vm";

const MAX_REAL = 7; // questions that need the user, per open round
const MAX_DEFAULTS = 12; // items one "accept all" click may decide
const STATUS = new Set(["open", "closed", "done"]);

const file = process.argv[2];
if (!file) {
  console.error("Usage: node check.mjs <path/to/data/current.js>");
  process.exit(2);
}

const sandbox = { window: {} };
try {
  vm.runInNewContext(readFileSync(file, "utf8"), sandbox, {
    filename: file,
    timeout: 1000,
  });
} catch (e) {
  console.error(`ERROR  ${file} does not run: ${e.message}`);
  process.exit(1);
}

const R = sandbox.window.REVIEW;
if (!R || typeof R !== "object") {
  console.error(`ERROR  ${file} does not set window.REVIEW`);
  process.exit(1);
}

const errors = [];
const warns = [];
const err = (at, msg) => errors.push(`${at}: ${msg}`);
const warn = (at, msg) => warns.push(`${at}: ${msg}`);

for (const k of ["id", "title", "context"])
  if (!R[k]) err("REVIEW", `missing '${k}'`);
if (R.id && !/^[\w-]+$/.test(R.id))
  err("REVIEW.id", "use letters, digits, - and _ only (it is the storage key)");
if (R.accent && !/^#[0-9a-f]{6}$/i.test(R.accent))
  err("REVIEW.accent", "use a #RRGGBB color");

// Builder words the person who decides may not know. REVIEW.terms lists words the user
// already uses; those are not flagged.
const JARGON =
  /\b(APIs?|webhooks?|endpoints?|schemas?|data models?|back-?ends?|front-?ends?|components?|deploy(?:s|ed|ment)?|repos?|repositories|cron|SDKs?|OAuth|JWTs?|migrations?|payloads?|middleware|env vars?|cach(?:e|ing))\b/gi;
const known = new Set((R.terms ?? []).map((t) => String(t).toLowerCase()));
const jargonIn = (text) =>
  [
    ...new Set(
      (String(text ?? "").match(JARGON) ?? []).map((w) => w.toLowerCase()),
    ),
  ].filter((w) => !known.has(w));

const rounds = Array.isArray(R.rounds) ? R.rounds : [];
if (!rounds.length) err("REVIEW", "'rounds' must be a non-empty list");

const ids = new Set();
const groupIds = new Set();
let openRounds = 0;

rounds.forEach((rd, ri) => {
  const at = `rounds[${ri}]${rd.id ? ` ${rd.id}` : ""}`;
  if (!rd.id || !rd.title || !rd.needed_by)
    err(at, "needs id, title, and needed_by");
  if (!STATUS.has(rd.status)) err(at, "status must be open, closed, or done");
  const open = rd.status === "open";
  if (open) openRounds++;
  let real = 0;
  let defaults = 0;

  (rd.groups ?? []).forEach((g, gi) => {
    const gat = `${at} > ${g.id ?? `groups[${gi}]`}`;
    if (!g.id || !g.title) err(gat, "a group needs id and title");
    if (g.id === "general")
      err(
        gat,
        "'general' is reserved for the page's own 'Anything else?' group",
      );
    if (groupIds.has(g.id)) err(gat, `duplicate group id '${g.id}'`);
    groupIds.add(g.id);

    (g.items ?? []).forEach((it, ii) => {
      const iat = `${gat} > ${it.id ?? `items[${ii}]`}`;
      const q = it.q ?? "";
      if (!it.id || !it.title || !q) err(iat, "an item needs id, title, and q");
      if (it.id === "NOTE")
        err(iat, "'NOTE' is reserved for the page's own 'Anything else?' item");
      if (ids.has(it.id))
        err(iat, `duplicate item id '${it.id}' (answers are saved by id)`);
      ids.add(it.id);
      const opts = it.options ?? [];
      if (!Array.isArray(opts)) return err(iat, "options must be a list");
      if (!open) return; // closed and done rounds only need id, title, and q

      if (g.defaults) defaults++;
      else real++;
      if (opts.length === 1)
        err(
          iat,
          "one option is not a choice: add another, or make it note-only (no options)",
        );
      if (opts.length > 5)
        warn(
          iat,
          `${opts.length} options are hard to compare; split the question`,
        );
      opts.forEach((o, oi) => {
        const oat = `${iat} > ${o.label ?? `options[${oi}]`}`;
        if (!o.label) err(oat, "missing label");
        if (!o.pro && !o.con) err(oat, "say what happens: add pro and/or con");
      });
      if (
        it.rec != null &&
        !(Number.isInteger(it.rec) && it.rec >= 0 && it.rec < opts.length)
      )
        err(iat, "rec must be the index of one of the options");
      if (g.defaults && it.rec == null)
        err(iat, "an item in a defaults group needs rec: 'accept all' uses it");
      if (g.defaults && it.multi)
        err(
          iat,
          "a defaults item cannot be multi: 'accept all' picks one option",
        );
      if (!g.defaults && opts.length && it.rec == null && !it.multi)
        warn(iat, "no rec: recommend a pick when you have a view");
      if ((q.match(/[.?!](\s|$)/g) ?? []).length > 1)
        warn(iat, "q has more than one sentence: move the rest into 'why'");
      if (q.length > 160)
        warn(iat, `q is ${q.length} characters; keep it to one short sentence`);
      if ((it.why ?? "").length > 240)
        warn(iat, "why is long; keep it to one or two lines");
      const words = jargonIn(
        [
          q,
          it.why,
          it.example,
          ...opts.flatMap((o) => [o.label, o.pro, o.con]),
        ].join(" "),
      );
      if (words.length)
        warn(
          iat,
          `builder words (${words.join(", ")}): say what the user will notice instead, or list the word in REVIEW.terms if the user uses it`,
        );
      const visuals = [it.visual, ...opts.map((o) => o.visual)].filter(Boolean);
      if (visuals.some((v) => /<script|\son\w+=/i.test(v)))
        err(iat, "a visual may not contain scripts or event handlers");
    });
  });

  if (open && real > MAX_REAL)
    err(
      at,
      `${real} questions need the user in this round; the limit is ${MAX_REAL}. Move safe ones into a defaults group and later ones into a closed round`,
    );
  if (open && defaults > MAX_DEFAULTS)
    warn(
      at,
      `${defaults} defaults in one round is a lot to trust to one click`,
    );
});

// No open round is normal between rounds: the page then lists only what comes later.
if (rounds.length && !openRounds)
  console.log(
    rounds.some((r) => r.status === "closed")
      ? "note   no open round: the page shows only the later rounds until one opens"
      : "note   every round is done: keep this file as the record, or archive it as data/<id>.js",
  );

for (const w of warns) console.warn(`warn   ${w}`);
for (const e of errors) console.error(`ERROR  ${e}`);
console.log(
  `\n${ids.size} items · ${rounds.length} rounds · ${errors.length} errors · ${warns.length} warnings`,
);
process.exit(errors.length ? 1 : 0);
