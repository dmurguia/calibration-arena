# Deploying Calibration Arena — Railway (API + data) · Vercel (frontend)

> Current ten-accountant setup: [Local CLI testing and hosted API sharing](pilot/LOCAL-AND-HOSTED.md). Use this newer guide for credentials and pilot settings. The older prototype instructions below include synthetic seeding, dev login and wildcard preview CORS; those settings do not apply to the current participant release.

One repo, two deploy targets. Railway runs the FastAPI backend and owns the
data; Vercel builds `frontend/` and gives per-PR preview URLs. No local
environment needed once this is wired — push to `main` and both redeploy.

## Railway — backend service

1. Railway → **New Project** (name it `calibrated`) → **Deploy from GitHub repo**
   → `dmurguia/calibration-arena`.
2. On the service: **Settings → Root Directory** = `backend`. Nixpacks detects
   Python via `backend/requirements.txt`; the start command, health check
   (`/api/health`) and restart policy come from `backend/railway.json`.
3. **Attach a volume** (service → right-click → Attach Volume), mount path
   `/data`. Railway's filesystem is ephemeral — without the volume every
   redeploy wipes votes, users, and snapshots.
4. **Variables** on the service:

   | Variable | Value | Why |
   |---|---|---|
   | `ARENA_DATABASE_URL` | `sqlite:////data/arena.db` | DB lives on the volume (four slashes = absolute path) |
   | `ARENA_SECRET_KEY` | long random string (`openssl rand -hex 32`) | session token signing |
   | `ARENA_CORS_ORIGINS` | the Vercel prod origin, e.g. `https://calibration-arena.vercel.app` | browser API calls |
   | `ARENA_CORS_ORIGIN_REGEX` | `https://.*\.vercel\.app` | Vercel preview deploys |
   | `ARENA_AUTO_SEED` | `1` (default) | first boot on an empty volume seeds the demo roster/boards |

5. **Settings → Networking → Generate Domain** — this is the public API URL
   the frontend needs.

First boot on a fresh volume auto-seeds (roster, synthetic votes, snapshots),
so the boards render immediately. Sign-in codes surface in the UI (dev-code
mode) until a real email provider is wired.

## Vercel — frontend project

1. Vercel → **Add New Project** → import `dmurguia/calibration-arena`.
2. **Root Directory** = `frontend` (Framework preset: Vite — auto-detected;
   build `npm run build`, output `dist`).
3. **Environment variable**: `VITE_API_URL` = the Railway domain from step 5
   above (no trailing slash), applied to Production and Preview.
4. Deploy. `frontend/vercel.json` carries the SPA rewrite so React Router
   deep links (`/leaderboards`, `/judge/…`) resolve.

Every PR now gets a preview URL; the preview talks to the same Railway
backend (allowed by the origin regex).

## Custom domains (later — after the brand rename is verified live)

- Vercel project ← `calibrationarena.ai` (Cloudflare CNAME per Vercel's
  instructions; DNS-only/grey cloud if the proxy causes redirect loops).
- Railway service ← `api.calibrationarena.ai` (custom domain on the service),
  then update `VITE_API_URL` and `ARENA_CORS_ORIGINS` to match.

## Headless setup (what Claude does with a token)

- **Railway**: a **project token** (Railway project → Settings → Tokens)
  scopes to one project + environment. It drives the CLI (`RAILWAY_TOKEN=…
  railway up --service <name>`) and the project-scoped GraphQL API — enough to
  create services, set variables, attach volumes, and deploy, but it cannot
  touch other projects or the account. Revoke it from the same screen after
  setup.
- **Vercel**: a personal **token** (vercel.com/account/settings/tokens) drives
  the CLI (`vercel --token …`) and REST API to create/link the project, set
  env vars, and deploy. Scope it to your personal team, set expiry to the
  shortest option, and delete it after setup.

Anything pasted into a chat is stored in the conversation — always use
scoped, short-lived tokens and revoke them once the wiring is done.

## Local dev (unchanged)

```
make dev-backend    # uvicorn :8000, SQLite in backend/
make dev-frontend   # vite :5173, /api proxied to :8000
```
