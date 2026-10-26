"use client";

import { useRef, useState, type FormEvent } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { PILOT_MANDALS } from "@/lib/locations";
import { formatPlaceLabel, isSearchable, MAX_QUERY, placeName, roundCoord, searchPlaces } from "@/lib/geocode";
import type { Place } from "@/lib/types";
import { savePlace } from "@/lib/prefs";
import { COVERAGE_MESSAGE, inCoverage } from "@/lib/coverage";
import { pick, useLang } from "@/lib/lang";

// Telugu-first location chooser. Three honest paths to a real coordinate:
//   1. GPS  → the farmer's exact spot (one tap, no typing — best for low literacy)
//   2. Quick-pick verified pilot mandals
//   3. Search a village/town by name — on submit (search button / keyboard "Go"), not per
//      keystroke: Nominatim's usage policy forbids autocomplete, and one request suits 3G better.
// Selecting anything updates ?lat&lon&place while preserving crop/water, so the
// server component re-fetches weather for that point.

export default function LocationPicker({ currentPlace }: { currentPlace: string }) {
  const { lang } = useLang();
  const router = useRouter();
  const params = useSearchParams();
  const [open, setOpen] = useState(false);
  const [gpsBusy, setGpsBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  // idle → searching → found (possibly nothing) | failed. "Nothing found" ≠ "could not search".
  const [search, setSearch] = useState<
    { state: "idle" } | { state: "searching" } | { state: "found"; places: Place[] } | { state: "failed" }
  >({ state: "idle" });
  const inflight = useRef<AbortController | null>(null);

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
      setMsg(pick(lang, "ఈ ఫోన్‌లో GPS అందుబాటులో లేదు", "GPS not available on this phone"));
      return;
    }
    setGpsBusy(true);
    setMsg(null);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setGpsBusy(false);
        const { latitude, longitude } = pos.coords;
        if (!inCoverage(latitude, longitude)) {
          // Don't navigate or save: the saved village stays usable for when they're back home.
          setMsg(pick(lang, COVERAGE_MESSAGE.te, COVERAGE_MESSAGE.en));
          return;
        }
        go(latitude, longitude, pick(lang, "నా ప్రాంతం", "My location"));
      },
      () => {
        setGpsBusy(false);
        setMsg(pick(lang, "ప్రాంతం అనుమతి ఇవ్వలేదు", "Location permission denied"));
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 },
    );
  }

  async function submitSearch(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!isSearchable(query)) return;
    inflight.current?.abort(); // a second tap replaces the first search
    const ctrl = new AbortController();
    inflight.current = ctrl;
    setSearch({ state: "searching" });
    const outcome = await searchPlaces(query, ctrl.signal);
    if (ctrl.signal.aborted) return;
    setSearch(outcome.ok ? { state: "found", places: outcome.places } : { state: "failed" });
  }

  return (
    <div className="mb-3">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center justify-between rounded-2xl bg-white/95 px-4 py-3 text-left shadow-[var(--shadow-1)] backdrop-blur"
      >
        <span className="flex items-center gap-2 truncate">
          <span aria-hidden>📍</span>
          <span className="truncate font-semibold text-stone-800">{currentPlace}</span>
        </span>
        <span className="shrink-0 text-sm font-medium text-green-700">
          {open ? pick(lang, "మూసివేయి", "Close") : pick(lang, "మార్చు", "Change")}
        </span>
      </button>

      {open && (
        <div className="mt-2 space-y-3 rounded-2xl bg-white p-3 text-stone-900 shadow-[var(--shadow-2)]">
          <button
            onClick={useGps}
            disabled={gpsBusy}
            className="flex w-full items-center justify-center gap-2 rounded-xl bg-green-600 px-4 py-3 font-semibold text-white disabled:opacity-60"
          >
            <span aria-hidden>🧭</span>
            {gpsBusy ? pick(lang, "వెతుకుతోంది…", "Locating…") : pick(lang, "నా ప్రాంతం వాడు", "Use my location")}
          </button>
          {msg && <p className="text-center text-sm text-amber-700">{msg}</p>}

          <div>
            <p className="mb-1 text-xs font-medium text-stone-500">
              {pick(lang, "భూపాలపల్లి జిల్లా", "Bhupalpally district")}
            </p>
            <div className="flex flex-wrap gap-2">
              {PILOT_MANDALS.map((m) => (
                <button
                  key={m.name_en}
                  onClick={() => go(m.lat, m.lon, pick(lang, m.name_te, m.name_en))}
                  className="rounded-full border border-green-600 px-3 py-1.5 text-sm text-green-800"
                >
                  {pick(lang, m.name_te, m.name_en)}
                </button>
              ))}
            </div>
          </div>

          <form role="search" onSubmit={submitSearch}>
            <div className="flex gap-2">
              <input
                type="search"
                enterKeyHint="search"
                value={query}
                maxLength={MAX_QUERY}
                onChange={(e) => setQuery(e.target.value)}
                aria-label={pick(lang, "మీ ఊరు పేరు", "Your village name")}
                placeholder={pick(lang, "మీ ఊరు వెతకండి", "Search your village")}
                className="min-w-0 flex-1 rounded-xl border border-stone-300 px-4 py-2.5 outline-none focus:border-green-600"
              />
              <button
                type="submit"
                disabled={!isSearchable(query) || search.state === "searching"}
                className="shrink-0 rounded-xl bg-green-600 px-4 py-2.5 font-semibold text-white disabled:opacity-50"
              >
                {pick(lang, "వెతుకు", "Search")}
              </button>
            </div>
            <div aria-live="polite">
              {search.state === "searching" && (
                <p className="mt-1 text-sm text-stone-500">{pick(lang, "వెతుకుతోంది…", "Searching…")}</p>
              )}
              {search.state === "failed" && (
                <p className="mt-1 text-sm text-amber-700">
                  {pick(lang, "ఇప్పుడు వెతకలేకపోయాం. మళ్ళీ ప్రయత్నించండి.", "Couldn't search right now. Please try again.")}
                </p>
              )}
              {search.state === "found" && search.places.length === 0 && (
                <p className="mt-1 text-sm text-stone-500">
                  {pick(lang, "ఈ పేరుతో ఊరు దొరకలేదు", "No village found with that name")}
                </p>
              )}
            </div>
            {search.state === "found" && search.places.length > 0 && (
              <ul className="mt-1 max-h-56 overflow-auto rounded-xl border border-stone-200">
                {search.places.map((r) => (
                  <li key={r.id}>
                    <button
                      type="button"
                      onClick={() => go(r.lat, r.lon, formatPlaceLabel(r, lang))}
                      className="flex w-full flex-col items-start px-3 py-2 text-left hover:bg-stone-50"
                    >
                      <span className="font-medium text-stone-800">{placeName(r, lang)}</span>
                      <span className="text-xs text-stone-500">
                        {[r.admin2, r.admin1].filter(Boolean).join(", ")}
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </form>
        </div>
      )}
    </div>
  );
}
