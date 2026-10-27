// Pure helpers for the post-build step (scripts/postbuild.mjs) and the budget check
// (scripts/check-budget.mjs). Tested in scripts/build-lib.test.ts.

import { createHash } from "node:crypto";
import { readdirSync, statSync } from "node:fs";
import { join, posix, relative, sep } from "node:path";

/** Every file under `dir`, as a site path ("/crops/index.html"). */
export function listSite(dir) {
  const out = [];
  const walk = (d) => {
    for (const name of readdirSync(d)) {
      const p = join(d, name);
      if (statSync(p).isDirectory()) walk(p);
      else out.push("/" + relative(dir, p).split(sep).join("/"));
    }
  };
  walk(dir);
  return out.sort();
}

const NOT_A_PAGE = /^\/(404|_not-found)(\/|\.html$)/;

/** Real pages: "/index.html" → "/", "/crops/index.html" → "/crops/". (404 is served by the host.) */
export function pages(files) {
  return files
    .filter((f) => f.endsWith("/index.html") && !NOT_A_PAGE.test(f))
    .map((f) => f.slice(0, -"index.html".length));
}

/** RSC payloads the client fetches when navigating between pages. */
export function rscPayloads(files) {
  return files.filter((f) => f.endsWith(".txt") && !NOT_A_PAGE.test(f));
}

/**
 * The scripts and styles a page loads in a modern browser. `noModule` scripts (legacy polyfills)
 * are skipped: browsers that run the app never download them.
 */
export function pageAssets(html) {
  const out = new Set();
  for (const m of html.matchAll(/<(script|link)\b[^>]*>/g)) {
    const tag = m[0];
    if (/\bnoModule\b/i.test(tag)) continue;
    const ref = tag.match(/\b(?:src|href)="(\/_next\/static\/[^"?#]+\.(?:js|css|woff2))"/);
    if (ref) out.add(ref[1]);
  }
  return [...out];
}

/** Fonts (and other media) a stylesheet pulls in; `cssPath` resolves its relative url()s. */
export function cssAssets(css, cssPath) {
  const out = new Set();
  for (const m of css.matchAll(/url\(\s*["']?([^"')]+)["']?\s*\)/g)) {
    const ref = m[1];
    if (ref.startsWith("data:") || /^[a-z]+:/i.test(ref)) continue;
    out.add(ref.startsWith("/") ? ref : posix.normalize(posix.join(posix.dirname(cssPath), ref)));
  }
  return [...out];
}

/** Bodies of inline <script> elements (no src), exactly as the browser hashes them. */
export function inlineScripts(html) {
  const out = [];
  for (const m of html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/g)) {
    if (/\bsrc=/.test(m[1]) || m[2].length === 0) continue;
    out.push(m[2]);
  }
  return out;
}

export function sha256Base64(text) {
  return createHash("sha256").update(text, "utf8").digest("base64");
}

/** A short version id that changes whenever any precached file's content changes. */
export function versionOf(entries) {
  const h = createHash("sha256");
  for (const [url, content] of [...entries].sort(([a], [b]) => (a < b ? -1 : 1))) {
    h.update(url).update("\0").update(content).update("\0");
  }
  return h.digest("hex").slice(0, 12);
}

/**
 * Content-Security-Policy for the static app. Scripts: our own files plus the exact inline
 * bootstrap scripts Next wrote into the HTML (by hash — no 'unsafe-inline'). Network: ourselves
 * and the API, nothing else.
 * @param {{ scriptHashes: string[], apiBase: string }} opts
 */
export function contentSecurityPolicy({ scriptHashes, apiBase }) {
  const connect = ["'self'", new URL(apiBase).origin];
  const hashes = [...new Set(scriptHashes)].sort().map((h) => `'sha256-${h}'`);
  return [
    "default-src 'self'",
    `script-src 'self' ${hashes.join(" ")}`.trim(),
    "style-src 'self' 'unsafe-inline'", // React style={{…}} attributes (bar heights)
    "img-src 'self' data:",
    "font-src 'self'",
    `connect-src ${connect.join(" ")}`,
    "manifest-src 'self'",
    "worker-src 'self'",
    "object-src 'none'",
    "base-uri 'none'",
    "form-action 'self'",
    "frame-ancestors 'none'",
  ].join("; ");
}

/** Azure Static Web Apps routing + headers (out/staticwebapp.config.json). */
export function staticWebAppConfig({ csp }) {
  return {
    trailingSlash: "auto",
    responseOverrides: { 404: { rewrite: "/404.html" } },
    globalHeaders: {
      "Content-Security-Policy": csp,
      "X-Content-Type-Options": "nosniff",
      "Referrer-Policy": "strict-origin-when-cross-origin",
      "Permissions-Policy": "geolocation=(self), camera=(), microphone=(), payment=()",
      "Strict-Transport-Security": "max-age=31536000",
      // Pages and payloads change every deploy; the service worker is what makes repeat opens instant.
      "Cache-Control": "no-cache",
    },
    routes: [
      { route: "/_next/static/*", headers: { "Cache-Control": "public, max-age=31536000, immutable" } },
      { route: "/sw.js", headers: { "Cache-Control": "no-cache" } },
      // Android verifies the app ↔ site link here. Served from a plain folder: dot-folders are easy
      // for deploy tooling to drop, and a missing file silently turns the app into a browser tab.
      { route: "/.well-known/assetlinks.json", rewrite: ASSET_LINKS_PATH },
    ],
    mimeTypes: { ".webmanifest": "application/manifest+json" },
  };
}

export const ASSET_LINKS_PATH = "/well-known/assetlinks.json";

const SHA256_FINGERPRINT = /^([0-9A-F]{2}:){31}[0-9A-F]{2}$/;

/**
 * Digital Asset Links statement letting the Android app (Trusted Web Activity) open this site full
 * screen. ``twa`` is apps/android/twa-manifest.json; its fingerprints are the SHA-256 of the Play
 * app-signing key (and the upload key, for testing a locally signed build). None yet → null (no
 * file): the app still works, as a Custom Tab with a URL bar. A malformed fingerprint fails the build
 * rather than shipping a link that silently never verifies.
 */
export function assetLinks(twa) {
  const fingerprints = (twa.fingerprints ?? []).map((f) => f.value.trim().toUpperCase());
  const bad = fingerprints.filter((f) => !SHA256_FINGERPRINT.test(f));
  if (bad.length) throw new Error(`twa-manifest.json: not a SHA-256 fingerprint: ${bad.join(", ")}`);
  if (!/^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$/.test(twa.packageId ?? "")) {
    throw new Error(`twa-manifest.json: bad packageId ${JSON.stringify(twa.packageId)}`);
  }
  if (!fingerprints.length) return null;
  return [
    {
      relation: ["delegate_permission/common.handle_all_urls"],
      target: { namespace: "android_app", package_name: twa.packageId, sha256_cert_fingerprints: fingerprints },
    },
  ];
}
