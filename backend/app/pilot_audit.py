"""Private inference evidence. Nothing here is serialized to a blind participant."""
from datetime import datetime, timezone
import hashlib
import json
import os
import re
import secrets


def timestamp():
    return datetime.now(timezone.utc).isoformat()


def text_hash(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def object_hash(value):
    return text_hash(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')))


class GenerationFailure(ValueError):
    def __init__(self, message, attempts):
        super().__init__(message)
        self.attempts = attempts


def new_attempt(provider, model, request):
    return {'id': secrets.token_hex(16), 'schema_version': 'inference-attempt-v1',
            'provider': provider, 'requested_model': model, 'request': request,
            'request_sha256': object_hash(request), 'started_at': timestamp(),
            'finished_at': None, 'status': 'started', 'resolved_model': None,
            'provider_response_id': None, 'provider_request_id': None,
            'finish_reason': None, 'usage': None, 'cost': None, 'error_type': None}


def hygiene(text, supplied_text=''):
    """Heuristic flags, not proof of identity or correctness. Never alter output."""
    emails = set(re.findall(r'[\w.+-]+@[\w-]+\.[\w.]+', text))
    supplied_emails = set(re.findall(r'[\w.+-]+@[\w-]+\.[\w.]+', supplied_text))
    # Explicit local configuration only; never read credential files or git identity.
    identifiers = [s.strip() for s in os.getenv('PILOT_HOST_IDENTIFIERS', '').split('|') if s.strip()]
    flags = []
    if emails - supplied_emails:
        flags.append('unexpected-email')
    if any(s.casefold() in text.casefold() and s.casefold() not in supplied_text.casefold() for s in identifiers):
        flags.append('host-identifier')
    if re.search(r'(?im)^\s*\*{0,2}(prepared by|author)\s*:', text):
        flags.append('preparer-signoff')
    if re.search(r"(?i)\b(?:I am|I'm|as) (?:an? )?(?:AI[^.\n]{0,35})?(?:ChatGPT|Claude|Codex)\b", text):
        flags.append('author-self-identification')
    return flags


def finish_artifact(attempt, text, task_type, settings, prompt_version, *, cli=None):
    if not isinstance(text, str) or not text.strip():
        raise ValueError('Empty response')
    # Store the original response verbatim. UI/export use the same bytes and hash.
    attempt.update(status='complete', finished_at=timestamp(), output_text=text, output_sha256=text_hash(text))
    supplied = json.dumps(attempt['request'], ensure_ascii=False)
    flags = hygiene(text, supplied)
    attempt['hygiene_flags'] = flags
    model = attempt['requested_model']
    author = f"{cli} · {attempt['resolved_model'] or model}" if cli else (attempt['resolved_model'] or model)
    return {'artifact_id': attempt['id'], 'text': text, 'text_sha256': text_hash(text),
            'author': author, 'model_id': model, 'actual_model_id': attempt['resolved_model'],
            'origin': attempt['provider'], 'cli': cli, 'checks': [], 'task_type': task_type,
            'review_note': 'Exploratory response. No independently verified accounting assessment.',
            'settings': settings, 'prompt_version': prompt_version,
            'request_sha256': attempt['request_sha256'], 'generated_at': attempt['finished_at'],
            'hygiene_flags': flags, 'attempt': attempt}
