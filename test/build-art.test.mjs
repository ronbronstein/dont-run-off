// Unit tests for scripts/build-art.mjs. Run: npm test
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import {
  ArtError,
  renderScene,
  checkPalette,
  checkScene,
  buildAll,
} from "../scripts/build-art.mjs";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");

const PALETTE = {
  light: { paper: "#f4ecd8", ink: "#3b3a36" },
  dark: { paper: "#1f1d1a", ink: "#e8e0cc" },
};

// The smallest scene that keeps every art rule.
const GOOD = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10">
<style>
.still { display: none; }
@media (prefers-reduced-motion: reduce) {
  .motion { display: none; }
  .still { display: inline; }
  * { animation: none !important; }
}
</style>
<rect width="10" height="10" fill="{{paper}}"/>
<g class="motion"><circle r="1" fill="{{ink}}"/></g>
<g class="still"><circle r="1" fill="{{ink}}"/></g>
</svg>`;

test("renderScene fills each token from the theme", () => {
  const light = renderScene(GOOD, PALETTE.light);
  const dark = renderScene(GOOD, PALETTE.dark);
  assert.match(light, /fill="#f4ecd8"/);
  assert.match(dark, /fill="#1f1d1a"/);
  assert.doesNotMatch(light + dark, /\{\{/);
});

test("renderScene refuses a token that the theme does not have", () => {
  assert.throws(
    () => renderScene('<rect fill="{{fog}}"/>', PALETTE.light),
    (err) =>
      err instanceof ArtError &&
      err.code === "UNKNOWN_TOKEN" &&
      /fog/.test(err.message),
  );
});

test("renderScene does not change the theme object", () => {
  const theme = { ...PALETTE.light };
  renderScene(GOOD, theme);
  assert.deepEqual(theme, PALETTE.light);
});

test("checkPalette refuses themes with different tokens", () => {
  assert.doesNotThrow(() => checkPalette(PALETTE));
  assert.throws(
    () =>
      checkPalette({
        light: { paper: "#fff" },
        dark: { paper: "#000", ink: "#fff" },
      }),
    (err) =>
      err instanceof ArtError &&
      err.code === "PALETTE_MISMATCH" &&
      /ink/.test(err.message),
  );
  assert.throws(
    () => checkPalette({ light: { paper: "#fff" } }),
    (err) => err instanceof ArtError && err.code === "PALETTE_MISMATCH",
  );
});

test("checkScene passes a scene that keeps the art rules", () => {
  assert.deepEqual(checkScene(renderScene(GOOD, PALETTE.light)), []);
});

test("checkScene names each broken art rule", () => {
  const cases = [
    [GOOD.replace('class="motion"', 'class="m"'), /motion/],
    [GOOD.replace('class="still"', 'class="s"'), /still/],
    [
      GOOD.replace("prefers-reduced-motion: reduce", "min-width: 1px"),
      /reduced-motion/,
    ],
    [
      GOOD.replace("<rect", '<image href="https://x.test/a.png"/><rect'),
      /external/,
    ],
    [GOOD.replace("<style>", "<style>@import url(a.css);"), /external/],
    [
      GOOD.replace(
        ".still { display: none; }",
        ".still { display: none; }\n.p { d: path('M0 0'); }",
      ),
      /CSS `d`/,
    ],
  ];
  const anim = (keyTimes, mode = "") =>
    GOOD.replace(
      '<circle r="1" fill="{{ink}}"/></g>',
      `<circle r="1" fill="{{ink}}"><animate attributeName="r" values="1;2;1" keyTimes="${keyTimes}" dur="2s"${mode}/></circle></g>`,
    );
  assert.deepEqual(checkScene(anim("0;0.5;1")), []);
  assert.deepEqual(checkScene(anim("0;0.5;0.9", ' calcMode="discrete"')), []);
  cases.push([anim("0;0.5;0.9"), /keyTimes/]);
  for (const [svg, want] of cases) {
    const issues = checkScene(svg);
    assert.ok(
      issues.some((i) => want.test(i)),
      `want ${want} in ${JSON.stringify(issues)}`,
    );
  }
});

test("the committed scene files match their sources", () => {
  const built = buildAll(ROOT);
  assert.ok(built.length > 0, "no scene sources in art/");
  for (const { file, svg } of built) {
    const onDisk = readFileSync(join(ROOT, file), "utf8");
    assert.equal(onDisk, svg, `${file} is stale: run npm run art`);
  }
});
