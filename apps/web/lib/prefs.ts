// Remember the farmer's choices so a basic user never re-enters them. Stored in
// localStorage (SSR-guarded). A first-time smartphone user sets their village once.

export interface SavedPlace {
  lat: number;
  lon: number;
  place: string;
}

const PLACE_KEY = "rythu.place";
const LANG_KEY = "rythu.lang";
const SEEN_KEY = "rythu.seenWelcome";

function ok(): boolean {
  return typeof window !== "undefined" && !!window.localStorage;
}

export function savePlace(p: SavedPlace): void {
  if (!ok()) return;
  try {
    window.localStorage.setItem(PLACE_KEY, JSON.stringify(p));
  } catch {
    /* storage full / disabled — non-fatal */
  }
}

export function loadPlace(): SavedPlace | null {
  if (!ok()) return null;
  try {
    const raw = window.localStorage.getItem(PLACE_KEY);
    if (!raw) return null;
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
  if (ok()) {
    try {
      window.localStorage.setItem(LANG_KEY, lang);
    } catch {
      /* non-fatal */
    }
  }
}

export function loadLang(): "te" | "en" | null {
  if (!ok()) return null;
  const v = window.localStorage.getItem(LANG_KEY);
  return v === "te" || v === "en" ? v : null;
}

export function hasSeenWelcome(): boolean {
  return ok() && window.localStorage.getItem(SEEN_KEY) === "1";
}

export function markWelcomeSeen(): void {
  if (ok()) {
    try {
      window.localStorage.setItem(SEEN_KEY, "1");
    } catch {
      /* non-fatal */
    }
  }
}
