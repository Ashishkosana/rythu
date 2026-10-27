// The farmer's fields (My-Field): what grows where, and since when. Kept on the phone; copied to
// Rythu's server only with consent, inside the profile (lib/profileSync.ts).

import { PREFS_EVENT } from "./prefs";
import type { Crop } from "./types";

export interface MyField {
  id: string;
  name: string;
  crop: Crop;
  reference_date: string; // YYYY-MM-DD: sowing, or transplanting for paddy and chilli
}

export const MAX_FIELDS = 5;
export const MAX_NAME = 40;
const KEY = "rythu.fields";

/** Crops whose calendar counts from TRANSPLANTING (the rest from sowing). Mirrors the backend's
 *  domain/calendar.py — fields.test.ts fails if the two drift. */
export const TRANSPLANTED: ReadonlySet<Crop> = new Set<Crop>(["paddy", "chilli"]);

export function newFieldId(): string {
  const bytes = crypto.getRandomValues(new Uint8Array(6));
  return Array.from(bytes, (b) => (b % 36).toString(36)).join("") + Date.now().toString(36).slice(-4);
}

function valid(f: unknown): f is MyField {
  const x = f as Partial<MyField> | null;
  return (
    !!x &&
    typeof x.id === "string" &&
    /^[a-z0-9]{6,16}$/.test(x.id) &&
    typeof x.name === "string" &&
    typeof x.crop === "string" &&
    typeof x.reference_date === "string" &&
    /^\d{4}-\d{2}-\d{2}$/.test(x.reference_date)
  );
}

/** The stored string (a stable snapshot for useSyncExternalStore). */
export function loadFieldsRaw(): string | null {
  try {
    return typeof window === "undefined" ? null : window.localStorage.getItem(KEY);
  } catch {
    return null;
  }
}

export function parseFields(raw: string | null): MyField[] {
  try {
    const list: unknown = JSON.parse(raw ?? "[]");
    return Array.isArray(list) ? list.filter(valid).slice(0, MAX_FIELDS) : [];
  } catch {
    return [];
  }
}

export function loadFields(): MyField[] {
  return parseFields(loadFieldsRaw());
}

export function saveFields(fields: MyField[]): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(KEY, JSON.stringify(fields.slice(0, MAX_FIELDS)));
  } catch {
    return;
  }
  window.dispatchEvent(new Event(PREFS_EVENT)); // the profile sync follows
}

export function upsertField(f: MyField): void {
  const others = loadFields().filter((x) => x.id !== f.id);
  saveFields([...others, { ...f, name: f.name.trim().slice(0, MAX_NAME) }]);
}

export function removeField(id: string): void {
  saveFields(loadFields().filter((x) => x.id !== id));
}
