# Rythu — Schemes Research & Gap Report (2026-07-14)

_Auto-generated via a verified multi-agent research workflow (central + Telangana schemes, competitor apps). Currency window 2024–mid-2026._

I have everything I need. The current app lists 5 schemes with keys `pm_kisan`, `rythu_bharosa`, `pmfby`, `soil_health`, `kcc`, and I can already see two accuracy problems in it (Rythu Bharosa points to the generic `telangana.gov.in`, not the live scheme portal; the `Scheme` interface carries no status/level/priority fields). Here is the synthesis report.

---

# Rythu /schemes — Comprehensive, Current & Honest Scheme Audit
**Scope:** Central + Telangana schemes for the Jayashankar Bhupalpally pilot · **Verification window:** 2024–mid-2026 sources · **Governing rule:** honesty wedge — no hard-coded rupee figure unless an official/PIB source confirms the *current* number; everything else says "verify on the official portal."

> **Political context that changes everything below:** Telangana had a government change in Dec 2023 (Congress). The BRS-era **Rythu Bandhu is retired as a name** — the live investment-support scheme is **Rythu Bharosa** (relaunched 26 Jan 2025). Land verification moved from **Dharani → Bhu Bharathi** (2025). The app must never present "Rythu Bandhu" as current.

---

## 1. Verified scheme catalogue

Priority = value to the Bhupalpally pilot (5 = surface first). "Verify" in the Benefit column is deliberate — the honest framing farmers should see.

### Central schemes

