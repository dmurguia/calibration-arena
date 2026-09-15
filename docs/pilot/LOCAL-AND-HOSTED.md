# Local CLI testing and hosted API sharing

Current operating choice, 15 September 2026: David tests the flow on his Mac using existing subscription CLI sign-ins. The shared website uses direct OpenAI and Anthropic APIs on Railway. Vercel serves the frontend. These are separate backend configurations, not a per-user billing switch.

| Use | Frontend/API destination | Inference | Credentials |
|---|---|---|---|
| David's routine flow testing | `http://127.0.0.1:8021`, same local origin | `local-cli` | Existing Codex and Claude Code sign-ins on the Mac |
| Hosted testing and friends | Vercel frontend → Railway API | `direct` | API keys in Railway backend service variables |

The current local `backend/.env` was checked and remains `ARENA_INFERENCE_BACKEND=local-cli`. No credentials were read, moved or replaced by this documentation update. Hosted configuration has not been inspected or deployed in this task.

## 1. Keep local testing local

Retain the existing Git-ignored `backend/.env`; do not overwrite it with an example file. Keep:

```dotenv
ARENA_INFERENCE_BACKEND=local-cli
LOCAL_CODEX_MODEL=<model available through your Codex sign-in>
LOCAL_CLAUDE_MODEL=<model available through your Claude Code sign-in>
```

Retain the current working local model IDs and binary paths. API keys are not required for this mode. CLI sign-ins stay with their applications; do not copy their tokens to Railway or Vercel. Confirm the CLIs are signed into the intended subscriptions, since a CLI can also be authenticated using paid API access. Subscription quotas still apply; “local CLI” means the process runs locally, not that the model runs offline.

Start from `/Users/david/Code/benchmark-stadium/pilot-cohort`, using the already installed environment:

```sh
ARENA_INFERENCE_BACKEND=local-cli /Users/david/Code/benchmark-stadium/.venv/bin/python -m uvicorn app.main:app --app-dir backend --env-file backend/.env --host 127.0.0.1 --port 8021 --no-proxy-headers
```

Do not start a second server on an occupied port. This command explicitly selects CLI mode even if an inherited environment has another mode. Open `http://127.0.0.1:8021/`; `/api/pilot/config` should report `inference_backend: local-cli` and `ask_mode: live`. Config readiness is not proof that a CLI login or quota is currently valid.

For this same-origin local build, leave `VITE_API_URL` unset/empty at frontend build time. Do not use a downloaded production environment or `railway run` for routine local testing: it can inject the hosted configuration. The separate Vite development server currently proxies to port 8000; the established port-8021 preview avoids that mismatch and the local CLI origin restrictions.

## 2. Put API secrets in Railway's backend service

Open the existing Railway project, choose the intended hosted environment, select the FastAPI/backend service, then **Variables**. Use **New Variable** or **RAW Editor** to add these values to that service (not the database service):

```dotenv
ARENA_INFERENCE_BACKEND=direct
OPENAI_API_KEY=<OpenAI API key>
ANTHROPIC_API_KEY=<Anthropic API key>
OPENAI_MODEL=<verified OpenAI API model ID>
ANTHROPIC_MODEL=<verified Anthropic API model ID>
PILOT_MAX_OUTPUT_TOKENS=2000
```

The placeholders are instructions, not working values. Retain/configure `PILOT_INVITE_CODE`, `PILOT_ADMIN_TOKEN`, and `ARENA_DATABASE_URL` on durable storage. Use a separate participant dataset from local QA. Set `ARENA_LEGACY_API=0`, `ARENA_AUTO_SEED=0`, and `ARENA_DEV_LOGIN_CODE=0`. Set `ARENA_CORS_ORIGINS` to the exact Vercel frontend HTTPS origin. Do not import the old prototype's wildcard preview-origin or synthetic-seeding settings.

Review Railway's staged changes and deploy them to apply the variables. The deployment must include the current pilot code with the `direct` adapter; adding variables to an older deployed build does not ship the local changes. Confirm `/api/pilot/config` reports `inference_backend: direct` and complete one actual paired API request before distributing.

Railway documents service-scoped variables and their staged deployment in [Using Variables](https://docs.railway.com/variables). This guide specifies configuration; it does not claim the Railway service is already configured.

## 3. Point Vercel at Railway

In the Vercel frontend project, open **Settings → Environment Variables**. For the friend-facing Production deployment, set:

```dotenv
VITE_API_URL=https://<your-backend-domain>
```

Use the Railway backend's public HTTPS origin without `/api` appended; the app adds its API paths. Redeploy the frontend to use the new build-time value. No OpenAI or Anthropic key belongs in this frontend project or in a `VITE_` variable.

A Vercel Preview deployment is still a hosted browser app. If it points at the same Railway backend, it uses API credits and that backend's data. Routine no-API testing stays on localhost. If a hosted QA environment is later needed, give it a separate backend/database and budget; it still uses APIs. Vercel explains environment scoping and deployment behavior in [Environment Variables](https://vercel.com/docs/environment-variables).

## 4. Compare different models

The implemented direct adapter selects one OpenAI model via `OPENAI_MODEL` and one Anthropic model via `ANTHROPIC_MODEL`. Change either ID on Railway and deploy the change to use that new pair for subsequent open prompts. Verify each candidate supports this app's text endpoint/configuration and the account has access. API model availability and CLI model availability are separate; a CLI alias is not automatically a valid API ID.

No new key is required per model when the existing provider account/project key already has access. The current code does not provide an admin model picker, a rotating pool, or OpenAI-vs-OpenAI / Anthropic-vs-Anthropic pairing. Those would require a small pair-configuration extension, not more credentials pasted into the frontend.

For the first friend collection, keep a fixed pair. Open-prompt records preserve requested/resolved models where available. Frozen shared cases keep their original outputs even if environment model IDs later change; changing their pair requires generating a new approved pack/version. Do not relabel old outputs or pool votes from different configurations as one comparison. Local CLI testing checks the journey, not equivalence to API results.

## Cost boundary and remaining checks

- Everyone opening the hosted website—including David—uses the hosted backend's API configuration.
- A fresh open comparison normally makes two provider calls; each follow-up makes two more. Serving an already frozen case does not call models again.
- There is no automatic fallback from CLI failure to paid APIs, or from API failure to authored answers.
- Token limits help bound an individual output but are not a total spending cap. Shared spend/concurrency controls remain COR-357; use deliberate, limited API smoke tests until that release work is complete.
- Subscription sign-in and API billing are different authentication paths; see [OpenAI authentication](https://learn.chatgpt.com/docs/auth). This setup uses each locally signed-in CLI only for David's local development and API credentials for sharing.
