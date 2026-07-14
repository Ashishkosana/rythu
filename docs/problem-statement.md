# Rythu — Problem Statement (LOCKED v1)

*A crop-advisory + weather + market app for farmers. Pilot: **Bhupalpally district, Telangana.***
Built by Ashish Kosana + [brother]. Working name "Rythu" (రైతు = farmer, Telugu).

---

## The core problem
A small/marginal farmer in Bhupalpally has **no single trustworthy, Telugu-first, low-friction tool** that tells them — for *their* exact location, weather, season, and soil — **what to grow, how to grow it, and how to make money from it.** Decisions today rely on intuition and neighbors, leading to wrong-crop/wrong-timing losses, over-planting (price crashes), and selling badly.

## Target user (pilot)
- **Bhupalpally district** small/marginal farmers (~1–5 acres).
- **Telugu-speaking**, variable literacy, entry-level Android, patchy connectivity.
- Design implication: **Telugu-first, icon/visual-heavy, minimal typing, offline-tolerant.**

## Locked v1 decisions
| # | Decision | Choice |
|---|---|---|
| 1 | Pilot geography | **Bhupalpally district only** |
| 2 | Data sources (v1) | Public APIs: **IMD / OpenWeather** (weather), **Agmarknet / e-NAM** (mandi prices), **Soil Health Card** data (soil) |
| 3 | Crop-recommendation brain | **Rule-based** (season + soil + rainfall → curated, *explainable* crop list). ML is a later phase. |
| 4 | Language | **Telugu ⇄ English toggle** — a first-class, always-visible language switch. Older farmers prefer Telugu, younger farmers English; both must be one tap away. Telugu is the *default* for the Bhupalpally pilot. (Built as proper i18n from day one — no hard-coded strings.) |
| 5 | "Make money" layer | **In v1** — mandi price view + best-time-to-sell signal (kept simple) |

## What the app does (grow → earn)
1. **Weather intelligence (Apple-Weather-grade):** accurate, hyperlocal — *"Will it rain today? How is it right now?"* — hourly + 7-day, rain probability, and **farming-relevant read** (good day to sow / irrigate / harvest / spray).
2. **Season + location crop recommendation:** given Bhupalpally + season (Kharif/Rabi) + soil + rainfall outlook → a short, ranked, *explained* list of crops likely to succeed AND sell well.
3. **Grow guidance:** stage-by-stage plan for the chosen crop (sowing window, water, fertilizer, common pests + action).
4. **Market layer:** nearby **mandi prices** + trend → *which crop is fetching good prices* and *when/where to sell.*

## Non-negotiables (make-or-break)
- **Telugu-first + visual** (not optional).
- **Data honesty:** app is only as good as its data — cite sources, stay conservative, show "last updated."
- **Trust:** explainable advice, never over-promise.
- **Offline/low-data** friendly.

## Success (v1)
A Bhupalpally farmer opens Rythu and can, in their language, see: *today's weather + will-it-rain*, *what to grow this season and why*, *how to grow it*, and *where it's selling well* — making a better, more profitable decision than they would alone.

## Phasing (paced to ship)
- **P0 (now):** problem statement ✅ → **HTML prototype (full flow)** → tech primer.
- **P1:** real weather integration (the accuracy centerpiece) + rule-based crop engine, English.
- **P2:** Telugu localization + mandi prices + Bhupalpally crop/soil data.
- **P3:** pilot with a handful of real farmers → iterate.

## Out of scope (v1)
All-India, ML yield prediction, in-app e-commerce/selling, scheme-API *integration* (Rythu Bharosa stalls on land records), and **conversational voice-AI / speech-to-text**. (Later phases.) — NOTE: **voice OUTPUT (tap-to-hear) is now IN v1**, see revisions.

---

# ⬆️ RESEARCH-DRIVEN REVISIONS (v1.1 — 2026-07-12)
*Supersedes conflicting items above. Full evidence in `research-findings.md`.*

**Data sources (corrected):**
- **Weather → Open-Meteo** (free, no key, live-verified — returns rain *probability*). IMD = phase-2 (gated, warnings only). Drop OpenWeather.
- **Mandi → data.gov.in Agmarknet** resource `9ef84268-d588-465a-a308-a864a43d0070` (free key, live-verified). Drop **e-NAM** (no API).
- **Soil Health Card farmer-level = BLOCKED** (no API, Aadhaar/OTP-gated). Replace with **district/village soil baseline + optional manual NPK entry.**
- **Backend proxy is now mandatory** (hide keys, nightly-cache the today-only mandi snapshot into history, precompute offline bundle).

**Facts corrected:**
- Bhupalpally soil = **RED/chalka (default)**, not black regur.
- Pilot season = **Kharif** (monsoon) — "will it rain today" is most valuable then.
- **Water source (canal/lift · tank · borewell · rainfed) is the #1 crop-rec input** and gates paddy. Steer rainfed users → cotton/chilli/red gram/sunflower.
- Crop set = **paddy, cotton, maize, red gram** (cotton was missing; it's the #2 crop + biggest pain).

**Scope changes:**
- **Voice OUTPUT (Telugu tap-to-hear) → IN v1** (biggest adoption lever). Only conversational voice-AI stays out.
- **New screens:** Onboarding (phone-only, NO Aadhaar; GPS/pin + water source) · Alerts/SMS (heavy-rain-tomorrow, sowing-window, price-crossed-MSP, pest-scouting-due).
- **Market = a sell DECISION** with an **MSP overlay (red when mandi < MSP)**, "reported on [date]", nearest-mandi fallback.
- **Grow = real pest teeth** (pink-bollworm scouting for cotton, stem-borer for paddy) tied to stage + weather.
- **Weather = honest** — probability + confidence + "forecasts can be wrong" + source/last-updated. Never "hyperlocal/Apple-grade."

**Positioning (the wedge):** **"We don't sell you anything."** Commission-free, neutral, explainable advice — vs incumbents whose advice is an input-sales funnel.

**Distribution/funding:** launch **through the Bhupalpally AEO / Rythu Vedika** trust network with assisted onboarding; **free forever** (grant/CSR/state), never a farmer paywall.

**Build order:** ship the **weather vertical slice end-to-end first** (Open-Meteo → backend cache → React screen → voice), then layer crops → market → onboarding → alerts.
