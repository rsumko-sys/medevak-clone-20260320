# Backend — FastAPI

## 1. Структура

```
backend/
├── app/
│   ├── main.py              # FastAPI entry, CORS
│   ├── api/
│   │   ├── router.py        # Збірка всіх v1 роутерів
│   │   ├── deps.py          # get_current_user, get_session, get_request_id
│   │   └── v1/              # API модулі
│   ├── core/
│   │   ├── config.py        # DATABASE_URL
│   │   ├── database.py      # async engine, session
│   │   └── utils.py         # envelope()
│   ├── models/
│   │   ├── base.py
│   │   └── cases.py         # Case, CaseHandoff, CaseInjury, ...
│   ├── schemas/             # Pydantic
│   ├── services/            # handoff_service
│   ├── repositories/        # cases, medications, handoff, observations, procedures
│   ├── mappers/             # case_to_fhir, case_to_qr
│   ├── exporters/           # fhir_exporter, pdf_exporter, qr_exporter
│   └── tests/
└── migrations/
```

---

## 2. Моделі (SQLAlchemy)

| Таблиця | Ключові поля |
|---------|---------------|
| `cases` | id, mechanism_of_injury, mechanism, notes, created_at |
| `case_handoffs` | id, case_id, mist_summary, operator_id, created_at |
| `case_injuries` | id, case_id, body_part_code, injury_type_code |
| `case_medication_administrations` | id, case_id, medication_code, dose_value, dose_unit_code, time_administered |
| `case_procedures` | id, case_id, procedure_code, notes |
| `case_observations` | id, case_id, observation_type, value |

---

## 3. API модулі (v1)

| Файл | Prefix | Призначення |
|------|--------|-------------|
| auth.py | /auth | get_current_user, /me |
| cases.py | /cases | CRUD кейсів |
| handoff.py | /handoffs, /cases/{id}/handoff | Handoff + MIST |
| medications.py | /medications, /cases/{id}/medications | Медикаменти |
| sync.py | /sync | stats, queue |
| audit.py | /audit | Аудит-лог |
| documents.py | /documents | Документи |
| exports.py | /exports | FHIR, PDF, QR |
| observations.py | /observations | Спостереження |
| procedures.py | /procedures | Процедури |
| body_markers.py | /body_markers | Stub |
| injuries.py | /injuries | Stub |
| tourniquets.py | /tourniquets | Stub |
| evacuation.py | /evacuation | Stub |
| march.py | /march | Stub |
| reference.py | /reference | Stub |

---

## 4. Handoff MIST aggregation

`_aggregate_mist(session, case_id)` збирає:
- **mechanism** — Case.mechanism_of_injury або Case.mechanism
- **injuries** — список з CaseInjury
- **signs.vitals** — з CaseObservation
- **treatment.medications** — з CaseMedicationAdministration
- **treatment.procedures** — з CaseProcedure

Ніколи не повертає null для цих полів (порожні масиви/рядки замість null). При помилках агрегації — повертає `warnings: ["failed to load ..."]` (контрольована деградація).

---

## 5. Config (ENV vars)

| Змінна | Опис | Production |
|--------|------|------------|
| `ENV` | development / production | `production` |
| `SECRET_KEY` | JWT secret | Обовʼязково, не `changeme` |
| `DEV_AUTH_BYPASS` | Bypass auth (тільки dev) | Заборонено в prod — app crash |
| `CORS_ORIGINS` | Comma-separated origins | `http://localhost:3000,https://your-domain.com` |

---

## 6. Міграції (Alembic)

```bash
cd backend
python3 -m alembic revision --autogenerate -m "опис"
python3 -m alembic upgrade head
```

**Важливо:** використовувати `python3 -m alembic`, не `alembic`.
