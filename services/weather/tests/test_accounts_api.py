"""/v1/devices, /v1/sessions, /v1/me — including the authorization boundary (ADR 0004)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import httpx
import pytest

from rythu_weather.adapters.budget import InMemoryUpstreamBudget
from rythu_weather.adapters.fake import FakeProvider
from rythu_weather.api.app import create_app
from rythu_weather.app.accounts import InMemoryUserStore, TokenSigner
from rythu_weather.app.composition import Accounts

PROFILE = {
    "village": {"name": "రేగొండ", "lat": 18.2378, "lon": 79.775},
    "crop": "chilli",
    "water": "borewell",
    "lang": "te",
}


class Clock:
    def __init__(self) -> None:
        self.now = datetime(2026, 10, 26, 6, 0, tzinfo=UTC)

    def __call__(self) -> datetime:
        return self.now


@pytest.fixture
def clock() -> Clock:
    return Clock()


@pytest.fixture
def accounts() -> Accounts:
    return Accounts(InMemoryUserStore(), TokenSigner(b"k" * 32), InMemoryUpstreamBudget(), registrations_per_hour=5)


@pytest.fixture
async def client(accounts, clock):
    app = create_app(FakeProvider(None), object(), accounts, clock)  # type: ignore[arg-type]
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as c:
        yield c


async def _device(client) -> tuple[str, dict[str, str]]:
    reg = await client.post("/v1/devices")
    assert reg.status_code == 201
    creds = reg.json()
    sess = await client.post("/v1/sessions", json=creds)
    assert sess.status_code == 200
    return creds["user_id"], {"Authorization": f"Bearer {sess.json()['token']}"}


async def test_register_session_and_profile_round_trip(client) -> None:
    reg = await client.post("/v1/devices")
    assert reg.headers["Cache-Control"] == "no-store"
    creds = reg.json()
    assert set(creds) == {"user_id", "device_secret"}

    sess = await client.post("/v1/sessions", json=creds)
    assert sess.json()["expires_at"] == "2026-10-26T07:00:00+00:00"
    auth = {"Authorization": f"Bearer {sess.json()['token']}"}

    assert (await client.get("/v1/me/profile", headers=auth)).status_code == 404
    put = await client.put("/v1/me/profile", json=PROFILE, headers={**auth, "If-None-Match": "*"})
    assert put.status_code == 200
    etag = put.headers["ETag"]
    got = await client.get("/v1/me/profile", headers=auth)
    assert got.json() == {**PROFILE, "updated_at": "2026-10-26T06:00:00+00:00"}
    assert got.headers["ETag"] == etag
    assert got.headers["Cache-Control"] == "no-store"

    upd = await client.put("/v1/me/profile", json={**PROFILE, "lang": "en"}, headers={**auth, "If-Match": etag})
    assert upd.status_code == 200 and upd.headers["ETag"] != etag
    stale = await client.put("/v1/me/profile", json=PROFILE, headers={**auth, "If-Match": etag})
    assert (stale.status_code, stale.json()["code"]) == (412, "precondition_failed")


async def test_user_a_can_never_reach_user_b(client) -> None:
    """IDOR: identity comes only from the verified token — there is no user id to tamper with."""
    a_id, a = await _device(client)
    b_id, b = await _device(client)
    await client.put("/v1/me/profile", json=PROFILE, headers={**b, "If-None-Match": "*"})

    # A sees nothing of B's, cannot overwrite it, and deleting A leaves B whole.
    assert (await client.get("/v1/me/profile", headers=a)).status_code == 404
    await client.put("/v1/me/profile", json={**PROFILE, "crop": "paddy"}, headers={**a, "If-None-Match": "*"})
    assert (await client.get("/v1/me/profile", headers=b)).json()["crop"] == "chilli"
    assert (await client.delete("/v1/me", headers=a)).status_code == 204
    assert (await client.get("/v1/me/profile", headers=b)).json()["crop"] == "chilli"

    # Smuggling B's id anywhere changes nothing: the body schema forbids unknown fields …
    sneaky = await client.put("/v1/me/profile", json={**PROFILE, "user_id": b_id}, headers={**a, "If-None-Match": "*"})
    assert (sneaky.status_code, sneaky.json()["code"]) == (400, "bad_request")
    # … and A's secret does not open B's session.
    a_secret = (await client.post("/v1/devices")).json()["device_secret"]
    assert (await client.post("/v1/sessions", json={"user_id": b_id, "device_secret": a_secret})).status_code == 401
    assert a_id != b_id


@pytest.mark.parametrize(
    "headers",
    [{}, {"Authorization": "Bearer"}, {"Authorization": "Basic abc"}, {"Authorization": "Bearer v1.x.1.y"}],
)
async def test_me_routes_need_a_valid_token(client, headers) -> None:
    for method, path in (("GET", "/v1/me/profile"), ("PUT", "/v1/me/profile"), ("DELETE", "/v1/me")):
        resp = await client.request(method, path, headers=headers, json=PROFILE if method == "PUT" else None)
        assert resp.status_code == 401, (method, path)
        assert resp.json()["code"] == "unauthorized"
        assert resp.headers["WWW-Authenticate"].startswith("Bearer")


async def test_tokens_expire_and_deleted_users_cannot_write(client, clock) -> None:
    _, auth = await _device(client)
    clock.now += timedelta(hours=1, seconds=1)
    assert (await client.get("/v1/me/profile", headers=auth)).status_code == 401

    _, auth = await _device(client)
    assert (await client.delete("/v1/me", headers=auth)).status_code == 204
    late = await client.put("/v1/me/profile", json=PROFILE, headers={**auth, "If-None-Match": "*"})
    assert late.status_code == 401  # the token is still in date, the user is not


async def test_wrong_secret_and_unknown_user_get_the_same_answer(client) -> None:
    creds = (await client.post("/v1/devices")).json()
    wrong = await client.post("/v1/sessions", json={**creds, "device_secret": "x" * 43})
    unknown = await client.post("/v1/sessions", json={"user_id": "0" * 32, "device_secret": "x" * 43})
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json()


async def test_profile_writes_validate_and_need_a_precondition(client) -> None:
    _, auth = await _device(client)
    none = await client.put("/v1/me/profile", json=PROFILE, headers=auth)
    assert (none.status_code, none.json()["code"]) == (428, "precondition_required")
    chennai = {**PROFILE, "village": {"name": "Chennai", "lat": 13.08, "lon": 80.27}}
    out = await client.put("/v1/me/profile", json=chennai, headers={**auth, "If-None-Match": "*"})
    assert (out.status_code, out.json()["code"]) == (400, "outside_coverage")
    bad_bodies = (
        {**PROFILE, "crop": "banana"},
        {**PROFILE, "lang": "hi"},
        {**PROFILE, "village": {"name": "", "lat": 18, "lon": 79}},
    )
    for bad in bad_bodies:
        resp = await client.put("/v1/me/profile", json=bad, headers={**auth, "If-None-Match": "*"})
        assert (resp.status_code, resp.json()["code"]) == (400, "bad_request"), bad
    assert "banana" not in (await client.put(
        "/v1/me/profile", json={**PROFILE, "crop": "banana"}, headers={**auth, "If-None-Match": "*"}
    )).text  # the reason, never the submitted value


async def test_registrations_are_rate_limited(client) -> None:
    codes = [(await client.post("/v1/devices")).status_code for _ in range(6)]
    assert codes == [201] * 5 + [429]


async def test_accounts_switched_off_answer_503_and_weather_still_works() -> None:
    app = create_app(FakeProvider(None), object(), None)  # type: ignore[arg-type]
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as c:
        resp = await c.post("/v1/devices")
        assert (resp.status_code, resp.json()["code"]) == (503, "unavailable")
        assert (await c.get("/healthz")).status_code == 200


async def test_a_failing_store_is_an_outage_not_a_crash(accounts, client) -> None:
    async def broken(*_a, **_k):
        raise TimeoutError("table storage slow")

    accounts.users.secret_hash = broken  # type: ignore[method-assign]
    resp = await client.post("/v1/sessions", json={"user_id": "0" * 32, "device_secret": "x" * 43})
    assert (resp.status_code, resp.json()["code"]) == (503, "unavailable")


async def test_the_browser_may_send_what_profile_sync_needs(client) -> None:
    """The web app is on another origin: its preflight must allow the auth and precondition headers,
    and it must be able to read the ETag it has to send back."""
    for method, headers in (("PUT", "authorization,content-type,if-none-match"), ("PUT", "authorization,if-match"),
                            ("DELETE", "authorization"), ("POST", "content-type")):
        pre = await client.options("/v1/me/profile", headers={
            "Origin": "https://rythu.example", "Access-Control-Request-Method": method,
            "Access-Control-Request-Headers": headers,
        })
        assert pre.status_code == 200, (method, headers)
    _, auth = await _device(client)
    put = await client.put("/v1/me/profile", json=PROFILE, headers={**auth, "If-None-Match": "*", "Origin": "https://rythu.example"})
    assert "etag" in put.headers["Access-Control-Expose-Headers"].lower()
