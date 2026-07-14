# Rythu Agronomy Data — verified (2026-07-14)

Live web checks confirm the load-bearing values (nutrient %s, paddy BPH ETL/doses, chilli 60:60:30 kg/ha). Here is the report.

---

# Rythu Agronomy Data — Verified Report for `lib/agronomy.ts`

Scope: Kharif, Jayashankar Bhupalpally (Telangana). Sources are neutral/official only (PJTSAU → ICAR/KVK → Soil Health Card/Dept of Agriculture → TNAU/other SAU cross-check → CIB&RC by active ingredient). **No company/brand recommendations used.** Conversion: **1 ha = 2.47 acre**; per-acre = per-ha ÷ 2.47.

Live-web spot-checks done this pass (all matched the JSON): TNAU nutrient-content table (Urea 46% N, grade 18-46-0 = DAP 18% N/46% P2O5, MOP 60% K2O), TNAU paddy BPH ETL + doses, TNAU chilli manuring (30:60:30 basal + 30 N top-dress = 60:60:30 kg/ha). PJTSAU's own site remained unreachable, consistent with the prior verification notes.

---

## 1. Verified fertilizer doses (per crop)

All rows **normalized to PER ACRE** (÷2.47), with the original source figure kept. Nutrient basis = **N : P2O5 : K2O** (elemental N / oxide P / oxide K), **NOT** urea/DAP/MOP bag weights.

| Crop (Telangana, Kharif) | N /acre | P2O5 /acre | K2O /acre | Original (as source states) | Confidence | needs_verification | Source |
|---|---|---|---|---|---|---|---|
| **Paddy (rice)** — irrigated/transplanted | **48.6** | **24.3** | **16.2** | 120 : 60 : 40 **kg/ha** | **high** | **false** | PJTSAU IRR Rajendranagar + PJTSAU J. Research vol.50 |
| **Cotton** — Bt/hybrid | **48** | **24** | **24** | 48 : 24 : 24 **kg/acre** (≈120:60:60 kg/ha) | medium | **true** | ANGRAU/PJTSAU-lineage POP (kg/acre table) + Sreenivas et al. 2020 |
| **Maize** — hybrid, irrigated | **101.2** | **30.4** | **30.4** | 250 : 75 : 75 **kg/ha** | **low** | **true** | TNAU CPG Maize p.129 (SAU cross-check only) |
| **Red gram (kandi)** — rainfed | **8.1** | **20.2** | **8.1** ⚠ | 20 : 50 : 20 **kg/ha** | medium | **true** | ZREAC/RARS 2015 + ICAR Kharif Advisory 2025 |
| **Chilli (mirchi)** — irrigated, open-pollinated | **24.3** | **24.3** | **12.1** | 60 : 60 : 30 **kg/ha** | **low** | **true** | TNAU Chilli Manuring (cross-check; not PJTSAU) |
| Chilli — hybrid (for reference) | 24.3 | 32.4 | 32.4 | 60 : 80 : 80 **kg/ha** | low | **true** | TNAU Chilli Manuring |

### Split timing (apply exactly as stated)

- **Paddy (120:60:40 kg/ha):** Full P2O5 (60) + full K2O (40) as **BASAL** at final puddling/before transplanting, mixed into soil. N (120) in **three equal splits ~40 kg/ha each**: (1) basal at transplanting, (2) active tillering ~25–30 DAT, (3) panicle initiation ~55–60 DAT. Do **not** top-dress P/complex after ~15 days. Light soils: split K2O half basal + half at panicle initiation. **Rabi is different/higher (150:60:40) — do not reuse. AP/ANGRAU kharif is 80:60:40 — do NOT apply in Telangana.** PJTSAU also lists Zinc Sulphate 50 kg/ha.
  - Source: https://www.agronomyjournals.com/archives/2024/vol7issue12/PartB/7-12-19-273.pdf ; https://www.pjtau.edu.in/files/publications/2023/Journal-of-Research-PJTSAU-50-4.pdf
- **Cotton (48:24:24 kg/acre):** Full P2O5 **BASAL** at sowing. N and K2O in **3 equal splits at 30, 60, 90 DAS**, placed 7–10 cm from the plant. (A 2-split N schedule at 30/60 DAS is for American varieties under Rayalaseema conditions — not the default here.)
  - Source: https://tnaucottondatabase.wordpress.com/wp-content/uploads/2012/03/ap.pdf ; https://www.chemijournal.com/archives/2020/vol8issue3/PartI/8-3-16-730.pdf
