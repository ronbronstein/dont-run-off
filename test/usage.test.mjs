// Unit tests for skills/lets-check/usage.mjs. Run: npm test
import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, dirname } from "node:path";
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const SCRIPT = join(
  dirname(fileURLToPath(import.meta.url)),
  "../skills/lets-check/usage.mjs",
);

// A custom config folder, an empty HOME, and a project with its own commands
// and MCP servers.
function fixture() {
  const root = mkdtempSync(join(tmpdir(), "usage-test-"));
  const config = join(root, "config");
  const home = join(root, "home");
  const project = join(root, "project");
  mkdirSync(join(config, "skills", "my-skill"), { recursive: true });
  writeFileSync(join(config, "skills", "my-skill", "SKILL.md"), "---\nname: my-skill\n---\n");
  mkdirSync(join(config, "commands"), { recursive: true });
  writeFileSync(join(config, "commands", "personal-cmd.md"), "Do it.\n");
  writeFileSync(
    join(config, ".claude.json"),
    JSON.stringify({ mcpServers: { "config-server": {} } }),
  );
  mkdirSync(home, { recursive: true });
  mkdirSync(join(project, ".claude", "commands"), { recursive: true });
  writeFileSync(join(project, ".claude", "commands", "project-cmd.md"), "Do it.\n");
  writeFileSync(
    join(project, ".mcp.json"),
    JSON.stringify({ mcpServers: { "project-server": {} } }),
  );
  return { config, home, project };
}

function run({ config, home, project }) {
  const out = execFileSync("node", [SCRIPT, "--json"], {
    cwd: project,
    env: { ...process.env, HOME: home, CLAUDE_CONFIG_DIR: config },
    encoding: "utf8",
  });
  return JSON.parse(out);
}

test("reads skills and commands from CLAUDE_CONFIG_DIR, not only ~/.claude", () => {
  const r = run(fixture());
  assert.ok(r.skills.some((s) => s.name === "my-skill"), "personal skill from the config folder");
  assert.ok(r.commands.some((c) => c.name === "personal-cmd"), "personal command from the config folder");
});

test("reads the project's own commands and .mcp.json servers", () => {
  const r = run(fixture());
  assert.ok(r.commands.some((c) => c.name === "project-cmd"), "project command");
  assert.ok(r.mcpServers.some((m) => m.name === "project-server"), "project MCP server");
});

test("reads MCP server names from .claude.json in the config folder", () => {
  const r = run(fixture());
  assert.ok(r.mcpServers.some((m) => m.name === "config-server"), "config-folder MCP server");
});
