# Security Fixes (2025-03-17)

## Виправлено

### 1. Auth bypass (CRITICAL)
- **config.py:** `DEV_AUTH_BYPASS` default змінено з `true` на `false`
- Без токена → 401
- Для локальної розробки: `DEV_AUTH_BYPASS=true`

### 2. Path traversal у filename (CRITICAL)
- **documents.py:** `os.path.basename()` для filename перед збереженням у DB
- `../../../etc/pwned` → зберігається як `pwned`

### 3. Invalid triage (HIGH)
- **cases.py:** Pydantic validator для `triage_code` (RED, YELLOW, GREEN, BLACK, EXPECTANT)
- `INVALID_TRIAGE` → 422

### 4. File size limit (MEDIUM)
- **documents.py:** `MAX_UPLOAD_BYTES = 10MB`
- Файл >10MB → 413

---

## Залишилось (не критично)

- `except: pass` у create_medication (time_administered)
- MIST aggregation — partial failure при exception
- CORS allow_origins=['*']
- SECRET_KEY default
