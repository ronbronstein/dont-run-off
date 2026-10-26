#!/usr/bin/env node
// Builds the README scenes. Run: npm run art
//
// Each scene has one source, `art/<scene>.svg`, with color tokens like
// `{{ink}}`. `art/palette.json` holds a light and a dark theme with the same
// tokens. The build writes `assets/scene-<scene>-light.svg` and `-dark.svg`,
// and refuses a file that breaks an art rule (GitHub serves the SVG with
// `default-src 'none'`, WebKit does not play the CSS `d` property, and a
// reader with reduced motion gets the still frame).

import { readdirSync, readFileSync, writeFileSync } from "node:fs";
import { join, dirname, basename } from "node:path";
import { fileURLToPath } from "node:url";

const THEMES = ["light", "dark"];

export class ArtError extends Error {
  constructor(code, message) {
    super(message);
    this.name = "ArtError";
    this.code = code;
  }
}

export function renderScene(source, theme) {
  return source.replace(/\{\{\s*([\w-]+)\s*\}\}/g, (_, token) => {
    if (!Object.hasOwn(theme, token))
      throw new ArtError(
        "UNKNOWN_TOKEN",
        `token {{${token}}} is not in the theme`,
      );
    return theme[token];
  });
}

export function checkPalette(palette) {
  const missing = THEMES.filter((t) => !palette[t]);
  if (missing.length)
    throw new ArtError(
      "PALETTE_MISMATCH",
      `palette has no ${missing.join(", ")} theme`,
    );
  const [a, b] = THEMES.map((t) => Object.keys(palette[t]));
  const diff = [
    ...a.filter((k) => !b.includes(k)),
    ...b.filter((k) => !a.includes(k)),
  ];
  if (diff.length)
    throw new ArtError(
      "PALETTE_MISMATCH",
      `light and dark need the same tokens; only in one: ${diff.join(", ")}`,
    );
}

// Returns the art rules that the SVG breaks (empty when it keeps them all).
export function checkScene(svg) {
  const issues = [];
  const styles = [...svg.matchAll(/<style[^>]*>([\s\S]*?)<\/style>/g)]
    .map((m) => m[1])
    .join("\n");
  if (!/class="[^"]*\bmotion\b/.test(svg))
    issues.push("no .motion group (art rule 3)");
  if (!/class="[^"]*\bstill\b/.test(svg))
    issues.push("no .still group (art rule 3)");
  if (!/prefers-reduced-motion:\s*reduce/.test(styles))
    issues.push("no prefers-reduced-motion: reduce rule (art rule 3)");
  const body = svg.replace(/\sxmlns(:\w+)?="[^"]*"/g, "");
  if (/https?:\/\/|@import|<image\b|url\(\s*['"]?(?!#)/.test(body))
    issues.push(
      "an external reference: GitHub loads nothing outside the file (art rule 4)",
    );
  if (/(^|[{;\s])d\s*:/.test(styles))
    issues.push(
      "the CSS `d` property: WebKit does not play it, use SMIL (art rule 1)",
    );
  return issues;
}

// Renders every scene in both themes. Returns [{ file, svg }]; writes nothing.
export function buildAll(root) {
  const artDir = join(root, "art");
  let palette;
  try {
    palette = JSON.parse(readFileSync(join(artDir, "palette.json"), "utf8"));
  } catch (err) {
    throw new ArtError(
      "NO_PALETTE",
      `cannot read art/palette.json: ${err.message}`,
    );
  }
  checkPalette(palette);
  const sources = readdirSync(artDir)
    .filter((f) => f.endsWith(".svg"))
    .sort();
  return sources.flatMap((src) => {
    const scene = basename(src, ".svg");
    const source = readFileSync(join(artDir, src), "utf8");
    return THEMES.map((theme) => {
      const file = `assets/scene-${scene}-${theme}.svg`;
      let svg;
      try {
        svg = renderScene(source, palette[theme]);
      } catch (err) {
        if (err instanceof ArtError)
          err.message = `art/${src} (${theme}): ${err.message}`;
        throw err;
      }
      const issues = checkScene(svg);
      if (issues.length)
        throw new ArtError("ART_RULE", `${file}: ${issues.join("; ")}`);
      return { file, svg };
    });
  });
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const root = join(dirname(fileURLToPath(import.meta.url)), "..");
  try {
    for (const { file, svg } of buildAll(root)) {
      writeFileSync(join(root, file), svg);
      console.log(`wrote ${file}`);
    }
  } catch (err) {
    console.error(err instanceof ArtError ? `build-art: ${err.message}` : err);
    process.exit(1);
  }
}
