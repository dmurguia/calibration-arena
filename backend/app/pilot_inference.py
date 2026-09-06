"""Matched, server-side Ask calls. Fail closed; never disguise a failed run as a fixture."""
import asyncio
import hashlib
import json
import os
from datetime import datetime, timezone

import httpx
from .pilot_tasks import TASKS
from . import pilot_local

SYSTEM = "You are a careful accounting reviewer. Answer the actual question provided. State the reporting framework and assumptions, show calculations and journal entries when appropriate, identify missing facts and uncertainty, and do not invent citations. Keep the response under 500 words."
CONFIG = {"temperature": 0.2, "top_p": 1, "max_tokens": 1000}


def inference_backend():
    return os.getenv("ARENA_INFERENCE_BACKEND", "openrouter")


def live_ready():
    if inference_backend() == "local-cli":
        return pilot_local.ready()
    if inference_backend() != "openrouter":
        return False
    values = [os.getenv(k, "") for k in ("OPENROUTER_API_KEY", "OPENROUTER_MODEL_A", "OPENROUTER_MODEL_B", "PILOT_INVITE_CODE")]
    return all(v and not v.startswith("PLACEHOLDER") for v in values) and values[1] != values[2]


async def generate(question, task_type="journal-entry"):
    if not live_ready():
        raise ValueError("Live models are not connected. Choose an authored sample case to try the review flow.")
    instructions = SYSTEM + "\n\n" + TASKS[task_type]["instruction"]
    if inference_backend() == "local-cli":
        return await pilot_local.generate_local(question, instructions, task_type)
    messages = [{"role": "system", "content": instructions}, {"role": "user", "content": question}]

    async def call(model):
        payload = {"model": model, "messages": messages, **CONFIG, "provider": {"data_collection": "deny", "zdr": True, "allow_fallbacks": False}}
        async with httpx.AsyncClient(timeout=45) as client:
            r = await client.post("https://openrouter.ai/api/v1/chat/completions", headers={"Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}"}, json=payload)
            r.raise_for_status()
            data = r.json()
        content = data["choices"][0]["message"]["content"]
        if not isinstance(content, str) or not content.strip():
            raise ValueError("No answer")
        return {"artifact_id": hashlib.sha256((model + content).encode()).hexdigest(), "text": content.strip(), "author": model,
                "model_id": model, "actual_model_id": data.get("model"), "origin": "openrouter", "checks": [],
                "review_note": "Exploratory answer. No independently verified ground truth.", "settings": CONFIG,
                "prompt_version": "ask-v2", "task_type": task_type, "request_sha256": hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest(),
                "generated_at": datetime.now(timezone.utc).isoformat()}
    results = await asyncio.gather(call(os.environ["OPENROUTER_MODEL_A"]), call(os.environ["OPENROUTER_MODEL_B"]), return_exceptions=True)
    if any(isinstance(r, BaseException) for r in results):
        raise ValueError("Both answers could not be generated. Your question is saved; please try again later or choose a practice case.")
    return results
