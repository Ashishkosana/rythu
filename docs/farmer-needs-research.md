# Rythu — Farmer Needs, Competitor Landscape & Sections Roadmap (2026-07-14)

_Verified multi-agent research (farmer JTBD, competitor teardowns, crop-management UX, agri-tech trends, Telangana-local). All load-bearing facts re-confirmed against live sources._

Confirmations are in. All load-bearing facts hold (data.gov.in Agmarknet API live, updated 17/06/2026; Telangana 2025-26 paddy distress sales at Rs 1,800-1,900 vs ~Rs 2,389 MSP, <1,000 of 8,000 centres operational, Rs 1,160 cr bonus unpaid to 4 lakh farmers; Saagu Baagu +21%/-9%/+66k confirmed; Kisan e-Mitra Telugu-via-Bhashini at 20k queries/day). Report below.

---

# REPORT A — Farmer Needs & Competitor Landscape
**Rythu | Pilot: Jayashankar Bhupalpally, Telangana | Compiled July 2026**

Scope: what small/marginal Telugu-speaking farmers actually need across the crop cycle, who serves those needs today, and the concrete crop-management UX patterns competitors ship — with each competitor's monetization bias and every hype/vaporware claim flagged. Grounded in the verified findings and re-confirmed against live sources July 2026.

---

## 1. What farmers need today

A ranked jobs-to-be-done (JTBD) map. Severity is 1-5 (5 = acute, causes real financial/loss pain now). Stage tags the crop cycle: **PRE-SOW → GROW → HARVEST → SELL**, plus **CROSS** (needs that span the whole cycle). The four SELL/GROW/scheme/voice needs at severity 5 are the ones Rythu does *not* yet serve at all — they are the frontier.

