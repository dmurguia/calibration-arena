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
    monkeypatch.setenv('PILOT_MAX_OUTPUT_TOKENS', '2000')  # budgets below assume the old 2,000 cap
    reset_limits()
    account = signup(client, "budget@example.com")
    monkeypatch.setattr("app.routers.pilot.live_ready", lambda: True)
    monkeypatch.setattr("app.routers.pilot.inference_backend", lambda: "direct")
    attempt = {"status": "complete", "requested_model": "openai:test", "usage": {"input_tokens": 2, "output_tokens": 2}}

    async def generate(*args, **kwargs):
        return [{"text": "one", "model_id": "one", "attempt": dict(attempt)}, {"text": "two", "model_id": "two", "attempt": dict(attempt)}]

    monkeypatch.setattr("app.routers.pilot.generate", generate)
    # Reservations count against the budget before any provider call; the
    # budget must exceed one reserved estimate (~4,020 tokens for this prompt).
    monkeypatch.setenv("PILOT_TOKEN_BUDGET", "4025")
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
    monkeypatch.setenv("PILOT_GUEST_TOKEN_BUDGET", "5000")
    failed = client.post("/api/pilot/runs", headers=auth(guest_auth["token"]), json={"question": "How should a lease schedule be reviewed?"})
    assert failed.status_code == 200 and failed.json()["status"] == "failed"
    # The failed attempt still reported usage, so the reservation reconciles to it.
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


def test_merge_gateway_pool_entry_calls_gateway_and_records_cost(monkeypatch):
    monkeypatch.setenv("PILOT_MODELS", "merge:xai/grok-test,merge:deepseek/deepseek-test")
    monkeypatch.setenv("MERGE_API_KEY", "DO-NOT-RECORD")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setenv("ARENA_INFERENCE_BACKEND", "pool")
    monkeypatch.setenv("PILOT_MAX_OUTPUT_TOKENS", "1500")
    assert [model.id for model in parse_pool()] == ["merge:xai/grok-test", "merge:deepseek/deepseek-test"]
    from app import pilot_inference
    import httpx
    seen = []

    async def post(self, url, headers=None, json=None):
        seen.append((url, headers, json))
        body = {"id": "resp-1", "model": json["model"], "choices": [{"finish_reason": "stop", "message": {"content": "Gateway answer for " + json["model"]}}],
                "usage": {"input_tokens": 10, "output_tokens": 5, "total_tokens": 15, "cost": 0.0021}}
        return httpx.Response(200, json=body, headers={"x-request-id": "req-1", "x-merge-vendor": json["model"].split("/")[0]}, request=httpx.Request("POST", url))

    monkeypatch.setattr(httpx.AsyncClient, "post", post)
    drafts = asyncio.run(pilot_inference.generate("question", "accounting-question"))
    assert {d["model_id"] for d in drafts} == {"merge:xai/grok-test", "merge:deepseek/deepseek-test"}
    assert all(url == "https://api-gateway.merge.dev/v1/chat/completions" for url, _, _ in seen)
    assert all(headers["Authorization"] == "Bearer DO-NOT-RECORD" for _, headers, _ in seen)
    assert all("provider" not in body and body["max_tokens"] == 1500 for _, _, body in seen)
    for draft in drafts:
        attempt = draft["attempt"]
        assert attempt["provider"] == "merge" and attempt["status"] == "complete"
        assert attempt["cost"] == 0.0021 and attempt["provider_request_id"] == "req-1"
        assert attempt["provider_routing"]["x-merge-vendor"] in ("xai", "deepseek")
        assert "DO-NOT-RECORD" not in str(attempt)
        assert draft["origin"] == "merge"
        assert draft["settings"]["max_tokens"] == 1500


def test_pool_routes_openai_and_anthropic_direct_and_only_merge_entries_through_merge(monkeypatch):
    monkeypatch.setenv("PILOT_MODELS", "openai:gpt-6-astra,anthropic:claude-fable-5-2,merge:google/gemini-4-argon,merge:deepseek/deepseek-v4-pro-0813,merge:zai/glm-5.3-flash,merge:mistral/mistral-medium-3-5")
    for key in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "MERGE_API_KEY"):
        monkeypatch.setenv(key, "test-" + key)
    monkeypatch.setenv("ARENA_INFERENCE_BACKEND", "pool")
    from app import pilot_inference
    routes = []

    def route(name):
        async def call(model, *args, **kwargs):
            routes.append((name, model))
            return {"text": model, "attempt": {"status": "complete", "usage": {}}}
        return call

    monkeypatch.setattr("app.pilot_direct.call_openai", route("openai-direct"))
    monkeypatch.setattr("app.pilot_direct.call_anthropic", route("anthropic-direct"))
    monkeypatch.setattr(pilot_inference, "call_merge", route("merge"))
    monkeypatch.setattr(pilot_inference, "call_openrouter", route("openrouter"))
    models = parse_pool()
    for i, first in enumerate(models):
        for second in models[i + 1:]:
            monkeypatch.setattr("secrets.SystemRandom.sample", lambda self, values, count, pair=(first, second): list(pair))
            asyncio.run(pilot_inference.generate("question", "accounting-question"))
    assert {model for name, model in routes if name == "openai-direct"} == {"gpt-6-astra"}
    assert {model for name, model in routes if name == "anthropic-direct"} == {"claude-fable-5-2"}
    assert {model for name, model in routes if name == "merge"} == {"google/gemini-4-argon", "deepseek/deepseek-v4-pro-0813", "zai/glm-5.3-flash", "mistral/mistral-medium-3-5"}
    assert not [r for r in routes if r[0] == "openrouter"]


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
    assert result["rows"][0]["weights"] == "closed"
    assert result["participants"] == 3


def test_default_cap_reserves_two_full_answers_within_guest_budget(monkeypatch):
    from app import pilot_limits
    from app.pilot_direct import token_limit
    monkeypatch.delenv("PILOT_MAX_OUTPUT_TOKENS", raising=False)
    monkeypatch.delenv("PILOT_GUEST_TOKEN_BUDGET", raising=False)
    assert token_limit() == 16000
    reserved = pilot_limits.reservation_tokens("How should a lease schedule be reviewed?")
    assert 32000 <= reserved < pilot_limits.participant_budget(None)


def test_weights_labels():
    from app.pilot_models import weights_for
    assert weights_for("openrouter:deepseek/deepseek-v4-pro") == "open"
    assert weights_for("openrouter:moonshotai/kimi-k3") == "open"
    assert weights_for("anthropic:claude-opus-5.5") == "closed"
    assert weights_for("openai:gpt-6.1-sol") == "closed"
    assert weights_for("merge:deepseek/deepseek-v4-pro-0813") == "open"
    assert weights_for("merge:moonshot/kimi-k3.1-pro") == "open"
    assert weights_for("merge:google/gemini-4-argon") == "closed"
    assert weights_for("merge:xai/grok-4.7") == "closed"
    assert weights_for("merge:zai/glm-5.3-flash") == "open"
    assert weights_for("merge:mistral/mistral-medium-3-5") == "closed"
    assert weights_for("openrouter:acme/mystery-model") == "closed"
