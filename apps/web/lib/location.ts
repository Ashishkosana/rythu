// Which place the home screen shows. Pure + tested; the component only supplies the inputs.
//   1. ?lat&lon in the URL (a village just picked, or a shared link)
//   2. the farmer's saved village (so a cold open never asks again)
//   3. the district HQ — the backend's own default (lat/lon omitted)

import { inCoverage } from "./coverage";
import { isValidCoord } from "./geocode";
import { DEFAULT_PLACE } from "./locations";
import type { SavedPlace } from "./prefs";

export interface ResolvedLocation {
  lat: number | null; // null with lon = let the backend use its default place
  lon: number | null;
  place: string;
  outside: boolean; // a URL point outside coverage (old link, GPS while travelling)
}

export const DEFAULT_LABEL = `${DEFAULT_PLACE.name_te} · ${DEFAULT_PLACE.name_en}`;
const SELECTED_LABEL = "ఎంచుకున్న ప్రాంతం · Selected";

export function resolveLocation(params: { get(key: string): string | null }, saved: SavedPlace | null): ResolvedLocation {
  const rawLat = params.get("lat");
  const rawLon = params.get("lon");
  const lat = Number(rawLat);
  const lon = Number(rawLon);
  if (rawLat !== null && rawLon !== null && rawLat !== "" && rawLon !== "" && isValidCoord(lat, lon)) {
    return { lat, lon, place: params.get("place") || SELECTED_LABEL, outside: !inCoverage(lat, lon) };
  }
  // A place saved before coverage existed could be outside it — restoring it would strand the
  // farmer on the coverage notice at every launch.
  if (saved && inCoverage(saved.lat, saved.lon)) {
    return { lat: saved.lat, lon: saved.lon, place: saved.place, outside: false };
  }
  return { lat: null, lon: null, place: DEFAULT_LABEL, outside: false };
}

/** Query string that keeps the place (and water source) when the crop changes. */
export function locationQuery(loc: ResolvedLocation, water: string): string {
  const q = new URLSearchParams({ water });
  if (loc.lat !== null && loc.lon !== null) {
    q.set("lat", String(loc.lat));
    q.set("lon", String(loc.lon));
  }
  q.set("place", loc.place);
  return q.toString();
}