| # | Job to be done (farmer's words) | Stage | Sev | Evidence | Rythu status |
|---|---|---|---|---|---|
| 1 | **"Tell me a fair price and where/when to sell so I'm not cheated at the mandi"** — today's local price, the MSP floor, and whether the procurement centre is open | SELL | 5 | 2025-26 Telangana paddy crisis is the sharpest proof: delays pushed farmers into **distress sales to millers at Rs 1,800-1,900/qtl vs ~Rs 2,389 MSP**, with Rs 300-400/qtl lost to talu/hamali/transport deductions; only **<1,000 of ~8,000 planned centres operational**, and **Rs 1,160 cr bonus still unpaid to ~4 lakh farmers** ([Open Magazine](https://openthemagazine.com/india/telanganas-26000-crore-paddy-procurement-a-high-stakes-agricultural-standoff), [Telangana Today](https://telanganatoday.com/telangana-paddy-crisis-deepens-protests-erupt-in-several-districts-over-procurement-delays)). Only **~9% (fewer than 1 in 10)** of ag households ever sell at MSP (NSSO 77th round, 8.8%; some methods put it at 5.6% — [ShankarIAS](https://www.shankariasparliament.com/current-affairs/the-reach-and-depth-of-msp)). | **NOT built — #1 gap** |
| 2 | **"Show me what's wrong with my crop and what to do — before the pest spreads"** | GROW | 5 | Universal headline feature of every private app (Plantix, AgroStar, DeHaat, BigHaat). Pink bollworm on cotton and brown planthopper on paddy are recurring Telangana pests. But honest delivery is *hard* (see §3). | NOT built |
| 3 | **"Give me weather I can act on — rain / spray / sow / irrigate today, as a Telugu action, not a %"** | CROSS | 5 | Govt itself moved this way: IMD launched **Gram-Panchayat-level 5-day forecasts (24 Oct 2024)** pushed via WhatsApp ([PIB](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2067232)). Weather-gated advice (don't spray before rain) is standard in BharatAgri/DeHaat. | **Built** (Rythu's strength — deepen it) |
| 4 | **"Help me actually GET the government money I'm owed and not miss deadlines"** — per-scheme eligibility + reminders | CROSS | 5 | Kisan e-Mitra exists *solely* for this and answers **20k queries/day, 92 lakh total** ([PIB](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2117392&reg=48&lang=2)). Telangana specificity matters: **Rythu Bharosa (Rs 12,000/acre) now requires land registered in the Bhu Bharati portal and EXCLUDES tenants**, who are redirected to **Indiramma Atmiya Bharosa (Rs 12,000/yr flat, MGNREGS-gated)** ([mulugu.telangana.gov.in](https://mulugu.telangana.gov.in/scheme/rythu-bharosa-agriculture-support/)). RoFR/Podu pattadars are *de jure* eligible but *de facto* denied via forest-dept objections. | **Built** (19-scheme section — deepen into eligibility/reminders) |
| 5 | **"Let me just LISTEN and TAP in Telugu"** — low-literacy, first-time smartphone user; voice is the substrate for every feature | CROSS | 5 | Validated at scale: Kisan e-Mitra does full **Telugu voice-in/out via Bhashini/IndicTrans2**; Saagu Baagu ran a **Telugu WhatsApp chatbot** for its whole cohort ([WEF](https://www.weforum.org/impact/ai-for-agriculture-in-india/)). YouTube is the #1 preferred channel among Telangana farmers (67.5% in a 12-village study — [IJBSM](https://ojs.pphouse.org/index.php/IJBSM/article/view/4919)). | **Partly built** (tap-to-hear TTS; add voice-query) |
| 6 | **"Tell me what to do on MY crop THIS WEEK"** — stage-timed, do-this-now advisory keyed to sowing date | GROW | 4-5 | PxD Ama Krushi/Odisha RCT (13.5k paddy farmers, 3 yr) measured **−26.4% pest/disease loss, −25.8% weather-shock loss, ~10% fewer severe-loss events, +4.1% harvest, $12-19 return per $1** ([Precision Development](https://precisiondev.org/2024-annual-report/customized-digital-advice-can-help-farmers-manage-crop-loss-and-weather-shocks-evidence-from-pxds-work-in-odisha/)). BharatAgri **monetizes exactly this** — 100k+ paying subscribers ([Triveous](https://www.triveous.com/case-studies/bharatagri)). Rule-based, no ML. | NOT built (strongest honest build after prices) |
| 7 | **"Get me input credit without land papers I don't have, so I skip the moneylender"** | PRE-SOW | 4 | NAFIS 2021-22: **88% have a bank account but only ~40% of farmers have formal credit access (~60% lack it); 44% hold a valid KCC** ([PIB](https://www.pib.gov.in/PressNoteDetails.aspx?NoteId=153270&ModuleId=3)); ~half of borrowers still depend on informal credit ([SAGE 2024](https://journals.sagepub.com/doi/10.1177/09730052241262599)). Route to eKCC/Flexi-KCC/JLG/SHG — advisory only, not lending. | NOT built |
| 8 | **"Tell me if this seed/pesticide/fertiliser is real before I waste money"** | PRE-SOW | 4 | Spurious cotton-seed rackets recur in Telangana pre-Vanakalam ([Telangana Today](https://telanganatoday.com/spurious-cotton-seed-racket-plagues-telangana-farmers-ahead-of-vanakalam)). The often-cited **"25-30% of pesticides are fake"** is a real, widely-echoed figure but is from a **2015 FICCI report on 2013 data** ([FoodNavigator](https://www.foodnavigator-asia.com/Article/2015/10/06/Ficci-report-One-third-of-Indian-pesticides-are-dangerous-fakes)) — present it as a long-standing structural problem, **not a current-year stat**. | NOT built |
| 9 | **"How much fertiliser do I actually need for my acre, so I don't overspend"** | GROW | 4 | Pure-formula NPK calculators are common standalone tools (Mahadhan, FarmAtma). Zero ML, works offline, on-brand ("buy this little"). | NOT built (quick win) |
| 10 | **"Track MY specific field(s): area, crop, sowing date"** | CROSS | 3-4 | The enabling primitive for personalization + the crop calendar; DeHaat/BharatAgri/Krish-e all center on a plot/crop profile. Basic version needs no backend (localStorage, like Rythu already does for village/language). | NOT built |
| 11 | **"Connect me to a real expert (free) when the app can't help"** | GROW | 4 | AgroStar runs **25k live agronomist calls/day** ([AgroStar](https://corporate.agrostar.in/)). Rythu can surface the **free Kisan Call Centre (1800-180-1551)** + weekly Rythu Vedika VC schedule at zero cost. | NOT built (cheap to surface) |
| 12 | **"Tell me which WhatsApp forward is TRUE"** — be the cited, no-agenda Telugu source | CROSS | 4 | Directly serves the honesty/commission-free wedge; low infra. | Partly (citations already in Crops/Schemes) |
| 13 | **"Where can I buy genuine seed/fertiliser nearby and what does it cost?"** | PRE-SOW | 3 | Kisan Suvidha ships a **neutral dealer directory (name + phone)** ([IndiaFilings](https://www.indiafilings.com/learn/kisan-suvidha-app)). A directory (not a store) keeps "we sell you nothing." | NOT built |
| 14 | **"Keep a simple tap-and-voice record of what I spent this season"** | CROSS | 2 | Krish-e Farm Khata / My Crop Manager do this; lower proven demand among marginal farmers than do-this-now advice. | NOT built |
| 15 | **"Roughly how much will I harvest / is my crop on track"** | HARVEST | 2 | Simple version = area × yield-per-acre lookup (honest, offline). Satellite NDVI version is enterprise infra — defer. | NOT built |

### Biggest UNMET needs (the frontier)
1. **Mandi price + MSP floor + sell-now/wait signal (SELL, Sev 5).** The single largest gap vs every competitor, and the most on-brand honest build: the **data.gov.in Agmarknet daily-price API is free, live, and was updated 17/06/2026** ([data.gov.in](https://www.data.gov.in/catalog/current-daily-price-various-commodities-various-markets-mandi)), filterable by Telangana state/district/market/commodity. This is an API integration, not infrastructure. **Caveat: ship real current + historical prices only — NOT ML price *prediction*** (dangerous for users who treat a forecast as fact; even a live app like Jai Kisan slaps a "may not reflect real-time prices, verify locally" disclaimer on its AI prices — a pattern Rythu should copy).
2. **Stage-timed crop advisory keyed to sowing date (GROW, Sev 4-5).** Rule-based, measurable impact (PxD), and Rythu's crops guide already has the season/sowing/water data to seed it. The hard part is the *push channel* (see below), not the rules.
3. **Scheme eligibility + deadline reminders, with correct Telangana routing (CROSS, Sev 5).** Rythu already curates 19 schemes; the deepening is a plain-Telugu decision tree ("do you have Bhu-Bharati land? are you a tenant?") that routes tenants to Indiramma Atmiya Bharosa — an honesty win competitors get wrong.
4. **Telugu voice as the substrate (CROSS, Sev 5).** Rythu has tap-to-hear; a Telugu voice-*query* layer over its own verified content (via free Bhashini ASR) is a credible differentiator with no model training.

### Constraints that gate the above (flag honestly)
- **Push channel is a real infra decision, not a UI detail.** PWA web-push is unreliable on cheap Android; the proven-in-Telangana channel is **WhatsApp** (Saagu Baagu) or SMS/IVR. Stage-timed reminders can't ship on the PWA alone.
- **Full IVR / feature-phone reach needs telephony** beyond a PWA — roadmap, don't promise.
- **Procurement-centre open/closed status has no reliable public API** — needs a TS Civil Supplies feed or manual verification (fits Rythu's "verified" model, but don't promise real-time until secured).
- **Offline mode is unbuilt** and matters given Bhupalpally connectivity — treat "works offline" as aspirational; design Weather/Crops/Schemes to be readable from cache first.

---

## 2. Competitor feature matrix

Legend: **✓** = present/strong · **~** = partial, weak, or human-in-the-loop · **✗** = absent. "Bias" = does advice funnel into selling the farmer inputs?

| App | Weather | Crop advisory | Photo diagnosis | Mandi price | Marketplace | Schemes | Credit | Community | Voice / Telugu | Monetization (input-sales bias) | Traction |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **Plantix** (PEAT) | ✓ | ✓ | ✓ **AI, best-in-class** | ✗ | ~ (brand links) | ✗ | ✗ | ✓ (500+ experts, outbreak alerts) | ~ Telugu since 2017 (text) | Free; monetizes via agri-input brand/govt/NGO partnerships → **treatment recs can carry buy-bias** | 10M+ Play installs; ICRISAT cites up to 45M users / ~1.2M MAU ([GSMA](https://www.gsma.com/solutions-and-impact/connectivity-for-good/mobile-for-development/programme/agritech/detecting-and-managing-crop-pests-and-diseases-with-ai-insights-from-plantix/)) |
| **DeHaat** (AgRevolution) | ✓ | ✓ (crop calendar, voice) | ~ **human expert, ~30 min** + product rec | ✓ | ✓ inputs + output selling | ~ | ✓ BNPL/own-book | ✓ Krishi Manch | ✓ regional voice advisory | **Full-stack: input margin + output margin + lending — NOT commission-free** | 12M+ farmers, 120k+ villages, 15k+ centres (co.); FY25 "profit" is a non-cash CCPS gain — **operating loss ~Rs 207 cr on ~Rs 3,010 cr rev** ([Entrackr](https://entrackr.com/fintrackr/dehaat-cuts-losses-by-15-to-rs-207-cr-in-fy25-10504383)) |
| **AgroStar** | ✓ | ✓ 500+ BSc agronomists | ✓ AgriDoctor (photo) | ~ | ✓ 200+ own brands, 7k-10k Saathi stores | ✗ | ✗ | ✓ Krishi Charcha | ✓ Telugu; **~6MB, works on 2G/3G offline** | **Agri-input e-commerce is the revenue; advisory is the funnel** | ~8.6M Play downloads (co. claims 10M+ reached); 25k live calls/day; $30M Just Climate Nov 2025, >$140M total |
| **BharatAgri** (Leancrop) | ✓ 3-day | ✓ **paid** season-long crop calendar ("Super Seva") | ~ via expert | ✗ | ✓ input store | ✗ | ✗ | ✗ | ✓ Telugu | **Freemium: personalized calendar + expert access paywalled (~Rs 600/acre/6mo) + input sales** | 300k+ users, **100k+ paid**, 20× paid growth/12mo, 65% renewal |
| **Kisan Suvidha** (Govt) | ✓ 5-day + alerts | ✓ district advisories | ~ **photo-to-expert** | ✓ incl. max price in state/India | ✗ | ~ KCC tile | ~ KCC info | ✗ | ✓ **9 languages incl. Telugu** | **None — no commerce, no commission** | Govt single-window app |
| **Kisan e-Mitra** (Wadhwani AI) | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ **PM-KISAN status/queries only** | ✗ | ✗ | ✓ **full Telugu voice-in/out via Bhashini** | **None (govt)** | 20k queries/day, 92 lakh answered, 2.69M in 186 days |
| **Saagu Baagu** (TS Govt + Digital Green) | ~ | ✓ **stage-based, push+pull** | ✗ (uses soil-test + CV grading instead) | ~ buyer-seller linkage | ~ e-market | ✗ | ✗ | ✗ | ✓ **Telugu WhatsApp chatbot (Glific)** | **None — philanthropy/govt-funded, commission-free** | Pilot 7,000 chilli farmers: **+21% yield, −9% pesticide, −5% fertiliser, +8% price, ~Rs 66k/acre/cycle** ([DeepLearning.AI](https://www.deeplearning.ai/the-batch/ai-elevates-chili-farming-in-india-with-smarter-yields/)) |
| **BigHaat** | ✓ | ✓ | ✓ AI "Crop Doctor" | ✓ | ✓ 10,000+ products | ✗ | ✗ | ✓ Kisan Vedika | ✓ Telugu | **Input marketplace-first — diagnosis/advisory funnel into sales** | Confirmed live; exact installs unverified |
| **NaPanta** | ~ | ✓ | ✗ | ✓ **3,000+ mkts, 300+ commodities, 7d-3yr trend, Telugu voice search** | ~ agri store, rentals, dealer links | ~ | ✗ | ✗ | ✓ Telugu voice search | **Supply-side: agri store + equipment rental + dealer/e-commerce listings** | **3,48,015 farmers as of 12-Jul-2026** ([napanta.com](https://www.napanta.com/)) |
| **Krish-e** (Mahindra) | ✓ | ✓ crop calendar + Farm Khata diary | ✓ Nidaan (photo, 20+ crops) | ~ | ~ equipment rental | ✗ | ✗ | ✗ | ✓ 8 langs incl. Telugu | Advisory relatively **product-neutral** vs pure-commerce apps; monetizes equipment/services | Established M&M product |
| **IFFCO Kisan** | ✓ IMD | ✓ agro-climatic | ✗ | ✓ AGMARKNET + trends | ✓ buyer-seller | ✗ | ✗ | ~ | ✓ 11 langs incl. Telugu; "Ask Our Experts" voice call | Cooperative (IFFCO fertiliser) — **moderate input bias** | Established (medium-confidence figures) |
| **Agmarknet / e-NAM** (Govt) | ✗ | ✗ | ✗ | ✓ **the source feed** | ~ e-NAM online bid/pay (largely fails for smallholders) | ✗ | ✗ | ✗ | ~ (e-NAM dashboard has Telugu) | **None (govt)** | ~1,473-1,522 e-NAM mandis; **inter-state trade −78% FY25** ([Rau's IAS](https://compass.rauias.com/current-affairs/inter-state-trade-electronic-national-agriculture-market-e-nam-declined-fy25/)) |
| **Gram Vaani / FarmPhone** | ~ | ✓ IVR Q&A | ✗ | ~ FarmPhone market linkage | ✗ | ~ | ✗ | ✓ voice IVR | ✓ **pure voice/IVR — bypasses literacy entirely** | Nonprofit — **neutral** | Long-running participatory-media proof |
| **Rythu Bharosa app** (TS Govt) | ✗ | ✗ (advisory is physical, at Rythu Vedikas) | ✗ | ✗ | ✗ | ✓ **DBT status only** (officer-facing crop booking) | ✗ | ✗ | ~ | **None (govt DBT)** | **Telangana has NO farmer-facing state advisory app — white space Rythu can own** |
| **Rythu (us)** | ✓ **honest, action-rule** | ~ (5-crop guide, not personalized) | ✗ | ✗ **#1 gap** | ✗ (by design) | ✓ **19 schemes, honesty badges** | ✗ | ✗ | ✓ **tap-to-hear Telugu** | **Commission-free — "we sell you nothing"** | Live PWA, pilot |

**How the market monetizes (the pattern Rythu inverts):** the private full-stack players (DeHaat, AgroStar, BigHaat, BharatAgri, Gramophone→Unnati) all make money from **selling inputs or a paid subscription**, so their advisory and even their disease diagnosis are structurally biased toward "buy this product." That standalone advisory-commerce is hard to sustain is shown by **Gramophone's stock-swap merger into Unnati, approved 3 Jan 2026** (Unnati FY25: Rs 291 Cr revenue, Rs 18.4 Cr loss — [Inc42](https://inc42.com/buzz/unnati-to-acquire-info-edge-backed-agritech-startup-gramophone/)). The **commission-free lane is occupied only by governments and philanthropies** (Kisan Suvidha, Kisan e-Mitra, Saagu Baagu, Gram Vaani) — none of which is a polished, farmer-facing, Telugu-first *consumer app for Telangana*. That is Rythu's wedge.

**Out of scope (not competitors for this segment):** **Fasal** (IoT smart-irrigation hardware — capex barrier, targets horticulture/orchards); **Cropin SmartFarm** (B2B/enterprise, needs org-issued credentials); **SatSure** (B2B satellite risk-score for banks). Real tech, wrong user.

---

## 3. How competitors handle crops ("crops and all that stuff")

The concrete crop-management UX patterns, who ships each, and what it costs to build honestly. Ordered from **cheapest/highest-ROI for Rythu** to **hardest/defer**.

### 3.1 Minimal crop onboarding (crop + sowing date, stepwise, icon-driven)
- **Pattern:** a short visual flow — pick crop from a photo/illustration grid, then sowing date, then optionally area/variety — not a form. Keep ≤3 taps to content, large sunlight-readable targets, Telugu voice at each step. *Structured menus beat open voice input for low-digital-literacy users.*
- **Who:** **Krish-e** and **BharatAgri** both onboard on essentially crop + sowing date + a couple of points.
- **Data/infra needed:** a crop list (Rythu already has 5 pilot crops) + date picker + Telugu voice strings. **No AI; ships on the existing PWA;** store in localStorage like village/language already are. *This is the primitive that unlocks 3.2, 3.3, and 3.6.*

### 3.2 Personalized stage-wise crop calendar (rule-based)
- **Pattern:** from crop + sowing date (+ optional location/variety/area), generate a season-long timeline — land prep, sowing, weeding, fertiliser splits, key sprays, irrigation, harvest window — surfaced as a simple **"what to do now / next" Telugu-voice card**, not a dense table.
- **Who:** **BharatAgri** (30+ params + Agri-Doctor curation, *paywalled*), **Krish-e** (computed from ~6 inputs), **DeHaat** ("Mere fasalon ki jankari" action calendar), **Saagu Baagu** (Telugu WhatsApp, push at 7 AM paddy / 6 PM chilli + pull by crop×stage).
- **Data/infra needed:** a **rule table (crop × stage × days-after-sowing → action)** authored from KVK/PJTSAU/ICAR for the 5 pilot crops. Rule-based like Rythu's existing weather advice — **no ML.** Main cost is agronomy content authoring + Telugu translation. **This is the strongest honest next build after prices; BharatAgri proves willingness to *pay* for it (100k+ subscribers).**

### 3.3 Stage-based task reminders, weather-gated (spray/irrigate/fertilise now)
- **Pattern:** compute days-since-sowing against the calendar for "do this today" nudges, then **gate weather-sensitive tasks on the forecast** (don't tell a farmer to spray before rain; adjust irrigation to rain probability).
- **Who:** **Saagu Baagu** (proven in Telangana via Telugu WhatsApp); **BharatAgri/DeHaat** tie spray/irrigation to a ~3-day forecast.
- **Data/infra needed:** the stage rule table + Rythu's existing Open-Meteo forecast + **a delivery channel**. This is the real infra decision: **PWA web-push is unreliable on cheap Android — WhatsApp (Saagu Baagu's proven Telangana channel) or SMS/IVR is required.** Flag as infra-dependent, not a current-PWA feature.

### 3.4 Fertiliser / NPK dose calculator (pure formula)
- **Pattern:** pick crop + area (acre/guntha) → N-P-K kg → convert to Urea/DAP/MOP/SSP bags (handling the DAP N+P overlap) → optionally split by growth stage. Formula: `dose = (nutrient requirement ÷ nutrient %) × 100`; Urea = N/0.46, DAP = P/0.46, MOP = K/0.60, SSP = P/0.16.
- **Who:** standalone tools — **Mahadhan**, "Fertilizers Calculator & MC," FarmAtma, Agri Farming (note: *not* integrated into AgriStack, contrary to earlier notes).
- **Data/infra needed:** just a per-crop recommended-dose table (KVK / Soil Health Card norms) + arithmetic. **Zero AI, works offline, fits "buy this little."** Strong quick win for the 5 pilot crops.

### 3.5 Per-plot / field management ("add my field")
- **Pattern:** add field(s) with name, area, crop, sowing date, notes; each field anchors its own calendar/reminders/records.
- **Who:** **My Crop Manager** (variety/planting-date/stage/harvest per field, offline, freemium); **DeHaat/BharatAgri** add satellite boundary mapping.
- **Data/infra needed:** basic version = a local data model `{field, area, crop, sowing date, notes}` in device storage — **no backend for a single-farmer PWA.** Satellite boundary/stress needs GPS polygons + a pipeline (**defer**); cross-device sync needs the **user-accounts layer Rythu hasn't built.**

### 3.6 Photo pest/disease diagnosis — the build trap (do NOT fake this)
- **Pattern:** camera → CNN classifier → disorder + severity + organic/chemical treatment + prevention.
- **Who:** **Plantix** (best-in-class; ~800 symptoms across ~60 crops, Telugu since 2017), **AgroStar** AgriDoctor, **Krish-e** Nidaan, **BigHaat** Crop Doctor. **DeHaat's "diagnosis" is actually human-expert** (a solution + product rec in ~30 min) — a human-in-the-loop commerce funnel, not on-device AI.
- **The honesty problem (CONFIRMED, load-bearing):** lab accuracy on PlantVillage (**99.35%**) collapses to **~31.4% on real field photos** because models learn *backgrounds*, not symptoms (Mohanty et al. 2016 — [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC5032846/); corroborated by Ferentinos ~33% and Noyan 2022's background-bias study — [arXiv](https://arxiv.org/pdf/2206.04374)). Even KissanAI's own field disease model self-reports ~36%. **Plantix's ">90%" is a real but *conditional* number** (degrades with light/sharpness/crop/symptom position), and its "reduces pesticide use" claim is contested because the model is tied to an input-sales funnel.
- **Data/infra needed:** a trained CNN + a **large FIELD-condition labelled dataset per crop×disease that Rythu does NOT have.** ⚠️ **Do not ship or imply AI photo diagnosis in v1 — it is the exact vaporware Rythu's honesty brand rejects.** Honest v1 options: (a) a **voiced Telugu symptom-decision guide** / static illustrated pest guide (pink bollworm on cotton, brown planthopper on paddy) + "show your AEO/KVK"; (b) **photo-to-human-agronomist over WhatsApp** (AgroStar/DeHaat model, needs only upload + a responder network); or (c) deep-link/surface a free existing route — **Kisan Suvidha already offers photo-to-expert.** Options (a)/(b) fit the commission-free wedge best.

### 3.7 Telugu voice / audio layer over everything (the substrate)
- **Pattern:** every screen has tap-to-hear Telugu; reminders and Q&A can also run as WhatsApp voice notes or dial-in IVR so a non-reader gets full value.
- **Who:** **Kisan e-Mitra** (full Telugu voice-in/out via Bhashini, 20k queries/day), **Saagu Baagu** (Telugu WhatsApp), **Farmer.Chat** (returns voice notes; multimodal, low-literacy design — the specific "Start→Category→Crop" onboarding flow could *not* be independently verified), **Gram Vaani/FarmPhone** (pure IVR).
- **Data/infra needed:** **Bhashini / IndicTrans2 is FREE govt Telugu STT/TTS**, reusable. Rythu already has tap-to-hear; the incremental, **hallucination-safe** build is Telugu speech-*input* + **RAG over Rythu's own verified crop/scheme content** (not a general LLM). ⚠️ Full IVR needs telephony beyond the PWA.

### 3.8 Human-expert fallback (free, zero-cost to surface)
- **Pattern:** missed-call / tap-to-call → a BSc agronomist calls back in Telugu.
- **Who:** **AgroStar** (25k calls/day, in-house — expensive/ops-heavy). Rythu's honest, zero-cost version: **surface the free Kisan Call Centre (1800-180-1551) + the weekly Rythu Vedika VC schedule** rather than staffing.

### 3.9 Community / Q&A forum
- **Who:** Plantix (500+ experts + outbreak alerts), AgroStar Krishi Charcha, BigHaat Kisan Vedika, DeHaat Krishi Manch.
- **Data/infra needed:** moderation + posting/feed backend. **Lower priority for Rythu** — moderation cost is real and it's risky for thin-connectivity/low-literacy users; defer until critical mass.

### 3.10 Satellite / yield estimation
- **Who:** Farmonaut, Cropin, Crop Analytica (Sentinel-2 NDVI → yield/harvest forecast 10-30 days pre-harvest).
- **Data/infra needed:** field polygons + Sentinel-2 + ML pipeline, with accuracy caveats — **enterprise/infra-heavy; defer.** A simple **area × yield-per-acre lookup** delivers most of the perceived value honestly.

### Distribution note (not a feature, but decisive)
Telangana has **2,601 Rythu Vedika centres** (one per ~5,000-acre AEO cluster) that already gather farmers for training — the proven offline distribution path Saagu Baagu used (via ICRISAT-trained AEOs). Rythu's go-to-market in Bhupalpally is a **field/partnership playbook** (seed via AEOs, Rythu Vedika demos, FPO/PACS tie-ups), not a growth-hacking channel.

---

### Hype / vaporware explicitly flagged (do not build or imply in v1)
- **AI photo disease diagnosis** — needs a labelled Telugu field dataset Rythu lacks; field accuracy collapses to ~31-36%. Ship a voiced symptom guide or photo-to-human instead.
- **Mandi price *prediction* ("sell now vs wait" ML)** — forecasting is genuinely hard and dangerous for users who treat it as fact. Ship real current + historical only, with a verify-before-selling disclaimer.
- **LLM/GenAI voice advisory** (Farmer.Chat, KissanAI/Dhenu, AIEP, Kissan-Dost) — emerging, unaudited reach claims, documented hallucination/unsafe-advice risk. Roadmap, not table stakes.
- **e-NAM's "unified national market / farmer-driven price discovery"** — effectively vaporware in practice (inter-state trade −78% FY25; agents operate it for smallholders). Copy only the price-*display* value.
- **Satellite NDVI yield/harvest estimation** — real but enterprise infra; defer.
- **IVR / feature-phone reach + stage-timed voice push** — needs telephony beyond a PWA.
- **Procurement-centre open/closed status** — no reliable public API yet.
- **"Works offline"** — aspirational; not currently built.
- **Vendor accuracy/reach numbers** (Plantix ">90%", DeHaat/AgroStar/KissanAI "XM farmers", DeHaat "Rs 369 cr profit") — treat as marketing/directional; the corrected figures are in §2.

*Sources are cited inline throughout; the fullest source lists are in the underlying verified findings for each area (farmer-JTBD, competitor-features, crop-management-UX, agritech-trends, telangana-local).*

---

Both load-bearing build recommendations are confirmed live. Here is REPORT B.

---

# REPORT B — Rythu Sections Roadmap

*Scope: what to build next for the Jayashankar Bhupalpally pilot, on the existing Next.js/TS + Python/AWS-serverless PWA, with a tiny team. Grounded in the verified findings + two live-web confirmations of the top enablers (data.gov.in AGMARKNET mandi API and Bhashini Telugu voice).*

**Strategic frame:** Telangana has **no farmer-facing state advisory app** — the govt Rythu Bandhu/Bharosa app is officer-facing (AEO crop-booking + DBT). That is white space Rythu can own in Bhupalpally. Every private competitor (NaPanta, Plantix, DeHaat, AgroStar, BharatAgri, BigHaat) ultimately funnels advice into **input sales** — the buy-bias is their business model. Rythu's "we sell you nothing" is not a limitation here; it is the one thing none of them can copy. Every recommendation below is chosen to widen that moat, not narrow it.

---

## 1. Gap analysis — what's missing and worth adding

Rythu today = honest weather + static crops guide + 19-scheme section + Telugu TTS + remembered village/language. Against the verified severity-5 farmer needs and competitor table stakes, the gaps, ordered by pain:

| # | Gap (vs what Rythu has) | Evidence it matters | Who has it (Rythu doesn't) |
|---|---|---|---|
| **1** | **No prices.** No mandi price, no MSP floor, no procurement signal. | #1 verified need (sev 5, high). TS 2025-26 paddy crisis is confirmed statewide: moisture-cap rejections, ~₹1,160 cr bonus unpaid to ~4 lakh farmers, 40-day waits → forced below-MSP distress sales. | NaPanta, Kisan Suvidha, e-NAM/Agmarknet, IFFCO Kisan, BigHaat — **every** major app. |
| **2** | **Crops guide is static.** No "what to do on MY crop this week" tied to sowing date/stage. | Sev 5. PxD Odisha RCT: stage-timed advisory cut pest/disease loss 26.4%, weather-shock loss 25.8%, +4.1% harvest, $12–19 return per $1. BharatAgri monetizes exactly this (100k+ paying). | BharatAgri, DeHaat, Krish-e, Saagu Baagu. |
| **3** | **Voice is output-only.** Rythu reads Telugu (TTS) but the farmer can't *ask* by voice. | Sev 5 — voice is the substrate for low-literacy first-time smartphone users. Kisan e-Mitra proves Telugu voice-in/out at scale (~20k queries/day via Bhashini). | Kisan e-Mitra, Saagu Baagu, Farmer.Chat. |
| **4** | **No crop-problem help.** No pest/disease path at all. | Sev 5. TS-specific: pink bollworm on cotton, brown planthopper on paddy; spurious-seed rackets confirmed. | Plantix, AgroStar, Krish-e Nidaan, DeHaat (photo-to-human). |
| **5** | **Schemes are read-only.** No per-scheme eligibility logic, no deadline reminders; **and the tenant copy is wrong.** | Sev 4-5. Correction: Rythu Bharosa now *excludes* tenants (requires Bhu Bharati-registered arable land); tenants/landless route to **Indiramma Atmiya Bharosa** (₹12,000/yr flat). RoFR/Podu pattadars are de-jure eligible but de-facto denied → the honest plain-Telugu explainer is a real wedge. | Kisan e-Mitra (scheme-status only, 92 lakh+ answered). |
| **6** | **No fertilizer math.** Farmer can't see "how much urea/DAP for my acre." | Sev 4 — over-spend pain; pure formula, offline, on-brand ("buy this little"). | Kisan Suvidha, BigHaat, standalone NPK apps. |
| **7** | **No dealer directory.** Where to buy genuine seed/fertilizer nearby. | Sev 3. A *directory* (name+phone), not a store, keeps the wedge. | Kisan Suvidha (neutral pattern). |
| **8** | **No "my field."** No plot record → nothing to personalize against. | Sev 3-4; enabling primitive for the calendar. | DeHaat, BharatAgri, Krish-e, My Crop Manager. |
| **9** | **Not offline.** Patchy Bhupalpally connectivity; Rythu is a PWA but hasn't hardened offline. | Sev 4-5. AgroStar deliberately ships ~6 MB / 2G-capable. Rythu is well-placed to win here. | AgroStar, Plantix (offline capture). |
| **10** | **No human bridge.** Nowhere to send a farmer the app can't help. | Sev 4. Free Kisan Call Centre (1800-180-1551) + Rythu Vedika VC schedule = zero-cost bridge. | AgroStar (paid agronomists), Kisan Suvidha (1-click KCC). |

Two constraints thread through all of it: **voice/offline are not features, they are the substrate** — anything that isn't listenable and isn't readable on a bad network excludes the target user.

---

## 2. Recommended new sections/features — prioritized

Ranked by **value ÷ effort for the Bhupalpally pilot**. Effort assumes the current Next.js/TS front end + Python Lambda + a two-person team. "Honesty-wedge fit" = how well it reinforces commission-free/no-vaporware.

| Rank | Section / feature | Farmer value (why) | Feasibility on our stack | Data / infra needed | Wedge fit | Blocker |
|---|---|---|---|---|---|---|
| **1** | **Mandi Prices** — today's min/max/modal for the 5 crops at Warangal/Enumamula + nearby markets, with the **MSP floor line** drawn on top and a "**verify before you sell**" disclaimer. | The #1 unmet need; directly targets distress-sale pain. Kills the "trader cheated me" problem with a public number. | **Low.** Python Lambda pulls daily on a cron, caches to DynamoDB/S3, Next.js renders Telugu labels + TTS. | **Confirmed free:** data.gov.in AGMARKNET resource `9ef84268-d588-465a-a308-a864a43d0070`, `filters[state]=Telangana` + district/market/commodity, JSON. Register a free key (sample key caps 10 rows). MSP = annual table (paddy KMS'25-26 ₹2,369/₹2,389). | **Highest** — pure info, no selling, honest disclaimer. | None. (Procurement-center OPEN/CLOSED is the *hard sub-part* — no public API; ship prices+MSP now, add center status later via manual/verified feed.) |
| **2** | **Fertilizer / NPK calculator** — pick crop + area (acre/guntha) → N-P-K kg → Urea/DAP/MOP bags, split by stage. | Stops over-spend; "buy this little" is the wedge made concrete. | **Very low.** Pure arithmetic in TS; works offline. | Per-crop dose table (PJTSAU/KVK/Soil Health Card norms) for 5 crops. No API, no ML. | Very high. | None. |
| **3** | **Offline-first hardening** of Weather/Crops/Schemes. | Patchy connectivity is a hard constraint; makes existing value survive a dead network. | **Low.** Service-worker caching + localStorage; Rythu is already a PWA. | None beyond frontend work. | High (matches cheap-phone user). | None. Keep "works offline" scoped/honest, not a blanket claim. |
| **4** | **Human-expert bridge** — surface **Kisan Call Centre 1800-180-1551** (1-tap dial) + weekly Rythu Vedika VC schedule. | Real fallback when the app can't help, by voice, for non-readers. | **Trivial.** A tap-to-call card + a static schedule. | Rythu Vedika schedule for Bhupalpally (manual). | High (free, no funnel). | None. |
| **5** | **Schemes v2** — per-scheme plain-Telugu eligibility decision-tree ("do you have Bhu-Bharati land? are you a tenant?") + deadline reminders + **fixed tenant routing to Indiramma Atmiya Bharosa.** | Turns a reading list into "am I eligible + what next + don't miss the date." | **Low-med.** Decision-tree JSON over existing 19-scheme data; in-app reminders. | Curated eligibility rules/deadlines (already Rythu's method). | Very high (honest curation is the brand). | Push reminders unreliable on cheap Android — deliver in-app first, defer WhatsApp/SMS. |
| **6** | **Static illustrated pest guide + photo-to-human** — Telugu-voiced symptom guide for the top cotton/paddy pests, "photograph it and show your AEO / call KCC." | Meets the sev-5 crop-problem need **honestly**, with no fake AI. | **Low-med.** Content + images; no model. | Agronomy content authoring (PJTSAU/KVK) + Telugu voice. | Very high (refuses the vaporware). | Content authoring time. |
| **7** | **Input-dealer directory** — Bhupalpally seed/fertilizer/pesticide dealers, name + phone + location. | "Where do I buy genuine input nearby" without a store. | **Low.** Static/curated JSON + tap-to-call. | Manual Bhupalpally dealer dataset. | High (directory, not commerce). | Manual data collection. |
| **8** | **"My Field" (local) + crop calendar view** — add field (name, area, crop, sowing date) → rule-based stage timeline. | Anchors advice to *my* plot; the sev-5 "what to do this week." | **Med.** localStorage record + a stage rules table; no backend, no accounts. | Per-crop stage×days-after-sowing×action rules (5 crops) + date picker. | High. | Cross-device sync needs the accounts layer Rythu hasn't built — defer sync, single-device first. |
| **9** | **Telugu voice-query** — speak a question → ASR → retrieval over Rythu's **own** verified content → TTS answer. | Voice-in closes the literacy gap; a credible differentiator. | **Med-high.** Bhashini pipeline (search-config → inference) from Lambda; RAG over own crop/scheme corpus. | **Confirmed free tier:** Bhashini/ULCA Telugu ASR+TTS (userID+apiKey at bhashini.gov.in/ulca). | High (retrieval-only = hallucination-safe). | ASR WER ~15-20% on clean speech, worse on noise; restrict answers to own content. |
| **10** | **Fake-input awareness** — short Telugu checklist to spot spurious seed/pesticide + how to report. | Sev-4 "is this real before I waste money." | **Very low.** Static content. | Content only. | High. | Frame fake-pesticide magnitude as a long-standing structural problem (2015 FICCI / 2013 data), not a current-year stat. |
| **11** | **Proactive stage-timed reminders** via WhatsApp/SMS. | The proven PxD/Saagu-Baagu impact channel; farmers live in WhatsApp. | **High effort + recurring cost.** Real infra decision, not UI. | WhatsApp Business API (or SMS/IVR) + a scheduler + accounts. | High. | **Cost + infra + accounts** — Phase 2, not now. PWA push is unreliable on cheap Android. |

**Do first (pilot sprint):** #1 Prices, #2 Fertilizer calc, #3 Offline, #4 Expert bridge, #5 Schemes v2 — all low-effort, high-trust, no new infra, and they make Rythu instantly competitive with NaPanta/Kisan Suvidha while staying on-wedge.

---

## 3. Crop-management: what Rythu should build

Move from a static guide to **personalized, honest, do-this-now** advice — without pretending to have AI it doesn't have. Phased so a tiny team ships value every step and never over-promises.

**Phase 0 — enrich the guide (no new infra, ship now).**
- **Fertilizer/NPK calculator** per crop (rank #2). Pure formula, offline.
- **Static illustrated pest guide** for the top TS pests (pink bollworm/cotton, brown planthopper/paddy), Telugu-voiced, ending in "photograph it → show your AEO / call KCC 1800-180-1551." This is the honest substitute for photo-AI.
- Everything readable offline + tap-to-hear.

**Phase 1 — "My Field" + rule-based crop calendar (the highest-leverage crop build).**
- **"My Field" local record:** name, area (acre/guntha), crop, sowing date, notes → `localStorage`, exactly like village/language today. **No accounts, no backend.** This one primitive unlocks all personalization.
- **Rule-based calendar:** author a `crop × stage × days-after-sowing × action` table for the 5 pilot crops from PJTSAU/KVK/ICAR. Render as a single **"what to do now / next"** Telugu-voice card, not a dense table. This is rule-based like Rythu's existing weather advice — **zero ML.**
- **Weather-gate** the spray/irrigate tasks against the existing Open-Meteo forecast: never advise spraying before rain; ease irrigation when rain is likely. This fuses Rythu's existing weather strength into crop management and is a genuine honesty differentiator over apps that push a fixed calendar.
- Still **pull-based** (farmer opens the app). No push cost yet.

**Phase 2 — proactive channel + voice-query (needs an infra decision + budget).**
- **Stage-timed reminders** over **WhatsApp Business API** (proven by Saagu Baagu in Telangana) or SMS. This is where user accounts, a scheduler, and recurring cost genuinely enter — treat as a funded decision, not a sprint task.
- **Telugu voice-query** (Bhashini ASR) over own content (rank #9), so a non-reader gets the calendar and schemes by speaking.

**Phase 3 — defer/partner-gated.**
- Photo-AI diagnosis (only if a labeled TS field dataset + honest field accuracy exist — see §4), satellite NDVI/plot-boundary mapping, yield forecasting. A **simple yield-per-acre lookup × area (with caveat)** delivers most of the perceived value honestly if farmers ask for it.

**Build FIRST inside crop-management:** the **fertilizer calculator + static pest guide** (cheapest, immediate), then **"My Field" + the rule-based, weather-gated calendar** — because that is the sev-5 "tell me what to do on my crop this week" need, and it's fully buildable on the current stack with no ML and no accounts.

---

## 4. What to deliberately NOT build (and why)

| Don't build | Why (verified) | Do instead |
|---|---|---|
| **Claimed AI photo disease diagnosis** in v1 | Lab-to-field accuracy collapses ~99.35% → ~31.4% (Mohanty 2016; KissanAI's own field model ~36%) from background bias. Claiming it is the exact vaporware Rythu's brand rejects; needs a large labeled Telugu field dataset Rythu doesn't have. | Static pest guide + photo-to-human (KCC / AEO / Rythu Vedika). |
| **Price prediction / "sell now vs wait" ML** | Forecasting is hard and dangerous for low-literacy users who read it as fact. | Ship **real current + historical** prices + MSP + a "verify before selling" disclaimer (the Jai Kisan honesty pattern). |
| **e-NAM-style trading / online bidding / "national market"** | Effectively vaporware in practice: inter-state e-NAM trade fell 78% in FY25; agents operate it for smallholders. | Copy only the price **display** value. |
| **Input marketplace / selling anything** | Breaks the wedge. Every competitor's advice carries buy-bias; Gramophone→Unnati (merger approved Jan 2026) shows standalone advisory-commerce is hard to sustain. | Neutral **dealer directory** (name+phone), never a store. |
| **Embedded credit / insurance / lending** (solo) | Needs a lending/insurance partner + alt-data underwriting + BaaS rails; NAFIS: ~60% of farmers lack formal credit — real need, wrong build. | Advisory-only **eligibility helper** routing to eKCC/Flexi-KCC/JLG/SHG + PMFBY. |
| **Satellite NDVI yield/stress + plot-boundary mapping** | Infra-heavy (Sentinel-2 + ML pipeline) with accuracy caveats; enterprise-grade (Cropin/Farmonaut). | Lightweight **"My Field"** record + optional yield-per-acre lookup. |
| **IoT hardware (Fasal-style)** | Capex barrier; targets higher-value horticulture — wrong segment for marginal paddy/cotton farmers. | Skip entirely. |
| **Full IVR / telephony as core v1** | Requires telephony infra beyond a PWA. | Surface the **free Kisan Call Centre**; consider IVR only if funded in Phase 2. |
| **Free-form LLM/GenAI chatbot** as table stakes | Emerging, unproven at scale, documented hallucination/unsafe-advice risk (Farmer.Chat/AIEP/KissanAI). | If voice-query, **restrict to RAG over Rythu's own verified content.** |
| **Community / Q&A forum** early | Moderation cost + thin connectivity + needs critical mass. | Defer; the human-expert bridge covers the "ask someone" need cheaply. |
| **Real-time procurement-center OPEN/CLOSED as a promise** | No reliable public API. | Honest eligibility/explainer now; add live status only once a TS Civil Supplies feed or manual-verify process is secured. |
| **"Works fully offline" as a current claim** | Offline is still unbuilt; over-claiming violates the honesty brand. | Harden offline incrementally; describe it accurately. |

**Copy-accuracy guardrails to honor everywhere:** MSP reach is **~9% (fewer than 1 in 10)**, not 10%; **tenants → Indiramma Atmiya Bharosa**, not "Rythu Bharosa tenant coverage"; Saagu Baagu's 500k is a *target* — only the 7,000-farmer Khammam chilli pilot is delivered; Plantix accuracy is conditional, not a flat guarantee.

**Distribution (not a feature, but load-bearing for the pilot):** seed adoption through Bhupalpally **AEOs + Rythu Vedika demos** (2,601 statewide; how Saagu Baagu scaled) + a local FPO/NGO tie-up. The app's honesty wins trust; the Rythu Vedika wins the first users.