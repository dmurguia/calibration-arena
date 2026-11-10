"""Streaming answers and visible thinking: provider stream parsing, audit parity and blinding."""
import asyncio
import json

import httpx
import pytest

from app import pilot_direct, pilot_inference, pilot_stream
from app.pilot_audit import text_hash, thinking_hygiene
from app.pilot_sse import (
    AnthropicMessagesReader, ChatCompletionsReader, OpenAIResponsesReader, StreamError, sse_events,
)


def sse(*items, done=False):
    """Wire lines for a list of (event name or None, payload) pairs."""
    lines = []
    for event, payload in items:
        if event:
            lines.append(f'event: {event}')
        lines.append('data: ' + (payload if isinstance(payload, str) else json.dumps(payload)))
        lines.append('')
    if done:
        lines += ['data: [DONE]', '']
    return lines


class FakeStream:
    def __init__(self, lines, status=200, headers=None):
        self.lines, self.status_code, self.headers = lines, status, headers or {'x-request-id': 'req-1'}

    async def __aenter__(self): return self
    async def __aexit__(self, *args): pass
    async def aread(self): return b''

    def raise_for_status(self):
        if self.status_code >= 400:
            request = httpx.Request('POST', 'https://provider.test')
            raise httpx.HTTPStatusError('error', request=request, response=httpx.Response(self.status_code, request=request))

    async def aiter_lines(self):
        for line in self.lines:
            yield line


def fake_client(monkeypatch, streams=None, body=None, sent=None):
    """httpx.AsyncClient stand-in: `.stream()` serves the queued streams, `.post()` the JSON body."""
    queue = list(streams or [])

    class Response:
        status_code = 200
        headers = {'x-request-id': 'req-1'}
        def raise_for_status(self): pass
        def json(self): return body

    class Client:
        def __init__(self, **kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *args): pass
        async def post(self, url, headers, json):
            if sent is not None: sent.append(json)
            return Response()
        def stream(self, method, url, headers, json):
            if sent is not None: sent.append(json)
            return queue.pop(0)

    monkeypatch.setattr(pilot_direct.httpx, 'AsyncClient', Client)


def collect():
    events = []
    return events, lambda kind, text: events.append((kind, text))


def joined(events, kind):
    return ''.join(text for k, text in events if k == kind)


def read(reader, lines):
    async def run():
        async def source():
            for line in lines:
                yield line
        async for event, data in sse_events(source()):
            reader.feed(event, data)
        return reader.result()
    return asyncio.run(run())


def test_sse_events_joins_data_lines_and_skips_comments():
    lines = [': keepalive', 'event: a', 'data: one', 'data: two', '', 'data: {"x": 1}', '', 'data: tail']
    async def run():
        async def source():
            for line in lines:
                yield line + '\n'
        return [pair async for pair in sse_events(source())]
    assert asyncio.run(run()) == [('a', 'one\ntwo'), (None, '{"x": 1}'), (None, 'tail')]


# --- OpenAI Responses -------------------------------------------------------

OPENAI_FINAL = {
    'id': 'resp_1', 'model': 'gpt-test-2026', 'status': 'completed',
    'output': [
        {'type': 'reasoning', 'summary': [{'type': 'summary_text', 'text': 'Check the service period.'}]},
        {'type': 'message', 'content': [{'type': 'output_text', 'text': 'Debit prepaid insurance 1,200.'}]},
    ],
    'usage': {'input_tokens': 40, 'output_tokens': 90, 'output_tokens_details': {'reasoning_tokens': 60}},
}
OPENAI_STREAM = sse(
    ('response.created', {'type': 'response.created', 'response': {'id': 'resp_1', 'status': 'in_progress'}}),
    ('response.reasoning_summary_part.added', {'type': 'response.reasoning_summary_part.added'}),
    ('response.reasoning_summary_text.delta', {'type': 'response.reasoning_summary_text.delta', 'delta': 'Check the '}),
    ('response.reasoning_summary_text.delta', {'type': 'response.reasoning_summary_text.delta', 'delta': 'service period.'}),
    ('response.output_text.delta', {'type': 'response.output_text.delta', 'delta': 'Debit prepaid '}),
    ('response.output_text.delta', {'type': 'response.output_text.delta', 'delta': 'insurance 1,200.'}),
    ('response.completed', {'type': 'response.completed', 'response': OPENAI_FINAL}),
)


