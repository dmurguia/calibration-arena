from __future__ import annotations

from ...config import get_settings
from ...models import ArenaModel
from .base import GenerationProvider, GenerationResult, ProviderNotConfigured
from .live import AnthropicProvider, GoogleProvider, OpenAIProvider, OpenRouterProvider, openrouter_model_id
from .professional import ProfessionalSampleProvider

__all__ = [
    "GenerationProvider",
    "GenerationResult",
    "ProviderNotConfigured",
    "get_provider_for",
    "openrouter_model_id",
    "sample_provider",
]

sample_provider = ProfessionalSampleProvider()
_live: dict[str, GenerationProvider] = {
    "anthropic": AnthropicProvider(),
    "openai": OpenAIProvider(),
    "google": GoogleProvider(),
    "openrouter": OpenRouterProvider(),
}


def get_provider_for(model: ArenaModel) -> GenerationProvider:
    """Route a model to its execution provider.

    `sample` mode (default): everything goes to the offline professional provider.
    `live` mode: every model goes through OpenRouter (one key, OPENROUTER_API_KEY);
    first-party slugs are mapped by `openrouter_model_id`. The direct
    Anthropic/OpenAI/Google adapters are used only when explicitly opted into
    with ARENA_DIRECT_PROVIDERS=1. Models with provider `sample` (vendor
    products) have no real endpoint and always stay on the sample provider.
    """
    settings = get_settings()
    if settings.generation_mode != "live" or model.provider == "sample":
        return sample_provider
    if settings.direct_providers and model.provider in _live:
        return _live[model.provider]
    return _live["openrouter"]
