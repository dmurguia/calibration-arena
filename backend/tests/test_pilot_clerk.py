from types import SimpleNamespace

from fastapi import HTTPException
from sqlalchemy import select

from app import pilot_clerk
from app.db import SessionLocal
from app.pilot_accounts import PilotAccount, reset_limits, verify_password
from app.routers.pilot import Event


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def identity(user_id="user_1", email="clerk@example.com", verified=True, name="Ada Lovelace"):
    return pilot_clerk.ClerkIdentity(user_id, email, verified, name)


def test_blank_authorized_parties_fall_back_to_cors_and_local_origins(monkeypatch):
    monkeypatch.setenv("CLERK_AUTHORIZED_PARTIES", " \t\n")
    monkeypatch.setenv("ARENA_CORS_ORIGINS", "https://pilot.example, https://preview.example")

    assert pilot_clerk.authorized_parties() == [
        "https://pilot.example",
        "https://preview.example",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8021",
        "http://127.0.0.1:8021",
    ]


def exchange(client, guest_token=None):
    return client.post(
        "/api/pilot/auth/clerk",
        json={"guest_token": guest_token},
    )


def test_new_user_and_repeat_exchange(client, monkeypatch):
    reset_limits()
    monkeypatch.setenv("CLERK_SECRET_KEY", "sk_test_dummy")
    current = identity()
    monkeypatch.setattr(pilot_clerk, "verify_clerk_request", lambda request: current)

    first = exchange(client)
    assert first.status_code == 200
    participant_id = first.json()["participant"]["id"]
    me = client.get("/api/pilot/me", headers=auth(first.json()["token"]))
    assert me.json()["account"] == {"email": "clerk@example.com", "provider": "clerk"}

    second = exchange(client)
    assert second.status_code == 200
    assert second.json()["participant"]["id"] == participant_id


def test_exchange_claims_guest_and_rotates_guest_token(client, monkeypatch):
    reset_limits()
    monkeypatch.setenv("CLERK_SECRET_KEY", "sk_test_dummy")
    current = identity(user_id="guest_claim_user", email="guest-claim@example.com")
    monkeypatch.setattr(pilot_clerk, "verify_clerk_request", lambda request: current)
    guest = client.post("/api/pilot/guests", json={}).json()
    case = client.get("/api/pilot/cases").json()[0]
    run = client.post(
        "/api/pilot/runs",
        headers=auth(guest["token"]),
        json={"case_id": case["id"], "independent_first": False},
    ).json()

    response = exchange(client, guest["token"])
    assert response.status_code == 200
    assert response.json()["participant"]["id"] == guest["participant"]["id"]
    me = client.get("/api/pilot/me", headers=auth(response.json()["token"]))
    assert run["id"] in {item["id"] for item in me.json()["runs"]}
    assert client.get("/api/pilot/me", headers=auth(guest["token"])).status_code == 401


def test_verified_email_links_password_account_and_unverified_is_rejected(client, monkeypatch):
    reset_limits()
    monkeypatch.delenv("CLERK_SECRET_KEY", raising=False)
    password_account = client.post("/api/pilot/auth/signup", json={
        "name": "Password user",
        "email": "link@example.com",
        "password": "long-enough-password",
    }).json()
    monkeypatch.setenv("CLERK_SECRET_KEY", "sk_test_dummy")
    current = identity(user_id="user_link", email="link@example.com")
    monkeypatch.setattr(pilot_clerk, "verify_clerk_request", lambda request: current)

    response = exchange(client)
    assert response.status_code == 200
    assert response.json()["participant"]["id"] == password_account["participant"]["id"]
    me = client.get("/api/pilot/me", headers=auth(response.json()["token"]))
    assert me.json()["account"]["provider"] == "clerk"
    with SessionLocal() as db:
        account = db.get(PilotAccount, password_account["participant"]["id"])
        assert account.clerk_user_id == "user_link"
        assert db.scalar(select(Event).where(
            Event.participant_id == account.participant_id,
            Event.name == "account_linked",
        ))

    unverified = identity(user_id="user_unverified", email="unverified@example.com", verified=False)
    monkeypatch.setattr(pilot_clerk, "verify_clerk_request", lambda request: unverified)
    rejected = exchange(client)
    assert rejected.status_code == 403
    assert rejected.json()["detail"] == "Verify your email address to continue."


def test_email_linked_to_different_clerk_identity_conflicts(client, monkeypatch):
    reset_limits()
    monkeypatch.setenv("CLERK_SECRET_KEY", "sk_test_dummy")
    current = identity(user_id="first_user", email="same@example.com")
    monkeypatch.setattr(pilot_clerk, "verify_clerk_request", lambda request: current)
    assert exchange(client).status_code == 200

    another = identity(user_id="different_user", email="same@example.com")
    monkeypatch.setattr(pilot_clerk, "verify_clerk_request", lambda request: another)
    response = exchange(client)
    assert response.status_code == 409
    assert response.json()["detail"] == "This email is already linked to another sign-in."


