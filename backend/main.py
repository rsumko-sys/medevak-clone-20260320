import os
import sys
import ipaddress
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy import text

# Ensure the backend and its parent are in the path for robust imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

app = FastAPI(title="MEDEVAK API")

PRIVATE_NETWORK_ONLY = False
api_router = None
startup_error: Optional[str] = None

# Fail-safe startup: keep the process alive even if some API modules fail to import.
try:
    from app.api.router import api_router as imported_api_router
    from app.core.config import PRIVATE_NETWORK_ONLY as imported_private_network_only
    from app.core.config import CORS_ORIGINS as imported_cors_origins
    from app.core.database import AsyncSessionLocal

    api_router = imported_api_router
    PRIVATE_NETWORK_ONLY = imported_private_network_only
    cors_origins = imported_cors_origins
except Exception as exc:  # noqa: BLE001
    startup_error = f"Startup import failure: {exc.__class__.__name__}: {exc}"
    cors_origins = ["http://localhost:3000", "http://localhost:5173"]


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

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
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


@app.get("/ready")
async def readiness_check():
    if startup_error is not None:
        return JSONResponse(
            status_code=503,
            content={
                "ready": False,
                "startup_error": startup_error,
            },
        )

    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
            await session.execute(text("SELECT 1 FROM field_positions LIMIT 1"))
        return {"ready": True}
    except Exception as exc:  # noqa: BLE001
        return JSONResponse(
            status_code=503,
            content={
                "ready": False,
                "error": f"DB check failed: {exc.__class__.__name__}",
            },
        )

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
