// Crop guide for the Bhupalpally Kharif pilot set. Keys match the backend Crop
// enum (services/weather domain) so weather farming-reads line up with these cards.
//
// HONESTY: this is GENERAL package-of-practices guidance, not a field prescription.
// Every card cites an official source and tells the farmer to confirm exact dates
// and doses with the local Agriculture Extension Officer (AEO / PJTSAU). We do not
// invent precise agronomic numbers.

export interface CropGuide {
  key: string;
  name_te: string;
  name_en: string;
  emoji: string;
  season_te: string;
  season_en: string;
  water_te: string;
  water_en: string;
  sow_te: string;
  sow_en: string;
  tips_te: string[];
  tips_en: string[];
  source: string;
}

export const CROP_GUIDES: readonly CropGuide[] = [
  {
    key: "paddy",
    name_te: "వరి",
    name_en: "Paddy (rice)",
    emoji: "🌾",
    season_te: "ఖరీఫ్ (జూన్–జూలై నారు)",
    season_en: "Kharif (nursery Jun–Jul)",
    water_te: "ఎక్కువ నీరు — నిశ్చిత నీటిపారుదల అవసరం",
    water_en: "High — needs assured irrigation / standing water",
    sow_te: "నైరుతి రుతుపవనాలతో నారు పోసి, 20–25 రోజులకు నాటాలి",
    sow_en: "Raise nursery with monsoon onset; transplant at 20–25 days",
    tips_te: [
      "పొలంలో నీటి మట్టం ఒక అంగుళం చుట్టూ ఉంచండి",
      "కలుపు నివారణకు మొదటి 40 రోజులు ముఖ్యం",
      "పంట కోత సమయంలో వర్షం ఉంటే ధాన్యం కప్పి ఉంచండి",
    ],
    tips_en: [
      "Keep ~1 inch standing water in the field",
      "First 40 days are critical for weed control",
      "Cover harvested grain if rain is forecast",
    ],
    source: "https://pjtsau.edu.in",
  },
  {
    key: "cotton",
    name_te: "పత్తి",
    name_en: "Cotton",
    emoji: "🧺",
    season_te: "ఖరీఫ్ (జూన్–జూలై విత్తనం)",
    season_en: "Kharif (sow Jun–Jul)",
    water_te: "మధ్యస్థం — వర్షాధారంగా పండుతుంది",
    water_en: "Moderate — grows well rainfed",
    sow_te: "రుతుపవనాలు స్థిరపడ్డాక సాళ్లలో విత్తండి",
    sow_en: "Sow in rows once the monsoon has settled",
    tips_te: [
      "గులాబీ రంగు కాయతొలుచు పురుగు (pink bollworm) కోసం ఎప్పటికప్పుడు చూడండి",
      "వరుస దూరం, మొక్కల దూరం పాటించండి",
      "అధిక తేమలో పిచికారీ నివారించండి",
    ],
    tips_en: [
      "Scout regularly for pink bollworm",
      "Maintain row and plant spacing",
      "Avoid spraying in high humidity",
    ],
    source: "https://pjtsau.edu.in",
  },
  {
    key: "maize",
    name_te: "మొక్కజొన్న",
    name_en: "Maize",
    emoji: "🌽",
    season_te: "ఖరీఫ్ (జూన్–జూలై విత్తనం)",
    season_en: "Kharif (sow Jun–Jul)",
    water_te: "మధ్యస్థం — నీరు నిలవకుండా చూడండి",
    water_en: "Moderate — avoid waterlogging",
    sow_te: "మంచి వర్షం తర్వాత తగిన లోతులో విత్తండి",
    sow_en: "Sow at proper depth after a good rain",
    tips_te: [
      "నీరు నిలిస్తే కాలువలు తీసి బయటకు పంపండి",
      "కత్తెర పురుగు (fall armyworm) కోసం చూడండి",
    ],
    tips_en: [
      "Drain excess water — maize hates waterlogging",
      "Watch for fall armyworm",
    ],
    source: "https://pjtsau.edu.in",
  },
  {
    key: "red_gram",
    name_te: "కంది",
    name_en: "Red gram (pigeon pea)",
    emoji: "🫛",
    season_te: "ఖరీఫ్ (జూన్–జూలై విత్తనం)",
    season_en: "Kharif (sow Jun–Jul)",
    water_te: "తక్కువ — కరువును తట్టుకుంటుంది",
    water_en: "Low — drought-tolerant",
    sow_te: "వర్షాధార పంటగా సాళ్లలో విత్తండి",
    sow_en: "Sow in rows as a rainfed crop",
    tips_te: [
      "నీరు నిలవకుండా ఎత్తు సాళ్లు మేలు",
      "పూత దశలో కాయతొలుచు పురుగును గమనించండి",
    ],
    tips_en: [
      "Ridge planting helps drainage",
      "Watch for pod borer at flowering",
    ],
    source: "https://pjtsau.edu.in",
  },
  {
    key: "chilli",
    name_te: "మిర్చి",
    name_en: "Chilli (mirchi)",
    emoji: "🌶️",
    season_te: "ఖరీఫ్ — నారు పోసి నాటాలి",
    season_en: "Kharif — nursery then transplant",
    water_te: "నీటిపారుదల అవసరం",
    water_en: "Needs irrigation",
    sow_te: "నారు పెంచి, ఆరోగ్యకరమైన మొక్కలను నాటండి",
    sow_en: "Raise a nursery and transplant healthy seedlings",
    tips_te: [
      "ఎక్కువ తేమ ఉంటే ఆంత్రాక్నోస్ (కాయకుళ్ళు) ప్రమాదం",
      "పండ్లు ఆరబెట్టేటప్పుడు వర్షం రాకుండా చూడండి",
    ],
    tips_en: [
      "High humidity raises anthracnose (fruit rot) risk",
      "Protect drying pods from rain",
    ],
    source: "https://pjtsau.edu.in",
  },
] as const;