def test_password_routes_are_disabled_when_clerk_is_enabled(client, monkeypatch):
    reset_limits()
    monkeypatch.setenv("CLERK_SECRET_KEY", "sk_test_dummy")
    login = client.post("/api/pilot/auth/login", json={
        "email": "person@example.com", "password": "long-enough-password",
    })
    signup = client.post("/api/pilot/auth/signup", json={
        "name": "Person", "email": "person@example.com", "password": "long-enough-password",
    })
    assert login.status_code == signup.status_code == 410
    assert login.json()["detail"] == "Password sign-in has been replaced. Use Sign in to continue."
    assert client.post("/api/pilot/auth/reset", json={
        "token": "reset-token", "password": "long-enough-password",
    }).status_code == 410
    reset_link = client.post("/api/pilot/founder/reset-link", json={
        "email": "person@example.com",
    })
    assert reset_link.status_code == 410
    assert reset_link.json()["detail"] == "Password resets are handled by the sign-in provider."
    assert client.get("/api/pilot/config").json()["auth_provider"] == "clerk"


def test_clerk_exchange_is_hidden_when_clerk_is_disabled(client, monkeypatch):
    monkeypatch.delenv("CLERK_SECRET_KEY", raising=False)
    assert client.post("/api/pilot/auth/clerk", json={}).status_code == 404


def test_sdk_signed_out_state_returns_401_without_network(client, monkeypatch):
    monkeypatch.setenv("CLERK_SECRET_KEY", "sk_test_dummy")
    monkeypatch.setattr(
        pilot_clerk.Clerk,
        "authenticate_request",
        lambda self, request, options: SimpleNamespace(is_signed_in=False, payload=None),
    )
    response = client.post("/api/pilot/auth/clerk", json={})
    assert response.status_code == 401
    assert response.json()["detail"] == "Your sign-in could not be verified. Please sign in again."


def test_clerk_verification_http_401_propagates(client, monkeypatch):
    monkeypatch.setenv("CLERK_SECRET_KEY", "sk_test_dummy")

    def reject(request):
        raise HTTPException(401, "Your sign-in could not be verified. Please sign in again.")

    monkeypatch.setattr(pilot_clerk, "verify_clerk_request", reject)
    response = client.post("/api/pilot/auth/clerk", json={})
    assert response.status_code == 401


def test_unusable_password_never_verifies():
    from app.pilot_accounts import UNUSABLE_PASSWORD

    assert not verify_password("anything", UNUSABLE_PASSWORD)


def test_config_reports_clerk_instance_from_key_prefix(client, monkeypatch):
    cases = {
        "sk_live_dummy": "production",
        "sk_test_dummy": "development",
        "pk_live_pasted_by_mistake": "unrecognized",
    }
    for secret, expected in cases.items():
        monkeypatch.setenv("CLERK_SECRET_KEY", secret)
        body = client.get("/api/pilot/config").json()
        assert body["auth_provider"] == "clerk"
        assert body["clerk_instance"] == expected
        assert secret not in str(body)

    monkeypatch.delenv("CLERK_SECRET_KEY", raising=False)
    body = client.get("/api/pilot/config").json()
    assert body["auth_provider"] == "password"
    assert body["clerk_instance"] is None


def test_secret_key_whitespace_is_trimmed_before_the_sdk(client, monkeypatch):
    reset_limits()
    monkeypatch.setenv("CLERK_SECRET_KEY", "sk_test_dummy\n")
    seen = {}

    def fake_authenticate(self, request, options):
        seen["secret"] = options.secret_key
        return SimpleNamespace(is_signed_in=False, payload=None)

    monkeypatch.setattr(pilot_clerk.Clerk, "authenticate_request", fake_authenticate)
    assert client.post("/api/pilot/auth/clerk", json={}).status_code == 401
    assert seen["secret"] == "sk_test_dummy"


def test_unexpected_sdk_error_logs_type_without_secret(client, monkeypatch, caplog):
    reset_limits()
    monkeypatch.setenv("CLERK_SECRET_KEY", "sk_test_secretvalue")

    def boom(self, request, options):
        raise RuntimeError("header contained sk_test_secretvalue")

    monkeypatch.setattr(pilot_clerk.Clerk, "authenticate_request", boom)
    with caplog.at_level("ERROR", logger="app.pilot_clerk"):
        response = client.post("/api/pilot/auth/clerk", json={})
    assert response.status_code == 503
    assert "RuntimeError" in caplog.text
    assert "sk_test_secretvalue" not in caplog.text


def test_whitespace_only_secret_keeps_password_mode(client, monkeypatch):
    monkeypatch.setenv("CLERK_SECRET_KEY", "  \n")
    assert client.get("/api/pilot/config").json()["auth_provider"] == "password"
