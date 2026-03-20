"""App configuration."""
import os
from typing import List

ENV = os.getenv("ENV", "development")

_raw_db_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./medevak.db")
# Railway provides postgresql:// — upgrade to asyncpg async driver
if _raw_db_url.startswith("postgresql://"):
    _raw_db_url = _raw_db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
elif _raw_db_url.startswith("postgres://"):
    _raw_db_url = _raw_db_url.replace("postgres://", "postgresql+asyncpg://", 1)
DATABASE_URL = _raw_db_url

# Auth
if ENV == "development":
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-in-production-medevak-2024")
else:
    SECRET_KEY = os.getenv("SECRET_KEY")
    if not SECRET_KEY or SECRET_KEY == "changeme":
        raise RuntimeError("SECRET_KEY is not set properly")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7
DEV_AUTH_BYPASS = os.getenv("DEV_AUTH_BYPASS", "true").lower() == "true"
if DEV_AUTH_BYPASS and ENV != "development":
    raise RuntimeError("DEV_AUTH_BYPASS is forbidden outside development")

# CORS: comma-separated origins, e.g. "http://localhost:3000,https://your-domain.com"
_CORS_RAW = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173")
CORS_ORIGINS: List[str] = [o.strip() for o in _CORS_RAW.split(",") if o.strip()]

# Rate limiting
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))  # seconds
CASES_CREATE_RATE_LIMIT = os.getenv("CASES_CREATE_RATE_LIMIT", "120/minute")
DOCUMENTS_UPLOAD_RATE_LIMIT = os.getenv("DOCUMENTS_UPLOAD_RATE_LIMIT", "30/minute")

# Security settings
ALLOWED_HOSTS = [h.strip() for h in os.getenv("ALLOWED_HOSTS", "*").split(",") if h.strip()]
SECURE_COOKIES = os.getenv("SECURE_COOKIES", "false").lower() == "true"
MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", "10485760"))  # 10MB

# Redis for caching/sessions (optional)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
STRUCTURED_LOGGING = os.getenv("STRUCTURED_LOGGING", "true").lower() == "true"

# Connectivity and location policy
# When enabled, API accepts requests only from loopback/private IP ranges
# (typical Wi-Fi LAN and VPN networks) and rejects public-source traffic.
PRIVATE_NETWORK_ONLY = os.getenv("PRIVATE_NETWORK_ONLY", "false").lower() == "true"
# When disabled, incoming GPS coordinates in case payloads are rejected.
ALLOW_GPS = os.getenv("ALLOW_GPS", "false").lower() == "true"