| Scheme (en / te) | Status | Who's eligible | Benefit (honest framing) | How to apply | Official URL | Pri |
|---|---|---|---|---|---|---|
| **PM-KISAN** / పీఎం-కిసాన్ | Active | Small/marginal landholding families in land records; standard exclusions (IT payers, govt staff). **Tenant/landless & ROFR-only often excluded** (tied to land title). | **Rs 6,000/yr = 3 × Rs 2,000** (CONFIRMED). Cadence: 21st 19 Nov 2025 → 22nd 13 Mar 2026 → 23rd 20 Jun 2026; 24th ≈ Oct/Nov 2026. **e-KYC + Aadhaar-bank seeding mandatory** or payment is withheld. | pmkisan.gov.in → Farmers Corner, or CSC/AEO. Check own status via "Know Your Status" + OTP. Helpline 155261. | https://pmkisan.gov.in | 5 |
| **PMFBY — Crop Insurance** / పంట బీమా | Active-**but-verify-locally** | Farmers (incl. tenants/sharecroppers with insurable interest) growing **notified crops in notified areas** that season. | Statutory farmer share cap 2% Kharif / 1.5% Rabi / 5% commercial. **Telangana is contested** — some 2024 sources say the *state* bears the farmer share (effectively free), others say the farmer pays. **Do not tell a farmer "you're covered"** — confirm the current-season district notification with the AEO. Sum insured is crop/area-specific — never hard-code. | Enrol before cut-off (≈31 Jul Kharif / Rabi date varies — Rabi 2024-25 was 15 Jan 2025) via bank/CSC/pmfby.gov.in "Guest Farmer". | https://pmfby.gov.in | 5 |
| **Kisan Credit Card (KCC + MISS)** / కిసాన్ క్రెడిట్ కార్డు | Active | Farmers, **tenant farmers, sharecroppers, oral lessees**; also allied (dairy/fisheries). *In practice TG tenants need a Loan Eligibility Card, rarely issued.* | Effective **≈4%** on timely repayment (7% − 3% prompt-repayment). **Collateral-free up to Rs 2 lakh** (from Rs 1.6 lakh, 1 Jan 2025; Parliament 28 Jul 2025 confirmed *no* further rise). The **Rs 5 lakh** figure (Budget 2025-26) is the **MISS interest-subvention limit, NOT the collateral-free cap** — do not conflate. Confirm the ceiling your bank applies. | Any bank branch; JanSamarth portal; simplified 1-page form for PM-KISAN beneficiaries. KCC must be Aadhaar-linked for MISS. | https://www.myscheme.gov.in/schemes/kcc | 5 |
| **Soil Health Card** / భూసార కార్డు | Active | Any farmer via a soil sample (taken after harvest, ~twice/yr). | **Free advisory, no cash.** 12 parameters (N,P,K,S,Zn,Fe,Cu,Mn,B,pH,EC,OC) + crop-wise fertiliser advice → cuts input cost. | Sample via AEO/KVK/lab; download on portal or SHC app. | https://www.soilhealth.dac.gov.in | 4 |
| **PMKSY – Per Drop More Crop** (drip/sprinkler) / సూక్ష్మ నీటిపారుదల | Active | Land-owning/lessee farmers; priority small/marginal + horticulture. | State-set subsidy (often higher for small/marginal). **% and cost ceilings vary by state/crop — verify the current Telangana figure; do NOT quote a national %.** DBT after installation. | TG agri/horticulture dept or KVK; empanelled-vendor quote → farm verification. | https://pmksy.gov.in | 4 |
| **PM-KMY — farmer pension** / రైతు పింఛను | Active (voluntary, LIC) | Small/marginal farmers **aged 18–40**, ≤2 ha, not in NPS/ESIC/EPFO, not IT payers. Enrolment closes at 40. | **Rs 3,000/month from age 60** (spouse 50% = Rs 1,500). Contribution Rs 55–200/mo by entry age, govt-matched. Verify slabs on portal. | CSC or portal with Aadhaar + auto-debit mandate. **Use pmkmy.gov.in — NOT maandhan.in (different scheme).** Helpline 1800-3000-3468. | https://pmkmy.gov.in (or myScheme /pmkmdy) | 3 |
| **SMAM — Farm Mechanization** / వ్యవసాయ యంత్రీకరణ | Active | Individual farmers (esp. small/marginal, women, SC/ST), SHGs, FPOs, co-ops; entrepreneurs for CHCs. | **~50% (SC/ST, small/marginal, women), ~40% others** on eligible machines (2025 guidelines, incl. drones). CHC/Farm-Machinery-Bank support capped — verify per machine. Periodic application windows. | Online (free) via TG agri portal linked to agrimachinery.nic.in; DBT after verification. | https://agrimachinery.nic.in | 3 |
| **e-NAM — National Agri Market** / ఈ-నామ్ | Active | Any farmer registered against a linked APMC. Telangana has 50+ integrated mandis. | **No fee.** Benefit = fairer price + direct bank payment, less middleman dependence. **No cash grant.** *Confirm a Warangal/Bhupalpally-belt mandi is integrated — not confirmed for Bhupalpally itself.* | enam.gov.in or e-NAM app → "Farmer" + APMC approval. **URL note: expired SSL cert — browsers warn; re-check before deep-linking.** | https://enam.gov.in | 3 |
| **PM-KUSUM — solar pumps** / సౌర పంపుసెట్లు | Active (in transition) | Individual farmers, groups, FPOs, co-ops, panchayats (component-dependent). | Standalone pump ~30% central + ~30% state + ~40% farmer (part loan-financeable) **for TG — but split/benchmark cost is shifting as projects fold into PM-KUSUM 2.0 (guidelines pending). Verify current terms; do not hard-code.** | **Telangana state portal (TGREDCO) — more actionable** than national. ⚠️ No registration fee — "Kusum ID/application fee" sites are scams (helpline 1800-180-3333). | https://pmkusum.telangana.gov.in/ | 3 |
| **Agriculture Infrastructure Fund (AIF)** / వ్యవసాయ మౌలిక నిధి | Active | Farmers via FPOs/PACS/SHGs + agri-entrepreneurs with a DPR. **Better for groups than a lone small farmer.** | A **subsidised LOAN, not a grant**: 3%/yr interest subvention on loans ≤Rs 2 cr for 7 yrs + govt-paid CGTMSE fee. No capital subsidy. *Portal returned HTTP 403 to bots — treat as likely-live, manual re-check.* | Register (mobile+Aadhaar OTP) → DPR → lending bank → PMU verifies. | https://agriinfra.dac.gov.in | 2 |
| **PM Dhan-Dhaanya Krishi Yojana (PMDDKY)** / ధన్-ధాన్య కృషి యోజన | Active (launched 11 Oct 2025) | Farmers in the **100 selected low-productivity districts** (6-yr run to 2030-31). | ~Rs 24,000 cr/yr via *existing* schemes — **no individual cash transfer**; benefit is better local infra/services. **TG got 4 districts — VERIFY whether Bhupalpally is one (names unconfirmed) before surfacing.** | No separate application — flows through converged schemes/District Agri Development Plan. Ask the district agri office. | https://agriwelfare.gov.in (district list) | 2 |
| **Namo Drone Didi** / నమో డ్రోన్ దీదీ | Active but **ending / behind** | **Women SHGs only** (DAY-NRLM), District-Committee shortlisted. | **80% CFA up to Rs 8 lakh** on the drone package + AIF loan for balance; ~Rs 1 lakh/yr extra SHG income. **⚠️ Sanctioned period 2023-24→2025-26 (ending now); only ~500 drones delivered by Mar 2026 — check for an extension before promising enrolment.** | SHGs identified by District Committees via Panchayat/Block office; ask nearest PM Kisan Samriddhi Kendra. | https://lakhpatididi.gov.in/power_to_empower/namo-drone-didi/ | 2 |

