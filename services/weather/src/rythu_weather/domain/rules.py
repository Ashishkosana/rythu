"""The farming-read rule registry.

Each rule is a small PURE predicate plus a :class:`RuleSpec` holding its static metadata
(scope, severity, mandatory caveat, citations). Thresholds live as named constants below so
they are easy to tune and to defend line-by-line. Several are marked TODO-VET: confirm the
exact number with the Bhupalpally district agriculture office / PJTSAU before pilot.

Design invariants (from the verified spec, ``docs/weather-slice-spec.md``):
* Rules look only FORWARD from ``ctx.now``.
* The ~11 km model under-detects convective monsoon showers, so a no-fire result never means
  "safe" — the mandatory caveat says so, and thresholds err toward warning.
* Probability-only triggers were removed (in monsoon "80% chance of any rain" fires daily).
* ``None`` = unknown: fire-on-risk rules ignore it; all-clear checks reject it.
"""

from __future__ import annotations

from datetime import date
from itertools import pairwise

from rythu_weather.domain.models import (
    Crop,
    DailyPoint,
    FarmAction,
    FarmerContext,
    Fired,
    Forecast,
    HourlyPoint,
    RuleSpec,
    Severity,
    WaterSource,
)
from rythu_weather.domain.windows import (
    all_below,
    any_at_or_above,
    choose_morning_day,
    longest_run,
    max_present,
    morning_hours,
    next_days,
    next_hours,
    sum_present,
)
from rythu_weather.domain.wmo import THUNDERSTORM_CODES, WET_CODES

# --- thresholds (cited; TODO-VET marks numbers needing agri-office sign-off) ---------------

SPRAY_WINDOW_H = 6  # forward hours checked for spray wash-off (systemic sprays: extend to 24h)
SPRAY_RAIN_PROB = 60  # % chance of rain that blocks spraying
SPRAY_RAIN_MM = 0.5  # mm in any hour that blocks spraying (even light rain washes contact product)
SPRAY_RAIN_SUM_MM = 2.0  # mm summed over the window that blocks spraying
SPRAY_WIND_KMH = 15.0  # TODO-VET: 10m wind that blocks spraying (10m→canopy ~0.75 → real margin)

IRRIGATE_SUM_MM = 20.0  # mm of forecast rain to justify skipping an irrigation (FAO effective-rain)
IRRIGATE_PROB = 60  # % chance that must accompany that amount, same day

SOW_MOISTURE_MM = 20.0  # TODO-VET: largest single-day mm below which sowing rain is "not enough yet"
SOW_MOISTURE_PROB = 60  # every day's max % chance must be below this to warn "wait"
SOW_WASHOUT_MM = 40.0  # mm/day of forecast heavy rain that risks washing out fresh seed (IMD "rather heavy")

HARVEST_PROB = 60  # % chance over next 3d that warrants "harvest ripe paddy now"
HARVEST_MM = 10.0  # mm/day over next 3d that warrants the same

FIELDWORK_RAIN_PROB = 60  # % chance that warrants delaying field work
FIELDWORK_WIND_KMH = 30.0  # 10m wind that warrants delaying field work

DRAINAGE_MM_HARD = 50.0  # mm/day of heavy rain → clear drains (waterlogging protection)
DRAINAGE_MM_SOFT = 35.0  # mm/day that, WITH high probability, also warrants clearing drains
DRAINAGE_PROB = 70  # % chance gating the softer amount

# Kharif calendar gates for Bhupalpally (tunable data; TODO-VET with the district office).
SOW_WINDOW = ((6, 1), (8, 15))  # monsoon-onset sowing window for dryland crops
PADDY_HARVEST_WINDOW = ((9, 1), (12, 31))  # Kharif paddy harvest — never fires on green monsoon paddy

# Chilli (mirchi) thresholds + season month-sets (verified spec; TODO-VET the numbers with the
# district agri office / PJTSAU). Months are disjoint Kharif+Rabi windows.
CHILLI_DRAIN_MM_HARD = 40.0
CHILLI_DRAIN_MM_SOFT = 25.0
CHILLI_DRAIN_PROB = 70

