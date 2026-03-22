import os
import sys
import ipaddress
import time
import threading
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Ensure the backend and its parent are in the path for robust imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# ── Global rate limiter (shared across all routers) ─────────────────────────
limiter = Limiter(key_func=get_remote_address)

# ── In-memory auth-failure metrics (lightweight monitoring) ─────────────────
_metrics_lock = threading.Lock()
_auth_metrics: dict = {
    "login_failures": 0,
    "token_invalid": 0,
    "permission_denied": 0,
    "rate_limited": 0,
    "window_start": time.time(),
}

def record_metric(key: str) -> None:
    with _metrics_lock:
        _auth_metrics[key] = _auth_metrics.get(key, 0) + 1

PRIVATE_NETWORK_ONLY = False
api_router = None
startup_error: Optional[str] = None

# Fail-safe startup: keep the process alive even if some API modules fail to import.
try:
    from app.api.router import api_router as imported_api_router
    from app.core.config import PRIVATE_NETWORK_ONLY as imported_private_network_only

    api_router = imported_api_router
    PRIVATE_NETWORK_ONLY = imported_private_network_only
except Exception as exc:  # noqa: BLE001
    startup_error = f"Startup import failure: {exc.__class__.__name__}: {exc}"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """On startup: run Alembic migrations (PostgreSQL) or create_all (SQLite/local dev)."""
    try:
        from app.core.database import engine, Base  # noqa: F401 — triggers model registration
        # Import all models so Base.metadata knows about them
        import app.models.user  # noqa: F401
        import app.models.blood  # noqa: F401
        import app.models.cases  # noqa: F401
        import app.models.personnel  # noqa: F401
        import app.models.injuries  # noqa: F401
        import app.models.medications  # noqa: F401
        import app.models.vitals  # noqa: F401
        import app.models.procedures  # noqa: F401
        import app.models.march  # noqa: F401
        import app.models.evacuation  # noqa: F401
        import app.models.events  # noqa: F401
        import app.models.documents  # noqa: F401
        import app.models.idempotency  # noqa: F401
        import app.models.sync_queue  # noqa: F401
        import app.models.audit  # noqa: F401
        import app.models.revoked_token  # noqa: F401
        from app.core.config import DATABASE_URL as _DB_URL
        if _DB_URL.startswith("postgresql"):
            # PostgreSQL (Neon/prod): apply all pending migrations via Alembic.
            # This is the only correct approach — create_all bypasses migration history.
            import asyncio
            from alembic.config import Config as AlembicConfig
            from alembic import command as alembic_command

            def _run_alembic_upgrade() -> None:
                _ini = os.path.join(os.path.dirname(os.path.abspath(__file__)), "alembic.ini")
                _scripts = os.path.join(os.path.dirname(os.path.abspath(__file__)), "migrations")
                cfg = AlembicConfig(_ini)
                cfg.set_main_option("script_location", _scripts)
                alembic_command.upgrade(cfg, "head")

            await asyncio.to_thread(_run_alembic_upgrade)
        else:
            # SQLite (local dev / fallback): create tables directly — fast, no history needed.
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
        # Prune expired revoked JTIs at startup to keep the table small
        try:
            from sqlalchemy import delete as sa_delete
            from datetime import datetime, timezone
            from app.models.revoked_token import RevokedToken
            async with engine.begin() as conn:
                await conn.execute(
                    sa_delete(RevokedToken).where(
                        RevokedToken.expires_at < datetime.now(timezone.utc)
                    )
                )
        except Exception:  # noqa: BLE001
            pass  # Non-fatal: pruning is a housekeeping optimisation
    except Exception as exc:  # noqa: BLE001
        # Non-fatal: log but continue (tables may already exist or DB is managed externally)
        import logging
        logging.getLogger(__name__).warning("Auto-migrate warning: %s", exc)
    yield


app = FastAPI(title="MEDEVAK API", lifespan=lifespan)

# ── Wire SlowAPI to the app (MUST be before routes) ─────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # → 429


def _is_private_client_ip(value: str) -> bool:
    try:
        ip = ipaddress.ip_address(value)
        return bool(ip.is_private or ip.is_loopback or ip.is_link_local)
    except ValueError:
        return False


@app.middleware("http")
async def enforce_private_network_only(request: Request, call_next):
    if not PRIVATE_NETWORK_ONLY:
        return await call_next(request)

    source_ip = None
    xff = request.headers.get("x-forwarded-for")
    if xff:
        source_ip = xff.split(",")[0].strip()
    elif request.client:
        source_ip = request.client.host

    if source_ip and _is_private_client_ip(source_ip):
        return await call_next(request)

    return JSONResponse(
        status_code=403,
        content={
            "detail": "Network policy: access allowed only via private LAN/VPN. Public networks are blocked.",
        },
    )

@app.middleware("http")
async def track_auth_metrics(request: Request, call_next):
    response = await call_next(request)
    path = request.url.path
    if path.startswith("/api/auth") or path.startswith("/api/"):
        if response.status_code == 401:
            record_metric("token_invalid")
        elif response.status_code == 403:
            record_metric("permission_denied")
        elif response.status_code == 429:
            record_metric("rate_limited")
    return response


# Add CORS middleware to allow frontend (port 3000) to communicate with backend (port 8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://0.0.0.0:3000",
        *[o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()],
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes first
if api_router is not None:
    app.include_router(api_router, prefix="/api")


@app.get("/startup-error")
async def startup_error_status():
    return {"startup_error": startup_error}

@app.get("/health")
async def health_check():
    status = "ok" if startup_error is None else "degraded"
    return {
        "status": status,
        "timestamp": str(datetime.now()),
        "startup_error": startup_error,
    }

@app.get("/api/metrics")
async def get_metrics(request: Request):
    """Auth and rate-limit metrics for monitoring. Admin-only in prod."""
    with _metrics_lock:
        snapshot = dict(_auth_metrics)
        elapsed = time.time() - snapshot["window_start"]
    return {
        "window_seconds": round(elapsed),
        "login_failures": snapshot["login_failures"],
        "token_invalid": snapshot["token_invalid"],
        "permission_denied": snapshot["permission_denied"],
        "rate_limited": snapshot["rate_limited"],
    }

# Robust static directory resolution
current_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(current_dir, "static")
if not os.path.exists(static_dir):
    # Fallback to current directory if 'static' subfolder is not found (sometimes occurs in Docker layouts)
    static_dir = current_dir


@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    # 1. Try serving requested path directly if it exists in static_dir
    potential_path = os.path.join(static_dir, full_path)
    if os.path.isfile(potential_path):
        return FileResponse(potential_path)
    
    # 2. Try adding .html (common for Next.js exports)
    html_path = os.path.join(static_dir, full_path.strip("/") + ".html")
    if os.path.isfile(html_path):
        return FileResponse(html_path)
        
    # 3. Fallback to index.html for SPA routing
    index_path = os.path.join(static_dir, "index.html")
    if os.path.isfile(index_path):
        return FileResponse(index_path)
        
    return {"message": "Backend is running, but frontend files were not found."}

# Mount static files as a backup (mostly for _next/ assets)
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir), name="static")