### Telangana state schemes

| Scheme (en / te) | Status | Who's eligible | Benefit (honest framing) | How to apply | Official URL | Pri |
|---|---|---|---|---|---|---|
| **Rythu Bharosa** / రైతు భరోసా — *renamed from Rythu Bandhu* | **Active** (relaunched 26 Jan 2025) | Owners of **actively cultivable** land in **Bhu Bharathi**, Aadhaar-bank linked. **⚠️ Tenant-farmer status conflicts across sources** (see honesty flag below). Non-cultivable/fallow/real-estate excluded. Landless → Indiramma Atmiya Bharosa. | Reported **Rs 12,000/acre/yr (Rs 6,000 Kharif + Rs 6,000 Rabi)**, up from Rs 10,000; **BUT paid on a phased "first-acre priority" model, not a flat lump sum**, and acreage caps/timing shift each season. The official portal does **not** publish a per-acre figure — link it and say "verify current amount/order/cap." | Auto via land records; verify at portal (Aadhaar/pattadar passbook) or the AEO/Rythu Vedika. | https://rythubharosa.telangana.gov.in/ | 5 |
| **Rythu Bima — group LIFE insurance** / రైతు బీమా | Active (renewed 2025-26) | Enrolled farmers **18–59**, land in Bhu Bharathi/CCLA, one policy/family. *Tenant/leased-land not covered.* | **Rs 5 lakh** to the nominee on the farmer's death (any cause), paid ~10 days by RTGS; state pays the full premium to LIC. (Older Rs 2 lakh pages are stale.) **Do NOT quote a per-farmer premium — sources conflict.** | Enrol/nominee via AEO; nominee need not visit an office. **⚠️ Old state URL `rythubandhu.telangana.gov.in/Default_LIC1.aspx` is DEAD (DNS fail) — route via myScheme + AEO.** | https://www.myscheme.gov.in/schemes/rythu-bima | 5 |
| **Free 24×7 Agricultural Power** / ఉచిత వ్యవసాయ విద్యుత్ | **Active** (reaffirmed 31 May 2026) | Farmers with ag power connections/pumpsets. | **Free, round-the-clock power for ag pumpsets — no cash, no per-unit charge.** CM reaffirmed 24×7 free power continues and denied smart meters on ag pumps; "Rythu Discom" proposed. | Automatic for existing connections; new connection via local DISCOM (**TGSPDCL** for Bhupalpally) / Mee-Seva. | https://www.telangana.gov.in/departments/energy/ | 5 |
| **Indiramma Atmiya Bharosa** / ఇందిరమ్మ ఆత్మీయ భరోసా | Active (launched 26 Jan 2025) | **Landless agri labourers / tenant cultivators** NOT getting Rythu Bharosa; **≥20 days MGNREGS work** in the qualifying year (job-card based); one member/family. | **Rs 12,000/yr (2 × Rs 6,000) DBT.** **State the 20-day MGNREGS condition plainly — it disqualifies many genuine tenant farmers; do not imply universal tenant coverage.** 2026 window closed 25 Mar 2026. | Beneficiaries from MGNREGS data; enrol/verify via rythubharosa portal / Rythu Vedika / CSC. Watch for next window. | https://rythubharosa.telangana.gov.in/ | 4 |
| **Subsidised Seed (incl. green-manure)** / సబ్సిడీ విత్తనాలు | Active (Vanakalam 2026 procurement started) | District farmers with **pattadar passbook + Aadhaar**; ~1 acre/farmer/crop, season-specific. | Subsidy varies by seed/district (e.g., Dhaincha green-manure ~60–65% in some districts). **Rates & offered seeds change every season — verify current list/rate on T-SEED or with the AEO.** | Mandal Sale Point → OSSDS/T-SEED shows eligibility + issues a permit slip. | https://ossds.telangana.gov.in/ | 3 |
| **Paddy Fine-Rice Bonus (Rs 500/qtl)** / సన్న ధాన్యం బోనస్ | **At-risk / uncertain** | Farmers growing one of **7 approved fine varieties** (BPT-5204, RNR-15048, HMT Sona, Jai Shriram, KNM-1638, WGL-44, KNM-7715) selling at a Procurement Centre. | **Rs 500/quintal above MSP — but govt is actively weighing dropping it for Rabi/Yasangi** (Centre advisory on surplus stocks), and past payments were delayed. **Verify it's still running + which varieties each season.** High value for paddy-heavy Bhupalpally. | Sell approved fine paddy at a Civil Supplies Paddy Procurement Centre (PPC). | https://www.civilsupplies.telangana.gov.in/ | 3 |
| **Podu Land Pattas (ROFR/FRA)** / పోడు భూమి పట్టాలు | **Uncertain — no new round** | ST + eligible traditional forest-dweller cultivators farming forest (podu) land under FRA/ROFR. | **A land title (no cash)** — which then unlocks Rythu Bharosa etc. First big round was 2023 (BRS). **~7.14 lakh acres of claims still pending; officials call ROFR one-time and resist a fresh round; Congress is reviewing BRS-era pattas. No new 2026 round announced — surface as "no confirmed new round; check with ITDA/Tribal Welfare."** Highly relevant to Bhupalpally's tribal fringe. | Gram Sabha claim → Tribal Welfare/Forest (ITDA). *Portal liveness reconfirm on-ground.* | https://tribal.telangana.gov.in/ | 3 |
| **Rythu Vedika (farmer hubs)** / రైతు వేదిక | Active (~2,601 built) | All farmers in the AEO cluster (~1 per 5,000 acres). | **Not a cash scheme — the physical access point** for Rythu Bharosa/Bima enrolment, mechanization, seed subsidy, advice. Best used as the app's "how to apply / where to go" anchor. | Visit your cluster's Rythu Vedika (AEO office). | https://kisan.telangana.gov.in/ | 3 |
| **Farm Mechanization Subsidy (state relaunch)** / యంత్రీకరణ సబ్సిడీ | **Relaunching — verify launch** | TG farmers ≥~1 acre; priority SC/ST/BC. Recent availers barred a few years. | **40–50% subsidy** on machinery by DBT. Minister announced a **Jan 2026 CM relaunch (1 lakh+ farmers)**; Jan 2026 reports say it's "back on track" but the 2026 machine list/guidelines were still being finalised — **confirm it has actually launched.** | Details via AEO/MAO → Mee-Seva → DD/NEFT payment. | https://mgov.telangana.gov.in/FarmMechGuide.html | 3 |
| **Crop Loan Waiver (Rythu Runa Mafi 2024)** / రైతు రుణమాఫీ | **CLOSED / one-time (historical)** | Families with short-term crop loans (≈12 Dec 2018–9 Dec 2023), ration-card keyed. Long-term loans excluded. | **Up to Rs 2 lakh/family, completed ~15 Aug 2024 (~Rs 31,000 cr).** **NOT a claimable benefit — new loans after the cut-off aren't covered.** Surface only as "check if your account was credited." | Was auto-applied to loan accounts; residual grievance/status only via portal/bank. | https://clw.telangana.gov.in/ | 2 |
| **Fisheries Support** / మత్స్య మద్దతు | Active | Registered fishermen / fisheries co-op members (licensees) on state water bodies. | **100% grant** fish/prawn seed stocking (IFDS); fishing-ban Saving-cum-Relief (fisher saves Rs 1,500/9 mo, govt adds Rs 3,000 → Rs 4,500 + interest); Group Accident cover. Verify amounts with District Fisheries Officer. *Portal geo-restricted from research env — reconfirm on-ground.* | Via District Fisheries Officer / co-op societies. | https://fisheries.telangana.gov.in/ | 2 |
| **Sheep Distribution (20+1 unit)** / గొర్రెల పంపిణీ | **SUSPENDED / not open** | Traditional shepherd (Golla/Kuruma) families via co-ops. | Historically **75% subsidy** on the 21-sheep unit. **⚠️ Phase 2 suspended for lack of funds and under ACB corruption probe (arrests); no Phase 3 confirmed. Do NOT present as claimable** — at most "not currently open — check with Animal Husbandry Dept." | Historically via Animal Husbandry Dept / co-ops — not open now. | https://www.telangana.gov.in/departments/animal-husbandry-and-fisheries/ | 1 |