- **Maize (250:75:75 kg/ha, hybrid):** **¼ of N + full P2O5 + full K2O basally before sowing** (verbatim from TNAU CPG p.129). Remaining N top-dressed N-only: ~½ total N at knee-high (~25 DAS), last ¼ at ~45 DAS (standard TNAU schedule; exact days not independently re-verified). ICAR-IIMR uses a different scheme (10% N basal + N in ~4 splits) at its lower 200:60:60 total.
  - Source: https://tnagriculture.in/dashboard/CPG/02_%20Maize.pdf
- **Red gram (20:50:20 kg/ha):** Entire dose as **BASAL by placement at sowing** — no top-dressing in kharif. Rhizobium + PSB seed treatment before sowing. P and K applied only where soil is deficient.
  - Source: https://www.rarstpt.org/files/rars/reports/Management%20practices%20for%20ZREAC%202015.pdf ; https://icar.org.in/sites/default/files/Circulars/ICAR-En-Kharif-Agro-Advisories-for-Farmers-2025.pdf
- **Chilli (60:60:30 kg/ha, open-pollinated):** Basal at last plough/transplanting = FYM 25 t/ha + **30:60:30** (all P, all K, half the N). Top-dress remaining **30 kg N/ha in equal splits at 30, 60, 90 DAP**. Apply K as K2SO4 (potassium sulphate) for fruit quality. Hybrid = FYM 30 t/ha + basal 30:80:80 + same 30 kg N top-dress → 60:80:80.
  - Source: https://agritech.tnau.ac.in/horticulture/horti_vegetables_chilli_Manuring.html

### Rows flagged `needs_verification = true` — render this farmer-facing fallback

> **మీ ఖచ్చితమైన మోతాదు మీ Soil Health Card ప్రకారం, స్థానిక వ్యవసాయ విస్తరణ అధికారి (AEO)/KVK తో నిర్ధారించుకోండి.**
> "Confirm the exact dose against your Soil Health Card and your local Agriculture Extension Officer (AEO)/KVK."

- **Cotton** — numbers agree across two official-lineage sources, but no live current standalone PJTSAU cotton POP page could be opened; dose depends on soil type (black vs red) and irrigated/rainfed status.
- **Maize** — TNAU 250:75:75 is a **valid SAU cross-check only**. A second official source (ICAR-IIMR) gives **lower 200:60:60 kg/ha**. Do **not** present 250:75:75 to farmers as *the* Telangana dose; the Telangana/ICAR N range is lower (~150–200 kg/ha). ⚠ **This is the least-trustworthy row — show the fallback prominently and consider hiding a hard number until a PJTSAU/KVK figure is obtained.**
- **Red gram** — N and P2O5 confirmed by a second official source; **K2O is unresolved** (KVK Palem 20 kg/ha vs ICAR/DPD 30 kg/ha vs ZREAC omits K). ⚠ Flag the K2O cell specifically.
- **Chilli** — `confirmed=false`. Only a **cross-check SAU (TNAU)** confirms 60:60:30; a second official SAU (Kerala AU) gives **75:40:25**, and AP/Telangana blog per-acre figures imply ~119:59:40 kg/ha (commercial, excluded). Sources materially disagree on N. Treat as indicative only.

---

## 2. Conversion formula — NPK (kg nutrient) → Urea / DAP / MOP bags

Recommendations are in **kg of NUTRIENT** (N, P2O5, K2O), not product. Convert with:

```
Fertilizer_qty (kg) = (100 / nutrient%) × nutrient_kg
bags = Fertilizer_qty / 50
```

**Nutrient grades (FCO standard, confirmed on TNAU nutrient-content table):**

| Fertilizer | Grade | Bag |
|---|---|---|
| Urea | **46% N** | 50 kg |
| DAP | **18% N + 46% P2O5** | 50 kg |
| MOP (muriate of potash / KCl) | **60% K2O** | 50 kg |

Source: https://agritech.tnau.ac.in/agriculture/agri_nutrientmgt_nutrientcontent.html

### CRITICAL sequencing (DAP carries N too — subtract it or you overdose N)

1. **MOP** for all K2O: `MOP = K2O × 100/60`
2. **DAP** for all P2O5: `DAP = P2O5 × 100/46`
3. **N already supplied by that DAP:** `N_from_DAP = DAP × 0.18`
4. **Remaining N via Urea:** `Urea = (N − N_from_DAP) × 100/46`

### Worked example A — per hectare (120:60:40 kg/ha, paddy)

