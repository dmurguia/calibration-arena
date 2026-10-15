import asyncio

import pytest

from app.config import get_settings
from app.models import ArenaModel
from app.services.providers import get_provider_for, openrouter_model_id, sample_provider
from app.services.providers.live import AnthropicProvider, OpenRouterProvider
from pipeline.seed import ROSTER


@pytest.fixture
def live(monkeypatch):
    def _set(**env):
        monkeypatch.setenv("ARENA_GENERATION_MODE", "live")
        for k, v in env.items():
            monkeypatch.setenv(k, v)
        get_settings.cache_clear()
    yield _set
    get_settings.cache_clear()


def _m(provider, pmid, slug="x"):
    return ArenaModel(slug=slug, name=slug, organization="o", provider=provider, provider_model_id=pmid)


def test_live_routes_every_seeded_model_through_openrouter(live):
    live()
    for slug, _, _, provider, pmid, _ in ROSTER:
        assert isinstance(get_provider_for(_m(provider, pmid, slug)), OpenRouterProvider), slug


def test_sample_products_stay_on_sample_provider_in_live(live):
    live()
    assert get_provider_for(_m("sample", "gavelpoint-drafts")) is sample_provider


def test_direct_providers_opt_in(live):
    live(ARENA_DIRECT_PROVIDERS="1")
    assert isinstance(get_provider_for(_m("anthropic", "claude-opus-4-8")), AnthropicProvider)
    assert isinstance(get_provider_for(_m("openrouter", "z-ai/glm-5.2")), OpenRouterProvider)


def test_seeded_models_map_to_openrouter_slugs():
    got = {slug: openrouter_model_id(_m(p, pmid, slug)) for slug, _, _, p, pmid, _ in ROSTER}
    assert got["claude-opus-4-8"] == "anthropic/claude-opus-4.8"
    assert got["claude-sonnet-4-6"] == "anthropic/claude-sonnet-4.6"
    assert got["gpt-5-5"] == "openai/gpt-5.5"
    assert got["gpt-5-mini"] == "openai/gpt-5-mini"
    assert got["gemini-3-flash"] == "google/gemini-3-flash-preview"
    assert got["glm-5-2"] == "z-ai/glm-5.2"
    assert all("/" in v for v in got.values())
    assert openrouter_model_id(_m("anthropic", "claude-haiku-5-1")) == "anthropic/claude-haiku-5.1"


def test_openrouter_payload_denies_data_collection_and_fallbacks(live, monkeypatch):
    live(OPENROUTER_API_KEY="sk-test")
    sent = {}

    class Resp:
        def raise_for_status(self): pass
        def json(self): return {"choices": [{"message": {"content": "<p>hi</p>"}}]}

    class Client:
        def __init__(self, *a, **k): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *a): pass
        async def post(self, url, headers=None, json=None):
            sent.update(json)
            return Resp()

    monkeypatch.setattr("app.services.providers.live.httpx.AsyncClient", Client)
    res = asyncio.run(OpenRouterProvider().generate(_m("anthropic", "claude-opus-4-8"), "p", "contract-redline"))
    assert res.html == "<p>hi</p>"
    assert sent["model"] == "anthropic/claude-opus-4.8"
    assert sent["provider"] == {"data_collection": "deny", "allow_fallbacks": False}
