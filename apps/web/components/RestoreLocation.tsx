"use client";

import { useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { loadPlace } from "@/lib/prefs";
import { inCoverage } from "@/lib/coverage";

// On a cold open with no location in the URL, jump to the farmer's saved village
// so they never re-pick it. Runs once on mount; no-op if a location is already set.
export default function RestoreLocation() {
  const router = useRouter();
  const params = useSearchParams();

  useEffect(() => {
    if (params.get("lat") && params.get("lon")) return; // already located
    const saved = loadPlace();
    // A place saved before coverage existed could be outside it — restoring it would strand the
    // farmer on an error screen at every launch.
    if (!saved || !inCoverage(saved.lat, saved.lon)) return;
    const p = new URLSearchParams(params.toString());
    p.set("lat", String(saved.lat));
    p.set("lon", String(saved.lon));
    p.set("place", saved.place);
    router.replace(`/?${p.toString()}`);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return null;
}
