# MEDEVAK (CCRM) — Combat Casualty Record Module

**Linear:** [DEA-5](https://linear.app/death-note/issue/DEA-5/medevak)  
**Контекст:** [Вовки Да Вінчі](https://vovkydavinci.army/) — батальйон ЗСУ

---

## Опис

МЕДЕВАК — модуль обліку бойових поранень для медичної евакуації. Відновлено з клону після втрати оригіналу.

| Компонент | Статус |
|-----------|--------|
| Backend | ✅ FastAPI, SQLite, Alembic |
| Dashboard | ✅ Next.js 14 |
| Android app | ❌ Відсутній |

---

## Що працює

- **Cases CRUD** — створення, перегляд, оновлення, видалення кейсів
- **Handoff MIST** — mechanism, injuries, signs, treatment з БД
- **Medications** — список, додавання до кейсу
- **Documents** — API upload (backend/uploads/), list
- **Audit** — логування create/update/delete
- **Exports** — FHIR Bundle, QR payload
- **Dashboard** — /cases, /handoffs, /medications, /blood, /sync, /audit, /documents

---

## Що не працює / stub

- **Sync** — hardcoded 0,0,0, порожня черга
- **Auth** — mock user, не production-safe
- **PDF export** — повертає JSON, не PDF
- **Documents upload UI** — немає в dashboard
- **March/Evacuation/Tourniquets** — порожні масиви

---

## Запуск

```bash
# Backend
cd backend && python3 -m uvicorn app.main:app --port 8000

# Dashboard
cd dashboard && npm run dev
```

- Backend: http://localhost:8000
- Dashboard: http://localhost:3000

---

## Документація

- [REAL_AUDIT_REPORT.md](../REAL_AUDIT_REPORT.md) — аудит коду
- [PROJECT_STATUS.md](../../PROJECT_STATUS.md) — статус проекту
- [docs/api.md](../api.md) — API контракт
