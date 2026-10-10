#!/usr/bin/env node
// Searches past Claude Code sessions for words, and prints the best matches with short quotes and the
// command that reopens each session. Reads local session files only; sends nothing anywhere.
//
//   node search.mjs <words...> [--exclude <session id>] [--all] [--days N] [--limit N] [--json]
//   node search.mjs --show <session id> [words...] [--around N]
//   Both take [--cwd <project folder>] and [--root <projects folder>] (repeatable), for tests or a
//   custom config folder. Default roots: $CLAUDE_CONFIG_DIR/projects, then ~/.claude/projects.

import { readdirSync, readFileSync, realpathSync } from "node:fs";
import { homedir } from "node:os";
import { join, basename } from "node:path";
import { execFileSync } from "node:child_process";
import { pathToFileURL } from "node:url";

// Claude Code names a project's session folder after the project path, with every character that is
// not a letter or a digit replaced by "-".
export const encodeProjectPath = (path) => path.replace(/[^a-zA-Z0-9]/g, "-");

export function defaultRoots(env = process.env) {
  const roots = [];
  if (env.CLAUDE_CONFIG_DIR)
    roots.push(join(env.CLAUDE_CONFIG_DIR, "projects"));
  roots.push(join(homedir(), ".claude", "projects"));
  return [...new Set(roots)];
}

// This project's paths: the folder, its git root, and every worktree copy of the repo.
export function projectPaths(cwd) {
  const paths = new Set();
  const add = (p) => {
    if (!p) return;
    paths.add(p);
    try {
      paths.add(realpathSync(p));
    } catch {
      // A path that does not exist on disk still names a session folder.
    }
  };
  const git = (args) => {
    try {
      return execFileSync("git", args, {
        cwd,
        encoding: "utf8",
        stdio: ["ignore", "pipe", "ignore"],
      }).trim();
    } catch {
      return ""; // Not a git repo, or no git: the folder alone is the project.
    }
  };
  add(cwd);
  add(git(["rev-parse", "--show-toplevel"]));
  for (const line of git(["worktree", "list", "--porcelain"]).split("\n"))
    if (line.startsWith("worktree ")) add(line.slice("worktree ".length));
  return [...paths];
}

function sessionFiles(roots, { all, paths }) {
  const wanted = new Set(paths.map(encodeProjectPath));
  const files = [];
  const unreadable = [];
  for (const root of roots) {
    let dirs;
    try {
      dirs = readdirSync(root, { withFileTypes: true })
        .filter((d) => d.isDirectory())
        .map((d) => d.name);
    } catch (e) {
      if (e.code !== "ENOENT") unreadable.push(root);
      continue;
    }
    for (const dir of dirs) {
      if (!all && !wanted.has(dir)) continue;
      try {
        for (const name of readdirSync(join(root, dir)))
          if (name.endsWith(".jsonl")) files.push(join(root, dir, name));
      } catch {
        unreadable.push(join(root, dir));
      }
    }
  }
  return { files, unreadable };
}

// Text that Claude Code adds to a user turn, which the user did not write.
const ADDED =
  /<(system-reminder|local-command-caveat|local-command-stdout|local-command-stderr)>[\s\S]*?<\/\1>/g;
const clean = (s) =>
  s
    .replace(ADDED, " ")
    .replace(/<\/?[a-zA-Z][\w-]*>/g, " ")
    .replace(/\s+/g, " ")
    .trim();

// What a person reads in the conversation: the user's words and the agent's text replies. Not tool
// calls, tool output, hidden reasoning, subagent turns, or Claude Code's own notes.
function messageText(d) {
  if (d.isMeta || d.isSidechain) return "";
  const content = d.message?.content;
  if (typeof content === "string") return clean(content);
  if (!Array.isArray(content)) return "";
  return clean(
    content
      .filter((b) => b?.type === "text" && typeof b.text === "string")
      .map((b) => b.text)
      .join("\n"),
  );
}

export function readSession(file) {
  const s = {
    sessionId: null,
    cwd: null,
    branch: null,
    first: null,
    last: null,
    messages: [],
  };
  let custom = null;
  let ai = null;
  let summary = null;
  let firstPrompt = null;
  for (const line of readFileSync(file, "utf8").split("\n")) {
    if (!line) continue;
    let d;
    try {
      d = JSON.parse(line);
    } catch {
      continue; // A line cut off while the session was writing.
    }
    s.sessionId ??= d.sessionId ?? null;
    if (d.type === "custom-title" && d.customTitle) custom = d.customTitle;
    else if (d.type === "ai-title" && d.aiTitle) ai = d.aiTitle;
    else if (d.type === "summary" && d.summary) summary = d.summary;
    if (d.type !== "user" && d.type !== "assistant") continue;
    if (d.timestamp) {
      s.first ??= d.timestamp;
      s.last = d.timestamp;
    }
    const text = messageText(d);
    if (!text) continue;
    s.cwd ??= d.cwd ?? null;
    s.branch = d.gitBranch ?? s.branch;
    if (d.type === "user") firstPrompt ??= text;
    s.messages.push({
      role: d.type === "user" ? "you" : "agent",
      at: d.timestamp ?? null,
      text,
    });
  }
  s.sessionId ??= basename(file, ".jsonl");
  s.title =
    custom ??
    ai ??
    summary ??
    (firstPrompt ? firstPrompt.slice(0, 60) : "(no name)");
  return s;
}

