"""Which alerts a farmer should get now — pure, so the rules are tested without a phone or a queue.

Inputs are what the server already knows, with consent: the profile (village, crop, water source,
language, fields) and the forecast contract for that village and crop. Three kinds, most urgent first:

1. the weather engine's own "act now" reads for their crop (e.g. "don't spray: rain coming") — the
   same rules the app shows, so an alert never says something the screen doesn't;
2. rain likely (≥ 70 %) in the next 12 hours;
3. a My-Field calendar task starting today or tomorrow.

Each alert has a KEY that is unique per user and occasion (a day, a half-day, a task), so the sender
can make delivery idempotent: the same alert is never sent twice. At most ``MAX_PER_RUN`` per run —
a phone that buzzes all day gets switched off.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any

from rythu_weather.domain.calendar import plan
from rythu_weather.domain.models import Crop

RAIN_ALERT_PCT = 70
RAIN_WINDOW_HOURS = 12
MAX_PER_RUN = 3


@dataclass(frozen=True, slots=True)
class Alert:
    key: str  # idempotency key, unique per user and occasion
    priority: int  # 0 = most urgent
    title: str
    body: str
    url: str  # where tapping the notification opens the app
    topic: str  # a newer alert on the same topic replaces an undelivered older one


def _pick(lang: str, te: str, en: str) -> str:
    return te if lang == "te" and te else en


def _place(profile: dict[str, Any]) -> str:
    village = profile.get("village") or {}
    return str(village.get("name") or "")


def _advice(contract: dict[str, Any], lang: str, today: date) -> list[Alert]:
    out = []
    for read in contract.get("farming_read", []):
        if read.get("triggered") and read.get("severity") == "act":
            out.append(Alert(
                key=f"read.{read['id']}.{today.isoformat()}",
                priority=0,
                title=_pick(lang, read.get("headline_te", ""), read["headline_en"]),
                body=_pick(lang, read.get("detail_te", ""), read["detail_en"]),
                url="/",
                topic="advice",
            ))
    return out


def _rain(contract: dict[str, Any], profile: dict[str, Any], lang: str, now: datetime) -> list[Alert]:
    probs = [h.get("precipitation_probability") for h in contract.get("hourly_rain", [])[:RAIN_WINDOW_HOURS]]
    known = [p for p in probs if isinstance(p, int)]
    if not known or max(known) < RAIN_ALERT_PCT:
        return []
    chance, place = max(known), _place(profile)
    half = "am" if now.hour < 12 else "pm"
    te_where, en_where = (f"{place}: ", f"{place}: ") if place else ("", "")
    return [Alert(
        key=f"rain.{now.date().isoformat()}.{half}",
        priority=1,
        title=_pick(lang, f"వర్షం రావచ్చు — {chance}%", f"Rain likely — {chance}%"),
        body=_pick(
            lang,
            f"{te_where}రాబోయే 12 గంటల్లో {chance}% వర్షం అవకాశం.",
            f"{en_where}{chance}% chance of rain in the next 12 hours.",
        ),
        url="/",
        topic="rain",
    )]


def _tasks(profile: dict[str, Any], lang: str, today: date) -> list[Alert]:
    out = []
    tomorrow = today + timedelta(days=1)
    for field in profile.get("fields") or []:
        try:
            crop, ref = Crop(field["crop"]), date.fromisoformat(field["reference_date"])
        except (KeyError, ValueError):
            continue  # a malformed field must not block everyone else's alerts
        for task in plan(crop, ref):
            if task.start not in (today, tomorrow):
                continue
            s = task.spec
            when = _pick(lang, "ఈరోజు" if task.start == today else "రేపు", "Today" if task.start == today else "Tomorrow")
            out.append(Alert(
                key=f"task.{field['id']}.{s.id}.{task.start.isoformat()}",
                priority=2,
                title=f"{field.get('name', '')}: {_pick(lang, s.title_te, s.title_en)}",
                body=f"{when}: {_pick(lang, s.detail_te, s.detail_en)}",
                url="/field/",
                topic=f"task-{field['id']}",
            ))
    return out


def due_alerts(profile: dict[str, Any], contract: dict[str, Any] | None, now: datetime) -> list[Alert]:
    """The alerts due for one farmer at ``now`` (local time), most urgent first, at most MAX_PER_RUN.

    ``contract`` is the forecast for their village and crop; None (no village saved, or upstream
    down) means weather alerts are skipped — never guessed. A degraded forecast counts as None.
    """
    lang = profile.get("lang") or "te"
    alerts: list[Alert] = []
    if contract is not None and not contract.get("degraded"):
        alerts += _advice(contract, lang, now.date())
        alerts += _rain(contract, profile, lang, now)
    alerts += _tasks(profile, lang, now.date())
    return sorted(alerts, key=lambda a: (a.priority, a.key))[:MAX_PER_RUN]
