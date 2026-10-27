"use client";

// The weather screen's container: works out the place and crop, asks the data layer, and picks
// the honest state to show. Presentational components below it never fetch.

import { useSearchParams } from "next/navigation";
import { useEffect, useMemo, useSyncExternalStore } from "react";
import FieldsThisWeek from "@/components/FieldsThisWeek";
import LocationPicker from "@/components/LocationPicker";
import WeatherScreen from "@/components/WeatherScreen";
import WeatherSkeleton from "@/components/WeatherSkeleton";
import { OutsideCoverage } from "@/lib/api";
import { COVERAGE_MESSAGE } from "@/lib/coverage";
import { asOf, isTooOld } from "@/lib/freshness";
import { pick, useLang } from "@/lib/lang";
import { locationQuery, resolveLocation, type ResolvedLocation } from "@/lib/location";
import { PREFS_EVENT, loadCrop, loadPlaceRaw, loadWater, parseSavedPlace, saveCrop, saveWater } from "@/lib/prefs";
import { isCrop, isWaterSource, type Crop, type WaterSource } from "@/lib/types";
import { useNow } from "@/lib/useNow";
import { useWeather } from "@/lib/useWeather";

function subscribeStorage(cb: () => void) {
  window.addEventListener("storage", cb); // other tabs
  window.addEventListener(PREFS_EVENT, cb); // this tab
  return () => {
    window.removeEventListener("storage", cb);
    window.removeEventListener(PREFS_EVENT, cb);
  };
}

export default function HomeScreen() {
  const params = useSearchParams();
  const savedRaw = useSyncExternalStore(subscribeStorage, loadPlaceRaw, () => null);
  const loc = useMemo(() => resolveLocation(params, parseSavedPlace(savedRaw)), [params, savedRaw]);
  // Crop and water: the link's, else the farmer's last choice, else mirchi (the main local crop).
  const savedCrop = useSyncExternalStore(subscribeStorage, loadCrop, () => null);
  const savedWater = useSyncExternalStore(subscribeStorage, loadWater, () => null);
  const rawCrop = params.get("crop") ?? undefined;
  const rawWater = params.get("water") ?? undefined;
  const crop: Crop = isCrop(rawCrop) ? rawCrop : (savedCrop ?? "chilli");
  const water: WaterSource = isWaterSource(rawWater) ? rawWater : (savedWater ?? "rainfed");

  // Remember a choice made by tapping a crop (or opening a link), so the next launch starts there.
  useEffect(() => {
    if (isCrop(rawCrop)) saveCrop(rawCrop);
    if (isWaterSource(rawWater)) saveWater(rawWater);
  }, [rawCrop, rawWater]);

  // Outside the area we serve: say so and offer the picker — never a dead-end error page.
  if (loc.outside) return <CoverageNotice place={loc.place} />;
  return <Forecast loc={loc} crop={crop} water={water} />;
}

function Forecast({ loc, crop, water }: { loc: ResolvedLocation; crop: Crop; water: WaterSource }) {
  const now = useNow();
  const q = useWeather({ lat: loc.lat, lon: loc.lon, crop, water });

  if (q.error instanceof OutsideCoverage) return <CoverageNotice place={loc.place} />; // backend is the authority
  const data = q.data;
  if (!data || isTooOld(data, now)) {
    if (q.isPending || q.isFetching) return <WeatherSkeleton />;
    return <Unavailable place={loc.place} tooOld={!!data} onRetry={() => void q.refetch()} />;
  }
  const offline = data.reliability.is_offline_cache || q.isError || q.fetchStatus === "paused";
  return (
    <WeatherScreen
      data={asOf(data, now)}
      crop={crop}
      place={loc.place}
      locationQuery={locationQuery(loc, water)}
      nowMs={now}
      offline={offline}
      adviceLoading={q.isPlaceholderData}
      fields={<FieldsThisWeek />}
    >
      <LocationPicker currentPlace={loc.place} />
    </WeatherScreen>
  );
}

function Unavailable({ place, tooOld, onRetry }: { place: string; tooOld: boolean; onRetry: () => void }) {
  const { lang } = useLang();
  return (
    <main className="mx-auto flex min-h-dvh w-full max-w-md flex-col justify-center gap-3 p-6 pb-28 text-center text-ink">
      <p className="text-3xl" aria-hidden>
        🌧️
      </p>
      <h1 className="font-semibold">
        {tooOld
          ? pick(lang, "సేవ్ చేసిన వాతావరణం 6 గంటల కంటే పాతది", "The saved forecast is more than 6 hours old")
          : pick(lang, "వాతావరణ సమాచారం అందుబాటులో లేదు", "Weather data unavailable")}
      </h1>
      <p className="text-sm text-ink-secondary">
        {pick(lang, "ఇంటర్నెట్ ఉన్నప్పుడు మళ్లీ ప్రయత్నించండి", "Please try again when you have internet")}
      </p>
      <button onClick={onRetry} className="tap mx-auto rounded-xl bg-brand px-6 py-3 font-semibold text-white">
        {pick(lang, "మళ్లీ ప్రయత్నించు", "Try again")}
      </button>
      <div className="mt-4 text-left">
        <LocationPicker currentPlace={place} />
      </div>
    </main>
  );
}

function CoverageNotice({ place }: { place: string }) {
  return (
    <main className="mx-auto flex min-h-dvh w-full max-w-md flex-col justify-center gap-4 p-6 pb-28 text-center text-ink">
      <p className="text-3xl" aria-hidden>
        📍
      </p>
      <h1 className="font-semibold">{COVERAGE_MESSAGE.te}</h1>
      <p className="text-sm text-ink-secondary">{COVERAGE_MESSAGE.en} · మీ ఊరిని ఎంచుకోండి / choose your village</p>
      <div className="text-left">
        <LocationPicker currentPlace={place} />
      </div>
    </main>
  );
}