const terms = (words) =>
  words.map((w) => String(w).toLowerCase().trim()).filter(Boolean);
const countIn = (text, ts) => {
  const low = text.toLowerCase();
  return ts.filter((t) => low.includes(t)).length;
};

function snippet(text, ts, max = 220) {
  if (text.length <= max) return text;
  const low = text.toLowerCase();
  const found = ts.map((t) => low.indexOf(t)).filter((p) => p >= 0);
  const pos = found.length ? Math.min(...found) : 0;
  const start = Math.max(0, Math.min(pos - 60, text.length - max));
  return (
    (start > 0 ? "…" : "") +
    text.slice(start, start + max) +
    (start + max < text.length ? "…" : "")
  );
}

// The first match shows the question; the last match of each side usually holds the conclusion.
function pickQuotes(hits) {
  const lastOf = (role) => [...hits].reverse().find((h) => h.m.role === role);
  const picked = [hits[0], lastOf("you"), lastOf("agent")].filter(Boolean);
  return [...new Set(picked)].sort((a, b) => a.i - b.i).slice(0, 3);
}

function loadSessions(o) {
  const roots = o.roots ?? defaultRoots();
  const paths = o.projectPaths ?? projectPaths(o.cwd ?? process.cwd());
  const { files, unreadable } = sessionFiles(roots, { all: o.all, paths });
  const since = o.days
    ? new Date((o.now ?? new Date()).getTime() - o.days * 864e5)
    : null;
  const sessions = [];
  for (const file of files) {
    let s;
    try {
      s = readSession(file);
    } catch {
      unreadable.push(file);
      continue;
    }
    if (s.sessionId === o.exclude || !s.messages.length) continue;
    if (since && s.last && new Date(s.last) < since) continue;
    sessions.push(s);
  }
  return { roots, sessions, unreadable };
}

export function search(words, o = {}) {
  const ts = terms(words);
  if (!ts.length) throw new Error("search needs at least one word");
  const { roots, sessions, unreadable } = loadSessions(o);
  const find = (need) =>
    sessions
      .map((s) => ({
        s,
        hits: s.messages
          .map((m, i) => ({ m, i, n: countIn(m.text, ts) }))
          .filter((h) => h.n >= need),
      }))
      .filter((x) => x.hits.length);
  let mode = "all";
  let found = find(ts.length);
  if (!found.length && ts.length > 1) {
    mode = "some";
    found = find(1);
  }
  const weight = (x) => x.hits.reduce((sum, h) => sum + h.n, 0);
  found.sort(
    (a, b) =>
      weight(b) - weight(a) || String(b.s.last).localeCompare(String(a.s.last)),
  );
  const dates = sessions
    .flatMap((s) => [s.first, s.last])
    .filter(Boolean)
    .sort();
  return {
    words: ts,
    mode,
    total: found.length,
    matches: found.slice(0, o.limit ?? 5).map(({ s, hits }) => ({
      sessionId: s.sessionId,
      title: s.title,
      cwd: s.cwd,
      branch: s.branch,
      first: s.first,
      last: s.last,
      hits: hits.length,
      quotes: pickQuotes(hits).map((h) => ({
        role: h.m.role,
        at: h.m.at,
        text: snippet(h.m.text, ts),
      })),
      resume: `claude --resume ${s.sessionId}`,
    })),
    searched: {
      sessions: sessions.length,
      from: dates[0]?.slice(0, 10) ?? null,
      to: dates.at(-1)?.slice(0, 10) ?? null,
      all: !!o.all,
      roots,
      unreadable,
    },
  };
}

// The messages around the matches in one session (or, with no words, what the user asked and how the
// session ended), so the agent can read the context before it answers.
export function show(sessionId, words = [], o = {}) {
  const { sessions } = loadSessions({
    ...o,
    all: true,
    exclude: undefined,
    days: undefined,
  });
  const s = sessions.find((x) => x.sessionId === sessionId);
  if (!s)
    throw new Error(
      `no session ${sessionId} in ${(o.roots ?? defaultRoots()).join(", ")}`,
    );
  const ts = terms(words);
  const keep = new Set();
  if (ts.length) {
    let hit = s.messages
      .map((m, i) => (countIn(m.text, ts) === ts.length ? i : -1))
      .filter((i) => i >= 0);
    if (!hit.length)
      hit = s.messages
        .map((m, i) => (countIn(m.text, ts) ? i : -1))
        .filter((i) => i >= 0);
    const around = o.around ?? 2;
    for (const i of hit)
      for (
        let j = Math.max(0, i - around);
        j <= Math.min(s.messages.length - 1, i + around);
        j++
      )
        keep.add(j);
  } else {
    s.messages.forEach((m, i) => m.role === "you" && keep.add(i));
    keep.add(s.messages.length - 1);
  }
  const lines = [
    `# ${s.title} · ${stamp(s.first)} to ${stamp(s.last)} · branch ${s.branch ?? "?"}`,
    `Reopen: claude --resume ${s.sessionId}`,
    "",
  ];
  let prev = -1;
  for (const i of [...keep].sort((a, b) => a - b)) {
    if (prev >= 0 && i > prev + 1) lines.push("[…]");
    const m = s.messages[i];
    const text = m.text.length > 700 ? `${m.text.slice(0, 700)}…` : m.text;
    lines.push(`[${m.role}, ${stamp(m.at)}] ${text}`);
    prev = i;
  }
  return lines.join("\n");
}

