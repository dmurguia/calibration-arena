"""Live provider adapters.

These implement the real vendor HTTP APIs via httpx, but every key defaults to a
PLACEHOLDER_* value (see app/config.py and .env.example). Until real keys are
swapped in, calling them raises ProviderNotConfigured with a clear message —
the app runs in `sample` generation mode by default so this never blocks the
core experience.

NOTE: exercised only against the documented API shapes, not real keys — verify
each adapter once credentials are added (ARENA_GENERATION_MODE=live).
"""
from __future__ import annotations

import re
import time

import httpx

from ...config import get_settings
from ...models import ArenaModel
from .base import CATEGORY_SYSTEM_PROMPTS, GenerationResult, ProviderNotConfigured

_HTML_FENCE = re.compile(r"```(?:html)?\s*(.*?)```", re.DOTALL)


def _extract_html(text: str) -> str:
    m = _HTML_FENCE.search(text)
    if m:
        return m.group(1).strip()
    return text.strip()


def _require_key(key: str, provider: str) -> str:
    if not key or key.startswith("PLACEHOLDER"):
        raise ProviderNotConfigured(
            f"{provider} API key is a placeholder. Set the real key in the environment "
            f"(see backend/.env.example) or keep ARENA_GENERATION_MODE=sample."
        )
    return key


# Seeded first-party ids -> OpenRouter slugs (checked against
# https://openrouter.ai/api/v1/models, 2026-10-15).
_OPENROUTER_SLUGS: dict[str, str] = {
    "gpt-5.5": "openai/gpt-5.5",
    "gpt-5-mini": "openai/gpt-5-mini",
    "claude-opus-4-8": "anthropic/claude-opus-4.8",
    "claude-sonnet-4-6": "anthropic/claude-sonnet-4.6",
    "gemini-3-pro": "google/gemini-3.1-pro-preview",  # no plain gemini-3-pro on OpenRouter
    "gemini-3-flash": "google/gemini-3-flash-preview",
}
_CLAUDE_VERSION = re.compile(r"-(\d+)-(\d+)$")


def openrouter_model_id(model: ArenaModel) -> str:
    """The OpenRouter slug for a model, whatever its native provider."""
    mid = model.provider_model_id or model.slug
    if "/" in mid:
        return mid
    if mid in _OPENROUTER_SLUGS:
        return _OPENROUTER_SLUGS[mid]
    if model.provider == "anthropic":
        return "anthropic/" + _CLAUDE_VERSION.sub(r"-\1.\2", mid)
    if model.provider in ("openai", "google"):
        return f"{model.provider}/{mid}"
    return mid


def _system_prompt(category: str) -> str:
    # The old default indexed a "website" key that no longer exists, so every
    # live call raised KeyError before reaching the network.
    return CATEGORY_SYSTEM_PROMPTS.get(category) or next(iter(CATEGORY_SYSTEM_PROMPTS.values()))


def _user_prompt(prompt: str, category: str) -> str:
    return f"Category: {category}\nRequest: {prompt}"


class AnthropicProvider:
    async def generate(self, model: ArenaModel, prompt: str, category: str, scenario: dict | None = None) -> GenerationResult:
        key = _require_key(get_settings().anthropic_api_key, "Anthropic")
        start = time.monotonic()
        async with httpx.AsyncClient(timeout=180) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={"x-api-key": key, "anthropic-version": "2023-06-01"},
                json={
                    "model": model.provider_model_id or model.slug,
                    "max_tokens": 8192,
                    "system": _system_prompt(category),
                    "messages": [{"role": "user", "content": _user_prompt(prompt, category)}],
                },
            )
            resp.raise_for_status()
            text = "".join(b.get("text", "") for b in resp.json().get("content", []))
        return GenerationResult(html=_extract_html(text), latency_ms=int((time.monotonic() - start) * 1000))


class OpenAIProvider:
    async def generate(self, model: ArenaModel, prompt: str, category: str, scenario: dict | None = None) -> GenerationResult:
        key = _require_key(get_settings().openai_api_key, "OpenAI")
        start = time.monotonic()
        async with httpx.AsyncClient(timeout=180) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {key}"},
                json={
                    "model": model.provider_model_id or model.slug,
                    "messages": [
                        {"role": "system", "content": _system_prompt(category)},
                        {"role": "user", "content": _user_prompt(prompt, category)},
                    ],
                },
            )
            resp.raise_for_status()
            text = resp.json()["choices"][0]["message"]["content"]
        return GenerationResult(html=_extract_html(text), latency_ms=int((time.monotonic() - start) * 1000))


class GoogleProvider:
    async def generate(self, model: ArenaModel, prompt: str, category: str, scenario: dict | None = None) -> GenerationResult:
        key = _require_key(get_settings().google_api_key, "Google")
        start = time.monotonic()
        model_id = model.provider_model_id or model.slug
        async with httpx.AsyncClient(timeout=180) as client:
            resp = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:generateContent",
                params={"key": key},
                json={
                    "systemInstruction": {"parts": [{"text": _system_prompt(category)}]},
                    "contents": [{"parts": [{"text": _user_prompt(prompt, category)}]}],
                },
            )
            resp.raise_for_status()
            text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
        return GenerationResult(html=_extract_html(text), latency_ms=int((time.monotonic() - start) * 1000))


class OpenRouterProvider:
    """Default live provider for every model (first-party ids mapped to OpenRouter slugs).

    Same routing policy as the pilot (PR #28): no prompt retention, no silent fallbacks.
    """

    async def generate(self, model: ArenaModel, prompt: str, category: str, scenario: dict | None = None) -> GenerationResult:
        key = _require_key(get_settings().openrouter_api_key, "OpenRouter")
        start = time.monotonic()
        async with httpx.AsyncClient(timeout=180) as client:
            resp = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {key}"},
                json={
                    "model": openrouter_model_id(model),
                    "messages": [
                        {"role": "system", "content": _system_prompt(category)},
                        {"role": "user", "content": _user_prompt(prompt, category)},
                    ],
                    "provider": {"data_collection": "deny", "allow_fallbacks": False},
                },
            )
            resp.raise_for_status()
            text = resp.json()["choices"][0]["message"]["content"]
        return GenerationResult(html=_extract_html(text), latency_ms=int((time.monotonic() - start) * 1000))
