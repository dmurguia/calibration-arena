import asyncio
from types import SimpleNamespace

import pytest

from app.pilot_accounts import reset_limits
from app.pilot_audit import GenerationFailure
from app.pilot_leaderboard import build_leaderboard
from app.pilot_models import parse_pool


def guest(client):
    response = client.post("/api/pilot/guests", json={})
    assert response.status_code == 200
    return response.json()


def signup(client, email="account@example.com", password="long-enough-password"):
    response = client.post("/api/pilot/auth/signup", json={
        "name": "Accountant", "email": email, "password": password,
    })
    assert response.status_code == 200
    return response.json()


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_signup_claims_guest_and_login_follows_notebook(client):
    reset_limits()
    old = guest(client)
    case = client.get("/api/pilot/cases").json()[0]
    run = client.post("/api/pilot/runs", headers=auth(old["token"]), json={"case_id": case["id"], "independent_first": False}).json()
    account = client.post("/api/pilot/auth/signup", headers=auth(old["token"]), json={
        "name": "Ada", "email": "claim@example.com", "password": "long-enough-password",
    })
    assert account.status_code == 200
    assert account.json()["participant"]["id"] == old["participant"]["id"]
    assert run["id"] in {item["id"] for item in client.get("/api/pilot/me", headers=auth(account.json()["token"])).json()["runs"]}
    assert client.get("/api/pilot/me", headers=auth(old["token"])).status_code == 401
    logged = client.post("/api/pilot/auth/login", json={"email": "claim@example.com", "password": "long-enough-password"}).json()
    assert run["id"] in {item["id"] for item in client.get("/api/pilot/me", headers=auth(logged["token"])).json()["runs"]}


def test_login_errors_logout_and_expiry(client):
    reset_limits()
    account = signup(client, "login@example.com")
    wrong = client.post("/api/pilot/auth/login", json={"email": "login@example.com", "password": "wrong-password"})
    unknown = client.post("/api/pilot/auth/login", json={"email": "missing@example.com", "password": "wrong-password"})
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json()["detail"] == unknown.json()["detail"] == "Email or password is incorrect."
    assert client.post("/api/pilot/auth/logout", headers=auth(account["token"])).json() == {"ok": True}
    assert client.get("/api/pilot/me", headers=auth(account["token"])).status_code == 401

    account = signup(client, "expiry@example.com")
    from app.db import SessionLocal
    from app.pilot_accounts import PilotSession
    from sqlalchemy import update
    with SessionLocal() as db:
        db.execute(update(PilotSession).where(PilotSession.participant_id == account["participant"]["id"]).values(expires_at="2000-01-01T00:00:00+00:00"))
        db.commit()
    assert client.get("/api/pilot/me", headers=auth(account["token"])).status_code == 401


def test_guest_rate_limit_uses_trusted_proxy_hop(client, monkeypatch):
    reset_limits()
    monkeypatch.setenv("ARENA_TRUST_PROXY", "1")
    monkeypatch.setenv("ARENA_PROXY_HOPS", "1")
    for index in range(21):
        response = client.post(
            "/api/pilot/guests",
            headers={"X-Forwarded-For": f"192.0.2.{index + 1}, 203.0.113.9"},
            json={},
        )
        assert response.status_code == (429 if index == 20 else 200)


def test_login_rate_limit_and_founder_endpoints(client, monkeypatch):
    reset_limits()
    for index in range(10):
        response = client.post("/api/pilot/auth/login", json={"email": f"limit-{index}@example.com", "password": "wrong-password"})
        assert response.status_code == 401
    assert client.post("/api/pilot/auth/login", json={"email": "another@example.com", "password": "wrong-password"}).status_code == 429

    monkeypatch.setenv("PILOT_ADMIN_TOKEN", "admin-token-that-is-long-enough-123")
    account = signup(client, "founder@example.com")
    bad = {"X-Pilot-Admin": "wrong"}
    assert client.post("/api/pilot/founder/reset-link", headers=bad, json={"email": "founder@example.com"}).status_code == 403
    assert client.post(f"/api/pilot/founder/participants/{account['participant']['id']}/budget", headers=bad, json={"token_budget": 10}).status_code == 403
    link = client.post("/api/pilot/founder/reset-link", headers={"X-Pilot-Admin": "admin-token-that-is-long-enough-123"}, json={"email": "founder@example.com"})
    assert link.status_code == 200
    reset_token = link.json()["reset_path"].split("#token=", 1)[1]
    fresh = client.post("/api/pilot/auth/reset", json={"token": reset_token, "password": "new-long-enough-password"})
    assert fresh.status_code == 200
    assert client.get("/api/pilot/me", headers=auth(account["token"])).status_code == 401
    assert client.post("/api/pilot/auth/reset", json={"token": reset_token, "password": "another-password"}).status_code == 400
    budget = client.post(f"/api/pilot/founder/participants/{account['participant']['id']}/budget", headers={"X-Pilot-Admin": "admin-token-that-is-long-enough-123"}, json={"token_budget": 10})
    assert budget.status_code == 200


