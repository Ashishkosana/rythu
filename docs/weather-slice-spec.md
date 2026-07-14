# Rythu — Weather Slice v0 Spec (verified)

*Derived 2026-07-13 from a research → adversarial-verify → synthesis pass. Every farming rule was
checked by an independent skeptic agent for farmer-safety; the honest-framing decision replaces the
prototype's faked "medium confidence". This doc is the source of truth for the weather service AND
the checklist to **vet with the Bhupalpally district agriculture office / Rythu Vedika before pilot**.*

Data source: **Open-Meteo** free forecast API (no key). ~11 km global deterministic model — **not**
convective-cell resolving; it can miss local monsoon showers. Point: Bhupalpally 18.44, 79.86
(model snaps to grid cell 18.4534, 79.8728, elev 199 m, ~1.6 km away). Timezone: Asia/Kolkata.

Fields used — hourly: `precipitation_probability` %, `precipitation` mm, `temperature_2m` °C,
`relative_humidity_2m` %, `weather_code` WMO, `wind_speed_10m` km/h · daily (7 d):
`precipitation_probability_max` %, `precipitation_sum` mm, `temperature_2m_max/min` °C,
`weather_code`, `wind_speed_10m_max` km/h.

---

## Honest framing (the "confidence" decision)

**We show NO confidence rating in v0.** The basic endpoint is a single deterministic run with no
ensemble/spread, so any "high/medium/low" would be fabricated. Instead, uniformly on every forecast:

1. **Lead with the real number** — the % chance of rain (`precipitation_probability`), worded as a
   *chance*, never relabelled "confidence".
2. **A fixed, identical reliability line** (same for day 1 and day 7):
   > ⚠️ General-area forecast (~11 km) — it can be wrong. Rain % shows the chance, not a promise; watch the sky too.
3. **Source + last-updated stamp**: `Source: Open-Meteo (~11 km) · updated <relative>`
   (`just now` <2 min · `N min ago` <60 min · `N hr ago` <24 h · else `DD Mon`). If served from stale
   cache after a fetch failure, prefix `Offline — showing saved forecast · `.

Rejected: faking a label · deriving pseudo-confidence from lead-time · reusing rain-% as confidence.
**Phase-2 upgrade** (a *real* "models agree/mixed/uncertain" badge): Open-Meteo Ensemble API
(`/v1/ensemble-mean` gives mean + spread) — but its models are coarser (~25 km), so plan it as an
upgrade, not a v1 requirement. Never say "hyperlocal" or "Apple-grade".

---

## Farming-read rules (post-verification)

Every rule fires **only forward from `now`**, is framed as probability, carries a mandatory caveat,
and cites an agronomic source. `confidence` below is **internal** (gates wording strength) — it is
**never** shown to the farmer as a reliability score.

