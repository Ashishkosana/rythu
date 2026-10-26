// Rythu service worker: app shell + offline.
//
// Generated per build: scripts/postbuild.mjs copies this file to out/sw.js and fills in VERSION and
// PRECACHE — every page, the scripts/styles/fonts each page loads, the RSC payloads used for
// client-side navigation, and the icons. So after the first visit the whole app opens instantly and
// offline, and a page can never be paired with code from another build.
//
// Data is NOT handled here. API calls are cross-origin and fall through untouched; the app's data
// layer keeps its own saved copy in IndexedDB and says how old it is (lib/query.tsx, lib/freshness.ts).
//
// Updates: a new build means a new sw.js. The browser installs it in the background (all files or
// none), it takes over at once, and the NEXT launch shows the new version — the usual app-shell
// trade-off: an instant open costs one launch of delay for updates.

const VERSION = "__VERSION__";
const PRECACHE = /* __PRECACHE__ */ [];
const CACHE = `rythu-${VERSION}`;

self.addEventListener("install", (event) => {
  event.waitUntil(
    (async () => {
      const cache = await caches.open(CACHE);
      await Promise.all(
        PRECACHE.map(async (url) => {
          // Content-hashed files never change: reuse the previous version's copy instead of
          // downloading it again (an update costs only what actually changed).
          const reusable = url.startsWith("/_next/static/") ? await caches.match(url) : undefined;
          const res = reusable ?? (await fetch(url, { cache: "reload" }));
          if (!res.ok) throw new Error(`precache ${url}: ${res.status}`); // all or nothing
          await cache.put(url, res);
        }),
      );
      await self.skipWaiting();
    })(),
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    (async () => {
      const keys = await caches.keys();
      await Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)));
      await self.clients.claim();
    })(),
  );
});

/** "/crops" and "/crops/?x=1" are both the page stored as "/crops/". */
function pageKey(url) {
  return url.pathname.endsWith("/") || url.pathname.includes(".") ? url.pathname : `${url.pathname}/`;
}

async function fromCache(key) {
  const cache = await caches.open(CACHE);
  return cache.match(key, { ignoreSearch: true });
}

const OFFLINE_HTML =
  "<!doctype html><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'>" +
  "<body style='font-family:system-ui,sans-serif;text-align:center;padding:2rem;color:#1c1917'>" +
  "📴 మీరు ఆఫ్‌లైన్‌లో ఉన్నారు · You are offline</body>";

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return; // the API and everything else cross-origin

  if (req.mode === "navigate") {
    event.respondWith(
      (async () => {
        const cached = await fromCache(pageKey(url));
        if (cached) return cached; // the app shell: instant, and the same build as its scripts
        try {
          return await fetch(req);
        } catch {
          return (
            (await fromCache("/offline/")) ??
            new Response(OFFLINE_HTML, { headers: { "Content-Type": "text/html; charset=utf-8" } })
          );
        }
      })(),
    );
    return;
  }

  // Everything else of ours (scripts, styles, fonts, RSC payloads, icons): cache first. Files that
  // were not precached (a lazily loaded chunk) are kept once fetched; hashed names never go stale.
  event.respondWith(
    (async () => {
      const cached = await fromCache(url.pathname);
      if (cached) return cached;
      const res = await fetch(req);
      if (res.ok && url.pathname.startsWith("/_next/static/")) {
        const copy = res.clone();
        event.waitUntil(caches.open(CACHE).then((c) => c.put(url.pathname, copy)));
      }
      return res;
    })(),
  );
});