**Renamed / replaced — the current truth:**
- **Rythu Bandhu → Rythu Bharosa.** Rythu Bandhu is defunct *as a name*; the live scheme is Rythu Bharosa (since 26 Jan 2025). **Exception:** the *Rythu Bima* LIC pages historically lived on the old `rythubandhu.telangana.gov.in` domain — but that host **no longer resolves (dead)**, so use the myScheme Rythu Bima page + AEO, not the old domain.
- **Dharani → Bhu Bharathi** is the land-record system now backing Rythu Bharosa/Bima eligibility.

**Three conflicts flagged honestly (do not paper over):**
1. **Rythu Bharosa & tenant farmers** — one verified pass says tenants with a *registered lease deed* now qualify; another says tenants are excluded in practice and routed to Indiramma Atmiya Bharosa. **App should say: registered-lease tenants *may* qualify, but tenants are widely excluded in practice — verify with your AEO; if excluded, apply for Indiramma Atmiya Bharosa.**
2. **PMFBY premium in Telangana** — contested whether the state pays the farmer's 2%/1.5% share or the farmer does. Say "verify the current-season notification," never "you are covered."
3. **KCC Rs 5 lakh** — that is the *interest-subvention* limit, not the collateral-free limit (Rs 2 lakh).

---

## 2. Gaps in Rythu's /schemes (currently only 5)

