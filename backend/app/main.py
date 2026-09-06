from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .config import get_settings
from .db import init_db
from .routers import auth, battles, catalog, leaderboard, releases, pilot

def _maybe_seed() -> None:
    """First boot on a fresh volume: seed the demo roster/votes so the boards
    aren't empty. No-op whenever any arena model already exists."""
    if os.getenv("ARENA_AUTO_SEED", "1") != "1":
        return
    from sqlalchemy import select

    from .db import SessionLocal
    from .models import ArenaModel

    with SessionLocal() as db:
        if db.execute(select(ArenaModel.id).limit(1)).first() is not None:
            return
    import subprocess
    import sys

    subprocess.run(
        [sys.executable, "-m", "pipeline.seed"],
        cwd=str(Path(__file__).resolve().parent.parent),
        check=True,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    if os.getenv("ARENA_LEGACY_API", "0") == "1":
        _maybe_seed()
    yield


app = FastAPI(title=get_settings().app_name, lifespan=lifespan)

# Dev servers are always allowed; hosted frontends come from env:
#   ARENA_CORS_ORIGINS       comma-separated exact origins (the Vercel prod URL)
#   ARENA_CORS_ORIGIN_REGEX  e.g. https://.*\.vercel\.app for preview deploys
_cors_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
_cors_origins += [o.strip() for o in os.getenv("ARENA_CORS_ORIGINS", "").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_origin_regex=os.getenv("ARENA_CORS_ORIGIN_REGEX") or None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def local_inference_boundary(request: Request, call_next):
    if os.getenv("ARENA_INFERENCE_BACKEND") == "local-cli":
        loopback = {"127.0.0.1", "::1", "localhost"}
        origin = request.headers.get("origin")
        if (not request.client or request.client.host not in loopback
                or request.url.hostname not in loopback
                or (origin and origin != str(request.base_url).rstrip("/"))
                or request.headers.get("sec-fetch-site") == "cross-site"
                or request.headers.get("x-forwarded-for")
                or request.headers.get("forwarded")):
            return JSONResponse({"detail": "Local model access is available only from this computer."}, status_code=403)
    return await call_next(request)


app.include_router(pilot.router)
# Archive prototype routes explicitly; never expose seeded boards in the pilot.
if os.getenv("ARENA_LEGACY_API", "0") == "1":
    for legacy_router in (auth, catalog, battles, leaderboard, releases):
        app.include_router(legacy_router.router)



@app.get("/api/health")
def health() -> dict:
    return {"ok": True, "mode": get_settings().generation_mode}


# Serve the built frontend (single-process deploy). `npm run build` in
# frontend/ writes to frontend/dist.
_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if _dist.exists():
    app.mount("/assets", StaticFiles(directory=_dist / "assets"), name="assets")

    @app.get("/{path:path}")
    def spa(path: str) -> FileResponse:
        candidate = (_dist / path).resolve()
        if path and candidate.is_relative_to(_dist.resolve()) and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(_dist / "index.html")
