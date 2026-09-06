# Local Codex and Claude Code bridge

Connected and smoke-tested on 6 September 2026. The open composer now uses two real signed-in CLI calls when `ARENA_INFERENCE_BACKEND=local-cli`. The five explicit authored samples are unchanged.

## Current machine

- Codex: `/Applications/Codex.app/Contents/Resources/codex`, authenticated through ChatGPT; requested model `gpt-6-astra`.
- Claude Code: `/Users/david/.local/bin/claude`, authenticated through claude.ai with Max; requested model `fable[1m]` from the existing user configuration.
- The Homebrew `codex` launcher currently fails with a missing native executable. The integration prefers the working app binary; no global installation was modified.
- The app is served on `http://127.0.0.1:8021`. These CLIs call hosted models using the signed-in accounts; they are not local model weights. Normal account usage limits apply. No OAuth tokens are extracted, copied or sent to the browser.

## Restart

From the worktree root, after building the frontend:

```bash
ARENA_INFERENCE_BACKEND=local-cli \
LOCAL_CODEX_MODEL=gpt-6-astra \
LOCAL_CLAUDE_MODEL='fable[1m]' \
/Users/david/Code/benchmark-stadium/.venv/bin/python -m uvicorn app.main:app \
  --app-dir backend --host 127.0.0.1 --port 8021 --no-proxy-headers
```

Stop only the existing server owned by this task before restarting. Use one worker. `LOCAL_CODEX_BIN` and `LOCAL_CLAUDE_BIN` can override executable paths. The usual founder token can be provided separately; it is not needed for prompting. A sandboxed terminal may be unable to access macOS Keychain even when the normal CLI is signed in.

To switch back, set `ARENA_INFERENCE_BACKEND=openrouter`, configure the OpenRouter key, two exact model IDs and invitation code from `.env.pilot.example`, and restart. Historical records keep their original source and settings.

## Execution and storage

The same exact user prompt is sent over stdin to each CLI with the same accounting/task instructions. Commands use argument arrays, never a shell. Each comparison uses a fresh temporary directory, Codex ephemeral execution and Claude's no-session-persistence mode. User/project customizations, external integrations and execution tools are disabled for these calls; Codex also runs read-only. The known Codex startup diagnostic about its deliberately disabled code-mode host is ignored only by exact message match; actual errors/tool events are rejected.

One pair runs at a time, with both processes in parallel. Each has a 120-second deadline, bounded output, and process-group cleanup on cancellation/timeout. A partial or failed result never becomes a sample answer. The existing per-profile daily limit remains in force.

The web middleware rejects remote clients, non-local Host values, cross-origin browser requests and forwarded/proxied requests while the local backend is selected. This bridge is for the owner testing on this computer, not a public subscription-backed inference service.

The normal frozen run record stores `mode=local-cli`, CLI name, requested model, resolved model ID when the CLI reports one unambiguously, prompt hash/version, generation timestamp and local settings. The completed smoke test did not expose an unambiguous resolved model ID from either CLI, so `actual_model_id` remains null; displayed labels identify the requested selections. The model names stay hidden until judgment. Notebook distinguishes local CLI output from authored samples and OpenRouter output.

These are comparisons of CLI outputs. Their underlying harnesses differ, and matched temperature/top-p cannot be enforced here. Do not combine their votes with a controlled OpenRouter model comparison. OpenRouter's ZDR request does not apply to these signed-in CLIs; the How it works disclosure follows the selected backend. Ephemeral CLI sessions do not erase the app's intentionally saved notebook or establish provider-side retention guarantees.

## Verification

- 41 backend tests passed; final targeted local tests: 7 passed. One upstream Starlette/httpx deprecation warning.
- TypeScript/Vite build and `git diff --check` passed.
- Synthetic browser question used $2,400 insurance paid July 1. Both generated responses addressed the actual figures and July adjustment. The full pair took 9.2 seconds in this one test, not a latency guarantee.
- Blind pair → saved readiness/preference/reasons/confidence → revealed requested model names. The saved record has source `local-cli` and ID `62d63bc69e909f607a8f18a261072fde` in the local preview database. This is integration QA, not recruited-accountant evidence.
- Tests cover literal stdin handling, stripped secret environment, fresh sessions/tool settings, timeout cleanup, partial failure, parser errors, source/blinding, and loopback/origin restrictions.

Supported interfaces: [Codex non-interactive mode](https://learn.chatgpt.com/docs/non-interactive-mode) and [Claude Code CLI reference](https://code.claude.com/docs/en/cli-reference). Actual flags were also checked against both installed binaries.
