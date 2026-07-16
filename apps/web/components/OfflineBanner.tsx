"use client";

import { useSyncExternalStore } from "react";

// A quiet, honest "you're offline" pill. Uses the browser's online/offline events
// via useSyncExternalStore (hydration-safe; server assumes online → renders nothing).
function subscribe(cb: () => void) {
  window.addEventListener("online", cb);
  window.addEventListener("offline", cb);
  return () => {
    window.removeEventListener("online", cb);
    window.removeEventListener("offline", cb);
  };
}

export default function OfflineBanner() {
  const online = useSyncExternalStore(
    subscribe,
    () => navigator.onLine,
    () => true,
  );
  if (online) return null;
  return (
    <div className="safe-top pointer-events-none fixed inset-x-0 top-0 z-40 flex justify-center">
      <div className="mt-2 rounded-full bg-stone-800/90 px-4 py-1.5 text-xs font-medium text-white shadow-lg backdrop-blur">
        📴 ఆఫ్‌లైన్ — సేవ్ చేసిన సమాచారం చూపిస్తున్నాం
      </div>
    </div>
  );
}
