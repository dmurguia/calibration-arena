"""Two direct API calls, no routing marketplace, CLI process or model fallback."""
import asyncio
import os
import httpx
from .pilot_audit import new_attempt, finish_artifact, timestamp, GenerationFailure


def ready():
    keys = ('OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'OPENAI_MODEL', 'ANTHROPIC_MODEL')
    return all(os.getenv(k, '').strip() and not os.environ[k].startswith('PLACEHOLDER') for k in keys)


def normalized_messages(provider, request):
    if provider == 'openai':
        return [{'role': 'system', 'content': request['instructions']}, *request['input']]
    if provider == 'anthropic':
        return [{'role': 'system', 'content': request['system']}, *request['messages']]
    return request.get('messages')


async def generate_direct(question, instructions, task_type, *, history=None):
    def messages(model):
        prior = history[model] if isinstance(history, dict) else (history or [])
        return [*prior, {'role': 'user', 'content': question}]
    token_limit = max(256, min(int(os.getenv('PILOT_MAX_OUTPUT_TOKENS', '2000')), 8000))
    requests = [
        ('openai', 'https://api.openai.com/v1/responses',
         {'Authorization': 'Bearer ' + os.environ['OPENAI_API_KEY']},
         {'model': os.environ['OPENAI_MODEL'], 'instructions': instructions, 'input': messages(os.environ['OPENAI_MODEL']),
          'max_output_tokens': token_limit, 'store': False}),
        ('anthropic', 'https://api.anthropic.com/v1/messages',
         {'x-api-key': os.environ['ANTHROPIC_API_KEY'], 'anthropic-version': '2023-06-01'},
         {'model': os.environ['ANTHROPIC_MODEL'], 'system': instructions, 'messages': messages(os.environ['ANTHROPIC_MODEL']),
          'max_tokens': token_limit}),
    ]

    async def call(provider, url, headers, payload):
        attempt = new_attempt(provider, payload['model'], payload)
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(url, headers=headers, json=payload)
                attempt['http_status'] = response.status_code
                attempt['provider_request_id'] = response.headers.get('x-request-id') or response.headers.get('request-id')
                response.raise_for_status()
                data = response.json()
            attempt.update(response=data, provider_response_id=data.get('id'), resolved_model=data.get('model'), usage=data.get('usage'))
            if provider == 'openai':
                attempt['finish_reason'] = data.get('status')
                if data.get('status') != 'completed':
                    raise ValueError('Incomplete response')
                output = data.get('output', [])
                if any(item.get('type') not in ('message', 'reasoning') for item in output):
                    raise ValueError('Unexpected tool output')
                blocks = [block for item in output if item.get('type') == 'message' for block in item.get('content', [])]
                if any(block.get('type') != 'output_text' for block in blocks):
                    raise ValueError('Refused or unsupported output')
                text = ''.join(block['text'] for block in blocks)
            else:
                attempt['finish_reason'] = data.get('stop_reason')
                if data.get('stop_reason') != 'end_turn':
                    raise ValueError('Incomplete response')
                blocks = data.get('content', [])
                if any(block.get('type') not in ('text', 'thinking', 'redacted_thinking') for block in blocks):
                    raise ValueError('Unexpected tool output')
                text = ''.join(block['text'] for block in blocks if block.get('type') == 'text')
            settings = {k: v for k, v in payload.items() if k not in ('model', 'instructions', 'input', 'system', 'messages')}
            # Omitted sampling/reasoning parameters use provider defaults, not invented matched values.
            settings['sampling'] = 'provider-default'
            return finish_artifact(attempt, text, task_type, settings, 'ask-direct-v2')
        except Exception as exc:
            attempt.update(status='failed', finished_at=timestamp(), error_type=type(exc).__name__)
            return attempt

    results = await asyncio.gather(*(call(*request) for request in requests))
    attempts = [result.get('attempt', result) for result in results]
    if any(a['status'] != 'complete' for a in attempts):
        raise GenerationFailure('Both model responses could not be completed. Your prompt is saved.', attempts)
    if any(a.get('hygiene_flags') for a in attempts):
        for attempt in attempts:
            if attempt.get('hygiene_flags'):
                attempt['status'] = 'quarantined'
        raise GenerationFailure('A response contained unexpected identifying content. Please try again.', attempts)
    return results
