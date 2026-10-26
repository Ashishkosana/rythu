import type { Crop } from "./types";

// Keyed by the backend's Crop enum: a crop added on the backend without a label won't compile.
export const CROP_LABEL: Record<Crop, { te: string; en: string; emoji: string }> = {
  chilli: { te: "మిర్చి", en: "Chilli", emoji: "🌶️" },
  cotton: { te: "పత్తి", en: "Cotton", emoji: "🧺" },
  paddy: { te: "వరి", en: "Paddy", emoji: "🌾" },
  red_gram: { te: "కంది", en: "Red gram", emoji: "🌿" }, // not 🫛: an empty box before Android 13
  maize: { te: "మొక్కజొన్న", en: "Maize", emoji: "🌽" },
};
