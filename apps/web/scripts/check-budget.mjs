// Performance budget (docs/architecture/README.md): each page's first-load JavaScript, as a modern
// browser downloads it (legacy noModule polyfills excluded), must stay ≤ 170 KB gzipped.
//   npm run check:budget   (after npm run build)

import { readFileSync } from "node:fs";
import { gzipSync } from "node:zlib";
import { listSite, pageAssets, pages } from "./build-lib.mjs";

const BUDGET_KB = 170;
const OUT = new URL("../out/", import.meta.url);
const read = (p) => readFileSync(new URL("." + p, OUT));

let failed = false;
for (const page of pages(listSite(OUT.pathname))) {
  const js = pageAssets(read(`${page}index.html`).toString("utf8")).filter((a) => a.endsWith(".js"));
  const kb = js.reduce((n, a) => n + gzipSync(read(a), { level: 9 }).length, 0) / 1024;
  const ok = kb <= BUDGET_KB;
  failed ||= !ok;
  console.log(`${ok ? "ok  " : "OVER"} ${page.padEnd(12)} ${kb.toFixed(1).padStart(6)} KB gz first-load JS (${js.length} files)`);
}
if (failed) {
  console.error(`\nA page is over the ${BUDGET_KB} KB budget. Lazy-load the heavy part or drop a dependency.`);
  process.exit(1);
}