CHILLI_HEAT_TMAX = 35.0
CHILLI_HEAT_TMAX_SEVERE = 40.0
CHILLI_HEAT_MONTHS = frozenset({2, 3, 4, 9, 10, 11, 12})  # Kharif + Rabi/summer flowering

CHILLI_HARVEST_PROB = 60
CHILLI_HARVEST_MM = 5.0  # open-yard drying chillies spoil at a few mm (lower than paddy's 10)
CHILLI_HARVEST_MONTHS = frozenset({11, 12, 1, 2, 3, 4, 5})

CHILLI_ANTHRAC_RH = 85
CHILLI_ANTHRAC_TEMP_LO = 20.0
CHILLI_ANTHRAC_TEMP_HI = 30.0
CHILLI_ANTHRAC_RUN_H = 6  # consecutive humid hours that set up fruit-rot infection
CHILLI_ANTHRAC_WET_MM = 0.2
CHILLI_ANTHRAC_MONTHS = frozenset({9, 10, 11})

CHILLI_THRIPS_DRY_MM = 2.0
CHILLI_THRIPS_DRY_PROB = 40
CHILLI_THRIPS_TMAX_LO = 28.0
CHILLI_THRIPS_TMAX_HI = 38.0
CHILLI_THRIPS_RH_DAY = 60  # afternoon RH below this = dry, thrips-favourable
CHILLI_THRIPS_MONTHS = frozenset({8, 9, 10, 11, 12, 1, 2, 3})

# Rules recorded but intentionally NOT run (need crop-stage/scouting/species data to be safe, or
# are redundant with shipped rules). See docs/chilli-rules-spec.md.
DEFERRED_RULE_IDS: frozenset[str] = frozenset(
    {
        "cotton-pinkbollworm-spray-window",
        "chilli-thrips-mite-rain-suppress-hold-spray",  # rain≠control for local black thrips
        "chilli-mite-warm-humid-leafcurl",  # contested weather premise
        "chilli-nursery-dampingoff-wet",  # needs nursery-stage the app can't see
        "chilli-spray-timing-rain-wind-washoff",  # duplicate of shipped spray rules
        "chilli-transplant-avoid-heavy-rain",  # duplicate of sow-avoid-before-washout
    }
)


# --- small text helpers -------------------------------------------------------------------


def _rel_day(target: date, today: date) -> str:
    delta = (target - today).days
    if delta <= 0:
        return "today"
    if delta == 1:
        return "tomorrow"
    return f"on {target.strftime('%A')}"


def _join_reasons(reasons: list[str]) -> str:
    if len(reasons) == 1:
        text = reasons[0]
    elif len(reasons) == 2:
        text = f"{reasons[0]} and {reasons[1]}"
    else:
        text = ", ".join(reasons[:-1]) + f" and {reasons[-1]}"
    return text[0].upper() + text[1:]


# --- predicates ---------------------------------------------------------------------------


def _spray_rain_washoff(forecast: Forecast, ctx: FarmerContext) -> Fired | None:
    hrs = next_hours(forecast, ctx.now, SPRAY_WINDOW_H)
    if not hrs:
        return None
    probs = [h.precipitation_probability for h in hrs]
    precs = [h.precipitation_mm for h in hrs]
    fires = (
        any_at_or_above(probs, SPRAY_RAIN_PROB)
        or any_at_or_above(precs, SPRAY_RAIN_MM)
        or sum_present(precs) >= SPRAY_RAIN_SUM_MM
    )
    if not fires:
        return None
    pct = max_present(probs)
    chance = f"{pct}% chance" if pct is not None else "rain likely"
    return Fired(
        headline_en=(
            f"Rain possible in the next few hours ({chance}) — better to wait so your spray does not wash off."
        ),
        detail_en=(
            "Most contact sprays need 2–6 dry hours to bind (systemic up to ~24 h). "
            "Spraying just before rain wastes the chemical and your money."
        ),
        window_note="checked now..now+6h (systemic sprays also need ~24h dry — not verified in v0)",
    )


