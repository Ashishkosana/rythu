// Government schemes farmers in Telangana can benefit from. Content is a plain-
// language summary; every card links to the OFFICIAL portal so the farmer (or an
// AEO) verifies current amounts and eligibility — these change year to year, so we
// deliberately avoid hard-coding rupee figures that could go stale or mislead.

export interface Scheme {
  key: string;
  name_te: string;
  name_en: string;
  what_te: string;
  what_en: string;
  who_te: string;
  who_en: string;
  how_te: string;
  how_en: string;
  url: string;
}

export const SCHEMES: readonly Scheme[] = [
  {
    key: "pm_kisan",
    name_te: "పీఎం-కిసాన్",
    name_en: "PM-KISAN",
    what_te: "కేంద్ర ప్రభుత్వం నుంచి ఏటా మూడు విడతల్లో నేరుగా ఖాతాలో సాయం.",
    what_en: "Central income support paid directly to your bank in three instalments a year.",
    who_te: "భూమి ఉన్న చిన్న, సన్నకారు రైతు కుటుంబాలు.",
    who_en: "Small & marginal land-holding farmer families.",
    how_te: "pmkisan.gov.in లో 'Farmers Corner' → New Registration. ఆధార్, బ్యాంక్, భూమి వివరాలు అవసరం.",
    how_en: "Register at pmkisan.gov.in → Farmers Corner. Needs Aadhaar, bank & land details.",
    url: "https://pmkisan.gov.in",
  },
  {
    key: "rythu_bharosa",
    name_te: "రైతు భరోసా",
    name_en: "Rythu Bharosa",
    what_te: "తెలంగాణ ప్రభుత్వం ఇచ్చే పంట పెట్టుబడి సాయం (ఎకరానికి).",
    what_en: "Telangana's per-acre crop investment support to farmers.",
    who_te: "రాష్ట్రంలో సాగు భూమి ఉన్న రైతులు.",
    who_en: "Farmers with cultivable land in Telangana.",
    how_te: "మీ గ్రామ వ్యవసాయ విస్తరణ అధికారి (AEO) / రైతు వేదిక ద్వారా వివరాలు తెలుసుకోండి.",
    how_en: "Check with your village Agriculture Extension Officer (AEO) / Rythu Vedika.",
    url: "https://www.telangana.gov.in",
  },
  {
    key: "pmfby",
    name_te: "పంట బీమా (PMFBY)",
    name_en: "Crop Insurance (PMFBY)",
    what_te: "వర్షాభావం, వరదలు, తెగుళ్ల వల్ల పంట నష్టపోతే బీమా పరిహారం.",
    what_en: "Insurance payout if your crop fails due to drought, flood, or pests.",
    who_te: "నోటిఫై చేసిన పంటలు సాగుచేసే రైతులు (రుణ / రుణేతర).",
    who_en: "Farmers growing notified crops (loanee & non-loanee).",
    how_te: "బ్యాంక్ / CSC / pmfby.gov.in లో గడువులోగా నమోదు చేసుకోండి.",
    how_en: "Enrol before the cut-off date via bank / CSC / pmfby.gov.in.",
    url: "https://pmfby.gov.in",
  },
  {
    key: "soil_health",
    name_te: "భూసార కార్డు",
    name_en: "Soil Health Card",
    what_te: "మీ నేలలో పోషకాల స్థాయి, ఎంత ఎరువు వాడాలో తెలిపే కార్డు — ఖర్చు తగ్గుతుంది.",
    what_en: "A card showing your soil's nutrients and how much fertiliser to use — cuts costs.",
    who_te: "ఏ రైతైనా — నమూనా ఇచ్చి పొందవచ్చు.",
    who_en: "Any farmer — get it by submitting a soil sample.",
    how_te: "గ్రామ AEO / మట్టి పరీక్ష కేంద్రం ద్వారా నమూనా ఇవ్వండి. soilhealth.dac.gov.in.",
    how_en: "Submit a sample via your AEO / soil-testing lab. soilhealth.dac.gov.in.",
    url: "https://soilhealth.dac.gov.in",
  },
  {
    key: "kcc",
    name_te: "కిసాన్ క్రెడిట్ కార్డు (KCC)",
    name_en: "Kisan Credit Card (KCC)",
    what_te: "తక్కువ వడ్డీకి పంట రుణం — వడ్డీ రాయితీతో.",
    what_en: "Low-interest crop loan with interest subvention.",
    who_te: "రైతులు, కౌలుదారులు, భాగస్వామ్య రైతులు.",
    who_en: "Farmers, tenant farmers & sharecroppers.",
    how_te: "మీ బ్యాంక్ శాఖలో KCC దరఖాస్తు చేయండి. భూమి / సాగు రుజువు అవసరం.",
    how_en: "Apply for KCC at your bank branch. Needs land / cultivation proof.",
    url: "https://www.myscheme.gov.in/schemes/kcc",
  },
];