def test_openai_stream_reports_summary_and_answer_and_returns_the_final_response():
    events, emit = collect()
    assert read(OpenAIResponsesReader(emit), OPENAI_STREAM) == OPENAI_FINAL
    assert joined(events, 'thinking') == 'Check the service period.'
    assert joined(events, 'answer') == 'Debit prepaid insurance 1,200.'


def test_openai_stream_without_a_terminal_event_or_with_an_error_fails():
    with pytest.raises(StreamError):
        read(OpenAIResponsesReader(), OPENAI_STREAM[:-3])
    with pytest.raises(StreamError):
        read(OpenAIResponsesReader(), sse(('error', {'type': 'error', 'message': 'overloaded'})))


def test_openai_streamed_artifact_matches_the_non_streamed_one(monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY', 'test-key')
    messages = [{'role': 'user', 'content': 'When is the insurance expensed?'}]
    fake_client(monkeypatch, body=OPENAI_FINAL)
    plain = asyncio.run(pilot_direct.call_openai('gpt-test', 'Be careful.', messages, 'accounting-question'))
    sent, (events, emit) = [], collect()
    fake_client(monkeypatch, streams=[FakeStream(OPENAI_STREAM)], sent=sent)
    live = asyncio.run(pilot_direct.call_openai('gpt-test', 'Be careful.', messages, 'accounting-question', on_event=emit))
    # A summary is requested for display; effort is never sent, so the model keeps its default.
    assert sent[0]['reasoning'] == {'summary': 'auto'} and sent[0]['stream'] is True
    assert 'effort' not in sent[0]['reasoning'] and 'reasoning_effort' not in sent[0]
    for key in ('text', 'text_sha256', 'truncated', 'hygiene_flags', 'actual_model_id', 'prompt_version'):
        assert live[key] == plain[key]
    assert live['settings'] == {**plain['settings'], 'reasoning': {'summary': 'auto'}}
    for key in ('usage', 'finish_reason', 'output_sha256', 'provider_response_id', 'status', 'response'):
        assert live['attempt'][key] == plain['attempt'][key]
    # Thinking is stored on the private attempt, apart from the judged answer.
    assert live['attempt']['thinking_text'] == 'Check the service period.'
    assert live['attempt']['thinking_sha256'] == text_hash('Check the service period.')
    assert 'Check the service period' not in live['text'] and 'thinking_text' not in live
    assert 'thinking_text' not in plain['attempt']


def test_openai_retries_without_a_summary_when_the_request_is_rejected(monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY', 'test-key')
    sent, (events, emit) = [], collect()
    answer_only = [line for line in OPENAI_STREAM if 'reasoning_summary' not in line]
    fake_client(monkeypatch, streams=[FakeStream([], status=400), FakeStream(answer_only)], sent=sent)
    result = asyncio.run(pilot_direct.call_openai('gpt-test', 'Be careful.', [{'role': 'user', 'content': 'Q'}], 'accounting-question', on_event=emit))
    assert 'reasoning' in sent[0] and 'reasoning' not in sent[1]
    assert result['text'] == 'Debit prepaid insurance 1,200.' and joined(events, 'thinking') == ''
    assert result['attempt']['request'] == sent[1] and result['attempt']['reasoning_summary'] == 'rejected'
    assert result['request_sha256'] == result['attempt']['request_sha256']


def test_openai_incomplete_stream_is_kept_as_truncated(monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY', 'test-key')
    final = {**OPENAI_FINAL, 'status': 'incomplete', 'incomplete_details': {'reason': 'max_output_tokens'}}
    stream = OPENAI_STREAM[:-3] + sse(('response.incomplete', {'type': 'response.incomplete', 'response': final}))
    fake_client(monkeypatch, streams=[FakeStream(stream)])
    result = asyncio.run(pilot_direct.call_openai('gpt-test', 'Be careful.', [{'role': 'user', 'content': 'Q'}], 'accounting-question', on_event=lambda *a: None))
    assert result['truncated'] is True and result['attempt']['status'] == 'complete'


# --- Anthropic Messages -----------------------------------------------------

def anthropic_stream(thinking_text='', stop_reason='end_turn'):
    items = [
        ('message_start', {'type': 'message_start', 'message': {'id': 'msg_1', 'type': 'message', 'role': 'assistant', 'model': 'claude-test-2026', 'content': [], 'stop_reason': None, 'usage': {'input_tokens': 30, 'output_tokens': 1}}}),
        ('content_block_start', {'type': 'content_block_start', 'index': 0, 'content_block': {'type': 'thinking', 'thinking': '', 'signature': ''}}),
    ]
    if thinking_text:
        items.append(('content_block_delta', {'type': 'content_block_delta', 'index': 0, 'delta': {'type': 'thinking_delta', 'thinking': thinking_text}}))
    items += [
        ('content_block_delta', {'type': 'content_block_delta', 'index': 0, 'delta': {'type': 'signature_delta', 'signature': 'sig=='}}),
        ('content_block_stop', {'type': 'content_block_stop', 'index': 0}),
        ('ping', {'type': 'ping'}),
        ('content_block_start', {'type': 'content_block_start', 'index': 1, 'content_block': {'type': 'text', 'text': ''}}),
        ('content_block_delta', {'type': 'content_block_delta', 'index': 1, 'delta': {'type': 'text_delta', 'text': 'Recognize over '}}),
        ('content_block_delta', {'type': 'content_block_delta', 'index': 1, 'delta': {'type': 'text_delta', 'text': 'twelve months.'}}),
        ('content_block_stop', {'type': 'content_block_stop', 'index': 1}),
        ('message_delta', {'type': 'message_delta', 'delta': {'stop_reason': stop_reason, 'stop_sequence': None}, 'usage': {'output_tokens': 75}}),
        ('message_stop', {'type': 'message_stop'}),
    ]
    return sse(*items)


def test_anthropic_default_display_returns_empty_thinking_so_nothing_is_shown():
    events, emit = collect()
    message = read(AnthropicMessagesReader(emit), anthropic_stream())
    assert [kind for kind, _ in events] == ['answer', 'answer']
    assert message['content'] == [{'type': 'thinking', 'thinking': '', 'signature': 'sig=='}, {'type': 'text', 'text': 'Recognize over twelve months.'}]
    assert message['stop_reason'] == 'end_turn' and message['usage'] == {'input_tokens': 30, 'output_tokens': 75}


def test_anthropic_thinking_text_is_shown_when_the_api_returns_it():
    events, emit = collect()
    read(AnthropicMessagesReader(emit), anthropic_stream('Policy starts in April.'))
    assert joined(events, 'thinking') == 'Policy starts in April.'
    assert joined(events, 'answer') == 'Recognize over twelve months.'


def test_anthropic_error_event_or_cut_stream_fails():
    with pytest.raises(StreamError):
        read(AnthropicMessagesReader(), sse(('error', {'type': 'error', 'error': {'type': 'overloaded_error'}})))
    with pytest.raises(StreamError):
        read(AnthropicMessagesReader(), anthropic_stream()[:-3])


def test_anthropic_stream_never_sends_a_thinking_setting_and_matches_non_streamed(monkeypatch):
    monkeypatch.setenv('ANTHROPIC_API_KEY', 'test-key')
    messages = [{'role': 'user', 'content': 'When is the insurance expensed?'}]
    body = {'id': 'msg_1', 'model': 'claude-test-2026', 'stop_reason': 'end_turn', 'usage': {'input_tokens': 30, 'output_tokens': 75},
            'content': [{'type': 'thinking', 'thinking': '', 'signature': 'sig=='}, {'type': 'text', 'text': 'Recognize over twelve months.'}]}
    fake_client(monkeypatch, body=body)
    plain = asyncio.run(pilot_direct.call_anthropic('claude-test', 'Be careful.', messages, 'accounting-question'))
    sent = []
    fake_client(monkeypatch, streams=[FakeStream(anthropic_stream())], sent=sent)
    live = asyncio.run(pilot_direct.call_anthropic('claude-test', 'Be careful.', messages, 'accounting-question', on_event=lambda *a: None))
    assert set(sent[0]) == {'model', 'system', 'messages', 'max_tokens', 'stream'}
    for key in ('text', 'text_sha256', 'settings', 'truncated', 'actual_model_id'):
        assert live[key] == plain[key]
    for key in ('usage', 'finish_reason', 'output_sha256', 'provider_response_id'):
        assert live['attempt'][key] == plain['attempt'][key]
    assert 'thinking_text' not in live['attempt']
    fake_client(monkeypatch, streams=[FakeStream(anthropic_stream(stop_reason='max_tokens'))])
    cut = asyncio.run(pilot_direct.call_anthropic('claude-test', 'Be careful.', messages, 'accounting-question', on_event=lambda *a: None))
    assert cut['truncated'] is True


# --- Merge Gateway chat completions ----------------------------------------

def chunk(delta=None, **extra):
    choices = [] if delta is None and 'finish_reason' not in extra else [{'index': 0, 'delta': delta or {}, 'finish_reason': extra.pop('finish_reason', None)}]
    return (None, {'id': 'cmpl-1', 'object': 'chat.completion.chunk', 'model': 'deepseek-test-0813', 'choices': choices, **extra})


MERGE_USAGE = {'prompt_tokens': 50, 'completion_tokens': 120, 'total_tokens': 170, 'cost': 0.0042}
MERGE_ROUTING = {'vendor_used': 'deepseek', 'model_used': 'deepseek/deepseek-test', 'policy_id': None, 'cost_usd': 0.0042}
MERGE_STREAM = sse(
    chunk({'role': 'assistant'}),
    chunk({'thinking': 'The policy runs April '}),
    chunk({'thinking': 'to March.'}),
    chunk({'content': 'Expense 100 '}),
    chunk({'content': 'per month.'}),
    chunk({}, finish_reason='stop', usage=MERGE_USAGE, routing=MERGE_ROUTING),
    done=True,
)


def test_merge_stream_reads_thinking_usage_cost_and_routing_from_the_chunks():
    events, emit = collect()
    data = read(ChatCompletionsReader(emit), MERGE_STREAM)
    assert joined(events, 'thinking') == 'The policy runs April to March.'
    assert joined(events, 'answer') == 'Expense 100 per month.'
    assert data['choices'] == [{'index': 0, 'message': {'role': 'assistant', 'content': 'Expense 100 per month.'}, 'finish_reason': 'stop'}]
    assert data['usage'] == MERGE_USAGE and data['routing'] == MERGE_ROUTING and data['model'] == 'deepseek-test-0813'


def test_merge_stream_accepts_reasoning_content_spelling():
    events, emit = collect()
    read(ChatCompletionsReader(emit), sse(chunk({'reasoning_content': 'Full reasoning.'}), chunk({'content': 'Answer.'}), chunk({}, finish_reason='stop'), done=True))
    assert joined(events, 'thinking') == 'Full reasoning.'


def test_merge_error_object_before_done_and_fallback_restart_fail_closed():
    error = (None, {'object': 'response.error', 'error': {'type': 'provider_error', 'message': 'upstream', 'status_code': '503'}})
    with pytest.raises(StreamError):
        read(ChatCompletionsReader(), sse(chunk({'content': 'Partial'}), error, done=True))
    with pytest.raises(StreamError):
        read(ChatCompletionsReader(), sse(chunk({'content': 'Partial'}), (None, {'fallback_restart': True, 'model': 'm', 'vendor': 'v'}), chunk({'content': 'rest'}), done=True))
    with pytest.raises(StreamError):
        read(ChatCompletionsReader(), sse(chunk({'content': 'Cut off mid-stream'})))


def merge_call(monkeypatch, **kwargs):
    monkeypatch.setenv('MERGE_API_KEY', 'test-key')
    messages = [{'role': 'system', 'content': 'Be careful.'}, {'role': 'user', 'content': 'When is the insurance expensed?'}]
    return asyncio.run(pilot_inference.call_merge('deepseek/deepseek-test', 'Be careful.', messages, 'accounting-question', **kwargs))


def test_merge_streamed_artifact_matches_the_non_streamed_one(monkeypatch):
    body = {'id': 'cmpl-1', 'model': 'deepseek-test-0813', 'usage': MERGE_USAGE,
            'choices': [{'message': {'content': 'Expense 100 per month.'}, 'finish_reason': 'stop'}]}
    fake_client(monkeypatch, body=body)
    plain = merge_call(monkeypatch)
    sent, (events, emit) = [], collect()
    fake_client(monkeypatch, streams=[FakeStream(MERGE_STREAM)], sent=sent)
    live = merge_call(monkeypatch, on_event=emit)
    assert sent[0]['stream'] is True and sent[0]['include_routing_metadata'] is True
    # No reasoning control of any spelling is sent: every model runs at its default.
    assert not {'reasoning', 'reasoning_effort', 'thinking'} & set(sent[0])
    for key in ('text', 'text_sha256', 'settings', 'truncated', 'hygiene_flags', 'actual_model_id', 'prompt_version'):
        assert live[key] == plain[key]
    for key in ('usage', 'cost', 'finish_reason', 'output_sha256', 'provider_response_id', 'status'):
        assert live['attempt'][key] == plain['attempt'][key]
    assert live['attempt']['cost'] == 0.0042 and live['attempt']['provider_routing'] == {'x-merge-vendor': 'deepseek', 'x-merge-model': 'deepseek/deepseek-test'}
    assert live['attempt']['thinking_text'] == 'The policy runs April to March.' and live['attempt']['thinking_hygiene_flags'] == []
    assert 'April to March' not in live['text']


def test_merge_stream_failures_follow_the_non_streaming_rules(monkeypatch):
    error = (None, {'object': 'response.error', 'error': {'message': 'upstream'}})
    fake_client(monkeypatch, streams=[FakeStream(sse(chunk({'thinking': 'Working.'}), chunk({'content': 'Partial'}), error, done=True))])
    failed = merge_call(monkeypatch, on_event=lambda *a: None)
    assert failed['status'] == 'failed' and failed['error'] == 'Provider stream error' and 'output_text' not in failed
    fake_client(monkeypatch, streams=[FakeStream([], status=503)])
    assert merge_call(monkeypatch, on_event=lambda *a: None)['error'] == 'The request did not complete.'
    fake_client(monkeypatch, streams=[FakeStream(sse(chunk({'content': 'Cut at the cap'}), chunk({}, finish_reason='length', usage=MERGE_USAGE), done=True))])
    assert merge_call(monkeypatch, on_event=lambda *a: None)['truncated'] is True
    fake_client(monkeypatch, streams=[FakeStream(sse(chunk({'thinking': 'Spent the whole budget reasoning.'}), chunk({}, finish_reason='stop', usage=MERGE_USAGE), done=True))])
    empty = merge_call(monkeypatch, on_event=lambda *a: None)
    assert empty['status'] == 'failed' and empty['error'] == 'Empty response' and empty['usage'] == MERGE_USAGE


def test_openrouter_is_not_streamed(monkeypatch):
    monkeypatch.setenv('OPENROUTER_API_KEY', 'test-key')
    sent = []
    fake_client(monkeypatch, body={'choices': [{'message': {'content': 'Answer'}, 'finish_reason': 'stop'}]}, sent=sent)
    asyncio.run(pilot_inference.call_gateway('openrouter', 'provider/a', 'I', [{'role': 'user', 'content': 'Q'}], 'accounting-question', on_event=lambda *a: None))
    assert 'stream' not in sent[0]


# --- Blinding ---------------------------------------------------------------

def test_thinking_hygiene_flags_model_and_lab_names_unless_the_person_supplied_them():
    assert thinking_hygiene('The lease term is 36 months, so compute the present value.') == []
    for text in ("As DeepSeek, I should check the dates.", "I am Claude and will be careful.", "GLM-5.3 reasoning here",
                 "This model was trained by Google.", "OpenAI policy says", "gemini would", "I'm ChatGPT"):
        assert 'model-or-lab-name' in thinking_hygiene(text), text
    assert thinking_hygiene('Record the OpenAI subscription as software expense.', 'How do I book our OpenAI subscription?') == []
    assert thinking_hygiene('Export the schedule to Google Sheets and claude the amounts.replace') == ['model-or-lab-name']
    assert thinking_hygiene('Use Google Sheets for the schedule.') == []
    assert 'unexpected-email' in thinking_hygiene('Send it to someone@example.com')


def panel_events(feeds, supplied=''):
    events = []
    panel = pilot_stream.Panel(events.append, 'a', supplied)
    for kind, text in feeds:
        panel.feed(kind, text)
    panel.finish(True)
    return events, panel


def test_panel_never_releases_a_name_split_across_chunks():
    filler = 'The policy period matters for the recognition pattern. ' * 4
    events, panel = panel_events([('thinking', filler), ('thinking', 'As Deep'), ('thinking', 'Seek, I should double-check.'), ('answer', 'Debit expense 100.')])
    shown = ''.join(e.get('text', '') for e in events)
    assert panel.withheld and 'Deep' not in shown and 'Debit' not in shown
    assert {'type': 'withheld', 'position': 'a'} in events
    assert events[-1] == {'type': 'state', 'position': 'a', 'state': 'complete'}


def test_panel_releases_clean_text_in_order_and_withholds_a_flagged_answer():
    thinking = 'Work out the monthly amount from the annual premium. ' * 5
    answer = 'Recognize 100 per month from April. ' * 5
    events, panel = panel_events([('thinking', thinking[:90]), ('thinking', thinking[90:]), ('answer', answer[:40]), ('answer', answer[40:])])
    assert not panel.withheld
    assert ''.join(e['text'] for e in events if e['type'] == 'thinking') == thinking
    assert ''.join(e['text'] for e in events if e['type'] == 'answer') == answer
    kinds = [e['type'] for e in events]
    assert kinds.index('answer') > max(i for i, k in enumerate(kinds) if k == 'thinking')
    events, panel = panel_events([('answer', 'Recognize it monthly.\n\nPrepared by: A. Model\n' + 'More detail follows here. ' * 6)])
    assert panel.withheld and 'Prepared by' not in ''.join(e.get('text', '') for e in events)
    # The answer keeps today's rule: a bare model name in an answer is not a flag, only self-identification is.
    events, panel = panel_events([('answer', 'Compare this with how Claude or Gemini pricing is expensed. ' * 3)])
    assert not panel.withheld


def test_relay_events_carry_only_position_and_text():
    channel = pilot_stream.Channel('owner')
    relay = pilot_stream.Relay(channel, ['merge:deepseek/x', 'openai:y'], '')
    relay.on_event(1, 'merge:deepseek/x', 'thinking', 'Consider the cut-off date carefully. ' * 5)
    relay.on_event(0, 'openai:y', 'answer', 'Book it in April. ' * 8)
    relay.on_event(1, 'merge:deepseek/x', 'done', True)
    relay.on_event(0, 'openai:y', 'done', False)
    relay.on_event(0, 'someone-else', 'answer', 'ignored')
    assert all(set(e) <= {'type', 'position', 'text', 'state'} for e in channel.events)
    assert {e['position'] for e in channel.events if e['type'] == 'thinking'} == {'a'}
    assert {e['position'] for e in channel.events if e['type'] == 'answer'} == {'b'}
    assert {'type': 'state', 'position': 'b', 'state': 'stopped'} in channel.events
    assert 'deepseek' not in json.dumps(channel.events) and 'openai' not in json.dumps(channel.events)


def read_stream(client, headers, stream_id):
    with client.stream('GET', f'/api/pilot/runs/stream/{stream_id}', headers=headers) as response:
        assert response.status_code == 200 and response.headers['content-type'].startswith('text/event-stream')
        return [json.loads(line[6:]) for line in response.iter_lines() if line.startswith('data: ')]


def live_run(client, monkeypatch, generate, stream_id, **body):
    from app.routers import pilot
    from tests.test_pilot import enroll
    monkeypatch.setattr(pilot, 'live_ready', lambda: True)
    monkeypatch.setattr(pilot, 'generate', generate)
    headers = enroll(client)
    response = client.post('/api/pilot/runs', headers=headers, json={'question': 'How should a twelve-month insurance premium be expensed?', 'stream_id': stream_id, **body})
    assert response.status_code == 200, response.text
    return headers, response.json()


def draft(model_id, text):
    return {'text': text, 'model_id': model_id, 'author': model_id, 'origin': 'merge'}


def test_run_streams_blinded_panels_that_match_the_voted_sides(client, monkeypatch):
    pilot_stream.reset()
    first = 'First model: recognize the premium evenly over the policy term. ' * 3
    second = 'Second model: expense one twelfth each month from the start date. ' * 3

    async def generate(question, task_type, *, on_event):
        on_event(0, 'merge:lab-one/model', 'thinking', 'Reasoning about the policy term and the start date. ' * 3)
        on_event(0, 'merge:lab-one/model', 'answer', first)
        on_event(1, 'merge:lab-two/model', 'answer', second)
        on_event(0, 'merge:lab-one/model', 'done', True)
        on_event(1, 'merge:lab-two/model', 'done', True)
        return [draft('merge:lab-one/model', first), draft('merge:lab-two/model', second)]

    for stream_id in ('a' * 32, 'b' * 32, 'c' * 32, 'd' * 32):
        headers, run = live_run(client, monkeypatch, generate, stream_id)
        events = read_stream(client, headers, stream_id)
        assert events[-1] == {'type': 'end'}
        shown = {p: ''.join(e['text'] for e in events if e['type'] == 'answer' and e['position'] == p) for p in 'ab'}
        # The side a person watched fill in is the side that holds that answer at the vote.
        assert shown == {d['position']: d['text'] for d in run['drafts']}
        assert all(set(d) == {'position', 'text', 'narrative', 'artifacts'} for d in run['drafts'])
        wire = json.dumps(events)
        assert 'lab-one' not in wire and 'lab-two' not in wire and 'model_id' not in wire
        assert all(set(e) <= {'type', 'position', 'text', 'state'} for e in events)
    # Someone else cannot listen in, and a malformed id is rejected.
    from tests.test_pilot import enroll
    assert client.get('/api/pilot/runs/stream/' + 'a' * 32, headers=enroll(client)).status_code == 404
    assert client.get('/api/pilot/runs/stream/not-an-id', headers=headers).status_code == 404
    assert client.get('/api/pilot/runs/stream/' + 'e' * 32).status_code == 401


def test_thinking_that_names_its_model_is_withheld_from_the_stream(client, monkeypatch):
    pilot_stream.reset()
    answer = 'Expense one twelfth each month from the start date of the policy. ' * 3

    async def generate(question, task_type, *, on_event):
        on_event(0, 'merge:lab-one/model', 'thinking', 'The user wants a schedule. As Gem')
        on_event(0, 'merge:lab-one/model', 'thinking', 'ini, I should be precise about the dates. ' * 4)
        on_event(0, 'merge:lab-one/model', 'answer', answer)
        on_event(1, 'merge:lab-two/model', 'answer', answer)
        return [draft('merge:lab-one/model', answer), draft('merge:lab-two/model', answer)]

    headers, run = live_run(client, monkeypatch, generate, 'f' * 32)
    events = read_stream(client, headers, 'f' * 32)
    withheld = [e['position'] for e in events if e['type'] == 'withheld']
    assert len(withheld) == 1
    assert 'Gem' not in json.dumps(events)
    assert not [e for e in events if e.get('position') == withheld[0] and e['type'] in ('thinking', 'answer')]
    # The answer itself is clean, so the comparison still goes ahead as it would without streaming.
    assert run['status'] == 'review' and len(run['drafts']) == 2


def test_streaming_off_or_absent_leaves_the_run_unchanged(client, monkeypatch):
    pilot_stream.reset()
    calls = []

    async def generate(question, task_type, **kwargs):
        calls.append(kwargs)
        return [draft('m1', 'One answer to compare.'), draft('m2', 'Another answer to compare.')]

    monkeypatch.setenv('PILOT_STREAMING', 'off')
    headers, run = live_run(client, monkeypatch, generate, '1' * 32)
    assert run['status'] == 'review' and calls[-1] == {}
    assert client.get('/api/pilot/runs/stream/' + '1' * 32, headers=headers).status_code == 404
    monkeypatch.delenv('PILOT_STREAMING')
    response = client.post('/api/pilot/runs', headers=headers, json={'question': 'How should a twelve-month insurance premium be expensed?'})
    assert response.status_code == 200 and calls[-1] == {}
    assert client.post('/api/pilot/runs', headers=headers, json={'question': 'How should this premium be expensed?', 'stream_id': 'nope'}).status_code == 422


def test_pool_generation_passes_live_events_per_slot(monkeypatch):
    monkeypatch.setenv('ARENA_INFERENCE_BACKEND', 'pool')
    monkeypatch.setenv('PILOT_MODELS', 'merge:lab-one/model,merge:lab-two/model')
    monkeypatch.setenv('MERGE_API_KEY', 'test-key')
    fake_client(monkeypatch, streams=[FakeStream(MERGE_STREAM), FakeStream(MERGE_STREAM)])
    seen = []
    results = asyncio.run(pilot_inference.generate('How should a twelve-month insurance premium be expensed?', on_event=lambda *event: seen.append(event)))
    assert [r['model_id'] for r in results] == [model_id for slot, model_id, kind, _ in sorted(e for e in seen if e[2] == 'done')]
    assert {(slot, kind) for slot, _, kind, _ in seen} == {(s, k) for s in (0, 1) for k in ('thinking', 'answer', 'done')}
    assert all(done for _, _, kind, done in seen if kind == 'done')