def _spray_wind_drift(forecast: Forecast, ctx: FarmerContext) -> Fired | None:
    day = choose_morning_day(ctx.now)
    # Forward-only: when the morning window is today and partly elapsed, drop past hours so a
    # squall that already passed can't warn "too windy" during a calm present.
    start = ctx.now.replace(minute=0, second=0, microsecond=0)
    hrs = [h for h in morning_hours(forecast, day) if h.time_local >= start]
    if not hrs:
        return None
    winds = [h.wind_speed_kmh for h in hrs]
    if not any_at_or_above(winds, SPRAY_WIND_KMH):
        return None
    peak = max_present(winds)
    when = "this morning" if day == ctx.now.date() else "tomorrow morning"
    peak_txt = f" (~{round(peak)} km/h)" if peak is not None else ""
    return Fired(
        headline_en=(
            f"Too windy {when}{peak_txt} to spray — wait for calm, still air "
            "and spray early with the wind at your back."
        ),
        detail_en=(
            "Strong wind blows spray off-target: poor coverage, wasted chemical, and drift onto you or nearby crops."
        ),
        window_note=f"checked 06:00–10:00 on {day.isoformat()}",
    )


def _irrigate_skip(forecast: Forecast, ctx: FarmerContext) -> Fired | None:
    for d in next_days(forecast, ctx.now, 2):
        s = d.precipitation_sum_mm
        p = d.precipitation_probability_max
        if s is not None and p is not None and s >= IRRIGATE_SUM_MM and p >= IRRIGATE_PROB:
            when = _rel_day(d.day, ctx.now.date())
            return Fired(
                headline_en=(
                    f"Good rain likely {when} (≈{round(s)} mm, {p}% chance) — "
                    "you can probably skip watering today and save water and power."
                ),
                detail_en="Light rain does not replace a full watering, so this is only for a genuinely good rain.",
                window_note="checked today and tomorrow (amount AND probability, same day)",
            )
    return None


def _sow_need_moisture(forecast: Forecast, ctx: FarmerContext) -> Fired | None:
    days = next_days(forecast, ctx.now, 3)
    if not days:
        return None
    # Conservative on unknowns: if ANY day's rain amount is unknown we do NOT tell a rainfed
    # farmer to wait — a missing value could hide a heavy soaker. (Same reasoning as all_below
    # for the probability leg below.)
    known_sums = [d.precipitation_sum_mm for d in days if d.precipitation_sum_mm is not None]
    if len(known_sums) != len(days) or max(known_sums) >= SOW_MOISTURE_MM:
        return None
    probs = [d.precipitation_probability_max for d in days]
    if not all_below(probs, SOW_MOISTURE_PROB):
        return None
    pct = max_present(probs)
    pct_txt = f"up to {pct}% chance" if pct is not None else "a low chance"
    return Fired(
        headline_en=(
            f"Only light rain expected so far ({pct_txt}) — it may not be enough to sow on. "
            "Check your field before deciding."
        ),
        detail_en=(
            "Sowing on a false start can fail if seeds dry out; wait for a genuine good rain — "
            "but do not delay past your usual sowing time."
        ),
        window_note="checked next 3 days (largest single day)",
    )


def _sow_avoid_washout(forecast: Forecast, ctx: FarmerContext) -> Fired | None:
    for d in next_days(forecast, ctx.now, 3):
        s = d.precipitation_sum_mm
        if s is not None and s >= SOW_WASHOUT_MM:
            when = _rel_day(d.day, ctx.now.date())
            return Fired(
                headline_en=(
                    f"Very heavy rain possible {when} (≈{round(s)} mm) — "
                    "it may be safer to sow after it passes and the field drains."
                ),
                detail_en=(
                    "Fresh seed can wash out or waterlog. Moderate rain is good for sowing; "
                    "this warns only about very heavy rain."
                ),
                window_note="checked next 3 days (amount only)",
            )
    return None


def _harvest_paddy(forecast: Forecast, ctx: FarmerContext) -> Fired | None:
    days = next_days(forecast, ctx.now, 3)
    fires = False
    for d in days:
        p = d.precipitation_probability_max
        s = d.precipitation_sum_mm
        if (p is not None and p >= HARVEST_PROB) or (s is not None and s >= HARVEST_MM):
            fires = True
            break
    if not fires:
        return None
    pct = max_present(d.precipitation_probability_max for d in days)
    chance = f"{pct}% chance" if pct is not None else "rain likely"
    return Fired(
        headline_en=(
            f"Rain expected soon ({chance}) — if your paddy is already mature, harvest it now and keep the grain dry."
        ),
        detail_en=(
            "Rain on ripe paddy causes shattering, sprouting and mould; harvest on a dry day and keep grain covered."
        ),
        window_note="checked next 3 days",
    )


