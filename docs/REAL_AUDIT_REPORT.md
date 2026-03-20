# MEDEVAK_clone — REAL AUDIT REPORT

**Date:** 2025-03-17  
**Method:** Code-only verification. No assumptions. No trust in docs/comments.

---

## 1. REAL STATUS TABLE

| Component | Status | % | Evidence |
|-----------|--------|---|----------|
| **Backend entry** | IMPLEMENTED | 100 | main.py: FastAPI, CORS, api_router @ /api/v1 |
| **Database** | IMPLEMENTED | 100 | No create_all. Alembic env.py + 4 migrations. Schema persistent. |
| **Auth** | STUB | 20 | deps.py:11 "Stub: return mock user" — no real auth |
| **Cases CRUD** | IMPLEMENTED | 100 | POST, GET, PATCH, DELETE, list — real DB |
| **Handoff MIST** | IMPLEMENTED | 100 | _aggregate_mist reads Case, CaseInjury, obs, meds, procs |
| **Medications** | IMPLEMENTED | 100 | GET from DB; POST via /cases/{id}/medications |
| **Sync** | STUB | 0 | sync.py:17-20 hardcoded pending:0, synced:0, failed:0; queue:[] |
| **Documents** | PARTIAL | 70 | Upload: real (backend/uploads). List: real. Dashboard: NO upload UI |
| **Audit** | IMPLEMENTED | 100 | AuditRepository, log_audit on case create/update/delete |
| **Exports FHIR** | IMPLEMENTED | 100 | map_case_to_fhir, real Bundle |
| **Exports PDF** | MISLEADING | 30 | API returns JSON (map_case_to_pdf_data), NOT PDF bytes. pdf_exporter returns b"" |
| **Exports QR** | IMPLEMENTED | 100 | map_case_to_qr_payload |
| **March/Evacuation/Tourniquets** | STUB | 0 | Return [] |
| **Body markers** | IMPLEMENTED | 100 | CaseInjury or BODY_PARTS reference |
| **Injuries** | IMPLEMENTED | 100 | CaseInjury from DB |
| **Procedures** | IMPLEMENTED | 100 | ProcedureRepository (comment says stub — wrong) |
| **Observations** | IMPLEMENTED | 100 | ObservationRepository |
| **Reference** | IMPLEMENTED | 100 | Static TRIAGE_CODES, BLOOD_CODES |
| **Dashboard pages** | IMPLEMENTED | 100 | /, /cases, /cases/[id], /handoffs, /medications, /blood, /sync, /audit, /documents, /handoff→redirect |
| **Dashboard API client** | IMPLEMENTED | 90 | Correct endpoints. documentsApi has NO upload method |
| **Dashboard build** | IMPLEMENTED | 100 | npm run build succeeds |
| **Android app** | NOT IMPLEMENTED | 0 | No android-app folder |
| **Migrations** | IMPLEMENTED | 100 | 4 versions: initial, notes, triage, audit+documents |

---

## 2. FEATURE MATRIX

| Feature | Status | Proof (file + line) |
|---------|--------|---------------------|
| Create case | IMPLEMENTED | cases.py:68-95 |
| List cases | IMPLEMENTED | cases.py:98-116 |
| Get case | IMPLEMENTED | cases.py:150-181 |
| Update case | IMPLEMENTED | cases.py:184-213 |
| Delete case | IMPLEMENTED | cases.py:216-235 |
| Handoff list with MIST | IMPLEMENTED | handoff.py:91-123, _aggregate_mist:25-87 |
| Handoff generate | IMPLEMENTED | handoff.py:159-176, handoff_service.py:14-33 |
| Medications list | IMPLEMENTED | medications.py:28-41 |
| Medications create | IMPLEMENTED | cases.py:250-281 |
| Sync stats | STUB | sync.py:17-20 hardcoded 0,0,0 |
| Sync queue | STUB | sync.py:34 return [] |
| Documents list | IMPLEMENTED | documents.py:31-42 |
| Documents upload | IMPLEMENTED | documents.py:45-75, UPLOAD_DIR, write_bytes |
| Documents upload UI | NOT IMPLEMENTED | documents/page.tsx — list only, no upload |
| Audit log | IMPLEMENTED | audit.py, audit_helper.py, log_audit on case ops |
| FHIR export | IMPLEMENTED | exports.py:58-71, fhir_exporter |
| PDF export | MISLEADING | exports.py:74-86 returns JSON, not PDF. pdf_exporter returns b"" |
| QR export | IMPLEMENTED | exports.py:89-97, qr_exporter |
| Auth | STUB | deps.py:10-12 mock user |
| March/Evacuation/Tourniquets | STUB | march.py:22, evacuation.py:21, tourniquets.py:21 return [] |