| id | action | crop scope | status | conf | trigger (verified) |
|---|---|---|---|---|---|
| `spray-rain-washoff` | spray | any | include+caveat | med | Forward `now..+6h` (systemic: `+24h`): fire if any hour `precip_prob ≥ 60` **or** `precip ≥ 0.5 mm` **or** Σ`precip ≥ 2 mm`. Backward calendar-day leg **removed**. No-fire ≠ "safe to spray". |
| `spray-wind-drift` | spray | any | include+caveat | med | Morning window `06:00–10:00`: fire "too windy" if any hour `wind ≥ 15 km/h`. Daily-max leg **removed** (only an info nudge). Wind-only all-clear. |
| `irrigate-skip-rain-coming` | irrigate | any except paddy | include+caveat | med | Skip watering only if today **or** tomorrow (same day) has `precip_sum ≥ 20 mm` **and** `precip_prob_max ≥ 60`. Prob-only & 10 mm legs **removed**. |
| `sow-need-soil-moisture` | sow | **rainfed only**, sow window | include+caveat | **low** | Soft caution if over next 3 d the **largest single-day** `precip_sum < 20 mm` **and** every day's `precip_prob_max < 60`. Silence ≠ "safe to sow". |
| `sow-avoid-before-washout` | sow | any except paddy, sow window | include+caveat | med | Fire on **amount** only: any of next 3 d `precip_sum ≥ 40 mm`. Prob-only branch **removed**. |
| `harvest-paddy-avoid-rain` | harvest | **paddy**, harvest window (~Sep+) | include+caveat | med | Protective: any of next 3 d `precip_prob_max ≥ 60` **or** `precip_sum ≥ 10 mm`. Season-gated so it never fires on green monsoon paddy. |
| `fieldwork-avoid-storm-wet` | fieldwork | any | include+caveat | med | Fire if any hour (next 6h) `precip_prob ≥ 60` **or** `weather_code ∈ {95,96,99}` **or** `wind ≥ 30 km/h`. Action scoped to postponable ops + open-field safety. |
| `drainage-heavy-rain-maize` | fieldwork | maize + red gram | **include-v0** | med | Fire if any of next 3 d `precip_sum ≥ 50 mm` **or** (`precip_sum ≥ 35 mm` **and** `precip_prob_max ≥ 70`). Prob-only branch **removed**. Low-regret prep. |
| `cotton-pinkbollworm-spray-window` | spray | cotton | **DEFERRED** | med | Deferred to the crop-stage/scouting milestone: safety hinges on scouting/ETL data v0 can't see; a farmer could read "spray now" and treat unwarranted cotton (PBW is low Jun–Sep). Ship only when the app is crop-stage-aware and can lead with the scouting gate. |

**Why every rule got hardened:** the ~11 km model *under-detects* convective monsoon showers, so for
any rule where "model says dry → do the risky thing" the safe direction is to be *more* eager to warn
and to treat silence as "possible, not guaranteed". Probability-only branches were removed because in
monsoon "80% chance of any rain" fires almost daily (cry-wolf → alarm fatigue).

### Caveats (verbatim, per rule) & citations
See `farming_read[].caveat_en` and `sources` in the served API. Key sources: pesticide rainfastness
(Sprayers101), IMD Gramin Krishi Mausam Seva agromet advisories, UC IPM + ICAR (pink bollworm),
Colorado State Extension (water-balance irrigation), PJTSAU/CRIDA (sowing & drainage), IRRI Rice
Knowledge Bank (paddy harvest moisture). **Numbers marked for district-agri-office confirmation:**
the wind cutoff (15 km/h) and the sowing/recharge mm thresholds.

---

## Implementation contract (hexagonal)

- **domain/** pure only (no httpx / boto / `os.environ` / `datetime.now()`). Models are
  `@dataclass(frozen=True, slots=True)`. The clock is an **input** (`FarmerContext.now`, tz-aware
  Asia/Kolkata) — this makes "next 6h crossing midnight" and morning-window rules deterministic.
- **Null handling (two opposite behaviours):** `None` = *unknown*, never 0. Fire-on-risk rules skip
  a `None` leg (don't fire on unknown). All-clear checks treat `None` conservatively (a missing value
  disqualifies the all-clear). Helpers: `any_at_or_above` (ignores None), `all_below` (False if any None).
- **Per-day pairing:** amount AND probability must come from the *same* `DailyPoint`.
  `sow-need-soil-moisture` uses the **max single-day** sum, not the 3-day sum.
- **Scoping is data**, not branches: `applies_to_crops` / `excludes_crops` /
  `applies_to_water_sources` / season window filter the registry before `evaluate()` runs.
- **Never leak raw Open-Meteo:** adapter maps JSON → domain `Forecast`; app serialises `Forecast` →
  the typed contract. Adding an ensemble provider later touches only the adapter + `ForecastReliability`.
- **Degraded forecast:** empty/short hourly ⇒ emit no read (never a false all-clear); on provider
  failure with no cache, return 200 with reliability + empty `farming_read`, not a raw 500.

Full field-by-field domain model + example response JSON live in the code
(`src/rythu_weather/domain/models.py`, `app/serialize.py`) and the workflow journal.