def _fieldwork_storm(forecast: Forecast, ctx: FarmerContext) -> Fired | None:
    hrs = next_hours(forecast, ctx.now, 6)
    if not hrs:
        return None
    probs = [h.precipitation_probability for h in hrs]
    winds = [h.wind_speed_kmh for h in hrs]
    codes = [h.weather_code for h in hrs]
    storm = any(c in THUNDERSTORM_CODES for c in codes if c is not None)
    rain = any_at_or_above(probs, FIELDWORK_RAIN_PROB)
    gale = any_at_or_above(winds, FIELDWORK_WIND_KMH)
    if not (storm or rain or gale):
        return None
    reasons: list[str] = []
    if storm:
        reasons.append("thunderstorms")
    if rain:
        reasons.append("rain")
    if gale:
        reasons.append("strong wind")
    return Fired(
        headline_en=(
            f"{_join_reasons(reasons)} possible in the next few hours — "
            "delay spraying and ploughing and stay out of open fields; "
            "if a crop is ready, harvest or secure it and clear drains first."
        ),
        detail_en="Working wet soil compacts it, and open-field lightning is a real danger in the monsoon.",
        window_note="checked now..now+6h",
    )


def _drainage_heavy_rain(forecast: Forecast, ctx: FarmerContext) -> Fired | None:
    for d in next_days(forecast, ctx.now, 3):
        s = d.precipitation_sum_mm
        if s is None:
            continue
        p = d.precipitation_probability_max
        heavy = s >= DRAINAGE_MM_HARD
        rather = p is not None and s >= DRAINAGE_MM_SOFT and p >= DRAINAGE_PROB
        if heavy or rather:
            when = _rel_day(d.day, ctx.now.date())
            chance = f", {p}% chance" if p is not None else ""
            return Fired(
                headline_en=(
                    f"Heavy rain possible {when} (up to ≈{round(s)} mm{chance}) — "
                    "clearing your field drains now is cheap insurance; "
                    "maize and red gram are hurt by even a few hours of standing water."
                ),
                window_note="checked next 3 days",
            )
    return None


# --- chilli (mirchi) predicates -----------------------------------------------------------


def _chilli_drainage(forecast: Forecast, ctx: FarmerContext) -> Fired | None:
    for d in next_days(forecast, ctx.now, 3):
        s = d.precipitation_sum_mm
        if s is None:
            continue
        p = d.precipitation_probability_max
        hard = s >= CHILLI_DRAIN_MM_HARD
        soft = p is not None and s >= CHILLI_DRAIN_MM_SOFT and p >= CHILLI_DRAIN_PROB
        if hard or soft:
            when = _rel_day(d.day, ctx.now.date())
            chance = f", {p}% chance" if p is not None else ""
            return Fired(
                headline_en=(
                    f"Heavy rain possible {when} (up to ≈{round(s)} mm{chance}) — clear and deepen "
                    "your field drains now; chilli roots and collar rot after only a few hours of standing water."
                ),
                detail_en=(
                    "Chilli is very waterlogging-sensitive. Open drains and low-spot channels, ridge/bed the "
                    "crop, and hold back irrigation before the rain. Low-regret field prep — no spraying."
                ),
                window_note="checked next 3 days",
            )
    return None


