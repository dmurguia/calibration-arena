"""Live view of a comparison while both models generate.

Display only. The stored artifact, hashes, usage and failure rules come from the
provider call exactly as without streaming; nothing here feeds the audit record.
A browser subscribes to a channel it named, the run publishes blinded events into
it, and the POST /runs response stays the source of truth.
"""
import asyncio
import json
import os
import secrets
import time

from .pilot_audit import hygiene, thinking_hygiene

# Text is released this many characters behind what has been checked, so a name
# split across two provider chunks is caught before any of it is shown.
HOLDBACK = 80
CHECK_CONTEXT = 200
MAX_EVENTS = 20000
CHANNEL_TTL_SECONDS = 600
KEEPALIVE_SECONDS = 15

_channels = {}


def enabled():
    return os.getenv('PILOT_STREAMING', 'on').strip().lower() not in ('off', '0', 'false')


class Channel:
    def __init__(self, owner):
        self.owner = owner
        self.events = []
        self.closed = False
        self.created = time.monotonic()
        self.changed = asyncio.Event()

    def publish(self, event):
        if self.closed or len(self.events) >= MAX_EVENTS:
            return
        self.events.append(event)
        self.changed.set()

    def close(self):
        if not self.closed:
            self.events.append({'type': 'end'})
            self.closed = True
            self.changed.set()


def _sweep():
    cutoff = time.monotonic() - CHANNEL_TTL_SECONDS
    for key in [k for k, c in _channels.items() if c.created < cutoff]:
        _channels.pop(key).close()


def open_channel(stream_id, owner):
    """The channel for this id, created on first touch. None when another person owns it."""
    _sweep()
    channel = _channels.get(stream_id)
    if channel is None:
        channel = _channels[stream_id] = Channel(owner)
    return channel if channel.owner == owner else None


def reset():
    _channels.clear()


async def subscribe(channel):
    """Server-sent events for one browser: replay what was published, then follow."""
    sent = 0
    while True:
        while sent < len(channel.events):
            yield 'data: ' + json.dumps(channel.events[sent], ensure_ascii=False) + '\n\n'
            sent += 1
        if channel.closed:
            return
        channel.changed.clear()
        if sent < len(channel.events) or channel.closed:
            continue
        try:
            await asyncio.wait_for(channel.changed.wait(), KEEPALIVE_SECONDS)
        except asyncio.TimeoutError:
            yield ': keepalive\n\n'


class Panel:
    """One model's side. Releases text only after it passes the identity checks."""

    def __init__(self, publish, position, supplied):
        self.publish = publish
        self.position = position
        self.supplied = supplied
        self.text = {'thinking': '', 'answer': ''}
        self.sent = {'thinking': 0, 'answer': 0}
        self.withheld = False
        self.flags = []

    def _check(self, kind):
        window = self.text[kind][max(0, self.sent[kind] - CHECK_CONTEXT):]
        flags = thinking_hygiene(window, self.supplied) if kind == 'thinking' else hygiene(window, self.supplied)
        if flags:
            self.withheld = True
            self.flags = flags
            self.publish({'type': 'withheld', 'position': self.position})
        return not flags

    def _release(self, kind, upto):
        if upto > self.sent[kind]:
            self.publish({'type': kind, 'position': self.position, 'text': self.text[kind][self.sent[kind]:upto]})
            self.sent[kind] = upto

    def feed(self, kind, delta):
        if kind not in self.text or not isinstance(delta, str) or not delta:
            return
        if kind == 'answer':
            self.flush('thinking')
        self.text[kind] += delta
        if self.withheld or not self._check(kind):
            return
        self._release(kind, len(self.text[kind]) - HOLDBACK)

    def flush(self, kind):
        """Everything received so far has been checked as a whole, so the tail can go out."""
        if not self.withheld and self.sent[kind] < len(self.text[kind]) and self._check(kind):
            self._release(kind, len(self.text[kind]))

    def finish(self, complete):
        self.flush('thinking')
        self.flush('answer')
        self.publish({'type': 'state', 'position': self.position, 'state': 'complete' if complete else 'stopped'})


class Relay:
    """Maps provider events to blinded A/B panels.

    The left/right order is fixed before the first token so the panels a person
    watches are the panels they vote on: a continued comparison keeps its
    order, a new one gets a coin flip (the pool pick is already random).
    """

    def __init__(self, channel, pair_order, supplied):
        self.channel = channel
        self.pair_order = list(pair_order or [])
        self.flip = secrets.randbits(1) if not self.pair_order else 0
        self.supplied = supplied
        self.panels = {}

    def position(self, slot, model_id):
        if self.pair_order:
            return 'ab'[self.pair_order.index(model_id)] if model_id in self.pair_order else None
        return 'ab'[slot ^ self.flip] if slot in (0, 1) else None

    def _panel(self, slot, model_id):
        position = self.position(slot, model_id)
        if position is None:
            return None
        if position not in self.panels:
            self.panels[position] = Panel(self.channel.publish, position, self.supplied)
        return self.panels[position]

    def on_event(self, slot, model_id, kind, text=None):
        panel = self._panel(slot, model_id)
        if panel is None:
            return
        if kind == 'done':
            panel.finish(bool(text))
        else:
            panel.feed(kind, text)

    def order(self, drafts):
        if self.flip:
            drafts.reverse()
        return drafts