- MOP = 40 × 100/60 = **66.7 kg** (1.33 bags)
- DAP = 60 × 100/46 = **130.4 kg** (2.61 bags)
- N from DAP = 130.4 × 0.18 = 23.5 kg
- Urea = (120 − 23.5) × 100/46 = **209.8 kg** (4.20 bags)
- **Per ha ≈ 2.6 bags DAP + 4.2 bags Urea + 1.3 bags MOP.**
- Sanity check: N delivered = 23.5 + 96.5 = 120 kg (exact). Ignoring DAP's N would give 260 kg urea and **overdose N by ~23.5 kg/ha**.

### Worked example B — per acre (the number the calculator shows) — paddy 48.6:24.3:16.2 kg/acre

- MOP = 16.2 × 100/60 = **27.0 kg** (0.54 bag)
- DAP = 24.3 × 100/46 = **52.8 kg** (1.06 bag)
- N from DAP = 52.8 × 0.18 = 9.5 kg
- Urea = (48.6 − 9.5) × 100/46 = **85.0 kg** (1.70 bag)
- **Per acre ≈ 1.06 bag DAP + 1.70 bag Urea + 0.54 bag MOP.** (= per-ha result ÷ 2.47 ✓)

Implementation notes for `agronomy.ts`: keep the exact grade constants (`UREA_N=0.46`, `DAP_N=0.18`, `DAP_P=0.46`, `MOP_K=0.60`, `BAG_KG=50`, `HA_PER_ACRE=1/2.47`). Compute in the order above. If soil test shows P or K already high, the corresponding nutrient (and its fertilizer) should be reduced/skipped — expose that as an input.

---

## 3. IPM thresholds table

Doses are by **active ingredient** (CIB&RC-registered); never brand. Threshold = ETL (economic threshold level). Where the official page has no ETL, the row is flagged.

| Crop | Pest | Threshold (ETL) | Action (active ingredient + CIB&RC/official dose, or consult AEO) | needs_verification | Source |
|---|---|---|---|---|---|
| **Paddy** | Brown planthopper (*Nilaparvata lugens*) | 1 hopper/tiller if no predatory spider; 2 hoppers/tiller if spider present at 1/hill. Scout from max tillering at plant base above water. | Avoid early broad-spectrum pyrethroids (cause resurgence). Neem oil 3% / Azadirachtin 0.03% first. If ETL crossed, spray to plant base: **Imidacloprid 17.8% SL 40–50 ml/acre**, or **Pymetrozine 50% WG 120 g/acre**, or **Buprofezin 25% SC 320 ml/acre**, or **Flonicamid 50% WG 60 g/acre**. | **false** | https://agritech.tnau.ac.in/crop_protection/rice/crop_prot_crop_insectpest%20_cereals_paddy_12.html |
| **Cotton** | Pink bollworm (*Pectinophora gossypiella*) | 8 moths/pheromone trap/night for 3 consecutive nights, OR 10% rosette flowers, OR 10% green-boll damage (~2 of 20 bolls). Monitor 90/105/120/135/150 DAS; 5 traps/acre from 45 DAS. | Non-chemical first: destroy rosette flowers (not on bund); release *Trichogrammatoidea bactrae* ~20,000/ha every 10 days; Azadirachtin 1500 ppm. Only if ETL crossed: **Thiodicarb 75% WP** or **Chlorantraniliprole 18.5% SC** — CIB&RC label dose/acre, **confirm with AEO**. | **true** | https://niphm.gov.in/IPMPackages/Cotton.pdf |
| **Maize** | Fall armyworm (*Spodoptera frugiperda*) | ICAR-IIMR: act at ~5% (5–10%) whorl/foliar damage at seedling→mid-whorl; scout weekly 'W' pattern (20 plants). **Chemical control not advised past mid-whorl / at tasseling-cob stage.** | Hand-pick egg masses; dry sand+lime or NSKE into whorl. If ETL crossed at early whorl: **Spinetoram 11.7% SC**, **Emamectin benzoate 5% SG**, or **Chlorantraniliprole 18.5% SC** applied **into the whorl** — **confirm exact label dose with AEO** (exact ml/g not verifiable from an official page this pass). | **true** | https://agriculture.vikaspedia.in/viewcontent/agriculture/crop-production/integrated-pest-managment/ipm-for-cerels/identification-and-management-of-fall-armyworm |
| **Red gram** | Gram pod borer (*Helicoverpa armigera*) | Pheromone trap 10 moths/trap/day (4–5 traps/acre, lure every 2–3 wk). At 25–50% flowering: 2 eggs/larvae per plant, or ~1 larva/2 plants / 3% pod damage. Bird perches ~8/acre. | Non-chemical: bird perches, HaNPV, NSKE. If ETL crossed: **Chlorantraniliprole 18.5% SC (~30 g a.i./ha)**, or Indoxacarb/Spinosad, or **Acetamiprid 20% SP (~20 g a.i./ha)** — **confirm exact CIB&RC per-acre dose with AEO**. | **true** | https://niphm.gov.in/IPMPackages/Redgram.pdf |
| **Chilli** | Thrips (*Scirtothrips dorsalis*) | ⚠ ETL **not on the official TNAU page**; commonly cited ~6 thrips/leaf or 10% affected plants (range 2–6/leaf). **Treat as UNCONFIRMED — confirm with AEO/PJTSAU.** | TNAU-listed registered actives: **Fipronil 5% SC 1.5 ml/L**, **Spinosad 45% SC 3.2 ml/10 L**, **Imidacloprid 17.8% SL 3.0 ml/10 L**, **Emamectin benzoate 5% SG 4 g/10 L**. Thrips + mites spread leaf-curl virus — scout early. | **true** | https://agritech.tnau.ac.in/crop_protection/crop_prot_crop_insect-veg_chillies_pest&disease.html |
| **Chilli** | Yellow mite (*Polyphagotarsonemus latus*) | ⚠ ETL **not on the official page**; commonly cited ~5–10 mites/leaf. **Treat as UNCONFIRMED — confirm with AEO/PJTSAU.** | TNAU-listed: **Buprofezin 25% SC 8.0 ml/10 L**, **Chlorfenapyr 10% SC 1.5 ml/L**; wettable sulphur also used. **Confirm exact CIB&RC label dose with AEO.** | **true** | https://agritech.tnau.ac.in/crop_protection/crop_prot_crop_insect-veg_chillies_pest&disease.html |