def _chilli_heat_flowerdrop(forecast: Forecast, ctx: FarmerContext) -> Fired | None:
    days = next_days(forecast, ctx.now, 7)

    def _rain_coming(d: DailyPoint) -> bool:
        p, s = d.precipitation_probability_max, d.precipitation_sum_mm
        return (p is not None and p >= 60) or (s is not None and s >= 2)

    for a, b in pairwise(days):
        ta, tb = a.temperature_max_c, b.temperature_max_c
        if ta is None or tb is None or ta < CHILLI_HEAT_TMAX or tb < CHILLI_HEAT_TMAX:
            continue
        if _rain_coming(a) or _rain_coming(b):
            continue  # rain will cool/wet the field — don't push irrigation into a wet window
        peak = max(ta, tb)
        lead = "Extreme heat" if peak >= CHILLI_HEAT_TMAX_SEVERE else "A hot spell"
        return Fired(
            headline_en=(
                f"If your chilli is flowering or setting fruit: {lead.lower()} (~{round(peak)}°C for 2+ days) "
                "is likely and some flowers may drop — give light, even irrigation early morning or evening."
            ),
            detail_en=(
                "Days above ~35°C (worse with warm nights) shed chilli flowers and young fruit. Water lightly "
                "at the cooler hours and mulch to keep roots cool. Do NOT flood or water daily — soggy soil "
                "also drops flowers and rots roots. Heat drop usually recovers on cooling; no spray is needed."
            ),
            window_note="checked next 7 days (2+ consecutive hot days)",
        )
    return None


def _chilli_harvest_drying(forecast: Forecast, ctx: FarmerContext) -> Fired | None:
    days = next_days(forecast, ctx.now, 3)
    fires = False
    for d in days:
        p, s = d.precipitation_probability_max, d.precipitation_sum_mm
        if (p is not None and p >= CHILLI_HARVEST_PROB) or (s is not None and s >= CHILLI_HARVEST_MM):
            fires = True
            break
    if not fires:
        return None
    pct = max_present(d.precipitation_probability_max for d in days)
    chance = f"{pct}% chance" if pct is not None else "rain likely"
    return Fired(
        headline_en=(
            f"Rain possible in the next 3 days ({chance}) — ONLY if your chilli is already red-ripe and ready, "
            "pick it now, and cover any harvested or drying chillies to prevent rot and mould."
        ),
        detail_en=(
            "Telangana chilli is mostly sold sun-dried; rain on ripe fruit and drying stock causes rot, mould "
            "and price loss. Do NOT strip green fruit early — chilli is picked in several rounds. If nothing is "
            "ripe yet, just cover harvested/drying stock."
        ),
        window_note="checked next 3 days",
    )


def _chilli_anthracnose(forecast: Forecast, ctx: FarmerContext) -> Fired | None:
    hrs = next_hours(forecast, ctx.now, 48)
    if not hrs:
        return None

    def _humid(h: HourlyPoint) -> bool:
        rh, t = h.relative_humidity, h.temperature_c
        return (
            rh is not None
            and t is not None
            and rh >= CHILLI_ANTHRAC_RH
            and CHILLI_ANTHRAC_TEMP_LO <= t <= CHILLI_ANTHRAC_TEMP_HI
        )

    if longest_run(hrs, _humid) < CHILLI_ANTHRAC_RUN_H:
        return None
    wet = any(
        (h.precipitation_mm is not None and h.precipitation_mm >= CHILLI_ANTHRAC_WET_MM)
        or (h.weather_code in WET_CODES)
        for h in hrs
    )
    if not wet:
        return None
    return Fired(
        headline_en=(
            "If your chilli is carrying fruit or turning red: a warm, humid, wet spell is possible in the next "
            "1–2 days that can raise fruit-rot (anthracnose) risk — walk your field and check the fruit."
        ),
        detail_en=(
            "Warm + humid + surface wetness during ripening drives anthracnose/fruit-rot (Colletotrichum). "
            "Remove and carry away any fruit with sunken dark or water-soaked spots, avoid overhead watering, "
            "and keep good spacing so plants dry faster. This is a reminder to LOOK, not to spray."
        ),
        window_note="checked next 48h (humid-wet run)",
    )


