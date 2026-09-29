from dataclasses import dataclass
import os


KEYS = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
}


@dataclass(frozen=True)
class PoolModel:
    provider: str
    model: str

    @property
    def id(self):
        return f"{self.provider}:{self.model}"


def parse_pool(value: str | None = None, environ: dict | None = None) -> list[PoolModel]:
    env = os.environ if environ is None else environ
    configured = env.get("PILOT_MODELS", "") if value is None else value
    models = []
    seen = set()
    for item in configured.split(","):
        item = item.strip()
        if not item:
            continue
        provider, separator, model = item.partition(":")
        model = model.strip()
        if not separator or provider not in KEYS or not model:
            raise ValueError("PILOT_MODELS entries must use openai:model, anthropic:model, or openrouter:model.")
        entry = PoolModel(provider, model)
        if entry.id in seen:
            raise ValueError("PILOT_MODELS must contain unique entries.")
        seen.add(entry.id)
        models.append(entry)
    if len(models) < 2:
        raise ValueError("PILOT_MODELS must contain at least two unique entries.")
    for provider in {model.provider for model in models}:
        key = KEYS[provider]
        value = env.get(key, "").strip()
        if not value or value.startswith("PLACEHOLDER"):
            raise ValueError(f"{key} is required for the configured model pool.")
    return models


def pool_ready() -> bool:
    try:
        parse_pool()
        return True
    except ValueError:
        return False


def pool_labels() -> list[str]:
    try:
        return [model.id for model in parse_pool()]
    except ValueError:
        return []
