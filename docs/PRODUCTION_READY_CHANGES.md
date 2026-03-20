# Production-ready changes (Partial MVP → v1)

**Дата:** 2025-03-17

---

## P0 — BLOCKERS (реалізовано)

### 1. Auth (JWT)

- **Файли:** `app/core/auth.py`, `app/api/deps.py`, `app/api/v1/auth.py`, `app/models/user.py`
- **Міграція:** `e1f2a3b4c5d6_users_and_sync_queue.py` (users table)
- **Endpoints:**
  - `POST /api/v1/auth/register` — реєстрація
  - `POST /api/v1/auth/login` — логін, повертає access_token + refresh_token
  - `POST /api/v1/auth/refresh` — оновлення access_token
  - `GET /api/v1/auth/me` — поточний користувач (потребує Bearer token)
- **Config:** `SECRET_KEY`, `DEV_AUTH_BYPASS` (true = mock user без token для dev)
- **Залежності:** python-jose, passlib[bcrypt]

### 2. Sync (outbox pattern)

- **Файли:** `app/core/sync_helper.py`, `app/models/sync_queue.py`, `app/api/v1/sync.py`
- **Міграція:** sync_queue table
- **Логіка:** `enqueue_sync()` викликається при create/update/delete case
- **API:** `/sync/stats` і `/sync/queue` повертають реальні дані з БД
- **Worker:** поки не реалізований (queue накопичується, статус не оновлюється автоматично)

### 3. PDF Export

- **Файли:** `app/exporters/pdf_exporter.py`, `app/api/v1/exports.py`
- **Логіка:** ReportLab генерує PDF з case, observations, medications, procedures
- **Endpoint:** `GET /exports/{case_id}/pdf` → `application/pdf`, Content-Disposition: attachment
- **Залежність:** reportlab

---

## P1 — UX (реалізовано)

### 4. Documents UI + API

- **api.ts:** `documentsApi.upload(caseId, file)`
- **documents/page.tsx:** форма з вибором кейсу + file input + кнопка завантаження

### 5. Error logging (handoff.py)

- Замінено `except: pass` на `logger.warning(...)` у MIST aggregation

---

## Конфігурація

```bash
# Production
export SECRET_KEY="your-secret-key"
export DEV_AUTH_BYPASS="false"

# Development (default)
# DEV_AUTH_BYPASS=true — не потрібен Bearer token
```

---

## Що залишилось (P2–P3)

- March / Evacuation / Tourniquets — таблиці та логіка
- SQLite → PostgreSQL
- Sync worker (retry, delivery)
- Cleanup: misleading comments, dead code
