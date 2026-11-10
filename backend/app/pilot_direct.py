"""Two direct API calls, no routing marketplace, CLI process or model fallback."""
import asyncio
import os
import httpx
from .pilot_audit import new_attempt, finish_artifact, timestamp, GenerationFailure, object_hash, record_thinking
from .pilot_sse import AnthropicMessagesReader, OpenAIResponsesReader, read_stream


def ready():
    keys = ('OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'OPENAI_MODEL', 'ANTHROPIC_MODEL')
    return all(os.getenv(k, '').strip() and not os.environ[k].startswith('PLACEHOLDER') for k in keys)


# Output ceiling per model call. Hidden reasoning counts against it, so it is set
# high enough that a full answer to a hard question is rarely cut off (Nov 2026).
DEFAULT_MAX_OUTPUT_TOKENS = 16000
# Per-call wait. Default-setting models can take ~90s on hard questions; this stays
# under PILOT_GENERATION_TIMEOUT_SECONDS (150) so the run records the real error.
PROVIDER_TIMEOUT_SECONDS = 140


def token_limit():
    return max(256, min(int(os.getenv('PILOT_MAX_OUTPUT_TOKENS', str(DEFAULT_MAX_OUTPUT_TOKENS))), 32000))


# Transport and display switches. They are sent to the provider and kept in the
# stored request, but they are not generation settings and stay out of the
# artifact's settings so a streamed answer records the same settings as before.
TRANSPORT_KEYS = ('stream', 'stream_options', 'include_routing_metadata')


async def post_stream(client, url, headers, payload, attempt, reader):
    """POST with stream=true and read the events; returns the rebuilt response object."""
    async with client.stream('POST', url, headers=headers, json=payload) as response:
        attempt['http_status'] = response.status_code
        attempt['provider_request_id'] = response.headers.get('x-request-id') or response.headers.get('request-id')
        if response.status_code >= 400:
            await response.aread()
        response.raise_for_status()
        return await read_stream(response, reader)


def normalized_messages(provider, request):
    if provider == 'openai':
        return [{'role': 'system', 'content': request['instructions']}, *request['input']]
    if provider == 'anthropic':
        return [{'role': 'system', 'content': request['system']}, *request['messages']]
    return request.get('messages')


def finish_openai(attempt, data, payload, task_type):
    attempt.update(response=data, provider_response_id=data.get('id'), resolved_model=data.get('model'), usage=data.get('usage'))
    attempt['finish_reason'] = data.get('status')
    truncated = data.get('status') == 'incomplete' and (data.get('incomplete_details') or {}).get('reason') == 'max_output_tokens'
    if data.get('status') != 'completed' and not truncated:
        raise ValueError('Incomplete response')
    output = data.get('output', [])
    if any(item.get('type') not in ('message', 'reasoning') for item in output):
        raise ValueError('Unexpected tool output')
    blocks = [block for item in output if item.get('type') == 'message' for block in item.get('content', [])]
    if any(block.get('type') != 'output_text' for block in blocks):
        raise ValueError('Refused or unsupported output')
    text = ''.join(block['text'] for block in blocks)
    settings = {k: v for k, v in payload.items() if k not in ('model', 'instructions', 'input', 'system', 'messages', *TRANSPORT_KEYS)}
    settings['sampling'] = 'provider-default'
    return finish_artifact(attempt, text, task_type, settings, 'ask-direct-v2', truncated=truncated)


async def call_openai(model, instructions, messages, task_type, on_event=None):
    payload = {
        'model': model, 'instructions': instructions, 'input': messages,
        'max_output_tokens': token_limit(), 'store': False,
    }
    if on_event:
        # A reasoning summary is display output only: reasoning.effort is not sent,
        # so the model keeps its default effort. Without this the API returns no
        # reasoning text at all.
        payload = {**payload, 'reasoning': {'summary': 'auto'}, 'stream': True}
    attempt = new_attempt('openai', model, payload)
    url = 'https://api.openai.com/v1/responses'
    headers = {'Authorization': 'Bearer ' + os.environ['OPENAI_API_KEY']}
    reader = OpenAIResponsesReader(on_event)
    try:
        async with httpx.AsyncClient(timeout=PROVIDER_TIMEOUT_SECONDS) as client:
            if on_event:
                async def streamed():
                    nonlocal payload
                    try:
                        return await post_stream(client, url, headers, payload, attempt, reader)
                    except httpx.HTTPStatusError as exc:
                        if exc.response.status_code != 400:
                            raise
                    # Some organizations cannot request summaries. Ask again without
                    # one rather than lose the answer; the stored request is the one sent.
                    payload = {k: v for k, v in payload.items() if k != 'reasoning'}
                    attempt.update(request=payload, request_sha256=object_hash(payload), reasoning_summary='rejected')
                    return await post_stream(client, url, headers, payload, attempt, reader)
                data = await asyncio.wait_for(streamed(), PROVIDER_TIMEOUT_SECONDS)
            else:
                response = await client.post(url, headers=headers, json=payload)
                attempt['http_status'] = response.status_code
                attempt['provider_request_id'] = response.headers.get('x-request-id') or response.headers.get('request-id')
                response.raise_for_status()
                data = response.json()
        record_thinking(attempt, reader.thinking, reader.thinking_kind)
        return finish_openai(attempt, data, payload, task_type)
    except Exception as exc:
        record_thinking(attempt, reader.thinking, reader.thinking_kind)
        attempt.update(status='failed', finished_at=timestamp(), error_type=type(exc).__name__)
        return attempt


def finish_anthropic(attempt, data, payload, task_type):
    attempt.update(response=data, provider_response_id=data.get('id'), resolved_model=data.get('model'), usage=data.get('usage'))
    attempt['finish_reason'] = data.get('stop_reason')
    truncated = data.get('stop_reason') == 'max_tokens'
    if data.get('stop_reason') != 'end_turn' and not truncated:
        raise ValueError('Incomplete response')
    blocks = data.get('content', [])
    if any(block.get('type') not in ('text', 'thinking', 'redacted_thinking') for block in blocks):
        raise ValueError('Unexpected tool output')
    text = ''.join(block['text'] for block in blocks if block.get('type') == 'text')
    settings = {k: v for k, v in payload.items() if k not in ('model', 'instructions', 'input', 'system', 'messages', *TRANSPORT_KEYS)}
    settings['sampling'] = 'provider-default'
    return finish_artifact(attempt, text, task_type, settings, 'ask-direct-v2', truncated=truncated)


async def call_anthropic(model, instructions, messages, task_type, on_event=None):
    # No `thinking` field is sent, so the model runs its default reasoning and the
    # API's default display. Thinking text is shown only if the API returns it.
    payload = {'model': model, 'system': instructions, 'messages': messages, 'max_tokens': token_limit()}
    if on_event:
        payload = {**payload, 'stream': True}
    attempt = new_attempt('anthropic', model, payload)
    url = 'https://api.anthropic.com/v1/messages'
    headers = {'x-api-key': os.environ['ANTHROPIC_API_KEY'], 'anthropic-version': '2023-06-01'}
    reader = AnthropicMessagesReader(on_event)
    try:
        async with httpx.AsyncClient(timeout=PROVIDER_TIMEOUT_SECONDS) as client:
            if on_event:
                data = await asyncio.wait_for(post_stream(client, url, headers, payload, attempt, reader), PROVIDER_TIMEOUT_SECONDS)
            else:
                response = await client.post(url, headers=headers, json=payload)
                attempt['http_status'] = response.status_code
                attempt['provider_request_id'] = response.headers.get('x-request-id') or response.headers.get('request-id')
                response.raise_for_status()
                data = response.json()
        record_thinking(attempt, reader.thinking, reader.thinking_kind)
        return finish_anthropic(attempt, data, payload, task_type)
    except Exception as exc:
        record_thinking(attempt, reader.thinking, reader.thinking_kind)
        attempt.update(status='failed', finished_at=timestamp(), error_type=type(exc).__name__)
        return attempt


async def generate_direct(question, instructions, task_type, *, history=None, on_event=None):
    def messages(model):
        prior = history[model] if isinstance(history, dict) else (history or [])
        return [*prior, {'role': 'user', 'content': question}]

    models = (os.environ['OPENAI_MODEL'], os.environ['ANTHROPIC_MODEL'])
    async def call(slot, fn):
        if not on_event:
            return await fn(models[slot], instructions, messages(models[slot]), task_type)
        result = await fn(models[slot], instructions, messages(models[slot]), task_type,
                          on_event=lambda kind, text: on_event(slot, models[slot], kind, text))
        on_event(slot, models[slot], 'done', result.get('attempt', result).get('status') == 'complete')
        return result

    results = await asyncio.gather(call(0, call_openai), call(1, call_anthropic))
    attempts = [result.get('attempt', result) for result in results]
    if any(a['status'] != 'complete' for a in attempts):
        raise GenerationFailure('Both model responses could not be completed. Your prompt is saved.', attempts)
    if any(a.get('hygiene_flags') for a in attempts):
        for attempt in attempts:
            if attempt.get('hygiene_flags'):
                attempt['status'] = 'quarantined'
        raise GenerationFailure('A response contained unexpected identifying content. Please try again.', attempts)
    return results
