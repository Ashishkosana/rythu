// Fertilizer recommendations for the 5 pilot crops. NEUTRAL, OFFICIAL sources only
// (PJTSAU / ICAR / TNAU cross-check) — NO company/brand formulas (that would break
// the "we sell you nothing" wedge). Values verified in docs/agronomy-data.md.
//
// SAFETY: doses are general Kharif-Telangana norms. A soil test (Soil Health Card)
// changes the real need, so the UI always shows the "confirm with AEO / Soil Health
// Card" fallback — prominently for any crop flagged needsVerification.
//
// Nutrient basis = N : P2O5 : K2O (kg PER ACRE). 1 ha = 2.47 acre.

export interface CropDose {
  key: string;
  name_te: string;
  name_en: string;
  emoji: string;
  n: number; // kg N / acre
  p: number; // kg P2O5 / acre
  k: number; // kg K2O / acre
  original: string; // source figure (as stated, per ha)
  splits_te: string;
  confidence: "high" | "medium" | "low";
  needsVerification: boolean;
  source: string;
}

export const CROP_DOSES: readonly CropDose[] = [
  {
    key: "paddy",
    name_te: "వరి",
    name_en: "Paddy",
    emoji: "🌾",
    n: 48.6,
    p: 24.3,
    k: 16.2,
    original: "120 : 60 : 40 kg/ha (PJTSAU)",
    splits_te: "P, K మొత్తం దుక్కిలో (basal). N ను 3 సమ భాగాలుగా — నాట్లు, పిలకల దశ (25–30 రోజులు), కంకి దశ (55–60 రోజులు).",
    confidence: "high",
    needsVerification: false,
    source: "https://pjtsau.edu.in",
  },
  {
    key: "cotton",
    name_te: "పత్తి",
    name_en: "Cotton",
    emoji: "🧺",
    n: 48,
    p: 24,
    k: 24,
    original: "48 : 24 : 24 kg/acre (ANGRAU/PJTSAU-lineage)",
    splits_te: "P మొత్తం దుక్కిలో. N, K లను 3 సమ భాగాలుగా — విత్తిన 30, 60, 90 రోజులకు.",
    confidence: "medium",
    needsVerification: true,
    source: "https://tnaucottondatabase.wordpress.com",
  },
  {
    // Two official figures conflict (TNAU 250:75:75 vs ICAR-IIMR 200:60:60). We use
    // the LOWER ICAR-IIMR dose to avoid over-application/overdose (farmer-protective),
    // and flag for local verification — never the higher, unverified number.
    key: "maize",
    name_te: "మొక్కజొన్న",
    name_en: "Maize",
    emoji: "🌽",
    n: 81,
    p: 24.3,
    k: 24.3,
    original: "200 : 60 : 60 kg/ha (ICAR-IIMR; TNAU lists higher)",
    splits_te: "P, K మొత్తం + N లో పావు వంతు దుక్కిలో. మిగతా N ను మోకాలి ఎత్తు (~25 రోజులు), పూత ముందు (~45 రోజులు) వేయండి.",
    confidence: "low",
    needsVerification: true,
    source: "https://icar.org.in",
  },
  {
    key: "red_gram",
    name_te: "కంది",
    name_en: "Red gram",
    emoji: "🫛",
    n: 8.1,
    p: 20.2,
    k: 8.1,
    original: "20 : 50 : 20 kg/ha (ZREAC/RARS; K unresolved)",
    splits_te: "మొత్తం మోతాదు విత్తనం వేసేటప్పుడు దుక్కిలో (basal). పైపాటు అవసరం లేదు. విత్తనానికి రైజోబియం పట్టించండి.",
    confidence: "medium",
    needsVerification: true,
    source: "https://www.rarstpt.org",
  },
  {
    key: "chilli",
    name_te: "మిర్చి",
    name_en: "Chilli",
    emoji: "🌶️",
    n: 24.3,
    p: 24.3,
    k: 12.1,
    original: "60 : 60 : 30 kg/ha (TNAU; sources differ on N)",
    splits_te: "పశువుల ఎరువు + P, K మొత్తం, సగం N దుక్కిలో. మిగతా N ను 30, 60, 90 రోజులకు వేయండి.",
    confidence: "low",
    needsVerification: true,
    source: "https://agritech.tnau.ac.in",
  },
];

// Fertilizer grades (FCO standard, confirmed on TNAU nutrient-content table).
const UREA_N = 0.46;
const DAP_N = 0.18;
const DAP_P = 0.46;
const MOP_K = 0.6;
export const UREA_BAG_KG = 45; // Indian urea bags = 45 kg (neem-coated, since 2018)
export const BAG_KG = 50; // DAP / MOP remain 50 kg
export const GUNTHA_PER_ACRE = 40;

export interface FertResult {
  n: number;
  p: number;
  k: number;
  ureaKg: number;
  dapKg: number;
  mopKg: number;
  ureaBags: number;
  dapBags: number;
  mopBags: number;
}

/**
 * Convert an N:P2O5:K2O requirement (kg) into Urea/DAP/MOP.
 * CRITICAL: DAP already carries N, so subtract that before sizing Urea — otherwise
 * the farmer over-applies nitrogen. (See worked example in docs/agronomy-data.md.)
 */
export function fertilizerFor(n: number, p: number, k: number): FertResult {
  const mopKg = k > 0 ? (k * 100) / (MOP_K * 100) : 0;
  const dapKg = p > 0 ? (p * 100) / (DAP_P * 100) : 0;
  const nFromDap = dapKg * DAP_N;
  const ureaKg = Math.max(0, n - nFromDap) / UREA_N;
  const round = (x: number) => Math.round(x * 10) / 10;
  const bags = (x: number, bagKg: number) => Math.round((x / bagKg) * 10) / 10;
  return {
    n: round(n),
    p: round(p),
    k: round(k),
    ureaKg: round(ureaKg),
    dapKg: round(dapKg),
    mopKg: round(mopKg),
    ureaBags: bags(ureaKg, UREA_BAG_KG),
    dapBags: bags(dapKg, BAG_KG),
    mopBags: bags(mopKg, BAG_KG),
  };
}

/** Scale a crop's per-acre dose to an area, then convert to bags. */
export function computeForArea(dose: CropDose, acres: number): FertResult {
  return fertilizerFor(dose.n * acres, dose.p * acres, dose.k * acres);
}