**Currently in the app, and INACCURATE / needs fixing:**
- **Rythu Bharosa card links to the generic `https://www.telangana.gov.in`** (`lib/schemes.ts` line 42). Replace with the live scheme portal **`https://rythubharosa.telangana.gov.in/`**. Also the copy says flat "per-acre support" — add the honest **"first-acre priority, phased; verify current amount"** note.
- **KCC** copy is fine, but if amounts are ever added, encode the **Rs 2 lakh collateral-free vs Rs 5 lakh MISS** distinction correctly.
- **Soil Health** URL `soilhealth.dac.gov.in` is OK (findings use the `www.` variant — either resolves).
- The **`Scheme` interface has no `status`, `level`, or `priority` field** — so the app cannot mark a scheme "closed/at-risk/verify-locally." This is the structural gap blocking honest content (see §5).

**MISSING — ranked by pilot value (add in this order):**

| Rank | Scheme to add | Why it matters for Bhupalpally |
|---|---|---|
| 1 | **Rythu Bima** (life insurance) | Rs 5 lakh cover, free, ~48 lakh farmers — a headline state scheme farmers know by name; conspicuously absent. |
| 2 | **Free 24×7 Ag Power** | Universally relevant, currently reaffirmed, zero-cost benefit; high-trust content. |
| 3 | **Indiramma Atmiya Bharosa** | The honest answer for the many Bhupalpally **tenant/landless** farmers who ask why they don't get Rythu Bharosa. |
| 4 | **Paddy Fine-Rice Bonus** | Bhupalpally is paddy-heavy; high-value **but at-risk** — perfect showcase for the honesty wedge. |
| 5 | **Subsidised Seed (T-SEED)** | Concrete, seasonal, low-literacy-friendly ("go to mandal sale point with passbook + Aadhaar"). |
| 6 | **PM-KMY pension** | Genuinely overlooked by small farmers; easy eligibility explainer. |
| 7 | **PMKSY Per-Drop-More-Crop + PM-KUSUM (state portal)** | Water/energy cost — big for irrigation-dependent farmers; frame subsidy as "verify." |
| 8 | **SMAM / state mechanization** | Rent-not-buy (CHCs) resonates with small farmers; note the pending 2026 state relaunch. |
| 9 | **e-NAM + Rythu Vedika** | e-NAM backs the mandi-price feature; Rythu Vedika is the universal "where to go" anchor. |
| 10 | **Podu/ROFR pattas** | Very high relevance to Bhupalpally's tribal/forest-fringe farmers — surface with "no confirmed new round." |
| 11 | **Crop Loan Waiver (historical)**, **Sheep Distribution (suspended)**, **Namo Drone Didi (women SHGs, ending)**, **PMDDKY (verify district)**, **AIF**, **Fisheries** | Include as honesty/awareness entries with clear "closed / suspended / verify" badges so farmers who know the name aren't left guessing. |

