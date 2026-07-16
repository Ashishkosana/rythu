"use client";

import { useEffect } from "react";

// Registers the offline service worker in production only (skipped in dev to avoid
// stale-cache confusion while developing). Failures are non-fatal.
export default function ServiceWorker() {
  useEffect(() => {
    if (process.env.NODE_ENV !== "production") return;
    if (!("serviceWorker" in navigator)) return;
    navigator.serviceWorker
      .register("/sw.js", { scope: "/", updateViaCache: "none" })
      .catch(() => undefined);
  }, []);
  return null;
}
