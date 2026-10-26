"""Device accounts and the user's own data (ADR 0004):

    POST   /v1/devices      register this phone → user id + device secret (rate-limited)
    POST   /v1/sessions     device secret → one-hour bearer token
    GET    /v1/me/profile   the saved profile, with its ETag
    PUT    /v1/me/profile   save it: If-None-Match: * to create, If-Match: <etag> to update
    DELETE /v1/me           erase everything stored for this user (DPDP Act: delete my data)

The user is ALWAYS the one in the verified token; no route takes a user id from the path or body
(tests/test_accounts_api.py checks that A cannot touch B). Private data is never cached (no-store).

No ``from __future__ import annotations`` here: FastAPI reads route annotations at runtime, and the
auth dependency is local to ``accounts_router``.
"""

import hashlib
import hmac
import logging
from collections.abc import Awaitable, Callable
from datetime import datetime
from typing import Annotated, Any, NoReturn

from fastapi import APIRouter, Depends, Header
from fastapi.responses import JSONResponse, Response

from rythu_weather.adapters.budget import BudgetContention, window_key
from rythu_weather.api.schemas import DeviceCredentialsOut, ErrorBody, ProfileIn, ProfileOut, SessionIn, SessionOut
from rythu_weather.app.accounts import PreconditionFailed, Unauthorized, new_credentials, secret_digest, utc_now
from rythu_weather.app.composition import Accounts
from rythu_weather.domain.coverage import in_coverage
from rythu_weather.observability import log_event

_log = logging.getLogger(__name__)

_PRIVATE = {"Cache-Control": "no-store"}


class ApiError(Exception):
    """An answer other than success, carried to the app's handler: status + stable code + headers."""

    def __init__(self, status: int, code: str, message: str, headers: dict[str, str] | None = None) -> None:
        super().__init__(message)
        self.status, self.code, self.headers = status, code, headers or {}


def error_response(exc: ApiError) -> JSONResponse:
    body = {"error": str(exc), "code": exc.code}
    return JSONResponse(body, status_code=exc.status, headers={**_PRIVATE, **exc.headers})


def _unauthorized() -> NoReturn:
    raise ApiError(401, "unauthorized", "sign in again", {"WWW-Authenticate": 'Bearer error="invalid_token"'})


def _pseudonym(user_id: str) -> str:
    """For logs: enough to follow one user's requests, not the id itself."""
    return hashlib.sha256(user_id.encode()).hexdigest()[:12]


def _err(description: str) -> dict[str, Any]:
    return {"model": ErrorBody, "description": description}