def _chilli_thrips(forecast: Forecast, ctx: FarmerContext) -> Fired | None:
    days = next_days(forecast, ctx.now, 3)
    if not days:
        return None
    # All-clear-style dryness: every day must be KNOWN and dry (a None day = unknown → no fire).
    if not all_below([d.precipitation_sum_mm for d in days], CHILLI_THRIPS_DRY_MM):
        return None
    if not all_below([d.precipitation_probability_max for d in days], CHILLI_THRIPS_DRY_PROB):
        return None
    if not any(
        t is not None and CHILLI_THRIPS_TMAX_LO <= t <= CHILLI_THRIPS_TMAX_HI
        for t in (d.temperature_max_c for d in days)
    ):
        return None
    daytime = [
        h for h in next_hours(forecast, ctx.now, 72) if 9 <= h.time_local.hour < 18 and h.relative_humidity is not None
    ]
    if not daytime:
        return None
    dry_hours = sum(
        1 for h in daytime if h.relative_humidity is not None and h.relative_humidity < CHILLI_THRIPS_RH_DAY
    )
    if dry_hours * 2 <= len(daytime):  # need a strict majority
        return None
    return Fired(
        headline_en=(
            "A hot, dry, rain-free spell is likely over the next 3 days, which can favour thrips leaf-curl "
            "(murda) — go and LOOK at the newest leaves and curled shoots; do not spray on a guess."
        ),
        detail_en=(
            "Thrips build up in dry warm weather and curl new growth. Turn over young leaves and check growing "
            "tips. Spraying blind wastes money, breeds resistance and can flare mites — scout first."
        ),
        window_note="checked next 3 days",
    )


# --- registry -----------------------------------------------------------------------------

