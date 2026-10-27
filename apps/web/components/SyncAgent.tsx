"use client";

import { useEffect } from "react";
import { PREFS_EVENT } from "@/lib/prefs";
import { syncProfile } from "@/lib/profileSync";

// Uploads the farmer's choices a moment after they change (and when the phone is back online).
// Does nothing at all unless they agreed to keep a copy on the server (lib/profileSync.ts).
const SETTLE_MS = 2000;

export default function SyncAgent() {
  useEffect(() => {
    let timer: ReturnType<typeof setTimeout> | undefined;
    const soon = () => {
      clearTimeout(timer);
      timer = setTimeout(() => void syncProfile(), SETTLE_MS);
    };
    soon(); // on launch: catch up on changes made offline
    window.addEventListener(PREFS_EVENT, soon);
    window.addEventListener("online", soon);
    return () => {
      clearTimeout(timer);
      window.removeEventListener(PREFS_EVENT, soon);
      window.removeEventListener("online", soon);
    };
  }, []);
  return null;
}
