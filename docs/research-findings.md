# Rythu — Market Research Findings (2026-07-12)

*Multi-agent research pass: 5 angles + 3 adversarial data-source verifications + synthesis. This replaces our assumptions with evidence. Full sourced findings in the workflow journal.*

---

## TL;DR — the bet is right, the spec had errors
The market (Plantix, AgroStar, DeHaat, BharatAgri, Kisan Suvidha, e-NAM, Meghdoot) is crowded but **structurally conflicted**: the best-funded apps monetize **selling inputs**, so their "advice" is a sales funnel. **Rythu's defensible wedge = commission-free, explainable, Telugu voice-first advice that closes the whole journey (will-it-rain → what-to-grow → how → where/when-to-sell) for a 1–5 acre farmer.** Win on **comprehension + trust + last-inch specificity**, not more features.

---

## Data-source verdicts (adversarially verified LIVE)
| Source | Verdict | Reality |
|---|---|---|
| **Weather — Open-Meteo** | ✅ **BUILD NOW** | Free, **no key**, verified live returning hourly + daily **rain-probability** for Bhupalpally. ⚠️ ~11 km global model (not 1–2 km) → misses monsoon convective cells. Free tier is **non-commercial + ~10k calls/day** → self-host/paid before scaling. |
| **Mandi prices — data.gov.in Agmarknet** (resource `9ef84268-d588-465a-a308-a864a43d0070`) | ✅ **BUILD NOW** | Free **registered key**, verified live (fresh record dated today), covers Telangana/Warangal. ⚠️ **today-only snapshot**, manual per-APMC entry → gaps likely; must cache nightly into history + show "reported on [date]" + nearest-mandi fallback. |
| **IMD official API** | 🟡 Phase-2 | Gated: onboarding + key + **static-IP whitelist** (un-callable from mobile). Use later for authoritative heavy-rain *warnings* only. |
| **Soil Health Card (farmer-level)** | ❌ **BLOCKED** | No public API; OTP/Aadhaar-gated portal. Plot-level data restricted. **v1 soil plan is unbuildable** → use district/village soil baseline + optional manual NPK entry. |
| **e-NAM API** | ❌ | Partner/MoU only, no self-serve API. Drop the label. |

---

## Fact corrections (our spec/prototype were WRONG)
1. **Soil:** Bhupalpally is predominantly **RED / chalka soil (~54%)**, not black regur (~6%). *(Prototype + primer hard-coded black — fixed.)*
2. **Season:** launch in **Kharif (monsoon, ~77% of rain Jun–Sep)** — when "will it rain today" matters most. *(Prototype said Rabi — fixed.)*
3. **#1 crop-rec input is WATER SOURCE, not soil:** assured canal/lift/tank vs rainfed/borewell decides paddy-vs-diversify. Telangana is actively steering farmers **off Rabi paddy → cotton/chilli/red gram/sunflower.** Rule engine must ask water source and gate paddy behind it.
4. **Cotton was missing** — it's the #2 state crop and the biggest pain point (pink-bollworm, Bt resistance, 30–50% loss). Must be in the crop set.

## Competitor gaps Rythu can own
- **Advice = sales funnel** (Plantix pesticide commissions post-Helm-AG; BharatAgri/AgroStar/DeHaat input e-commerce; "sells at every step").
- **No one owns the end-to-end decision** — each app grabs one slice.
- **Weather is district-level & twice-weekly** (Meghdoot Tue/Fri) — useless for "spray/irrigate today on MY field," and trust is dented by misses.
- **Govt apps** crash, no offline, text above farmers' reading level (Gunning Fog ~11) — "showpieces of no practical use."
- **Mandi data = raw stale tables**, no "sell here, this week, ~₹Y" decision; **no MSP/procurement view** anywhere (the real 2025 pain: paddy/maize/cotton all sold below MSP).
- **Text-first, no voice output** → excludes the ~75% not digitally literate.

## Rythu's differentiators (the positioning)
1. **"We don't sell you anything"** — commission-free, neutral advice. THE marketable wedge.
2. **The only single explainable rain→grow→sell flow** for a small plot, in Telugu (NaPanta proved the bundle: ~124k users).
3. **Explainability AS trust** — "because" chips on every recommendation (season fits · soil suits · water enough · price/MSP).
4. **Voice-first Telugu + big-icon ~5th-grade UI** — the actual moat (digital literacy ~25%).
5. **Radically honest weather** — probability + confidence + "forecasts can be wrong" + last-updated/source stamp.
6. **A sell DECISION** — "sell [crop] at [mandi], ~₹Y, Z km, this week," **MSP overlay flags red when mandi < MSP.**
7. **Offline-first tiny PWA** — precomputed daily bundle survives monsoon dead-zones.
8. **Inside the trust network** — launch via **AEO / Rythu Vedika**, free forever (grant/CSR), SMS fallback. Never a farmer paywall.

## Top risks
- **Mandi coverage/freshness** — validate Warangal/Bhupalpally with a real key over 1–2 weeks before building sell-advice.
- **Weather honesty** — Open-Meteo misses convective cells; probability framing is mandatory.
- **Distribution cold-start** — organic installs fail; AEO/Rythu Vedika buy-in is the #1 make-or-break, line it up before build.
- **Advice-correctness liability** — vet the rule table with the district agri office before pilot.
- **Scope for a 2-person team** — sequence the **weather slice end-to-end first**, then layer the rest.
- **Open-Meteo license** (non-commercial) + **Telugu TTS quality** — budget for both before scaling.