---

## 3. CRITICAL LIES (IMPORTANT)

| Claim | Reality |
|-------|---------|
| "Export case as PDF" (exports.py:81) | Returns JSON envelope with map_case_to_pdf_data, NOT PDF file. pdf_exporter.export_case_to_pdf returns b"" and is NOT used by API. |
| "Procedures router — stub" (procedures.py:1) | Actually uses ProcedureRepository, returns real DB data. Comment is wrong. |
| Sync "production-ready" (if docs claim) | sync.py returns hardcoded zeros and empty list. No queue, no retry, no status. |
| documentsApi complete | api.ts has list only. No upload() for dashboard. |

---

## 4. TOP 10 BREAKING ISSUES

| # | Severity | Issue |
|---|----------|-------|
| 1 | HIGH | Sync is fake — stats 0,0,0 and empty queue. No offline/retry logic. |
| 2 | HIGH | Auth is mock — any client can access. No production auth. |
| 3 | MEDIUM | PDF export endpoint returns JSON, not PDF. Misleading name. |
| 4 | MEDIUM | Dashboard has no document upload UI — API exists but unusable from UI. |
| 5 | MEDIUM | documentsApi has no upload method — dashboard cannot upload even if UI added. |
| 6 | LOW | March, Evacuation, Tourniquets return empty — no data model or logic. |
| 7 | LOW | pdf_exporter returns b"" — dead code path (API uses map_case_to_pdf_data). |
| 8 | LOW | Procedures comment says "stub" but it's implemented. |
| 9 | LOW | handoff.py:49,60,73,86 — bare `pass` in except blocks (swallows errors). |
| 10 | INFO | Android app absent — documented as not restored. |

---

## 5. WHAT ACTUALLY WORKS (END-TO-END)

- GET /api/v1/cases — real DB list
- POST /api/v1/cases — create case, audit log, real DB
- GET /api/v1/cases/{id} — case + observations, medications, procedures
- PATCH /api/v1/cases/{id} — update, audit
- DELETE /api/v1/cases/{id} — delete + cascade (handoff, injuries, meds, procs, obs, documents)
- GET /api/v1/handoffs — handoffs with real MIST (mechanism, injuries, signs, treatment from DB)
- GET /api/v1/cases/{id}/handoff — handoff for case with MIST
- POST /api/v1/cases/{id}/handoff/generate — create handoff, persist
- GET /api/v1/medications — real DB
- POST /api/v1/cases/{id}/medications — create medication
- GET /api/v1/documents — real DB
- POST /api/v1/documents/upload — real file storage (backend/uploads/)
- GET /api/v1/audit — real audit log
- GET /api/v1/exports/{id}/fhir — real FHIR Bundle
- GET /api/v1/exports/{id}/qr — real QR payload
- Dashboard: cases list, create, detail; handoffs; medications; blood filter; sync (shows 0); audit; documents list
- Dashboard build: succeeds

---

## 6. WHAT IS FAKE

- Sync stats and queue — hardcoded
- Auth — mock user
- PDF export — JSON, not PDF; pdf_exporter returns empty bytes
- March, Evacuation, Tourniquets — empty arrays
- Android app — does not exist

---

## 7. DATABASE: PRODUCTION-READY?

**Answer: YES (with caveats)**

- Schema managed by Alembic (4 migrations)
- No create_all in app — schema applied via `alembic upgrade head`
- SQLite + aiosqlite for runtime
- Persistent medevak.db

Caveat: SQLite single-writer. For production scale, consider PostgreSQL.

---

## 8. SYNC: PRODUCTION-READY?

**Answer: NO**

- sync.py returns hardcoded `{ pending: 0, synced: 0, failed: 0 }` and `[]`
- No queue table, no retry logic, no status tracking
- Stub only

---

## 9. FINAL VERDICT

**⚠️ Partial MVP (limited usage)**

**Justification:**

- Core CCRM flow works: create case → add meds/obs/procs → handoff with MIST → audit
- Documents: upload works via API, but dashboard has no upload UI
- Sync: fake — no offline/retry capability
- Auth: mock — not production-safe
- PDF export: misleading (returns JSON, not PDF)

**Can be used for:** Local/demo, single-user, no offline sync.  
**Cannot be used for:** Production multi-user, offline sync, real PDF export, secure auth.