def accounts_router(accounts: Accounts | None, clock: Callable[[], datetime] = utc_now) -> APIRouter:
    router = APIRouter(tags=["me"])

    def enabled() -> Accounts:
        if accounts is None:
            raise ApiError(503, "unavailable", "accounts are not available right now")
        return accounts

    async def guarded[T](action: str, call: Awaitable[T]) -> T:
        """A store failure is an outage (503), never a 500 or a wrong answer."""
        try:
            return await call
        except (ApiError, PreconditionFailed):
            raise
        except Exception as exc:
            log_event(_log, logging.ERROR, "accounts.store_failed", action=action, error=repr(exc))
            raise ApiError(503, "unavailable", "please try again shortly") from exc

    def current_user(authorization: Annotated[str | None, Header()] = None) -> str:
        acc = enabled()
        scheme, _, token = (authorization or "").partition(" ")
        if scheme.lower() != "bearer" or not token:
            _unauthorized()
        try:
            return acc.signer.verify(token.strip(), clock())
        except Unauthorized:
            _unauthorized()

    User = Annotated[str, Depends(current_user)]

    @router.post(
        "/v1/devices", status_code=201, response_model=DeviceCredentialsOut, summary="Register this phone",
        responses={429: _err("Too many new devices this hour."), 503: _err("Accounts unavailable.")},
    )
    async def register_device() -> JSONResponse:
        acc = enabled()
        now = clock()
        try:
            allowed = await guarded(
                "register_budget",
                acc.registrations.try_acquire(f"devices#{window_key(now)}", acc.registrations_per_hour),
            )
        except BudgetContention:
            allowed = False
        if not allowed:
            log_event(_log, logging.WARNING, "accounts.registration_refused")
            raise ApiError(429, "rate_limited", "too many new devices right now", {"Retry-After": "600"})
        creds = new_credentials()
        await guarded("create_user", acc.users.create_user(creds.user_id, secret_digest(creds.device_secret), now))
        log_event(_log, logging.INFO, "accounts.registered", user=_pseudonym(creds.user_id))
        body = DeviceCredentialsOut(user_id=creds.user_id, device_secret=creds.device_secret)
        return JSONResponse(body.model_dump(), status_code=201, headers=_PRIVATE)

    @router.post(
        "/v1/sessions", response_model=SessionOut, summary="Trade the device secret for a one-hour token",
        responses={400: _err("Malformed body."), 401: _err("Unknown device or wrong secret.")},
    )
    async def start_session(body: SessionIn) -> JSONResponse:
        acc = enabled()
        stored = await guarded("secret_hash", acc.users.secret_hash(body.user_id))
        # Same answer for "no such user" and "wrong secret"; constant-time comparison of digests.
        if stored is None or not hmac.compare_digest(stored, secret_digest(body.device_secret)):
            log_event(_log, logging.WARNING, "accounts.session_refused")
            _unauthorized()
        token, expires = acc.signer.issue(body.user_id, clock())
        return JSONResponse(SessionOut(token=token, expires_at=expires.isoformat()).model_dump(), headers=_PRIVATE)

    @router.get(
        "/v1/me/profile", response_model=ProfileOut, summary="The profile saved by this device",
        responses={401: _err("Missing or expired token."), 404: _err("Nothing saved yet.")},
    )
    async def get_profile(user: User) -> JSONResponse:
        acc = enabled()
        found = await guarded("get_profile", acc.users.get_profile(user))
        if found is None:
            raise ApiError(404, "not_found", "no profile saved yet")
        profile, etag = found
        return JSONResponse(profile, headers={**_PRIVATE, "ETag": etag})

    @router.put(
        "/v1/me/profile", response_model=ProfileOut, summary="Save the profile (conditional)",
        responses={
            400: _err("Malformed body, or a village outside coverage (code=outside_coverage)."),
            401: _err("Missing or expired token."),
            412: _err("The saved profile changed since you read it (or one already exists)."),
            428: _err("Send If-Match: <etag> to update, or If-None-Match: * to create."),
        },
    )
    async def put_profile(
        body: ProfileIn,
        user: User,
        if_match: Annotated[str | None, Header()] = None,
        if_none_match: Annotated[str | None, Header()] = None,
    ) -> JSONResponse:
        acc = enabled()
        create_only = (if_none_match or "").strip() == "*"
        if not create_only and not if_match:
            raise ApiError(428, "precondition_required", "send If-Match: <etag> or If-None-Match: *")
        if body.village is not None and not in_coverage(body.village.lat, body.village.lon):
            raise ApiError(400, "outside_coverage", "Rythu currently covers Telangana only")
        # A token outlives a deleted account by up to an hour: never write for a user who is gone.
        if await guarded("secret_hash", acc.users.secret_hash(user)) is None:
            _unauthorized()
        stored = {**body.model_dump(mode="json"), "updated_at": clock().isoformat()}
        try:
            etag = await guarded(
                "put_profile", acc.users.put_profile(user, stored, if_match=if_match, create_only=create_only)
            )
        except PreconditionFailed as exc:
            raise ApiError(412, "precondition_failed", "the saved profile changed — read it again") from exc
        return JSONResponse(stored, headers={**_PRIVATE, "ETag": etag})

    @router.delete(
        "/v1/me", status_code=204, summary="Delete everything stored for this user",
        responses={401: _err("Missing or expired token.")},
    )
    async def delete_me(user: User) -> Response:
        acc = enabled()
        removed = await guarded("delete_user", acc.users.delete_user(user))
        log_event(_log, logging.INFO, "accounts.deleted", user=_pseudonym(user), records=removed)
        return Response(status_code=204, headers=_PRIVATE)

    return router
