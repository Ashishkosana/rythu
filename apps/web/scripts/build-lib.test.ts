import { mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import {
  contentSecurityPolicy,
  cssAssets,
  inlineScripts,
  listSite,
  pageAssets,
  pages,
  rscPayloads,
  sha256Base64,
  staticWebAppConfig,
  versionOf,
} from "./build-lib.mjs";

const HTML = `<!DOCTYPE html><html><head>
<link rel="preload" href="/_next/static/media/te.p.woff2" as="font" crossorigin=""/>
<link rel="stylesheet" href="/_next/static/chunks/app.css" data-precedence="next"/>
<link rel="icon" href="/icon.png?icon.x.png"/>
<script src="/_next/static/chunks/polyfills.js" noModule=""></script>
</head><body>
<script src="/_next/static/chunks/main.js" async=""></script>
<script>(self.__next_f=self.__next_f||[]).push([0])</script>
<script>self.__next_f.push([1,"a"])</script>
</body></html>`;

describe("site listing", () => {
  it("finds pages (not 404s) and the RSC payloads used for client navigation", () => {
    const dir = mkdtempSync(join(tmpdir(), "rythu-out-"));
    for (const f of ["index.html", "index.txt", "crops/index.html", "crops/__next.crops.__PAGE__.txt",
      "404.html", "404/index.html", "_not-found/index.html", "_not-found/index.txt", "_next/static/chunks/a.js"]) {
      mkdirSync(join(dir, f, ".."), { recursive: true });
      writeFileSync(join(dir, f), "x");
    }
    const files = listSite(dir);
    expect(pages(files)).toEqual(["/crops/", "/"]);
    expect(rscPayloads(files)).toEqual(["/crops/__next.crops.__PAGE__.txt", "/index.txt"]);
  });
});

describe("page assets", () => {
  it("takes what a modern browser loads, never the noModule polyfills or query strings", () => {
    expect(pageAssets(HTML).sort()).toEqual([
      "/_next/static/chunks/app.css",
      "/_next/static/chunks/main.js",
      "/_next/static/media/te.p.woff2",
    ]);
  });

  it("resolves a stylesheet's relative font urls", () => {
    const css = `@font-face{src:url(../media/a.woff2) format("woff2")}x{background:url("data:image/png;base64,AA")}`;
    expect(cssAssets(css, "/_next/static/chunks/app.css")).toEqual(["/_next/static/media/a.woff2"]);
  });
});

describe("CSP", () => {
  it("allows exactly the inline scripts in the HTML, by hash", () => {
    const bodies = inlineScripts(HTML);
    expect(bodies).toEqual(["(self.__next_f=self.__next_f||[]).push([0])", 'self.__next_f.push([1,"a"])']);
    // Known vector: echo -n 'alert(1)' | openssl sha256 -binary | base64
    expect(sha256Base64("alert(1)")).toBe("bhHHL3z2vDgxUt0W3dWQOrprscmda2Y5pLsLg4GF+pI=");
  });

  it("lets the app reach itself and the API, and nothing else", () => {
    const csp = contentSecurityPolicy({ scriptHashes: ["b", "a", "a"], apiBase: "https://api.example.net/x/" });
    expect(csp).toContain("script-src 'self' 'sha256-a' 'sha256-b';");
    expect(csp).toContain("connect-src 'self' https://api.example.net;");
    expect(csp).not.toContain("unsafe-inline' 'sha256"); // scripts never get 'unsafe-inline'
    expect(csp).toContain("frame-ancestors 'none'");
    expect(csp).toContain("object-src 'none'");
  });

  it("connects to the local API in development", () => {
    const csp = contentSecurityPolicy({ scriptHashes: [], apiBase: "http://127.0.0.1:8001" });
    expect(csp).toContain("connect-src 'self' http://127.0.0.1:8001;");
  });
});

describe("Static Web Apps config", () => {
  it("caches hashed files forever, revalidates the rest, and never caches sw.js", () => {
    const cfg = staticWebAppConfig({ csp: "default-src 'self'" });
    expect(cfg.globalHeaders["Cache-Control"]).toBe("no-cache");
    expect(cfg.routes).toContainEqual({ route: "/_next/static/*", headers: { "Cache-Control": "public, max-age=31536000, immutable" } });
    expect(cfg.routes).toContainEqual({ route: "/sw.js", headers: { "Cache-Control": "no-cache" } });
    expect(cfg.trailingSlash).toBe("auto");
  });
});

describe("version", () => {
  it("changes when any file changes, not when the order does", () => {
    const a = versionOf([["/a", "1"], ["/b", "2"]]);
    expect(versionOf([["/b", "2"], ["/a", "1"]])).toBe(a);
    expect(versionOf([["/a", "1"], ["/b", "3"]])).not.toBe(a);
    expect(a).toMatch(/^[0-9a-f]{12}$/);
  });
});
