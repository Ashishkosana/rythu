// Keep a copy of the farmer's choices on Rythu's server — ONLY with their consent (DPDP Act):
// village, crop, water source, language. No name, no phone number. Server-side alerts (S14) and the
// crop calendar (S16) need it; nothing else reads it.
//
// The phone is the source of truth (one phone per account), so a version conflict is resolved by
// re-reading the server's version and writing again. Uploads are skipped when nothing changed.

import { ApiUnavailable } from "./api";
import { NoDevice, authedFetch, forgetDevice, hasDevice } from "./device";
import { inCoverage } from "./coverage";
import { loadFields, type MyField } from "./fields";
import { localDate } from "./freshness";
import {
  loadCrop,
  loadLang,
  loadPlace,
  loadSyncState,
  loadWater,
  saveSyncState,
  setSyncConsent,
  syncConsent,
  type SavedPlace,
} from "./prefs";
import type { Crop, ProfileIn, WaterSource } from "./types";

const MAX_NAME = 80;
// The server's window for a field's date (app/calendar_request.py): older fields are history, and
// sending one would make the whole upload fail.
const FIELD_MAX_PAST_DAYS = 400;
const FIELD_MAX_AHEAD_DAYS = 60;

function shift(today: string, days: number): string {
  const d = new Date(`${today}T00:00:00Z`);
  d.setUTCDate(d.getUTCDate() + days);
  return d.toISOString().slice(0, 10);
}

/** Pure: the profile as the phone knows it. Anything the API would refuse (a place outside coverage,
 *  a field dated outside its window) is left out rather than failing the whole upload. */
export function buildProfile(p: {
  place: SavedPlace | null;
  crop: Crop | null;
  water: WaterSource | null;
  lang: "te" | "en" | null;
  fields?: MyField[];
  today?: string; // YYYY-MM-DD (IST)
}): ProfileIn {
  const village =
    p.place && inCoverage(p.place.lat, p.place.lon)
      ? { name: p.place.place.trim().slice(0, MAX_NAME) || "—", lat: p.place.lat, lon: p.place.lon }
      : null;
  const today = p.today ?? localDate(Date.now(), "Asia/Kolkata");
  const [from, to] = [shift(today, -FIELD_MAX_PAST_DAYS), shift(today, FIELD_MAX_AHEAD_DAYS)];
  const fields = (p.fields ?? [])
    .filter((f) => f.reference_date >= from && f.reference_date <= to)
    .map((f) => ({ id: f.id, name: f.name.trim() || "—", crop: f.crop, reference_date: f.reference_date }));
  return { village, crop: p.crop, water: p.water ?? "rainfed", lang: p.lang ?? "te", fields };
}

export function localProfile(): ProfileIn {
  return buildProfile({
    place: loadPlace(),
    crop: loadCrop(),
    water: loadWater(),
    lang: loadLang(),
    fields: loadFields(),
  });
}

// ── status, for the "My data" screen ──────────────────────────────────────────────────────────
export type SyncStatus =
  | { state: "off" }
  | { state: "syncing" }
  | { state: "saved"; at: number }
  | { state: "failed" };

let status: SyncStatus = { state: "off" };
const listeners = new Set<() => void>();

function setStatus(s: SyncStatus): void {
  status = s;
  listeners.forEach((l) => l());
}

export function subscribeSyncStatus(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export function syncStatus(): SyncStatus {
  return status;
}

// ── sync ──────────────────────────────────────────────────────────────────────────────────────
let running: Promise<SyncStatus> | null = null;

/** Upload the local profile if consent is on and it changed. Never throws; returns the outcome. */
export function syncProfile(): Promise<SyncStatus> {
  running ??= upload().finally(() => {
    running = null;
  });
  return running;
}

async function upload(): Promise<SyncStatus> {
  if (!syncConsent()) {
    setStatus({ state: "off" });
    return status;
  }
  const profile = localProfile();
  const body = JSON.stringify(profile);
  const state = loadSyncState();
  if (state.synced === body && state.etag && (await hasDevice())) {
    if (status.state !== "saved") setStatus({ state: "saved", at: Date.now() });
    return status;
  }
  setStatus({ state: "syncing" });
  try {
    let etag = state.etag;
    for (let attempt = 0; attempt < 2; attempt++) {
      const res = await authedFetch(
        "/v1/me/profile",
        {
          method: "PUT",
          headers: { "Content-Type": "application/json", ...(etag ? { "If-Match": etag } : { "If-None-Match": "*" }) },
          body,
        },
        { create: true },
      );
      if (res.ok) {
        saveSyncState({ etag: res.headers.get("ETag"), synced: body });
        setStatus({ state: "saved", at: Date.now() });
        return status;
      }
      if (res.status !== 412) throw new ApiUnavailable(`profile ${res.status}`);
      etag = await currentEtag(); // someone (an older upload) wrote first: take their version, write ours
    }
    throw new ApiUnavailable("profile kept changing");
  } catch (err) {
    if (!(err instanceof ApiUnavailable) && !(err instanceof NoDevice)) console.error("profile sync", err);
    setStatus({ state: "failed" });
    return status;
  }
}

async function currentEtag(): Promise<string | null> {
  const res = await authedFetch("/v1/me/profile", { method: "GET" }, { create: false });
  if (res.status === 404) return null; // nothing there: create
  if (!res.ok) throw new ApiUnavailable(`profile ${res.status}`);
  return res.headers.get("ETag");
}

/** Turn the server copy on (and upload now) or off (stop uploading; data stays until deleted). */
export async function setConsent(on: boolean): Promise<SyncStatus> {
  setSyncConsent(on);
  return syncProfile();
}

/**
 * Delete everything Rythu's server holds for this phone, then forget the account. Turns consent off.
 * Returns false if the server could not be reached (nothing is forgotten then, so it can be retried).
 */
export async function deleteServerData(): Promise<boolean> {
  setSyncConsent(false);
  if (!(await hasDevice())) {
    saveSyncState(null);
    setStatus({ state: "off" });
    return true;
  }
  try {
    const res = await authedFetch("/v1/me", { method: "DELETE" }, { create: false });
    if (res.status !== 204) return false;
  } catch (err) {
    if (!(err instanceof NoDevice)) return false; // NoDevice: the server had already forgotten us
  }
  await forgetDevice();
  saveSyncState(null);
  setStatus({ state: "off" });
  return true;
}
