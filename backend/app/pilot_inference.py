"""Matched, server-side Ask calls. Fail closed; never disguise a failed run as a fixture."""
import asyncio
import os

import httpx
from .pilot_tasks import TASKS
from . import pilot_local, pilot_direct
from .pilot_audit import GenerationFailure, new_attempt, finish_artifact, timestamp

SYSTEM = "You are a careful accounting reviewer. Answer the actual question provided. State the reporting framework and assumptions, show calculations and journal entries when appropriate, identify missing facts and uncertainty, and do not invent citations. Do not add preparer names, signatures, email addresses or model identities. Be concise, but include the calculations, proposed entries and open questions needed to review the work. You only have the supplied text; do not claim to inspect files or post entries without tool evidence."
CONFIG = {"temperature": 0.2, "top_p": 1, "max_tokens": 1000}


def inference_backend():
    return os.getenv("ARENA_INFERENCE_BACKEND", "openrouter")


def live_ready():
    if inference_backend() == "local-cli":
        return pilot_local.ready()
    if inference_backend() == 'direct':
        return pilot_direct.ready()
    if inference_backend() != "openrouter":
        return False
    values = [os.getenv(k, "") for k in ("OPENROUTER_API_KEY", "OPENROUTER_MODEL_A", "OPENROUTER_MODEL_B")]
    return all(v and not v.startswith("PLACEHOLDER") for v in values) and values[1] != values[2]


async def generate(question, task_type="accounting-question", *, history=None):
    if not live_ready():
        raise ValueError("Live models are not connected. Choose an authored sample case to try the review flow.")
    if isinstance(history, dict):
        keys = {'direct': ('OPENAI_MODEL', 'ANTHROPIC_MODEL'), 'local-cli': ('LOCAL_CODEX_MODEL', 'LOCAL_CLAUDE_MODEL'), 'openrouter': ('OPENROUTER_MODEL_A', 'OPENROUTER_MODEL_B')}[inference_backend()]
        if set(history) != {os.getenv(k) for k in keys}:
            raise ValueError('The model pair changed. Start a new comparison.')
    instructions = SYSTEM + "\n\n" + TASKS[task_type]["instruction"]
    if inference_backend() == "local-cli":
        return await pilot_local.generate_local(question, instructions, task_type, history=history)
    if inference_backend() == 'direct':
        return await pilot_direct.generate_direct(question, instructions, task_type, history=history)
    messages = [{"role": "system", "content": instructions}, *(history if isinstance(history, list) else []), {"role": "user", "content": question}]

    async def call(model):
        payload = {"model": model, "messages": ([{"role": "system", "content": instructions}, *history[model], {"role": "user", "content": question}] if isinstance(history, dict) else messages), **CONFIG, "provider": {"data_collection": "deny", "zdr": True, "allow_fallbacks": False}}
        attempt = new_attempt('openrouter', model, payload)
        try:
            async with httpx.AsyncClient(timeout=45) as client:
                r = await client.post("https://openrouter.ai/api/v1/chat/completions", headers={"Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}"}, json=payload)
                attempt['http_status'] = getattr(r, 'status_code', None)
                attempt['provider_request_id'] = getattr(r, 'headers', {}).get('x-request-id')
                r.raise_for_status()
                data = r.json()
            attempt.update(response=data, provider_response_id=data.get('id'),
                           resolved_model=data.get('model'), usage=data.get('usage'),
                           cost=(data.get('usage') or {}).get('cost'), provider_routing=data.get('provider'))
            choice = data['choices'][0]
            attempt['finish_reason'] = choice.get('finish_reason')
            if choice.get('finish_reason') not in (None, 'stop'):
                raise ValueError('Incomplete or refused response')
            return finish_artifact(attempt, choice['message']['content'], task_type, CONFIG, 'ask-v4')
        except Exception as exc:
            attempt.update(status='failed', finished_at=timestamp(), error_type=type(exc).__name__)
            return attempt
    results = await asyncio.gather(call(os.environ["OPENROUTER_MODEL_A"]), call(os.environ["OPENROUTER_MODEL_B"]), return_exceptions=True)
    attempts = [r.get('attempt', r) for r in results if isinstance(r, dict)]
    if len(attempts) != 2 or any(a['status'] != 'complete' for a in attempts):
        raise GenerationFailure("Both answers could not be generated. Your question is saved; please try again later.", attempts)
    if any(a.get('hygiene_flags') for a in attempts):
        for a in attempts:
            if a.get('hygiene_flags'):
                a['status'] = 'quarantined'
        raise GenerationFailure('A response contained unexpected identifying content. Please try again.', attempts)
    return results