Note: TNAU spray doses above are per-acre or per-10-litre exactly as the source states. For any `needs_verification=true` row the app must **not** present a spray as a one-tap recommendation — surface the ETL/scouting step and the AEO-confirmation fallback first.

---

## 4. Honesty notes (what to render as "confirm with Soil Health Card / AEO")

**Always render the AEO/Soil Health Card fallback for:**
- Every fertilizer row with `needs_verification=true`: **Cotton, Maize, Red gram (esp. its K2O cell), Chilli**. Maize and Chilli are the weakest — either show the number with a strong caveat or gate it behind "this is a general SAU figure, confirm locally."
- Every IPM row with `needs_verification=true`: **Cotton PBW, Maize FAW, Red gram pod borer, Chilli thrips, Chilli mite** — and specifically the two chilli ETLs which are not on any official page.
- Any case where the user's Soil Health Card shows P or K already sufficient — then that nutrient should be cut, so the generic dose is wrong by design.

**Calculator disclaimer (show on every result screen; Telugu + English):**

> ఈ మోతాదులు PJTSAU/ICAR సాధారణ సిఫార్సులు (Kharif, తెలంగాణ). మీ నేల పరీక్ష (Soil Health Card), నేల రకం, నీటి వసతిని బట్టి అసలు అవసరం మారుతుంది. చివరి నిర్ణయానికి మీ Soil Health Card మరియు స్థానిక వ్యవసాయ విస్తరణ అధికారి (AEO)/KVK ను సంప్రదించండి.
>
> "These doses are **general PJTSAU/ICAR norms for Telangana Kharif**. Your actual need depends on your **soil test (Soil Health Card)**, soil type and irrigation. For the final decision, confirm with your Soil Health Card and local **Agriculture Extension Officer (AEO)/KVK**."

**Pesticide-specific line (show on the pest guide):**

> "We show the **legally registered active ingredient**, not any brand. Try non-chemical/IPM steps first and only spray after the pest crosses the threshold (ETL). **Read the product label and confirm the exact dose and pre-harvest interval with your AEO.** Rythu sells you nothing."

**Data-integrity rules baked into the design (why this is trustworthy):**
- Numbers reported in the **exact source units** (kg/ha vs kg/acre) and normalized with the fixed factor **1 ha = 2.47 acre**; both figures stored so nothing is silently rounded away.
- **No company/brand recommendations** anywhere — university/ICAR/CIB&RC only.
- Where a second official source disagreed (maize N, chilli N, red gram K2O), we did **not** average or invent — we flagged it and pushed the farmer to the Soil Health Card/AEO.
- The AP/ANGRAU-vs-Telangana state difference (paddy 80:60:40 vs 120:60:40) is documented so the wrong-state figure is never applied in Bhupalpally.