from dataclasses import dataclass
from functools import lru_cache
import json
import os
from pathlib import Path
import re


KEYS = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
}

# Org fallback when the benchmark catalog has no record for a model slug.
CLOSED_ORGS = {"anthropic", "openai", "google", "x-ai"}

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _norm(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


@lru_cache
def _catalog_weights() -> dict[str, str]:
    """normalized id/name -> open|closed|unknown, from benchmarks/models.json."""
    try:
        data = json.loads((_REPO_ROOT / "benchmarks" / "models.json").read_text())
    except (OSError, ValueError):
        return {}
    models = data if isinstance(data, list) else data.get("models", [])
    index = {}
    for record in models:
        weights = record.get("weights")
        if weights not in ("open", "closed", "unknown"):
            continue
        for key in (record.get("id"), record.get("name")):
            if key:
                index.setdefault(_norm(key), weights)
    return index


def weights_for(model_id: str) -> str:
    """Weights label for a pool model id like 'openrouter:deepseek/deepseek-v4-pro'."""
    model = model_id.partition(":")[2] or model_id
    if "/" in model:
        org, _, slug = model.partition("/")
    else:
        org, slug = model_id.partition(":")[0], model
    match = _catalog_weights().get(_norm(slug))
    if match:
        return match
    return "closed" if org in CLOSED_ORGS else "unknown"


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