// How long Claude Code keeps session files (setting cleanupPeriodDays; the default is 30 days).
export function keepDays(env = process.env) {
  const dirs = [env.CLAUDE_CONFIG_DIR, join(homedir(), ".claude")].filter(
    Boolean,
  );
  for (const dir of dirs) {
    try {
      const days = JSON.parse(
        readFileSync(join(dir, "settings.json"), "utf8"),
      ).cleanupPeriodDays;
      if (Number.isFinite(days))
        return { days, source: join(dir, "settings.json") };
    } catch {
      // No settings file, or no setting in it: try the next one.
    }
  }
  return { days: 30, source: null };
}

const pad = (n) => String(n).padStart(2, "0");
function stamp(at) {
  if (!at) return "?";
  const d = new Date(at);
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function report(r, keep) {
  const where = r.searched.all ? "all projects" : "this project";
  const range = r.searched.from
    ? `, ${r.searched.from} to ${r.searched.to}`
    : "";
  const out = [
    `Searched ${r.searched.sessions} sessions of ${where}${range}. Words: ${r.words.join(" ")}`,
  ];
  if (r.mode === "some")
    out.push("No message has all the words. These messages have some of them.");
  if (!r.matches.length)
    out.push(
      "",
      "No match. Try other words, fewer words, or --all for every project.",
    );
  r.matches.forEach((m, n) => {
    out.push(
      "",
      `${n + 1}. ${m.title} · ${stamp(m.first).slice(0, 10)} · branch ${m.branch ?? "?"} · ${m.hits} matching messages`,
    );
    for (const q of m.quotes)
      out.push(`   ${q.role}, ${stamp(q.at)}: "${q.text}"`);
    if (r.searched.all && m.cwd) out.push(`   Folder: ${m.cwd}`);
    out.push(`   Reopen: ${m.resume}`);
  });
  if (r.total > r.matches.length)
    out.push(
      "",
      `${r.total - r.matches.length} more sessions match. Use --limit to see them.`,
    );
  for (const u of r.searched.unreadable) out.push("", `Could not read: ${u}`);
  out.push(
    "",
    keep.source
      ? `Claude Code keeps sessions for ${keep.days} days (cleanupPeriodDays in ${keep.source}).`
      : "Claude Code keeps sessions for 30 days by default (setting: cleanupPeriodDays).",
  );
  return out.join("\n");
}

function parseArgs(argv) {
  const o = { words: [] };
  const num = (flag, v) => {
    const n = Number(v);
    if (!Number.isInteger(n) || n < 0)
      throw new Error(`${flag} needs a whole number, not "${v}"`);
    return n;
  };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--all") o.all = true;
    else if (a === "--json") o.json = true;
    else if (a === "--days" || a === "--limit" || a === "--around")
      o[a.slice(2)] = num(a, argv[++i]);
    else if (a === "--exclude") o.exclude = argv[++i];
    else if (a === "--show") o.show = argv[++i];
    else if (a === "--cwd") o.cwd = argv[++i];
    else if (a === "--root") (o.roots ??= []).push(argv[++i]);
    else if (a === "--help" || a === "-h") o.help = true;
    else if (a.startsWith("--")) throw new Error(`unknown option ${a}`);
    else o.words.push(a);
  }
  return o;
}

function main() {
  const o = parseArgs(process.argv.slice(2));
  if (o.help || (!o.show && !o.words.length)) {
    console.log(
      readFileSync(new URL(import.meta.url), "utf8")
        .split("\n")
        .slice(1, 8)
        .join("\n")
        .replace(/^\/\/ ?/gm, ""),
    );
    return;
  }
  if (o.show) return console.log(show(o.show, o.words, o));
  const r = search(o.words, o);
  console.log(
    o.json
      ? JSON.stringify({ ...r, keep: keepDays() }, null, 2)
      : report(r, keepDays()),
  );
}

if (
  process.argv[1] &&
  import.meta.url === pathToFileURL(realpathSync(process.argv[1])).href
) {
  try {
    main();
  } catch (e) {
    console.error(`lets-look-back search: ${e.message}`);
    process.exit(1);
  }
}