ACTIVE_RULES: tuple[RuleSpec, ...] = (
    RuleSpec(
        id="spray-rain-washoff",
        action=FarmAction.SPRAY,
        crop_label="any",
        severity=Severity.CAUTION,
        confidence="medium",
        caveat_en=(
            "Rain chance is from a ~11 km global forecast (Open-Meteo) that can be wrong and often "
            "MISSES local monsoon showers: a warning is a probability, not a certainty, and NO warning "
            "is NOT a guarantee of dry weather. Watch the sky and let contact sprays dry 2–6 hours "
            "(systemic up to 24 h) before any rain."
        ),
        sources=(
            "https://sprayers101.com/rainfastness-pesticide/",
            "https://mausam.imd.gov.in/responsive/servicesMetAgriculture.php",
        ),
        predicate=_spray_rain_washoff,
    ),
    RuleSpec(
        id="spray-wind-drift",
        action=FarmAction.SPRAY,
        crop_label="any",
        severity=Severity.CAUTION,
        confidence="medium",
        caveat_en=(
            "This checks WIND ONLY; 'wind is OK' does not mean 'safe to spray' — do not spray if rain "
            "is likely within a few hours, avoid the hot midday, and follow the product label. The "
            "~11 km forecast can miss local gusts, so also look at your field: if leaves and branches "
            "move a lot, it is too windy. (Wind limit to be confirmed with the district agriculture office.)"
        ),
        sources=("https://mausam.imd.gov.in/responsive/servicesMetAgriculture.php",),
        predicate=_spray_wind_drift,
    ),
    RuleSpec(
        id="irrigate-skip-rain-coming",
        action=FarmAction.IRRIGATE,
        crop_label="any",
        severity=Severity.INFO,
        confidence="medium",
        excludes_crops=frozenset({Crop.PADDY}),  # paddy is managed by standing-water depth
        caveat_en=(
            "One-day skip only. The ~11 km forecast can be wrong and often over- or under-calls local "
            "showers. Check the top ~5 cm of soil before your next watering, and water anyway at a "
            "sensitive stage (flowering, boll-fill, grain-fill) or if the crop wilts."
        ),
        sources=("https://extension.colostate.edu/resource/irrigation-scheduling-the-water-balance-approach/",),
        predicate=_irrigate_skip,
    ),
    RuleSpec(
        id="sow-need-soil-moisture",
        action=FarmAction.SOW,
        crop_label="any",
        severity=Severity.INFO,
        confidence="low",
        applies_to_water_sources=frozenset({WaterSource.RAINFED}),
        season=SOW_WINDOW,
        caveat_en=(
            "Forecasts can be wrong; this ~11 km area model often MISSES local monsoon showers, so real "
            "rain may exceed what is shown — treat as a chance, not a promise. Check your own field: if "
            "soil is moist to a hand's depth you may be able to sow. Do NOT delay past your usual sowing time."
        ),
        sources=(
            "https://www.siasat.com/telangana-pjtsau-advises-farmers-to-utilise-rains-for-sowing-dry-crops-2688339/",
            "https://www.downtoearth.org.in/agriculture/kharif-2026-sowing-gets-off-to-a-slow-start-as-el-ni%C3%B1o-casts-shadow-over-monsoon",
        ),
        predicate=_sow_need_moisture,
    ),
    RuleSpec(
        id="sow-avoid-before-washout",
        action=FarmAction.SOW,
        crop_label="any",
        severity=Severity.CAUTION,
        confidence="medium",
        excludes_crops=frozenset({Crop.PADDY}),  # transplanted/puddled paddy wants standing water
        season=SOW_WINDOW,
        caveat_en=(
            "Show as caution, not instruction. The ~11 km forecast can miss local showers — a "
            "probability, not a certainty. Moderate rain is GOOD for sowing; this warns only about VERY "
            "heavy rain that could wash out fresh seed. Do NOT delay past the monsoon-moisture window on "
            "this alone — sowing on ridges/furrows for drainage is often better than waiting."
        ),
        sources=(
            "https://www.siasat.com/telangana-pjtsau-advises-farmers-to-utilise-rains-for-sowing-dry-crops-2688339/",
        ),
        predicate=_sow_avoid_washout,
    ),
    RuleSpec(
        id="harvest-paddy-avoid-rain",
        action=FarmAction.HARVEST,
        crop_label="paddy",
        severity=Severity.CAUTION,
        confidence="medium",
        applies_to_crops=frozenset({Crop.PADDY}),
        season=PADDY_HARVEST_WINDOW,
        caveat_en=(
            "ONLY if your paddy is already mature and ready to cut — grain firm/hard and about 80% of the "
            "panicle turned straw/golden (~20–25% moisture). If still green/milky, do NOT harvest early: "
            "it lowers yield and cracks grain in milling. Rain chance is from a ~11 km model that can miss "
            "or over-call local showers."
        ),
        sources=(
            "http://www.knowledgebank.irri.org/step-by-step-production/postharvest/harvesting",
            "http://www.knowledgebank.irri.org/training/fact-sheets/item/when-to-harvest-fact-sheet",
        ),
        predicate=_harvest_paddy,
    ),
    RuleSpec(
        id="fieldwork-avoid-storm-wet",
        action=FarmAction.FIELDWORK,
        crop_label="any",
        severity=Severity.CAUTION,
        confidence="medium",
        caveat_en=(
            "This is a probability from a wide-area (~11 km) forecast that can MISS sudden local storms — "
            "no warning does not guarantee safe weather. If you see dark clouds building or hear thunder, "
            "stop work and take shelter immediately; do not stand under a lone tree or near metal. The "
            "'delay' applies to postponable operations — a harvest-ready crop should be secured, not left."
        ),
        sources=("https://mausam.imd.gov.in/responsive/servicesMetAgriculture.php",),
        predicate=_fieldwork_storm,
    ),
    RuleSpec(
        id="drainage-heavy-rain-maize",
        action=FarmAction.FIELDWORK,
        crop_label="maize",
        severity=Severity.INFO,
        confidence="medium",
        applies_to_crops=frozenset({Crop.MAIZE, Crop.RED_GRAM}),
        caveat_en=(
            "Rain is a probability, not a certainty. Source: Open-Meteo (~11 km); forecasts can be wrong "
            "and may miss local showers, so also watch the sky. Clearing drains is low-cost insurance even "
            "if the rain turns out lighter than forecast."
        ),
        sources=(
            "https://www.siasat.com/telangana-pjtsau-advises-farmers-to-utilise-rains-for-sowing-dry-crops-2688339/",
        ),
        predicate=_drainage_heavy_rain,
    ),
    # --- chilli (mirchi) specific reads (verified spec; see docs/chilli-rules-spec.md) ---
    RuleSpec(
        id="chilli-waterlogging-drainage",
        action=FarmAction.FIELDWORK,
        crop_label="chilli",
        severity=Severity.CAUTION,
        confidence="high",
        applies_to_crops=frozenset({Crop.CHILLI}),
        caveat_en=(
            "Rain is a CHANCE from a ~11 km model (Open-Meteo) that can be wrong and often MISSES local "
            "downpours — a warning is a probability, not a promise, and NO warning is not a guarantee of dry "
            "weather, so watch your own field and low spots. This is a drainage/field-prep alert, not a spray order."
        ),
        sources=(
            "https://pnwhandbooks.org/plantdisease/host-disease/pepper-capsicum-spp-phytophthora-blight-root-crown-rot",
            "https://ipm.ucanr.edu/agriculture/peppers/root-and-crown-rots-and-damping-off-diseases/",
        ),
        predicate=_chilli_drainage,
    ),
    RuleSpec(
        id="chilli-heat-flowerdrop",
        action=FarmAction.IRRIGATE,
        crop_label="chilli",
        severity=Severity.CAUTION,
        confidence="medium",
        applies_to_crops=frozenset({Crop.CHILLI}),
        months=CHILLI_HEAT_MONTHS,
        caveat_en=(
            "Only relevant once the crop is flowering/fruiting. Temperatures are from a ~11 km model that can be "
            "wrong; a 'no-rain' forecast can miss local showers, so check the topsoil before watering and do NOT "
            "over-irrigate. Heat cutoffs (35/40°C) to be vetted with the Bhupalpally agri office / PJTSAU."
        ),
        sources=(
            "https://data.longpaddock.qld.gov.au/static/dcap/DCAP3/DCAP%203__3%20Capsicum%20CTT%20Final.pdf",
            "https://agritech.tnau.ac.in/horticulture/horti_vegetables_chilli.html",
        ),
        predicate=_chilli_heat_flowerdrop,
    ),
    RuleSpec(
        id="chilli-harvest-drying-rain",
        action=FarmAction.HARVEST,
        crop_label="chilli",
        severity=Severity.CAUTION,
        confidence="medium",
        applies_to_crops=frozenset({Crop.CHILLI}),
        months=CHILLI_HARVEST_MONTHS,
        caveat_en=(
            "Only helps if fruit is actually mature — do not harvest immature fruit on a forecast. Rain chance is "
            "from a ~11 km model (no leaf-wetness sensor) that can over- or under-call local showers. Watch the "
            "sky and keep drying chillies covered whenever rain threatens."
        ),
        sources=(
            "https://agritech.tnau.ac.in/crop_protection/chilli_diseases_2.html",
            "https://www.pjtsau.edu.in/files/AgriMkt/2023/December/yasangi-pre-harvest-chilli-2023.pdf",
        ),
        predicate=_chilli_harvest_drying,
    ),
    RuleSpec(
        id="chilli-anthracnose-humid-wet-fruiting",
        action=FarmAction.SCOUT,
        crop_label="chilli",
        severity=Severity.CAUTION,
        confidence="medium",
        applies_to_crops=frozenset({Crop.CHILLI}),
        months=CHILLI_ANTHRAC_MONTHS,
        caveat_en=(
            "Only if the crop is already fruiting/ripening. We cannot measure leaf wetness or see your plants; "
            "humidity and rain are from a ~11 km model that can be wrong and often MISSES local showers, so a quiet "
            "forecast is NOT a guarantee of dry leaves. Decide by what you see, and ask your KVK/agri officer before "
            "any treatment."
        ),
        sources=(
            "https://pmc.ncbi.nlm.nih.gov/articles/PMC5044472/",
            "https://agritech.tnau.ac.in/crop_protection/chilli_diseases_2.html",
        ),
        predicate=_chilli_anthracnose,
    ),
    RuleSpec(
        id="chilli-thrips-dry-warm-leafcurl",
        action=FarmAction.SCOUT,
        crop_label="chilli",
        severity=Severity.INFO,
        confidence="medium",
        applies_to_crops=frozenset({Crop.CHILLI}),
        months=CHILLI_THRIPS_MONTHS,
        caveat_en=(
            "A SCOUT prompt from a ~11 km model (misses local showers), not a spray order or a diagnosis. The local "
            "black thrips also spreads in HUMID/RAINY weather, so NO alert here does NOT mean your crop is safe — "
            "keep checking in wet weather too. Curl can be thrips, mites or virus; take a leaf to your KVK officer "
            "before using any product."
        ),
        sources=(
            "https://agritech.tnau.ac.in/crop_protection/crop_prot_crop_insect-veg_chillies_pest&disease.html",
            "https://www.intechopen.com/chapters/71703",
        ),
        predicate=_chilli_thrips,
    ),
)
