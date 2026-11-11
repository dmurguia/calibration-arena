"""Expert profiles: one identity, participant self-report, founder verification."""
from __future__ import annotations

import pytest

from app.pilot_accounts import reset_limits

ADMIN_TOKEN = "a-long-private-test-admin-token"


@pytest.fixture(autouse=True)
def _fresh_limits():
    # Sign-ups share one per-IP window with the rest of the session; don't
    # spend the sprint tests' guest budget.
    reset_limits()
    yield
    reset_limits()


def signed_in(client, email):
    r = client.post("/api/pilot/auth/signup", json={
        "email": email, "password": "correct horse battery staple 42",
        "name": "Expert Person", "role": "Public accountant", "experience": "8–15 years",
        "framework": "US GAAP",
    })
    assert r.status_code == 200, r.text
    return {"Authorization": "Bearer " + r.json()["token"]}


def guest(client):
    r = client.post("/api/pilot/guests", json={"source": "qa-experts"})
    assert r.status_code == 200, r.text
    return {"Authorization": "Bearer " + r.json()["token"]}


PROFILE = {
    "vertical": "accounting",
    "specialty": "Revenue recognition for SaaS",
    "experience": "Twelve years closing the books for subscription businesses under ASC 606.",
    "profile_url": "https://example.com/people/expert",
    "intake_reference": "3F2504E0-4F89-41D3-9A0C-0305E82C3301",
}


def test_guest_cannot_submit_expert_profile(client):
    r = client.post("/api/pilot/expert-profile", headers=guest(client), json=PROFILE)
    assert r.status_code == 403


def test_profile_round_trip_and_me(client):
    h = signed_in(client, "expert-one@example.com")
    r = client.post("/api/pilot/expert-profile", headers=h, json=PROFILE)
    assert r.status_code == 200, r.text
    expert = r.json()["expert"]
    assert expert["verification_status"] == "pending" and expert["rate_tier"] == "standard"
    assert "verification_note" not in expert and "intake_reference" not in expert
    me = client.get("/api/pilot/me", headers=h).json()
    assert me["expert"]["specialty"] == PROFILE["specialty"]


def test_rejects_unsafe_profile_url_and_bad_reference(client):
    h = signed_in(client, "expert-two@example.com")
    bad = {**PROFILE, "profile_url": "http://example.com/x"}
    assert client.post("/api/pilot/expert-profile", headers=h, json=bad).status_code == 422
    bad = {**PROFILE, "profile_url": "https://user:pw@example.com/x"}
    assert client.post("/api/pilot/expert-profile", headers=h, json=bad).status_code == 422
    bad = {**PROFILE, "intake_reference": "not-a-uuid"}
    assert client.post("/api/pilot/expert-profile", headers=h, json=bad).status_code == 422
    bad = {**PROFILE, "vertical": "astrology"}
    assert client.post("/api/pilot/expert-profile", headers=h, json=bad).status_code == 422


def test_founder_lists_and_verifies_then_edit_resets(client, monkeypatch):
    monkeypatch.setenv("PILOT_ADMIN_TOKEN", ADMIN_TOKEN)
    admin = {"X-Pilot-Admin": ADMIN_TOKEN}
    h = signed_in(client, "expert-three@example.com")
    pid = client.get("/api/pilot/me", headers=h).json()["participant"]["id"]
    client.post("/api/pilot/expert-profile", headers=h, json=PROFILE)

    assert client.get("/api/pilot/founder/experts").status_code == 403
    listed = client.get("/api/pilot/founder/experts", headers=admin, params={"status": "pending"}).json()["experts"]
    row = next(e for e in listed if e["participant_id"] == pid)
    assert row["email"] == "expert-three@example.com"
    assert row["intake_reference"] == PROFILE["intake_reference"].lower()
    assert client.get("/api/pilot/founder/experts", headers=admin, params={"status": "bogus"}).status_code == 422

    r = client.post(f"/api/pilot/founder/experts/{pid}/verification", headers=admin,
                    json={"verification_status": "verified", "rate_tier": "senior", "note": "CPA confirmed"})
    assert r.status_code == 200, r.text
    assert r.json()["expert"]["verification_status"] == "verified" and r.json()["expert"]["rate_tier"] == "senior"
    me = client.get("/api/pilot/me", headers=h).json()["expert"]
    assert me["verification_status"] == "verified" and me["verified_at"]

    # Editing a verified claim sends it back for review but keeps the tier.
    client.post("/api/pilot/expert-profile", headers=h, json={**PROFILE, "specialty": "Lease accounting"})
    me = client.get("/api/pilot/me", headers=h).json()["expert"]
    assert me["verification_status"] == "pending" and me["verified_at"] is None and me["rate_tier"] == "senior"

    assert client.post("/api/pilot/founder/experts/nobody/verification", headers=admin,
                       json={"verification_status": "declined"}).status_code == 404
