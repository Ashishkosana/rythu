"""The two halves of push alerts (docs/architecture: Async, item 3):

* ``evaluate`` — run by a timer a few times a day: for every farmer who has a phone subscribed, work
  out the alerts due (app/alerts.py) and return them as queue messages. Alerts already sent are
  skipped. One farmer's bad data or a weather outage never stops the others.
* ``deliver`` — run per queue message (the queue gives retries and a poison queue for free): claim
  the alert, send it to each of the farmer's subscribed browsers, drop subscriptions the push service
  says are gone. If nothing could be delivered for a retryable reason, the claim is released and the
  message fails, so the queue tries again later.

Idempotency: an alert key is claimed in the user's partition BEFORE sending, so a retried or
duplicated message never buzzes the phone twice. (A crash between claim and send loses that one
alert — chosen over duplicates.)
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import httpx

from rythu_weather.app.accounts import UserStore
from rythu_weather.app.alerts import due_alerts
from rythu_weather.app.service import get_weather
from rythu_weather.app.webpush import PushRetryable, SubscriptionGone, VapidSigner, send
from rythu_weather.domain.models import Crop, FarmerContext, GeoPoint, ProviderError, WaterSource, WeatherProvider
from rythu_weather.observability import log_event

_log = logging.getLogger(__name__)

IST = ZoneInfo("Asia/Kolkata")
KEEP_SENT_FOR = timedelta(days=30)


async def _forecast(provider: WeatherProvider, profile: dict[str, Any], now: datetime) -> dict[str, Any] | None:
    village = profile.get("village")
    if not village:
        return None
    try:
        crop = Crop(profile["crop"]) if profile.get("crop") else None
        water = WaterSource(profile.get("water") or WaterSource.RAINFED)
    except ValueError:
        crop, water = None, WaterSource.RAINFED
    ctx = FarmerContext(now=now, water_source=water, crop=crop)
    try:
        return await get_weather(provider, GeoPoint(float(village["lat"]), float(village["lon"])), ctx)
    except ProviderError:
        return None  # no forecast → no weather alerts; field-task alerts still go out


async def evaluate(users: UserStore, provider: WeatherProvider, now: datetime) -> list[dict[str, Any]]:
    """Queue messages for every alert due now. ``now`` must be timezone-aware."""
    local = now.astimezone(IST)
    messages: list[dict[str, Any]] = []
    farmers = failed = 0
    async for user_id, profile in users.profiles():
        try:
            if not await users.push_subscriptions(user_id):
                continue  # no phone to tell
            farmers += 1
            await users.prune_alerts(user_id, now - KEEP_SENT_FOR)
            for alert in due_alerts(profile, await _forecast(provider, profile, local), local):
                if not await users.has_alert(user_id, alert.key):
                    messages.append({"user_id": user_id, **asdict(alert)})
        except Exception as exc:  # one farmer's problem must not cost everyone their alerts
            failed += 1
            log_event(_log, logging.ERROR, "alerts.evaluate_failed", error=repr(exc))
    log_event(_log, logging.WARNING if failed else logging.INFO, "alerts.evaluated",
              farmers=farmers, queued=len(messages), failed=failed)
    return messages


async def deliver(
    message: dict[str, Any], users: UserStore, signer: VapidSigner, *, subject: str, now: datetime,
    client: httpx.AsyncClient,
) -> str:
    """Send one queued alert. Returns the outcome; raises PushRetryable to make the queue retry."""
    user_id, key = message["user_id"], message["key"]
    if not await users.claim_alert(user_id, key, now):
        log_event(_log, logging.INFO, "alerts.duplicate", key=key)
        return "duplicate"
    payload = json.dumps(
        {"title": message["title"], "body": message["body"], "url": message["url"], "tag": message["topic"]},
        ensure_ascii=False,
    ).encode("utf-8")
    sent = gone = 0
    retry: str | None = None
    for sub in await users.push_subscriptions(user_id):
        try:
            await send(sub, payload, signer, subject=subject, now=now, client=client, topic=message["topic"])
            sent += 1
        except SubscriptionGone:
            gone += 1
            await users.delete_push_subscription(user_id, sub.endpoint)
        except PushRetryable as exc:
            retry = str(exc)
        except ValueError as exc:  # the push service refused the message itself: retrying won't help
            log_event(_log, logging.ERROR, "alerts.refused", key=key, error=str(exc))
    if sent == 0 and retry is not None:
        await users.release_alert(user_id, key)  # let the queue's retry claim it again
        log_event(_log, logging.WARNING, "alerts.retry", key=key, reason=retry)
        raise PushRetryable(retry)
    log_event(_log, logging.INFO, "alerts.delivered", key=key, sent=sent, gone=gone)
    return "sent" if sent else "undeliverable"
