from dataclasses import dataclass
import os

import httpx
from clerk_backend_api import Clerk
from clerk_backend_api.security import AuthenticateRequestOptions
from fastapi import HTTPException, Request


def clerk_enabled() -> bool:
    return bool(os.getenv("CLERK_SECRET_KEY"))


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


def verify_clerk_request(request: Request) -> ClerkIdentity:
    secret = os.getenv("CLERK_SECRET_KEY", "")
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
        raise HTTPException(
            503, "Sign-in is temporarily unavailable. Please try again."
        ) from exc
    if not state.is_signed_in or not state.payload or not state.payload.get("sub"):
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
        raise HTTPException(
            503, "Sign-in is temporarily unavailable. Please try again."
        ) from exc

    return ClerkIdentity(
        user_id=state.payload["sub"],
        email=email,
        email_verified=verified,
        name=name,
    )