def test_usage_budget_failed_generation_and_global_cap(client, monkeypatch):
    reset_limits()
    account = signup(client, "budget@example.com")
    monkeypatch.setattr("app.routers.pilot.live_ready", lambda: True)
    monkeypatch.setattr("app.routers.pilot.inference_backend", lambda: "direct")
    attempt = {"status": "complete", "requested_model": "openai:test", "usage": {"input_tokens": 2, "output_tokens": 2}}

    async def generate(*args, **kwargs):
        return [{"text": "one", "model_id": "one", "attempt": dict(attempt)}, {"text": "two", "model_id": "two", "attempt": dict(attempt)}]

    monkeypatch.setattr("app.routers.pilot.generate", generate)
    monkeypatch.setenv("PILOT_TOKEN_BUDGET", "7")
    response = client.post("/api/pilot/runs", headers=auth(account["token"]), json={"question": "How should a prepaid expense be recorded?"})
    assert response.status_code == 200
    assert response.json()["status"] == "review"
    assert client.get("/api/pilot/me", headers=auth(account["token"])).json()["usage"]["used"] == 8
    assert client.post("/api/pilot/runs", headers=auth(account["token"]), json={"question": "How should a deferred revenue balance be reviewed?"}).status_code == 402

    guest_auth = guest(client)
    failed_attempt = {"status": "failed", "requested_model": "anthropic:test", "usage": {"input_tokens": 3, "output_tokens": 1}}

    async def fail(*args, **kwargs):
        raise GenerationFailure("failed", [failed_attempt])

    monkeypatch.setattr("app.routers.pilot.generate", fail)
    monkeypatch.setenv("PILOT_GUEST_TOKEN_BUDGET", "100")
    failed = client.post("/api/pilot/runs", headers=auth(guest_auth["token"]), json={"question": "How should a lease schedule be reviewed?"})
    assert failed.status_code == 200 and failed.json()["status"] == "failed"
    assert client.get("/api/pilot/me", headers=auth(guest_auth["token"])).json()["usage"]["used"] == 4
    monkeypatch.setenv("PILOT_GLOBAL_DAILY_TOKENS", "4")
    assert client.post("/api/pilot/runs", headers=auth(guest_auth["token"]), json={"question": "How should a lease schedule be reviewed again?"}).status_code == 503


def test_pool_parsing_pair_history_and_pair_validation(monkeypatch):
    monkeypatch.setenv("PILOT_MODELS", "openai:gpt-test,anthropic:claude-test,openrouter:router/test")
    monkeypatch.setenv("OPENAI_API_KEY", "openai-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "anthropic-key")
    monkeypatch.setenv("OPENROUTER_API_KEY", "router-key")
    assert [model.id for model in parse_pool()] == ["openai:gpt-test", "anthropic:claude-test", "openrouter:router/test"]
    monkeypatch.setattr("secrets.SystemRandom.sample", lambda self, values, count: list(values)[:count])
    from app import pilot_inference

    async def result(*args, **kwargs):
        model = args[0]
        return {"model_id": model, "text": model, "attempt": {"status": "complete", "usage": {}}}

    monkeypatch.setattr("app.pilot_direct.call_openai", result)
    monkeypatch.setattr("app.pilot_direct.call_anthropic", result)
    monkeypatch.setattr(pilot_inference, "call_openrouter", result)
    monkeypatch.setenv("ARENA_INFERENCE_BACKEND", "pool")
    first = asyncio.run(pilot_inference.generate("question", "accounting-question"))
    pair = {draft["model_id"] for draft in first}
    assert pair == {"openai:gpt-test", "anthropic:claude-test"}
    followup = asyncio.run(pilot_inference.generate("follow-up", "accounting-question", history={key: [] for key in pair}))
    assert {draft["model_id"] for draft in followup} == pair
    with pytest.raises(ValueError, match="model pair changed"):
        asyncio.run(pilot_inference.generate("follow-up", "accounting-question", history={"openai:gpt-test": [], "other:model": []}))


def test_leaderboard_filters_unblinded_and_authored_runs():
    def run(participant, preference, *, mode="pool", scope="blind-conversation", task="accounting-question"):
        drafts = [{"model_id": "openai:gpt"}, {"model_id": "anthropic:claude"}]
        return SimpleNamespace(participant_id=participant, data={
            "mode": mode, "evaluation_scope": scope, "task_type": task,
            "drafts": drafts, "judgment": {"mechanism": "preference-v2", "preference": preference},
        })

    result = build_leaderboard([run("a", "a"), run("b", "a"), run("c", "b"), run("d", "a", scope="unblinded-conversation"), run("e", "a", mode="authored-fixture")])
    assert result["total_votes"] == 3
    assert result["rows"][0]["model_id"] == "openai:gpt"
    assert result["participants"] == 3
