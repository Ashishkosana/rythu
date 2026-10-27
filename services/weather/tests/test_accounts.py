"""Device credentials, tokens, and the UserStore contract (in-memory AND Azure Table on Azurite)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest

from rythu_weather.app.accounts import (
    InMemoryUserStore,
    PreconditionFailed,
    TokenSigner,
    Unauthorized,
    is_user_id,
    new_credentials,
    secret_digest,
)
from test_cache_store_contract import AZURITE, _azurite_running

NOW = datetime(2026, 10, 26, 6, 0, tzinfo=UTC)
KEY = b"k" * 32


# --- credentials + tokens --------------------------------------------------------------------------


def test_credentials_are_random_and_only_a_digest_is_kept() -> None:
    a, b = new_credentials(), new_credentials()
    assert is_user_id(a.user_id) and a.user_id != b.user_id
    assert len(a.device_secret) >= 43 and a.device_secret != b.device_secret  # 256 bits
    assert secret_digest(a.device_secret) != a.device_secret
    assert len(secret_digest(a.device_secret)) == 64


def test_token_round_trip_and_expiry() -> None:
    signer = TokenSigner(KEY)
    uid = new_credentials().user_id
    token, expires = signer.issue(uid, NOW)
    assert expires == NOW + timedelta(hours=1)
    assert signer.verify(token, NOW + timedelta(minutes=59)) == uid
    with pytest.raises(Unauthorized):
        signer.verify(token, NOW + timedelta(hours=1))


@pytest.mark.parametrize(
    "mutate",
    [
        lambda t: t[:-2] + ("AA" if not t.endswith("AA") else "BB"),  # forged signature
        lambda t: t.replace("v1.", "v2.", 1),
        lambda t: ".".join(t.split(".")[:3]),  # signature stripped
        lambda t: "v1." + "0" * 32 + "." + ".".join(t.split(".")[2:]),  # someone else's user id, old signature
        lambda t: "v1." + t.split(".")[1] + ".99999999999." + t.split(".")[3],  # extended expiry
        lambda t: "",
        lambda t: "Bearer " + t,
    ],
)
def test_tampered_tokens_are_refused(mutate) -> None:
    signer = TokenSigner(KEY)
    token, _ = signer.issue(new_credentials().user_id, NOW)
    with pytest.raises(Unauthorized):
        signer.verify(mutate(token), NOW)


def test_a_token_from_another_key_is_refused_and_the_key_never_prints() -> None:
    token, _ = TokenSigner(b"x" * 32).issue(new_credentials().user_id, NOW)
    with pytest.raises(Unauthorized):
        TokenSigner(KEY).verify(token, NOW)
    assert "kkkk" not in repr(TokenSigner(KEY))
    with pytest.raises(ValueError):
        TokenSigner(b"short")


# --- UserStore contract ----------------------------------------------------------------------------


@pytest.fixture(params=["in_memory", "azure_table"])
def users(request):
    if request.param == "in_memory":
        return InMemoryUserStore()
    if not _azurite_running():
        import os

        if os.environ.get("RYTHU_REQUIRE_AZURITE") == "1":
            pytest.fail("RYTHU_REQUIRE_AZURITE=1 but Azurite is not reachable on 127.0.0.1:10002")
        pytest.skip("Azurite not running")
    from rythu_weather.adapters.azure_table import AzureTableUserStore, TableAuth

    return AzureTableUserStore(TableAuth(connection_string=AZURITE), f"u{uuid.uuid4().hex[:24]}")


async def test_store_keeps_the_secret_digest(users) -> None:
    uid = new_credentials().user_id
    assert await users.secret_hash(uid) is None
    await users.create_user(uid, "ab" * 32, NOW)
    assert await users.secret_hash(uid) == "ab" * 32


async def test_profile_writes_are_conditional(users) -> None:
    uid = new_credentials().user_id
    await users.create_user(uid, "ab" * 32, NOW)
    assert await users.get_profile(uid) is None
    with pytest.raises(PreconditionFailed):  # nothing to update yet
        await users.put_profile(uid, {"lang": "te"}, if_match='W/"1"', create_only=False)

    etag1 = await users.put_profile(uid, {"lang": "te", "village": {"name": "రేగొండ"}}, if_match=None, create_only=True)
    assert await users.get_profile(uid) == ({"lang": "te", "village": {"name": "రేగొండ"}}, etag1)
    with pytest.raises(PreconditionFailed):  # create only once
        await users.put_profile(uid, {"lang": "en"}, if_match=None, create_only=True)

    etag2 = await users.put_profile(uid, {"lang": "en"}, if_match=etag1, create_only=False)
    assert etag2 != etag1
    with pytest.raises(PreconditionFailed):  # a stale version loses
        await users.put_profile(uid, {"lang": "te"}, if_match=etag1, create_only=False)
    with pytest.raises(PreconditionFailed):  # so does no version, or a made-up one
        await users.put_profile(uid, {"lang": "te"}, if_match=None, create_only=False)
    with pytest.raises(PreconditionFailed):
        await users.put_profile(uid, {"lang": "te"}, if_match='W/"garbage"', create_only=False)
    assert (await users.get_profile(uid)) == ({"lang": "en"}, etag2)


async def test_users_are_isolated_and_delete_removes_everything(users) -> None:
    a, b = new_credentials().user_id, new_credentials().user_id
    for uid in (a, b):
        await users.create_user(uid, secret_digest(uid), NOW)
        await users.put_profile(uid, {"lang": uid[:2]}, if_match=None, create_only=True)
    assert await users.delete_user(a) == 2
    assert await users.secret_hash(a) is None
    assert await users.get_profile(a) is None
    assert (await users.get_profile(b))[0] == {"lang": b[:2]}  # untouched
    assert await users.delete_user(a) == 0


# --- push subscriptions, profile scan, alert claims (same contract, both stores) -------------------

from rythu_weather.app.push_subscription import Subscription  # noqa: E402

SUB_A = Subscription("https://fcm.googleapis.com/fcm/send/aaa", "p" * 87, "a" * 22)
SUB_B = Subscription("https://fcm.googleapis.com/fcm/send/bbb", "q" * 87, "b" * 22)


async def test_push_subscriptions_upsert_by_endpoint_and_delete(users) -> None:
    uid = new_credentials().user_id
    await users.create_user(uid, "ab" * 32, NOW)
    assert await users.push_subscriptions(uid) == []
    await users.put_push_subscription(uid, SUB_A, NOW)
    await users.put_push_subscription(uid, SUB_A, NOW)  # same endpoint: replaced, not duplicated
    await users.put_push_subscription(uid, SUB_B, NOW)
    assert sorted(s.endpoint for s in await users.push_subscriptions(uid)) == [SUB_A.endpoint, SUB_B.endpoint]
    await users.delete_push_subscription(uid, SUB_A.endpoint)
    await users.delete_push_subscription(uid, SUB_A.endpoint)  # already gone: fine
    assert await users.push_subscriptions(uid) == [SUB_B]
    assert await users.delete_user(uid) == 2  # device + subscription: delete-my-data covers it


async def test_profiles_lists_only_users_with_a_profile(users) -> None:
    with_profile, without = new_credentials().user_id, new_credentials().user_id
    for uid in (with_profile, without):
        await users.create_user(uid, "ab" * 32, NOW)
    await users.put_profile(with_profile, {"lang": "te"}, if_match=None, create_only=True)
    found = {uid: p async for uid, p in users.profiles()}
    assert found.get(with_profile) == {"lang": "te"}
    assert without not in found


async def test_alert_claims_are_idempotent_releasable_and_pruned(users) -> None:
    uid = new_credentials().user_id
    await users.create_user(uid, "ab" * 32, NOW)
    key = "rain.2026-10-27.am"
    assert not await users.has_alert(uid, key)
    assert await users.claim_alert(uid, key, NOW) is True
    assert await users.claim_alert(uid, key, NOW) is False  # already sent (or being sent)
    assert await users.has_alert(uid, key)
    await users.release_alert(uid, key)  # sending failed: a retry may claim again
    assert await users.claim_alert(uid, key, NOW) is True
    await users.claim_alert(uid, "task.f1a2b3.cotton.split1", NOW - timedelta(days=40))
    assert await users.prune_alerts(uid, NOW - timedelta(days=30)) == 1
    assert await users.has_alert(uid, key)  # the recent one stays
