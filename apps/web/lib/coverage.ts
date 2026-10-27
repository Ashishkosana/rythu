// Where Rythu gives weather + advice. The rules, crop doses and schemes are Telangana-specific,
// so the app serves Telangana plus a border margin. The backend enforces the same box
// (services/weather/src/rythu_weather/app/handler.py COVERAGE_LAT/LON) — keep them in sync.

export const COVERAGE = { latMin: 15.7, latMax: 20.0, lonMin: 77.1, lonMax: 81.5 } as const;

export const COVERAGE_MESSAGE = {
  te: "రైతు ప్రస్తుతం తెలంగాణకు మాత్రమే అందుబాటులో ఉంది",
  en: "Rythu currently covers Telangana only",
} as const;

export function inCoverage(lat: number, lon: number): boolean {
  return (
    Number.isFinite(lat) &&
    Number.isFinite(lon) &&
    lat >= COVERAGE.latMin &&
    lat <= COVERAGE.latMax &&
    lon >= COVERAGE.lonMin &&
    lon <= COVERAGE.lonMax
  );
}
