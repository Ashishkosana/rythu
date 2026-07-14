// Pilot location seed for Jayashankar Bhupalpally district, Telangana.
//
// HONESTY NOTE: every coordinate here was resolved from the Open-Meteo geocoding
// source and verified to fall inside the district's bounding box — none are
// hand-guessed. We ship only mandals we could verify (better 3 correct chips than
// 10 wrong ones). Farmers who want their exact spot use GPS or the search box,
// which hit real coordinates directly. Expand this list from LGD / OpenStreetMap
// as the pilot grows.

export interface Place {
  name_en: string;
  name_te: string;
  lat: number;
  lon: number;
}

export const PILOT_MANDALS: readonly Place[] = [
  { name_en: "Bhupalpally", name_te: "భూపాలపల్లి", lat: 18.4287, lon: 79.8638 },
  { name_en: "Malharrao", name_te: "మల్హర్‌రావు", lat: 18.5341, lon: 79.749 },
  { name_en: "Regonda", name_te: "రేగొండ", lat: 18.2378, lon: 79.775 },
] as const;

// Falls back to the district HQ when no location is chosen — matches the backend default.
export const DEFAULT_PLACE: Place = PILOT_MANDALS[0];
