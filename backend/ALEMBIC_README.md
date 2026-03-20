# Alembic Migrations

## Setup

- **Sync driver for migrations:** `sqlite:///./medevak.db` (Alembic does not support async)
- **Async driver for app:** `sqlite+aiosqlite:///./medevak.db` (runtime)

## Commands

```bash
# Перейти в backend (з будь-якої директорії)
cd /Users/admin/Desktop/MEDEVAK_clone/backend

# Нова міграція після змін моделей
python3 -m alembic revision --autogenerate -m "description"

# Застосувати міграції
python3 -m alembic upgrade head

# Відкотити одну міграцію
python3 -m alembic downgrade -1

# Поточна ревізія
python3 -m alembic current
```

## Migrations

| Revision | Description |
|----------|-------------|
| a05ce5293cc6 | initial_schema — cases, case_handoffs, case_injuries, case_medication_administrations, case_observations, case_procedures |
| 73769e30d780 | add_notes_to_case — notes column on cases |

## Note

- `create_all` has been **removed** from `app/main.py`
- Schema is managed exclusively by Alembic
