"""Loopback-only CLI inference using the owner's existing signed-in applications."""
import asyncio
import hashlib
import json
import os
import shutil
import signal
import tempfile
from datetime import datetime, timezone
from pathlib import Path

# One comparison at a time, two independent CLI processes in parallel.
_PAIR_LOCK = asyncio.Lock()
_TIMEOUT = 120
_OUTPUT_LIMIT = 1_000_000
_CODEX_APP = '/Applications/Codex.app/Contents/Resources/codex'


def binaries():
    codex = os.getenv('LOCAL_CODEX_BIN') or (_CODEX_APP if Path(_CODEX_APP).is_file() else shutil.which('codex'))
    claude = os.getenv('LOCAL_CLAUDE_BIN') or shutil.which('claude')
    return codex, claude


def ready():
    return all(binaries()) and all(os.getenv(k) for k in ('LOCAL_CODEX_MODEL', 'LOCAL_CLAUDE_MODEL'))


def child_env():
    # Preserve normal CLI authentication discovery without forwarding API keys,
    # app secrets, nested-agent state or the parent task's instruction context.
    return {k: v for k, v in os.environ.items() if k in {
        'HOME', 'PATH', 'USER', 'LOGNAME', 'TMPDIR', 'LANG', 'LC_ALL',
        'CODEX_HOME', 'CLAUDE_CONFIG_DIR', 'SSL_CERT_FILE', 'SSL_CERT_DIR',
    }}


def commands(directory, instructions):
    codex, claude = binaries()
    codex_args = [codex, 'exec', '--ignore-user-config', '--ephemeral', '--skip-git-repo-check',
                  '--sandbox', 'read-only', '--json', '--color', 'never',
                  '--model', os.environ['LOCAL_CODEX_MODEL'], '-C', directory,
                  '-c', 'approval_policy="never"', '-c', 'web_search="disabled"',
                  '-c', 'project_doc_max_bytes=0', '-c', 'model_reasoning_effort="low"',
                  '-c', 'developer_instructions=' + json.dumps(instructions)]
    for feature in ('shell_tool', 'unified_exec', 'apps', 'plugins', 'browser_use',
                    'computer_use', 'view_image', 'image_generation', 'multi_agent',
                    'multi_agent_v2', 'code_mode', 'code_mode_host', 'memories', 'hooks',
                    'goals', 'sleep_tool', 'workspace_dependencies', 'skill_search', 'tool_suggest'):
        codex_args += ['--disable', feature]
    codex_args += ['-']
    claude_args = [claude, '-p', '--safe-mode', '--no-session-persistence',
                   '--output-format', 'json', '--tools', '', '--strict-mcp-config',
                   '--mcp-config', '{"mcpServers":{}}', '--disable-slash-commands',
                   '--no-chrome', '--permission-mode', 'dontAsk',
                   '--model', os.environ['LOCAL_CLAUDE_MODEL'], '--effort', 'low',
                   '--system-prompt', instructions]
    return codex_args, claude_args


async def execute(args, prompt, directory):
    process = await asyncio.create_subprocess_exec(
        *args, cwd=directory, env=child_env(), stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, start_new_session=True)

    async def read_bounded(stream):
        data = bytearray()
        while chunk := await stream.read(8192):
            data.extend(chunk)
            if len(data) > _OUTPUT_LIMIT:
                raise ValueError('Local response exceeded the output limit.')
        return bytes(data)

    async def communicate():
        process.stdin.write(prompt.encode())
        await process.stdin.drain()
        process.stdin.close()
        stdout, stderr = await asyncio.gather(read_bounded(process.stdout), read_bounded(process.stderr))
        await process.wait()
        # Never surface stderr: a CLI can include account details or local paths.
        if process.returncode:
            raise ValueError('A local model request failed. Check the CLI sign-in and usage limits.')
        return stdout.decode('utf-8')

    try:
        return await asyncio.wait_for(communicate(), timeout=_TIMEOUT)
    finally:
        if process.returncode is None:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            await process.wait()


def parse_codex(raw):
    events = [json.loads(line) for line in raw.splitlines() if line.strip()]
    if any(e.get('type') in ('error', 'turn.failed') for e in events):
        raise ValueError('Codex did not complete the response.')
    items = [e['item'] for e in events if e.get('type') == 'item.completed']
    # This bundled CLI emits a startup diagnostic when the intentionally disabled
    # code-mode host is unavailable. It is not a model tool call or a failed turn.
    diagnostic = 'Code Mode is unavailable because code-mode host is disabled. Code mode will fail closed; enable `features.code_mode_host` and install `codex-code-mode-host`.'
    items = [i for i in items if not (i.get('type') == 'error' and i.get('message') == diagnostic)]
    if any(i.get('type') not in ('agent_message', 'reasoning') for i in items):
        raise ValueError('Local comparison attempted to use a tool.')
    messages = [i.get('text', '') for i in items if i.get('type') == 'agent_message']
    if not messages or not any(e.get('type') == 'turn.completed' for e in events):
        raise ValueError('Codex returned no complete answer.')
    # This CLI event schema does not report the resolved model ID.
    return messages[-1], None


def parse_claude(raw):
    result = json.loads(raw)
    if result.get('is_error') or result.get('subtype') != 'success' or result.get('permission_denials'):
        raise ValueError('Claude did not complete the response.')
    model_ids = list(result.get('modelUsage', {}))
    return result.get('result', ''), model_ids[0] if len(model_ids) == 1 else None


async def generate_local(question, instructions, task_type):
    if not ready():
        raise ValueError('Configure both local CLIs and model IDs first.')
    if _PAIR_LOCK.locked():
        raise ValueError('Another local comparison is running. Try again when it finishes.')
    async with _PAIR_LOCK:
        with tempfile.TemporaryDirectory(prefix='calibrated-models-') as directory:
            args = commands(directory, instructions)
            results = await asyncio.gather(*(execute(a, question, directory) for a in args), return_exceptions=True)
        if any(isinstance(r, BaseException) for r in results):
            raise ValueError('Both local answers could not be generated. Check CLI sign-in or usage limits and try again.')
        drafts = []
        for name, model, raw, parse in zip(('Codex', 'Claude Code'),
                (os.environ['LOCAL_CODEX_MODEL'], os.environ['LOCAL_CLAUDE_MODEL']),
                results, (parse_codex, parse_claude)):
            try:
                content, actual = parse(raw)
                if not isinstance(content, str) or not content.strip():
                    raise ValueError('Empty response')
            except (ValueError, KeyError, TypeError) as exc:
                raise ValueError('A local CLI returned an incomplete response.') from exc
            drafts.append({
                'artifact_id': hashlib.sha256((name + model + content).encode()).hexdigest(),
                'text': content.strip(), 'author': f'{name} · {actual or model}',
                'model_id': model, 'actual_model_id': actual, 'origin': 'local-cli',
                'cli': name, 'checks': [], 'task_type': task_type,
                'review_note': 'Generated through a signed-in CLI. No independently verified ground truth.',
                'prompt_version': 'ask-local-v1',
                'request_sha256': hashlib.sha256(json.dumps({'question': question, 'instructions': instructions, 'model': model}, sort_keys=True).encode()).hexdigest(),
                'settings': {'effort': 'low', 'tools': False, 'fresh_session': True, 'timeout_seconds': _TIMEOUT,
                             'temperature': None, 'note': 'CLI harnesses differ; API generation settings are not matched.'},
                'generated_at': datetime.now(timezone.utc).isoformat(),
            })
        return drafts
