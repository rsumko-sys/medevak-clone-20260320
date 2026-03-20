# API Contract — Backend

**Base:** `http://localhost:8000/api/v1`

Всі відповіді обгорнуті в `{ data: T, request_id?: string }` (envelope).

---

## 1. Auth

| Method | Path | Опис |
|--------|------|------|
| GET | /auth/me | Поточний користувач (stub) |

---

## 2. Cases

| Method | Path | Опис |
|--------|------|------|
| GET | /cases | Список кейсів (offset, limit) |
| POST | /cases | Створити кейс |
| GET | /cases/{id} | Отримати кейс (з observations, medications, procedures) |

---

## 3. Handoffs

| Method | Path | Query/Body | Опис |
|--------|------|------------|------|
| GET | /handoffs | case_id?, offset?, limit? | Список handoffs з MIST |
| GET | /cases/{case_id}/handoff | — | Handoff для кейсу |
| POST | /cases/{case_id}/handoff/generate | — | Згенерувати handoff |
| PUT | /cases/{case_id}/handoff | body | Оновити handoff |
| POST | /cases/{case_id}/handoff/confirm | body | Підтвердити передачу |

**MIST у відповіді:** mechanism, injuries, signs, treatment (ніколи null).

---

## 4. Medications

| Method | Path | Query/Body | Опис |
|--------|------|------------|------|
| GET | /medications | case_id?, offset?, limit? | Список медикаментів |
| POST | /cases/{case_id}/medications | body | Додати медикамент |
| PATCH | /cases/{case_id}/medications/{med_admin_id} | body | Оновити |
| POST | /cases/{case_id}/medications/preset | body | Preset |

---

## 5. Sync

| Method | Path | Query | Опис |
|--------|------|-------|------|
| GET | /sync/stats | — | pending, synced, failed |
| GET | /sync/queue | status?, entity_type?, limit? | Черга синхронізації |

---

## 6. Audit

| Method | Path | Query | Опис |
|--------|------|-------|------|
| GET | /audit | table_name?, row_id?, limit? | Аудит-лог |

---

## 7. Documents

| Method | Path | Query | Опис |
|--------|------|-------|------|
| GET | /documents | case_id? | Список документів |

---

## 8. Exports (stubs)

| Method | Path | Опис |
|--------|------|------|
| GET | /exports/{case_id}/fhir | FHIR bundle |
| GET | /exports/{case_id}/pdf | PDF |
| GET | /exports/{case_id}/qr | QR payload |

---

## 9. Observations, Procedures

| Method | Path | Опис |
|--------|------|------|
| GET | /observations | case_id? |
| GET | /procedures | case_id? |

---

## 10. Stub endpoints (повертають [])

- /body_markers
- /injuries
- /tourniquets
- /evacuation
- /march
- /reference
