// After `next build` (static export to out/): write the service worker with its precache list and
// version, the Static Web Apps config with a CSP that allows exactly this build's inline scripts, and
// the Android app's Digital Asset Links (from apps/android/twa-manifest.json).
//   node scripts/postbuild.mjs            (run by `npm run build`)

import { mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import {
  ASSET_LINKS_PATH,
  assetLinks,
  contentSecurityPolicy,
  cssAssets,
  inlineScripts,
  listSite,
  pageAssets,
  pages,
  rscPayloads,
  sha256Base64,
  staticWebAppConfig,
  withCspMeta,
  versionOf,
} from "./build-lib.mjs";

const OUT = new URL("../out/", import.meta.url);
const read = (sitePath) => readFileSync(new URL("." + sitePath, OUT));
const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://127.0.0.1:8001";

const files = listSite(OUT.pathname);
const has = new Set(files);
const pageList = pages(files);

const precache = new Set(pageList);
const scriptHashes = [];
for (const page of pageList) {
  const html = read(`${page}index.html`).toString("utf8");
  for (const a of pageAssets(html)) precache.add(a);
  for (const s of inlineScripts(html)) scriptHashes.push(sha256Base64(s));
}
for (const a of [...precache].filter((a) => a.endsWith(".css"))) {
  for (const f of cssAssets(read(a).toString("utf8"), a)) precache.add(f);
}
for (const r of rscPayloads(files)) precache.add(r);
// The favicon is used by every page; the large install icons are fetched by the OS, not by pages.
for (const extra of ["/manifest.webmanifest", "/icon.png"]) {
  if (has.has(extra)) precache.add(extra);
}
// The 404 page's own inline scripts must pass the CSP too.
for (const f of files.filter((f) => f.endsWith(".html") && !pageList.includes(f.replace(/index\.html$/, "")))) {
  for (const s of inlineScripts(read(f).toString("utf8"))) scriptHashes.push(sha256Base64(s));
}

// The CSP goes into every page as a <meta> tag too: the Storage static website sends no headers.
const csp = contentSecurityPolicy({ scriptHashes, apiBase: API_BASE });
for (const f of files.filter((f) => f.endsWith(".html"))) {
  writeFileSync(new URL("." + f, OUT), withCspMeta(read(f).toString("utf8"), csp));
}

const missing = [...precache].filter((u) => !has.has(u.endsWith("/") ? `${u}index.html` : u));
if (missing.length) throw new Error(`precache refers to files not in out/: ${missing.join(", ")}`);

const list = [...precache].sort();
const version = versionOf(list.map((u) => [u, read(u.endsWith("/") ? `${u}index.html` : u)]));
const sw = readFileSync(new URL("../sw/sw.js", import.meta.url), "utf8")
  .replace('"__VERSION__"', JSON.stringify(version))
  .replace("/* __PRECACHE__ */ []", JSON.stringify(list));
if (sw.includes("__VERSION__") || sw.includes("__PRECACHE__")) throw new Error("sw.js placeholders not filled");
writeFileSync(new URL("sw.js", OUT), sw);

const links = assetLinks(JSON.parse(readFileSync(new URL("../../android/twa-manifest.json", import.meta.url), "utf8")));
if (links) {
  // At the real path for the Storage website (no rewrites there), and at the plain one for SWA.
  for (const path of [ASSET_LINKS_PATH, "/.well-known/assetlinks.json"]) {
    mkdirSync(new URL("." + path.replace(/[^/]+$/, ""), OUT), { recursive: true });
    writeFileSync(new URL("." + path, OUT), JSON.stringify(links, null, 2) + "\n");
  }
} else {
  for (const path of [ASSET_LINKS_PATH, "/.well-known/assetlinks.json"]) rmSync(new URL("." + path, OUT), { force: true });
}
writeFileSync(new URL("staticwebapp.config.json", OUT), JSON.stringify(staticWebAppConfig({ csp }), null, 2) + "\n");

const bytes = list.reduce((n, u) => n + read(u.endsWith("/") ? `${u}index.html` : u).length, 0);
console.log(`postbuild: sw ${version} precaches ${list.length} files (${Math.round(bytes / 1024)} KB raw); CSP allows ${new Set(scriptHashes).size} inline scripts; API ${new URL(API_BASE).origin}; asset links: ${links ? links[0].target.sha256_cert_fingerprints.length + " key(s)" : "none yet"}`);
