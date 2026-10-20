from dataclasses import dataclass
import base64
import json
import logging
import os

import httpx
from clerk_backend_api import Clerk
from clerk_backend_api.security import AuthenticateRequestOptions
from fastapi import HTTPException, Request

logger = logging.getLogger(__name__)


def _secret_key() -> str:
    # Hosting dashboards make it easy to paste a trailing space or newline. The SDK
    # puts the key in an HTTP header, where that whitespace makes httpx raise.
    return os.getenv("CLERK_SECRET_KEY", "").strip()


def clerk_enabled() -> bool:
    return bool(_secret_key())


def clerk_instance() -> str | None:
    """Which Clerk instance the secret key belongs to, read from its prefix.

    Public config reports this so a deploy can be checked without reading the
    sealed secret. The browser bundle already reveals the same fact through the
    publishable key, so nothing new is exposed.
    """
    secret = _secret_key()
    if not secret:
        return None
    if secret.startswith("sk_live_"):
        return "production"
    if secret.startswith("sk_test_"):
        return "development"
    return "unrecognized"


def authorized_parties() -> list[str]:
    configured = os.getenv("CLERK_AUTHORIZED_PARTIES")
    if configured:
        parties = [origin.strip() for origin in configured.split(",") if origin.strip()]
        if parties:
            return parties
    origins = [
        origin.strip()
        for origin in os.getenv("ARENA_CORS_ORIGINS", "").split(",")
        if origin.strip()
    ]
    origins.extend([
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8021",
        "http://127.0.0.1:8021",
    ])
    return list(dict.fromkeys(origins))


@dataclass(frozen=True)
class ClerkIdentity:
    user_id: str
    email: str
    email_verified: bool
    name: str


def _unverified_claim(request: Request, claim: str) -> str | None:
    """Read a claim from the bearer token without verifying it, for diagnostics only."""
    token = request.headers.get("authorization", "").removeprefix("Bearer ").strip()
    try:
        payload = token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        return json.loads(base64.urlsafe_b64decode(payload)).get(claim)
    except Exception:
        return None


def verify_clerk_request(request: Request) -> ClerkIdentity:
    secret = _secret_key()
    try:
        sdk = Clerk(bearer_auth=secret)
        clerk_request = httpx.Request(
            method=request.method,
            url=str(request.url),
            headers=dict(request.headers),
        )
        state = sdk.authenticate_request(
            clerk_request,
            AuthenticateRequestOptions(
                secret_key=secret,
                authorized_parties=authorized_parties(),
                jwt_key=os.getenv("CLERK_JWT_KEY") or None,
            ),
        )
    except Exception as exc:
        # Log the type only: some messages (httpx header errors) echo the secret key.
        logger.error("Clerk token check failed: %s", type(exc).__name__)
        raise HTTPException(
            503, "Sign-in is temporarily unavailable. Please try again."
        ) from exc
    if not state.is_signed_in or not state.payload or not state.payload.get("sub"):
        # The reason (expired token, unauthorized party, ...) is operational, not for the user.
        logger.warning(
            "Clerk sign-in rejected: %s (azp=%s, allowed=%s)",
            getattr(state, "reason", None),
            _unverified_claim(request, "azp"),
            authorized_parties(),
        )
        raise HTTPException(
            401, "Your sign-in could not be verified. Please sign in again."
        )

    try:
        user = sdk.users.get(user_id=state.payload["sub"])
        primary_id = user.primary_email_address_id
        primary = next(
            (address for address in user.email_addresses if address.id == primary_id),
            None,
        )
        email = primary.email_address.strip().lower() if primary else ""
        verified = bool(
            primary
            and primary.verification
            and primary.verification.status == "verified"
        )
        # Names are not collected; ignore any that Google or Microsoft supply.
        name = email.partition("@")[0]
    except Exception as exc:
        logger.error("Clerk user lookup failed: %s", type(exc).__name__)
        raise HTTPException(
            503, "Sign-in is temporarily unavailable. Please try again."
        ) from exc

    return ClerkIdentity(
        user_id=state.payload["sub"],
        email=email,
        email_verified=verified,
        name=name,
    )
