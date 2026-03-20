# Structural Analysis and Settings (2026-03-19)

## 1. Current Structure Snapshot

- Frontend: `frontend/` (Next.js 14)
- Backend: `backend/` (FastAPI + async SQLAlchemy)
- Runtime launcher: `run.sh` from repository root
- Main DB: `medevak.db` in repository root (sqlite+aiosqlite)
- Additional storage roots:
  - `backend/uploads`
  - `backend/archives`
  - `backend/exports`

## 2. Structural Findings

1. Docs drift:
- Some docs referenced `dashboard/` instead of `frontend/`.
- Some docs referenced `/api/v1` while runtime API is mounted under `/api`.

2. Config drift:
- No reusable frontend env template existed.
- No reusable backend env template with new security/network policy flags.

3. Startup rigidity:
- `run.sh` previously forced `DEV_AUTH_BYPASS=true` and ignored external override.

## 3. Settings Baseline (Applied)

### Backend policy baseline
- `PRIVATE_NETWORK_ONLY=true`
- `ALLOW_GPS=false`
- `DEV_AUTH_BYPASS=true` for local development only

### Frontend API baseline
- `NEXT_PUBLIC_API_BASE=http://localhost:8000/api`

## 4. Changes Applied

1. Startup behavior
- Updated `run.sh` to allow environment override:
  - `DEV_AUTH_BYPASS=${DEV_AUTH_BYPASS:-true}`

2. Backend env files
- Updated `backend/.env` with:
  - `PRIVATE_NETWORK_ONLY=true`
  - `ALLOW_GPS=false`
- Added `backend/.env.example` with complete baseline variables.

3. Frontend env template
- Added `frontend/.env.local.example` with current API base.

4. Documentation updates
- Updated `docs/run.md` paths, API base, and policy flags.
- Updated `docs/COMBAT_CONNECTIONS.md` API base and security-policy note.

## 5. Recommended Operational Profiles

### Local secure dev
- Backend:
  - `DEV_AUTH_BYPASS=true`
  - `PRIVATE_NETWORK_ONLY=true`
  - `ALLOW_GPS=false`
- Frontend:
  - `NEXT_PUBLIC_API_BASE=http://localhost:8000/api`

### Production-like
- Backend:
  - `DEV_AUTH_BYPASS=false`
  - `PRIVATE_NETWORK_ONLY=true`
  - `ALLOW_GPS=false` (unless mission profile requires geodata)
  - Strong `SECRET_KEY`

## 6. Follow-up Hardening Tasks

1. Add CIDR allowlist for VPN subnets (instead of generic private-ranges).
2. Add startup self-check endpoint to report active env profile.
3. Add CI check for docs/API base drift.
4. Add queue worker for real sync outbox delivery lifecycle.
