"""Expert profiles for Arena participants.

This is the Arena-side replacement for the legacy Corsac Expert Network's
`expert_profiles` table (see docs/marketplace/expert-network-arena-audit.md).
It deliberately keeps one identity: a profile hangs off an existing
`pilot_participants` row, so an expert is just a participant with extra,
founder-verified attributes. No second sign-up flow, no credential uploads yet.
"""
from __future__ import annotations

from typing import Literal

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base

Vertical = Literal["accounting", "finance", "legal", "medical", "other"]
RateTier = Literal["standard", "senior", "principal"]
VerificationStatus = Literal["pending", "verified", "declined"]

VERTICALS: tuple[str, ...] = ("accounting", "finance", "legal", "medical", "other")
RATE_TIERS: tuple[str, ...] = ("standard", "senior", "principal")
VERIFICATION_STATUSES: tuple[str, ...] = ("pending", "verified", "declined")


class PilotExpertProfile(Base):
    __tablename__ = "pilot_expert_profiles"

    participant_id: Mapped[str] = mapped_column(ForeignKey("pilot_participants.id"), primary_key=True)
    vertical: Mapped[str] = mapped_column(String)
    specialty: Mapped[str] = mapped_column(String)
    experience: Mapped[str] = mapped_column(String)
    profile_url: Mapped[str | None] = mapped_column(String, nullable=True)
    # Reference the calibrated.co intake submission_id when the expert arrived
    # through the /experts/ interest form, so founder review can join the two.
    intake_reference: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    rate_tier: Mapped[str] = mapped_column(String, default="standard")
    verification_status: Mapped[str] = mapped_column(String, default="pending", index=True)
    verification_note: Mapped[str | None] = mapped_column(String, nullable=True)
    verified_at: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[str] = mapped_column(String)
    updated_at: Mapped[str] = mapped_column(String)


def public_expert(profile: PilotExpertProfile | None) -> dict | None:
    """What the participant themself sees: no founder notes."""
    if profile is None:
        return None
    return {
        "vertical": profile.vertical,
        "specialty": profile.specialty,
        "experience": profile.experience,
        "profile_url": profile.profile_url,
        "rate_tier": profile.rate_tier,
        "verification_status": profile.verification_status,
        "verified_at": profile.verified_at,
        "updated_at": profile.updated_at,
    }


def founder_expert(profile: PilotExpertProfile, email: str | None, name: str | None) -> dict:
    return {
        "participant_id": profile.participant_id,
        "email": email,
        "name": name,
        **{k: v for k, v in public_expert(profile).items()},
        "intake_reference": profile.intake_reference,
        "verification_note": profile.verification_note,
        "created_at": profile.created_at,
    }
