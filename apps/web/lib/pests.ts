// Pest guide for the pilot crops. Data from the VERIFIED IPM research
// (docs/agronomy-data.md): economic thresholds (ETL) + IPM-first actions, with
// chemicals named by ACTIVE INGREDIENT and CIB&RC/official dose — never a brand.
//
// HONESTY: this is a symptom + threshold guide, NOT an "AI diagnosis". The farmer
// is always pushed to scout, try non-chemical steps first, and photograph +
// confirm with their AEO / Kisan Call Centre before spraying. Rows where the
// official ETL/dose is unconfirmed are flagged so we never present a one-tap spray.

export interface Pest {
  key: string;
  cropKey: string;
  crop_te: string;
  name_te: string;
  name_en: string;
  emoji: string;
  symptom_te: string;
  threshold_te: string;
  ipmFirst_te: string;
  chemical_te: string;
  needsVerification: boolean;
  source: string;
}

export const PESTS: readonly Pest[] = [
  {
    key: "paddy_bph",
    cropKey: "paddy",
    crop_te: "వరి",
    name_te: "సుడి దోమ",
    name_en: "Brown planthopper",
    emoji: "🦗",
    symptom_te:
      "మొక్క అడుగున గోధుమ రంగు దోమలు గుంపులుగా. పైరు మచ్చలుగా ఎండి 'సుడి తెగులు (hopper burn)' ఏర్పడుతుంది.",
    threshold_te:
      "పిలకల దశ నుంచి మొక్క అడుగున నీటి పైన చూడండి. సాలీడు (మిత్ర పురుగు) లేకపోతే పిలకకు 1 దోమ, ఉంటే పిలకకు 2 దోమలు దాటితేనే చర్య.",
    ipmFirst_te:
      "మొదట్లో విస్తృత మందులు (పైరెత్రాయిడ్స్) వాడకండి — పురుగు మరింత పెరుగుతుంది. నీటిని కొన్ని రోజులు తీసేయండి; వేప నూనె 3% పిచికారీ.",
    chemical_te:
      "ETL దాటితే మొక్క అడుగుకు: ఇమిడాక్లోప్రిడ్ 17.8% SL 40–50 మి.లీ/ఎకరం, లేదా పైమెట్రోజిన్ 50% WG 120 గ్రా/ఎకరం, లేదా బుప్రోఫెజిన్ 25% SC 320 మి.లీ/ఎకరం.",
    needsVerification: false,
    source: "https://agritech.tnau.ac.in",
  },
  {
    key: "cotton_pbw",
    cropKey: "cotton",
    crop_te: "పత్తి",
    name_te: "గులాబీ కాయతొలుచు పురుగు",
    name_en: "Pink bollworm",
    emoji: "🐛",
    symptom_te: "పూత 'రోసెట్'గా మూసుకుపోవడం; కాయలో గింజలు తినేసి రంధ్రాలు.",
    threshold_te:
      "45 రోజుల నుంచి ఎకరానికి 5 ఫిరమోన్ ట్రాప్‌లు. వరుసగా 3 రాత్రులు ట్రాప్‌కు 8 రెక్కల పురుగులు, లేదా 10% కాయలు దెబ్బతింటే చర్య.",
    ipmFirst_te:
      "రోసెట్ పూలను తీసి నాశనం చేయండి (గట్టుపై వేయవద్దు). ట్రైకోగ్రామా విడుదల; వేప (అజాడిరాక్టిన్).",
    chemical_te:
      "ETL దాటితేనే — థయోడికార్బ్ 75% WP లేదా క్లోరాంట్రానిలిప్రోల్ 18.5% SC. ఖచ్చితమైన మోతాదును AEOతో నిర్ధారించుకోండి.",
    needsVerification: true,
    source: "https://niphm.gov.in",
  },
  {
    key: "maize_faw",
    cropKey: "maize",
    crop_te: "మొక్కజొన్న",
    name_te: "కత్తెర పురుగు",
    name_en: "Fall armyworm",
    emoji: "🐛",
    symptom_te: "ఆకుల్లో వరుస రంధ్రాలు; సుడి (whorl)లో పురుగు, రెట్టలు కనిపిస్తాయి.",
    threshold_te:
      "~5–10% సుడి ఆకులు దెబ్బతింటే చర్య. వారానికోసారి 'W' ఆకారంలో 20 మొక్కలు పరిశీలించండి. కంకి దశ దాటాక మందు వద్దు.",
    ipmFirst_te: "గుడ్ల సముదాయాలను చేతితో తీసి నాశనం చేయండి. సుడిలో ఇసుక+సున్నం వేయండి.",
    chemical_te:
      "లేత సుడి దశలో ETL దాటితే: స్పినెటోరమ్ 11.7% SC / ఎమామెక్టిన్ బెంజోయేట్ 5% SG / క్లోరాంట్రానిలిప్రోల్ 18.5% SC — సుడిలోకి. మోతాదును AEOతో నిర్ధారించుకోండి.",
    needsVerification: true,
    source: "https://agriculture.vikaspedia.in",
  },
  {
    key: "redgram_podborer",
    cropKey: "red_gram",
    crop_te: "కంది",
    name_te: "కాయతొలుచు పురుగు",
    name_en: "Gram pod borer",
    emoji: "🐛",
    symptom_te: "పూత, కాయల్లో రంధ్రాలు; లోపలి గింజలు తినేస్తుంది.",
    threshold_te:
      "ఎకరానికి 4–5 ట్రాప్‌లు, రోజుకు ట్రాప్‌కు 10 రెక్కల పురుగులు; పూత దశలో మొక్కకు 2 గుడ్లు/పురుగులు లేదా 2 మొక్కలకు 1 పురుగు.",
    ipmFirst_te: "పక్షి స్థావరాలు (ఎకరానికి ~8), HaNPV, వేప గింజ కషాయం (NSKE).",
    chemical_te:
      "ETL దాటితే: క్లోరాంట్రానిలిప్రోల్ 18.5% SC, లేదా ఇండాక్సాకార్బ్/స్పినోసాడ్, లేదా ఎసిటామిప్రిడ్. ఖచ్చిత మోతాదును AEOతో నిర్ధారించుకోండి.",
    needsVerification: true,
    source: "https://niphm.gov.in",
  },
  {
    key: "chilli_thrips",
    cropKey: "chilli",
    crop_te: "మిర్చి",
    name_te: "తామర పురుగు (త్రిప్స్)",
    name_en: "Thrips",
    emoji: "🐛",
    symptom_te: "ఆకులు పైకి ముడుచుకుని పడవలా మారడం; ఆకుల అడుగున వెండి రంగు. ఆకుముడత వైరస్ వ్యాప్తి.",
    threshold_te:
      "⚠ అధికారిక ETL అందుబాటులో లేదు — సాధారణంగా ఆకుకు ~6 పురుగులు. AEO/PJTSAUతో నిర్ధారించుకోండి. త్రిప్స్‌ను ముందుగానే గమనించండి.",
    ipmFirst_te: "నీలం/తెలుపు జిగురు అట్టలు అమర్చండి; తరచూ పరిశీలించండి.",
    chemical_te:
      "TNAU నమోదిత: ఫిప్రోనిల్ 5% SC 1.5 మి.లీ/లీ, లేదా స్పినోసాడ్ 45% SC 3.2 మి.లీ/10లీ. మోతాదును AEOతో నిర్ధారించుకోండి.",
    needsVerification: true,
    source: "https://agritech.tnau.ac.in",
  },
  {
    key: "chilli_mite",
    cropKey: "chilli",
    crop_te: "మిర్చి",
    name_te: "పసుపు నల్లి",
    name_en: "Yellow mite",
    emoji: "🕷️",
    symptom_te: "లేత ఆకులు కిందికి ముడుచుకోవడం, గట్టిపడటం, చిన్నవిగా మారడం.",
    threshold_te:
      "⚠ అధికారిక ETL అందుబాటులో లేదు — సాధారణంగా ఆకుకు ~5–10 నల్లులు. AEOతో నిర్ధారించుకోండి.",
    ipmFirst_te: "ముందుగా గమనించి, ఎక్కువ ప్రభావిత ఆకులను తీసివేయండి.",
    chemical_te:
      "TNAU నమోదిత: బుప్రోఫెజిన్ 25% SC 8 మి.లీ/10లీ, లేదా క్లోర్‌ఫెనాపిర్ 10% SC 1.5 మి.లీ/లీ; నీటిలో కరిగే గంధకం.",
    needsVerification: true,
    source: "https://agritech.tnau.ac.in",
  },
];
