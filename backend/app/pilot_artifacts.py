"""Split a model response into its narrative and its deliverables (artifacts).

An artifact is a journal entry, schedule, reconciliation, invoice, memo or table the
reviewer compares as a thing in itself. The raw response text is never altered; the
split is derived from it so the stored bytes, hashes and exports stay the verbatim
model output. Models are asked to fence each deliverable as

    ```artifact kind="journal-entry" title="Proposed entry"
    | Account | Debit | Credit |
    ...
    ```

Responses that ignore the convention still get their markdown tables and Dr/Cr
blocks lifted out, so the two columns compare on the same footing.
"""
import re

KINDS = ('journal-entry', 'schedule', 'reconciliation', 'invoice', 'memo', 'table', 'workpaper')
LABELS = {'journal-entry': 'Journal entry', 'schedule': 'Schedule', 'reconciliation': 'Reconciliation',
          'invoice': 'Invoice', 'memo': 'Memo', 'table': 'Table', 'workpaper': 'Workpaper'}
MAX_ARTIFACTS = 8

_FENCE = re.compile(r'(?ms)^(?P<indent>[ \t]*)```[ \t]*artifact\b(?P<attrs>[^\n]*)\n(?P<body>.*?)^(?P=indent)```[ \t]*$')
_ATTR = re.compile(r'(\w[\w-]*)\s*=\s*"([^"]*)"|(\w[\w-]*)\s*=\s*\'([^\']*)\'')
_CODE = re.compile(r'(?ms)^[ \t]*```[^\n]*\n.*?^[ \t]*```[ \t]*$')
_TABLE = re.compile(r'(?m)^[ \t]*\|.*\|[ \t]*\n[ \t]*\|?[ \t:]*-{2,}[-| :\t]*\n(?:[ \t]*\|.*\|[ \t]*\n?)+')
_DRCR = re.compile(r'(?i)^\s*(?:dr|cr|debit|credit)\b')
_HEADING = re.compile(r'(?m)^(?:#{1,6}[ \t]+(?P<h>[^\n]+?)[ \t#]*|\*\*(?P<b>[^*\n]+?)\*\*:?[ \t]*)$')


def _attrs(raw):
    out = {}
    for key, value, key2, value2 in _ATTR.findall(raw or ''):
        out[(key or key2).lower()] = (value if key else value2).strip()
    return out


def _kind(value, body):
    value = (value or '').strip().lower().replace('_', '-').replace(' ', '-')
    if value in KINDS:
        return value
    if value in ('je', 'entry', 'entries', 'journal', 'journal-entries', 'posting', 'postings'):
        return 'journal-entry'
    if value in ('recon', 'bank-reconciliation'):
        return 'reconciliation'
    if value in ('aging', 'ar-aging', 'amortization', 'amortization-schedule'):
        return 'schedule'
    lines = [line for line in body.splitlines() if line.strip()]
    if lines and sum(bool(_DRCR.match(line)) for line in lines) >= 2:
        return 'journal-entry'
    return 'table' if _TABLE.search(body + '\n') else 'workpaper'


def _title_before(text, start, kind):
    """The heading or bold label directly above the block and where it starts, else the kind's label."""
    above = text[:start].rstrip()
    tail = above[-400:]
    offset = len(above) - len(tail)
    for match in _HEADING.finditer(tail):
        if not above[offset + match.end():].strip():
            return (match.group('h') or match.group('b')).strip().rstrip(':'), offset + match.start()
    return LABELS[kind], start


def _refine(kind, title):
    """A heading above a plain table often names the deliverable better than its shape does."""
    if kind != 'table':
        return kind
    lowered = title.lower()
    for word, named in (('reconcil', 'reconciliation'), ('aging', 'schedule'), ('schedule', 'schedule'), ('amortiz', 'schedule'),
                        ('invoice', 'invoice'), ('journal', 'journal-entry'), ('entry', 'journal-entry'), ('entries', 'journal-entry')):
        if word in lowered:
            return named
    return kind


def _looks_like_entry(body):
    lines = [line for line in body.splitlines() if line.strip()]
    return len(lines) >= 2 and sum(bool(_DRCR.match(line)) for line in lines) >= 2


def split(text):
    """Return (narrative, artifacts). Both derive from text; text itself is untouched."""
    if not isinstance(text, str) or not text.strip():
        return text or '', []
    artifacts, spans = [], []

    def add(start, end, kind, title, content, source, from_heading=False):
        if len(artifacts) >= MAX_ARTIFACTS or not content.strip():
            return
        if any(s <= start < e or s < end <= e for s, e in spans):
            return
        if from_heading:
            kind = _refine(kind, title)
        artifacts.append({'id': f'{kind}-{len(artifacts) + 1}', 'kind': kind, 'title': title[:120],
                          'format': 'markdown', 'content': content.strip('\n'), 'source': source, 'from_heading': from_heading})
        spans.append((start, end))

    for match in _FENCE.finditer(text):
        attrs = _attrs(match.group('attrs'))
        kind = _kind(attrs.get('kind') or attrs.get('type'), match.group('body'))
        title = attrs.get('title') or attrs.get('name')
        heading, start = _title_before(text, match.start(), kind)
        add(start if not title else match.start(), match.end(), kind, title or heading, match.group('body'), 'fenced', not title)
    for match in _CODE.finditer(text):
        body = '\n'.join(match.group(0).splitlines()[1:-1])
        if _looks_like_entry(body):
            title, start = _title_before(text, match.start(), 'journal-entry')
            add(start, match.end(), 'journal-entry', title, body, 'code-block', True)
    for match in _TABLE.finditer(text + '\n'):
        body = match.group(0)
        kind = 'journal-entry' if re.search(r'(?i)\|\s*(debit|credit|dr|cr)\s*\|', body.splitlines()[0]) else 'table'
        title, start = _title_before(text, match.start(), kind)
        add(start, min(match.end(), len(text)), kind, title, body, 'table', True)

    if not artifacts:
        return text, []
    for artifact in artifacts:
        artifact.setdefault('from_heading', False)
    order = sorted(range(len(artifacts)), key=lambda i: spans[i][0])
    artifacts = [artifacts[i] for i in order]
    spans = [spans[i] for i in order]
    for n, artifact in enumerate(artifacts, 1):
        artifact['id'] = f"{artifact['kind']}-{n}"
    narrative, cursor = [], 0
    for (start, end), artifact in zip(spans, artifacts):
        artifact.pop('from_heading')
        label = LABELS[artifact['kind']] if artifact['title'] == LABELS[artifact['kind']] else f"{LABELS[artifact['kind']]}: {artifact['title']}"
        narrative.append(text[cursor:start].rstrip('\n') + f"\n\n*↓ {label}*\n\n")
        cursor = end
    narrative.append(text[cursor:].lstrip('\n'))
    joined = re.sub(r'\n{3,}', '\n\n', ''.join(narrative)).strip()
    return joined, artifacts


def attach(draft):
    """Add narrative and artifacts to a draft dict in place and return it."""
    narrative, artifacts = split(draft.get('text', ''))
    draft['narrative'] = narrative
    draft['artifacts'] = artifacts
    return draft


def public(draft):
    """The blind-safe artifact view: derived from the text, never from identity fields."""
    if 'artifacts' in draft and 'narrative' in draft:
        return {'narrative': draft['narrative'], 'artifacts': draft['artifacts']}
    narrative, artifacts = split(draft.get('text', ''))
    return {'narrative': narrative, 'artifacts': artifacts}
