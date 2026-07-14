"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { PILOT_MANDALS } from "@/lib/locations";
import { formatPlaceLabel, roundCoord, searchPlaces, type GeoResult } from "@/lib/geocode";
import { savePlace } from "@/lib/prefs";

// Telugu-first location chooser. Three honest paths to a real coordinate:
//   1. GPS  → the farmer's exact spot (one tap, no typing — best for low literacy)
//   2. Quick-pick verified pilot mandals
//   3. Search any Indian village/town (real geocoding)
// Selecting anything updates ?lat&lon&place while preserving crop/water, so the
// server component re-fetches weather for that point.

export default function LocationPicker({ currentPlace }: { currentPlace: string }) {
  const router = useRouter();
  const params = useSearchParams();
  const [open, setOpen] = useState(false);
  const [gpsBusy, setGpsBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<GeoResult[]>([]);
  const [searching, setSearching] = useState(false);

  function go(lat: number, lon: number, place: string) {
    const rlat = roundCoord(lat);
    const rlon = roundCoord(lon);
    savePlace({ lat: rlat, lon: rlon, place }); // remember for next time
    const p = new URLSearchParams(params.toString());
    p.set("lat", String(rlat));
    p.set("lon", String(rlon));
    p.set("place", place);
    router.push(`/?${p.toString()}`);
    setOpen(false);
  }

  function useGps() {
    if (!("geolocation" in navigator)) {
      setMsg("ఈ ఫోన్‌లో GPS అందుబాటులో లేదు · GPS not available");
      return;
    }
    setGpsBusy(true);
    setMsg(null);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setGpsBusy(false);
        go(pos.coords.latitude, pos.coords.longitude, "నా ప్రాంతం · My location");
      },
      () => {
        setGpsBusy(false);
        setMsg("ప్రాంతం అనుమతి ఇవ్వలేదు · Location permission denied");
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 },
    );
  }

  // Debounced live search. All state updates happen inside the async callback
  // (never synchronously in the effect body) to avoid cascading renders.
  useEffect(() => {
    const q = query.trim();
    const ctrl = new AbortController();
    const id = setTimeout(async () => {
      if (q.length < 2) {
        setResults([]);
        setSearching(false);
        return;
      }
      setSearching(true);
      const r = await searchPlaces(q, ctrl.signal);
      if (!ctrl.signal.aborted) {
        setResults(r);
        setSearching(false);
      }
    }, 300);
    return () => {
      clearTimeout(id);
      ctrl.abort();
    };
  }, [query]);

  return (
    <div className="mb-3">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center justify-between rounded-xl border border-stone-300 bg-white px-4 py-3 text-left"
      >
        <span className="flex items-center gap-2">
          <span aria-hidden>📍</span>
          <span className="font-semibold text-stone-800">{currentPlace}</span>
        </span>
        <span className="text-sm text-green-700">{open ? "మూసివేయి" : "మార్చు · Change"}</span>
      </button>

      {open && (
        <div className="mt-2 space-y-3 rounded-xl border border-stone-200 bg-white p-3">
          <button
            onClick={useGps}
            disabled={gpsBusy}
            className="flex w-full items-center justify-center gap-2 rounded-xl bg-green-600 px-4 py-3 font-semibold text-white disabled:opacity-60"
          >
            <span aria-hidden>🧭</span>
            {gpsBusy ? "వెతుకుతోంది… · Locating…" : "నా ప్రాంతం వాడు · Use my location"}
          </button>
          {msg && <p className="text-center text-sm text-amber-700">{msg}</p>}

          <div>
            <p className="mb-1 text-xs font-medium text-stone-500">భూపాలపల్లి జిల్లా · Quick pick</p>
            <div className="flex flex-wrap gap-2">
              {PILOT_MANDALS.map((m) => (
                <button
                  key={m.name_en}
                  onClick={() => go(m.lat, m.lon, `${m.name_te} · ${m.name_en}`)}
                  className="rounded-full border border-green-600 px-3 py-1.5 text-sm text-green-800"
                >
                  {m.name_te}
                </button>
              ))}
            </div>
          </div>

          <div>
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="మీ ఊరు వెతకండి · Search your village"
              className="w-full rounded-xl border border-stone-300 px-4 py-2.5 outline-none focus:border-green-600"
            />
            {searching && <p className="mt-1 text-xs text-stone-400">వెతుకుతోంది…</p>}
            {results.length > 0 && (
              <ul className="mt-1 max-h-56 overflow-auto rounded-xl border border-stone-200">
                {results.map((r) => (
                  <li key={r.id}>
                    <button
                      onClick={() => go(r.lat, r.lon, formatPlaceLabel(r))}
                      className="flex w-full flex-col items-start px-3 py-2 text-left hover:bg-stone-50"
                    >
                      <span className="font-medium text-stone-800">{r.name}</span>
                      <span className="text-xs text-stone-500">
                        {[r.admin2, r.admin1].filter(Boolean).join(", ")}
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            )}
            {!searching && query.trim().length >= 2 && results.length === 0 && (
              <p className="mt-1 text-xs text-stone-400">ఫలితాలు లేవు · No results</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
