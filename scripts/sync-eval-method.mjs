#!/usr/bin/env node
// Copies the current method (skills/setup/method.md) into every eval case.
// Run: npm run evals:sync (npm run evals runs it first).

import { readFileSync, writeFileSync } from "node:fs";
import { METHOD, caseFiles, withMethod } from "./eval-method.mjs";

const method = readFileSync(METHOD, "utf8");
const cases = caseFiles();
const errors = [];
let updated = 0;
let skipped = 0;

for (const { rel, path, profile } of cases) {
  const text = readFileSync(path, "utf8");
  const result = withMethod(text, method, profile);
  if (!result.found) {
    skipped++;
    continue;
  }
  if (result.error) {
    errors.push(`${rel}: ${result.error}`);
    continue;
  }
  if (result.text !== text) {
    writeFileSync(path, result.text);
    updated++;
  }
}

for (const e of errors) console.error(`ERROR  ${e}`);
console.log(
  `${cases.length} eval cases · ${updated} updated · ${skipped} without a method block · ${errors.length} errors`,
);
process.exit(errors.length ? 1 : 0);
