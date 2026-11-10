"""Provider stream parsing.

Each reader consumes one provider's server-sent events, reports text as it
arrives, and rebuilds the same response object the non-streaming call returns,
so everything after it (status rules, hashes, usage, cost) runs unchanged.
Reasoning text is reported and kept separately; it is never part of the answer.
"""
import json


class StreamError(ValueError):
    """The provider reported a failure inside an open stream."""


async def sse_events(lines):
    """(event name, data string) pairs from an async iterator of text lines."""
    event, data = None, []
    async for raw in lines:
        line = raw.rstrip('\r\n')
        if not line:
            if data:
                yield event, '\n'.join(data)
            event, data = None, []
        elif line.startswith(':'):
            continue
        elif line.startswith('event:'):
            event = line[6:].strip()
        elif line.startswith('data:'):
            data.append(line[5:].lstrip(' '))
    if data:
        yield event, '\n'.join(data)


def _json(data):
    try:
        value = json.loads(data)
    except ValueError:
        raise StreamError('Unreadable stream event') from None
    if not isinstance(value, dict):
        raise StreamError('Unreadable stream event')
    return value


class OpenAIResponsesReader:
    """OpenAI Responses API. Reasoning arrives only as a summary, when requested."""

    thinking_kind = 'summary'

    def __init__(self, emit=None):
        self.emit = emit or (lambda kind, text: None)
        self.response = None
        self.thinking = ''

    def feed(self, event, data):
        if data == '[DONE]':
            return
        item = _json(data)
        kind = item.get('type') or event
        if kind == 'response.output_text.delta':
            self.emit('answer', item.get('delta') or '')
        elif kind == 'response.reasoning_summary_part.added':
            if self.thinking:
                self._think('\n\n')
        elif kind == 'response.reasoning_summary_text.delta':
            self._think(item.get('delta') or '')
        elif kind in ('response.completed', 'response.incomplete', 'response.failed'):
            self.response = item.get('response')
        elif kind == 'error':
            raise StreamError('Provider stream error')

    def _think(self, text):
        self.thinking += text
        self.emit('thinking', text)

    def result(self):
        if not isinstance(self.response, dict):
            raise StreamError('Incomplete response')
        return self.response


class AnthropicMessagesReader:
    """Anthropic Messages API. Thinking blocks are empty unless the API returns their text."""

    thinking_kind = 'summary'

    def __init__(self, emit=None):
        self.emit = emit or (lambda kind, text: None)
        self.message = None
        self.stopped = False
        self.thinking = ''

    def feed(self, event, data):
        item = _json(data)
        kind = item.get('type') or event
        if kind == 'message_start':
            self.message = dict(item.get('message') or {})
            self.message['content'] = []
            self.message['usage'] = dict(self.message.get('usage') or {})
        elif kind == 'error':
            raise StreamError('Provider stream error')
        elif self.message is None:
            return
        elif kind == 'content_block_start':
            blocks = self.message['content']
            index = item.get('index', len(blocks))
            while len(blocks) <= index:
                blocks.append({})
            blocks[index] = dict(item.get('content_block') or {})
        elif kind == 'content_block_delta':
            blocks = self.message['content']
            index = item.get('index', len(blocks) - 1)
            if not 0 <= index < len(blocks):
                raise StreamError('Unreadable stream event')
            block, delta = blocks[index], item.get('delta') or {}
            if delta.get('type') == 'text_delta':
                block['text'] = block.get('text', '') + (delta.get('text') or '')
                self.emit('answer', delta.get('text') or '')
            elif delta.get('type') == 'thinking_delta':
                text = delta.get('thinking') or ''
                block['thinking'] = block.get('thinking', '') + text
                if text:
                    if self.thinking and not block['thinking'][:-len(text)]:
                        text = '\n\n' + text
                    self.thinking += text
                    self.emit('thinking', text)
            elif delta.get('type') == 'signature_delta':
                block['signature'] = block.get('signature', '') + (delta.get('signature') or '')
        elif kind == 'message_delta':
            self.message.update({k: v for k, v in (item.get('delta') or {}).items()})
            self.message['usage'].update(item.get('usage') or {})
        elif kind == 'message_stop':
            self.stopped = True

    def result(self):
        if self.message is None or not self.stopped:
            raise StreamError('Incomplete response')
        return self.message


class ChatCompletionsReader:
    """OpenAI-compatible chat completion chunks (Merge Gateway, OpenRouter).

    Merge sends reasoning as `delta.thinking`; other gateways use
    `reasoning_content` or `reasoning`. A `response.error` object can arrive
    before `[DONE]`. After a `fallback_restart` the start of the new vendor's
    answer can be missing, so the call fails rather than judge a spliced answer.
    """

    thinking_kind = 'provider'

    def __init__(self, emit=None):
        self.emit = emit or (lambda kind, text: None)
        self.meta = {}
        self.content = ''
        self.thinking = ''
        self.finish_reason = None
        self.usage = None
        self.extra = {}
        self.done = False
        self.chunks = 0

    def feed(self, event, data):
        if data.strip() == '[DONE]':
            self.done = True
            return
        item = _json(data)
        if item.get('object') == 'response.error' or item.get('error') or event == 'error':
            raise StreamError('Provider stream error')
        if item.get('fallback_restart'):
            raise StreamError('Provider restarted the response')
        self.chunks += 1
        for key in ('id', 'model', 'created', 'system_fingerprint'):
            if item.get(key) is not None:
                self.meta.setdefault(key, item[key])
        for key in ('provider', 'routing', 'service_tier', 'warnings', 'guardrails'):
            if item.get(key) is not None:
                self.extra[key] = item[key]
        if item.get('usage') is not None:
            self.usage = item['usage']
        for choice in item.get('choices') or []:
            if choice.get('index', 0) != 0:
                continue
            delta = choice.get('delta') or {}
            if delta.get('tool_calls'):
                raise StreamError('Unexpected tool output')
            thinking = delta.get('thinking') or delta.get('reasoning_content') or delta.get('reasoning')
            if isinstance(thinking, str) and thinking:
                self.thinking += thinking
                self.emit('thinking', thinking)
            if isinstance(delta.get('content'), str) and delta['content']:
                self.content += delta['content']
                self.emit('answer', delta['content'])
            if choice.get('finish_reason') is not None:
                self.finish_reason = choice['finish_reason']

    def result(self):
        if not self.chunks or (self.finish_reason is None and not self.done):
            raise StreamError('Incomplete response')
        message = {'role': 'assistant', 'content': self.content}
        return {**self.meta, 'object': 'chat.completion',
                'choices': [{'index': 0, 'message': message, 'finish_reason': self.finish_reason}],
                'usage': self.usage, **self.extra}


async def read_stream(response, reader):
    async for event, data in sse_events(response.aiter_lines()):
        reader.feed(event, data)
    return reader.result()