---

## 3. Competitor landscape & where Rythu wins

**How the market monetizes (the wedge):** Every major *farmer-facing* app that scaled did it by **selling inputs**, so advice is structurally biased toward products:
- **Plantix** (AI crop-doctor, Telugu-supported) — acquired by chemicals marketer **Helm AG (2023)**; its "Plantix Partner" arm buys inputs in bulk from Dow/BASF/Syngenta/Bayer and its B2B API markets **"3–5× higher product conversion."** The "reduce pesticides" pitch is contradicted by the business model.
- **BharatAgri, AgroStar (raised $30M Nov 2025), DeHaat, AgriApp, IFFCO Kisan** — advisory is the hook for an **input marketplace / margin / agri-loan** engine. None has a real government-scheme eligibility module; most assume literacy + online payment and aren't offline-first or Telugu-voice-first.

**Government/neutral apps (Rythu's real reference points, not input-sellers):**
- **Kisan e-Mitra** (Wadhwani AI + NIC) — voice AI chatbot, **Telugu + Bhashini**, now covers PM-KISAN + PMFBY + KCC. **But central-schemes only — no Telangana state schemes.** This is Rythu's single closest analog and its clearest opening.
- **Kisan Suvidha** (govt omnibus, 9 languages incl. Telugu) — has a schemes section but flat/pan-India, no personalized eligibility, weak TG-state coverage.
- **Meghdoot** (IMD/ICRISAT) — **Telugu weather advisories CONFIRMED.** The gold-standard neutral weather source Rythu should **link/integrate, not compete with.**
- **T App Folio / Farmer Registry TL / Dharani-Bhu Bharathi** — the official rails; bureaucratic UX. Rythu should sit **on top** of these as a friendly Telugu front-end.
- **Telangana Fertilizer Booking App** (NIC, 2025) — "India's first"; **1 lakh downloads in 2 days → ~12.73 lakh farmers / 50.48 lakh bags by Feb 2026.** Proof that **Telangana farmers WILL install a focused state app** — validates Rythu's thesis.

**Where Rythu wins (defensible openings):**
1. **Commission-free / "we sell you nothing"** — structurally credible vs every input-seller above.
2. **Both central AND Telangana state schemes** with **personalized eligibility** — no competitor does state schemes well; Kisan e-Mitra explicitly doesn't.
3. **Telugu-first, voice-first, low-literacy, offline-tolerant** for the Bhupalpally profile.
4. **The honesty wedge** — validated by the fact that the official Rythu Bharosa portal itself publishes *no* per-acre figure; Rythu linking the portal instead of asserting a number is both safer and more trustworthy.

**Features Rythu lacks that farmers demonstrably value (borrow, don't rebuild):**
- **Photo crop-diagnosis** (Plantix's draw) — high demand, but keep it rule/advisory-grounded to protect the honesty wedge.
- **Weather agro-advisory** — link **Meghdoot** (Telugu-confirmed) rather than build.
- **Mandi prices** — back with **e-NAM** as the cited source.
- **Voice Q&A** — Kisan e-Mitra proves Telugu voice works; Rythu's differentiator is grounding it in *state* schemes.

---

## 4. Honesty & eligibility watch-outs (Bhupalpally focus)

These are where farmers most often *think* they qualify but don't — surface them explicitly:

- **Tenant farmers (huge in Bhupalpally):**
  - **Rythu Bharosa** is tied to land ownership in Bhu Bharathi; tenants are **widely excluded in practice** (registered-lease eligibility is claimed by one source but contested). Don't imply coverage.
  - **Rythu Bima** and **PM-KISAN** are **also owner-tied** — tenants routinely miss both.
  - **KCC** *legally* covers tenants/oral lessees, but in Telangana this needs a **Loan Eligibility Card (LEC) that is largely not issued** — say so.
  - **The honest route for tenants/landless = Indiramma Atmiya Bharosa**, but only with **≥20 days of MGNREGS work** in the qualifying year — state that condition plainly; it disqualifies many genuine tenant farmers.

- **Podu / forest-land (ROFR) farmers (tribal/forest-fringe Bhupalpally):**
  - Without a **patta**, they're excluded from Rythu Bharosa, PM-KISAN, Rythu Bima (all land-record-gated).
  - **No new ROFR round is confirmed;** ~7.14 lakh acres of claims are pending and existing pattas are under review. Say **"no confirmed new round — check with ITDA / Tribal Welfare,"** not "apply now."

- **PM-KISAN silent drop-off:** many stop receiving instalments because **e-KYC / Aadhaar-bank seeding lapsed.** Surface a "check your status + complete e-KYC" nudge — this is a common, fixable Bhupalpally failure.

- **PMFBY:** never say "you're covered." Coverage is crop/area-notified each season and who pays the premium in TG is contested — point to the **current district notification / AEO**.

- **Closed or suspended, but still asked about:**
  - **Crop Loan Waiver 2024** — closed one-time; only "check if you were credited."
  - **Sheep Distribution** — suspended, under ACB probe; not claimable.
  - **Paddy fine-rice bonus** — may be dropped for Rabi; "verify it's running this season."
  - **Namo Drone Didi** — women SHGs only, sanctioned period ending; check for extension.

- **Never hard-code rupees for state-set / in-flux items:** Rythu Bharosa amount (phased first-acre model), PMKSY-PDMC %, PM-KUSUM split, PMFBY sum insured, Rythu Bima premium — all "verify on portal."

---

## 5. Recommended next actions for Rythu

**A. Add to `lib/schemes.ts` in this priority order** (matches §2 ranking):
1. `rythu_bima` · 2. `free_ag_power` · 3. `indiramma_atmiya_bharosa` · 4. `paddy_fine_rice_bonus` · 5. `subsidised_seed` · 6. `pm_kmy` · 7. `pmksy_pdmc` + `pm_kusum` · 8. `smam` · 9. `enam` + `rythu_vedika` · 10. `podu_rofr` · 11. honesty/awareness set (`crop_loan_waiver`, `sheep_distribution`, `namo_drone_didi`, `pmddky`, `aif`, `fisheries`).

**B. Fix the two existing inaccuracies now (low effort, high honesty payoff):**
- Change `rythu_bharosa.url` from `https://www.telangana.gov.in` → **`https://rythubharosa.telangana.gov.in/`** (line 42), and add the "first-acre priority / verify current amount" note to `what_te`/`what_en`.
- Ensure no "Rythu Bandhu" string survives anywhere; if amounts are added to `kcc`, keep the Rs 2 lakh (collateral-free) vs Rs 5 lakh (MISS) distinction correct.

**C. Extend the `Scheme` interface — this is the structural unblock.** Add:
- `status: "active" | "verify_locally" | "at_risk" | "closed" | "suspended"` (renders a colored badge),
- `level: "central" | "state"`,
- `priority: 1|2|3|4|5` (drives sort order for the low-literacy list),
- optional `honesty_note_te/en` (for the tenant/ROFR/"don't assume covered" caveats),
- optional `status_as_of` date string (so stale content is visible).
This lets the app tell the truth ("closed," "suspended," "verify this season") instead of silently omitting schemes farmers know by name.

**D. Keep content current (process, not one-off):**
- **Anchor every card to an official URL** (already the app's rule) and prefer **myScheme.gov.in** for schemes whose state portals are flaky (Rythu Bima's old domain is dead; AIF/SHC/JanSamarth 403 to bots; e-NAM has an expired SSL cert).
- **Seasonal review cadence** (schemes change with the season and the govt): before **Kharif (~Jun/Jul)** and **Rabi (~Dec/Jan)**, re-verify Rythu Bharosa amount/window, PMFBY notification + deadline, Paddy bonus status, seed list/rates, and enrolment windows (Rythu Bima closed ~12 Aug 2025; Indiramma window closed 25 Mar 2026).
- **Watch-list for change:** PM-KUSUM 2.0 guidelines, state mechanization relaunch (Jan 2026), PMDDKY district list (is Bhupalpally in TG's 4?), any new ROFR round, and whether the paddy bonus survives Rabi.
- **Prefer official/PIB for any rupee figure**; if not confirmable, render "verify on the official portal" — that discipline *is* the product's wedge.

---

**Key official URLs cited:** pmkisan.gov.in · pmfby.gov.in · myscheme.gov.in/schemes/kcc · soilhealth.dac.gov.in · rythubharosa.telangana.gov.in · myscheme.gov.in/schemes/rythu-bima · telangana.gov.in/departments/energy · ossds.telangana.gov.in · civilsupplies.telangana.gov.in · tribal.telangana.gov.in · kisan.telangana.gov.in · pmkusum.telangana.gov.in · pmkmy.gov.in · enam.gov.in (⚠ expired SSL) · agrimachinery.nic.in · clw.telangana.gov.in.

**Relevant files:** `/Users/ashishk/projects/rythu/apps/web/lib/schemes.ts` (edit target), `/Users/ashishk/projects/rythu/apps/web/lib/schemes.test.ts`, `/Users/ashishk/projects/rythu/apps/web/app/schemes` (screen).