// Rythu offline service worker — so the app opens on patchy Bhupalpally networks.
// Strategy: network-first for pages (fresh when online, last-cached when offline),
// cache-first for static assets. Only ok/same-origin responses are cached, and old
// cache versions are cleaned on activate. Bump CACHE to invalidate everything.

const CACHE = "rythu-v3";
const APP_SHELL = ["/", "/crops", "/schemes", "/account", "/offline", "/manifest.webmanifest", "/icon-192.png"];
const NAV_TIMEOUT_MS = 3500; // don't leave a farmer on a blank screen when the network stalls

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE).then((c) =>
      // Cache each shell URL independently so one failure doesn't drop the rest.
      Promise.allSettled(APP_SHELL.map((u) => c.add(u))),
    ),
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim()),
  );
});

function cachePut(request, response) {
  // Only cache successful, same-origin (basic), non-redirected responses.
  if (response && response.ok && response.type === "basic" && !response.redirected) {
    const copy = response.clone();
    caches.open(CACHE).then((c) => c.put(request, copy)).catch(() => undefined);
  }
  return response;
}

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return; // leave cross-origin alone

  // Pages: network-first WITH A TIMEOUT (a stalled socket is the common rural case —
  // fall back to the cached page fast instead of a blank screen). Fallback order:
  // cached exact page → static /offline → a synthesized offline HTML (always resolves).
  if (req.mode === "navigate") {
    event.respondWith(
      (async () => {
        try {
          const ctrl = new AbortController();
          const timer = setTimeout(() => ctrl.abort(), NAV_TIMEOUT_MS);
          try {
            return cachePut(req, await fetch(req, { signal: ctrl.signal }));
          } finally {
            clearTimeout(timer);
          }
        } catch {
          return (
            (await caches.match(req)) ||
            (await caches.match("/offline")) ||
            new Response(
              "<!doctype html><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'>" +
                "<body style='font-family:system-ui,sans-serif;text-align:center;padding:2rem;color:#1c1917'>" +
                "📴 మీరు ఆఫ్‌లైన్‌లో ఉన్నారు · You are offline</body>",
              { status: 200, headers: { "Content-Type": "text/html; charset=utf-8" } },
            )
          );
        }
      })(),
    );
    return;
  }

  // Cache-first only for genuinely immutable assets: Next's content-hashed
  // /_next/static bundles, and icons/images/fonts. (Mutable JS/CSS outside
  // /_next/static falls through to network-first below, so it can't go stale.)
  const isImmutable =
    url.pathname.startsWith("/_next/static") ||
    url.pathname.startsWith("/icon") ||
    /\.(?:png|jpg|jpeg|svg|webp|woff2?)$/.test(url.pathname);
  if (isImmutable) {
    event.respondWith(
      caches.match(req).then((cached) => cached || fetch(req).then((res) => cachePut(req, res))),
    );
    return;
  }

  // Everything else: try network, fall back to cache if we have it.
  event.respondWith(fetch(req).catch(() => caches.match(req)));
});
