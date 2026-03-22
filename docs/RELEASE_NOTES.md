# MEDEVAK Release Notes

---

## v1.0-smoke — Smoke-Validated Baseline

**Tag/commit:** `8b6d027`  
**Tag name:** `v1.0-smoke`  
**Date:** 2026-03-22

### Status: ✅ CANONICAL STABLE BASELINE

This is the last smoke-validated release. Production smoke test ran 13/13 checks passed against the live deployment.

### Included

- Stabilized frontend after visual and workflow repair passes
- Fixed navigation and auth flow regressions
- Blood inventory persistence (API + ORM + migrations)
- Production smoke test passed (13/13)
- Verified login / logout / re-login flow
- Verified evac status state contract
- Production alias confirmed live at `https://medevak-clone-front-clone-20260321.vercel.app`

---

## v1.1-event-layer — Post-Smoke Development

**Tag/commit:** `f11f86c`  
**Tag name:** `v1.1-event-layer`  
**Date:** 2026-03-22

### Status: ⚠️ POST-SMOKE / NOT YET INDEPENDENTLY VERIFIED

Commits after baseline:

| Hash | Description |
|---|---|
| `5f5b9fe` | Release evidence + BACKLOG.md |
| `3991ef4` | Production smoke test script (`smoke_prod.py`) |
| `3e253ec` | State machine validation + system events on status change + blood–case event link |
| `4bc4519` | Event Layer + SSE stream |
| `f11f86c` | Fix Pyright type errors in smoke_prod.py and events_stream.py |

### Included themes

- **State-machine tightening** — `ALLOWED_TRANSITIONS` dict, 409 on invalid case status transitions, terminal states enforced
- **Event layer** — Generic domain event store (`type`, `entity_type`, `entity_id`, `unit`), `services/events.py` with centralized `log_event()`, Alembic migration `g2h3i4j5k6l7`
- **SSE / streaming** — `GET /events/stream` Server-Sent Events endpoint, 1s poll, unit-scoped
- **Workflow extensions** — `GET /events?since=&limit=`, `POST /events/case/{id}`, blood events linked to case timeline

### Conclusion

`v1.0-smoke` is the canonical stable baseline.  
Current HEAD (`v1.1-event-layer`) is ahead of that baseline and **should not be described as fully smoke-validated** without an additional verification pass.

---

## Backlog (from BACKLOG.md)

| Priority | Item |
|---|---|
| 🔴 P0 | Persistent DB — migrate from ephemeral SQLite to Neon PostgreSQL + asyncpg |
| 🟡 P1 | Access token revocation — Upstash Redis JTI blacklist or TTL=5min |
| 🟢 P2 | Playwright E2E tests for UI flows |
