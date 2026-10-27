// Remember the farmer's choices so a basic user never re-enters them. Stored in localStorage
// (SSR-guarded; every access survives a full or disabled storage). A first-time smartphone user sets
// their village once.
//
// Every write announces itself with a "rythu:prefs" event, so the profile sync (lib/profileSync.ts)
// can follow changes without each screen knowing about it.

import { isCrop, isWaterSource, type Crop, type WaterSource } from "./types";

export interface SavedPlace {
  lat: number;
  lon: number;
  place: string;
}

export const PREFS_EVENT = "rythu:prefs";

const PLACE_KEY = "rythu.place";
const LANG_KEY = "rythu.lang";
const SEEN_KEY = "rythu.seenWelcome";
const CROP_KEY = "rythu.crop";
const WATER_KEY = "rythu.water";
const SYNC_KEY = "rythu.sync"; // "on" = the farmer agreed to keep a copy on Rythu's server
const SYNC_STATE_KEY = "rythu.syncState"; // { etag, synced } of the last successful upload

function ok(): boolean {
  return typeof window !== "undefined" && !!window.localStorage;
}

function read(key: string): string | null {
  if (!ok()) return null;
  try {
    return window.localStorage.getItem(key);
  } catch {
    return null;
  }
}

function write(key: string, value: string | null, announce = true): void {
  if (!ok()) return;
  try {
    if (value === null) window.localStorage.removeItem(key);
    else window.localStorage.setItem(key, value);
  } catch {
    return; // storage full / disabled — non-fatal
  }
  if (announce) window.dispatchEvent(new Event(PREFS_EVENT));
}

export function savePlace(p: SavedPlace): void {
  write(PLACE_KEY, JSON.stringify(p));
}

export function loadPlace(): SavedPlace | null {
  return parseSavedPlace(loadPlaceRaw());
}

/** The stored string itself (a stable snapshot for useSyncExternalStore). */
export function loadPlaceRaw(): string | null {
  return read(PLACE_KEY);
}

export function parseSavedPlace(raw: string | null): SavedPlace | null {
  if (!raw) return null;
  try {
    const p = JSON.parse(raw) as Partial<SavedPlace>;
    if (typeof p.lat === "number" && typeof p.lon === "number" && typeof p.place === "string") {
      return { lat: p.lat, lon: p.lon, place: p.place };
    }
  } catch {
    /* corrupt value — ignore */
  }
  return null;
}

export function saveLang(lang: "te" | "en"): void {
  write(LANG_KEY, lang);
}

export function loadLang(): "te" | "en" | null {
  const v = read(LANG_KEY);
  return v === "te" || v === "en" ? v : null;
}

export function saveCrop(crop: Crop): void {
  if (read(CROP_KEY) !== crop) write(CROP_KEY, crop);
}

export function loadCrop(): Crop | null {
  const v = read(CROP_KEY) ?? undefined;
  return isCrop(v) ? v : null;
}

export function saveWater(water: WaterSource): void {
  if (read(WATER_KEY) !== water) write(WATER_KEY, water);
}

export function loadWater(): WaterSource | null {
  const v = read(WATER_KEY) ?? undefined;
  return isWaterSource(v) ? v : null;
}

export function hasSeenWelcome(): boolean {
  return read(SEEN_KEY) === "1";
}

export function markWelcomeSeen(): void {
  write(SEEN_KEY, "1", false);
}

// ── Profile sync bookkeeping (lib/profileSync.ts) ─────────────────────────────────────────────

export function syncConsent(): boolean {
  return read(SYNC_KEY) === "on";
}

export function setSyncConsent(on: boolean): void {
  write(SYNC_KEY, on ? "on" : null);
}

export interface SyncState {
  etag: string | null; // the server's version of what we last uploaded
  synced: string | null; // JSON of that upload, to skip identical writes
}

export function loadSyncState(): SyncState {
  try {
    const s = JSON.parse(read(SYNC_STATE_KEY) ?? "null") as Partial<SyncState> | null;
    return { etag: typeof s?.etag === "string" ? s.etag : null, synced: typeof s?.synced === "string" ? s.synced : null };
  } catch {
    return { etag: null, synced: null };
  }
}

export function saveSyncState(s: SyncState | null): void {
  write(SYNC_STATE_KEY, s ? JSON.stringify(s) : null, false);
}

/** "Clear this phone": every Rythu preference (the forecast copy is cleared separately). */
export function clearAllPrefs(): void {
  for (const key of [PLACE_KEY, LANG_KEY, CROP_KEY, WATER_KEY, SYNC_KEY, SYNC_STATE_KEY]) write(key, null, false);
  if (ok()) window.dispatchEvent(new Event(PREFS_EVENT));
}
