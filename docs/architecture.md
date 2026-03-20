# Архітектура MEDEVAK

## 1. Огляд

**CCRM (Combat Casualty Record Module)** — система обліку бойових поранень для медичної евакуації.

### 1.1 Два інтерфейси

| Інтерфейс | Призначення | UX |
|-----------|-------------|-----|
| **Бойовий (польовий)** | Швидке внесення даних на місці поранення | Великі кнопки, touch, мінімум дій, голосовий ввід |
| **Командний (штабний)** | Архів, запаси, кров, координація | Таблиці, фільтри, огляд масиву даних |

Детальна верифікація: [FUNCTIONAL_VERIFICATION.md](FUNCTIONAL_VERIFICATION.md)

### 1.2 Компоненти

Три технічні компоненти:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Dashboard     │────▶│    Backend       │◀────│  Android app    │
│   (Next.js)     │     │   (FastAPI)      │     │  (відсутній)     │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │  SQLite (async)  │
                        └─────────────────┘
```

---

## 2. Доменні сутності

| Сутність | Опис | Backend model |
|----------|------|---------------|
| **Case** | Кейс пораненого | `Case` |
| **CaseHandoff** | Передача пацієнта (MIST) | `CaseHandoff` |
| **CaseInjury** | Травми за локацією | `CaseInjury` |
| **CaseMedicationAdministration** | Введені медикаменти | `CaseMedicationAdministration` |
| **CaseProcedure** | Виконані процедури | `CaseProcedure` |
| **CaseObservation** | Вітали, спостереження | `CaseObservation` |

---

## 3. Ключові потоки

### 3.1 Intake → Handoff → Export

1. **Intake** — створення кейсу, механізм травми, triage
2. **Observations** — вітали, спостереження
3. **Medications** — введені препарати (включно з кров'ю)
4. **Procedures** — процедури
5. **Handoff** — генерація MIST, підтвердження передачі
6. **Export** — FHIR, PDF, QR

### 3.2 MIST (Mechanism, Injuries, Signs, Treatment)

Handoff агрегує:
- **Mechanism** — з `Case.mechanism_of_injury` / `Case.mechanism`
- **Injuries** — з `CaseInjury` (body_part_code, injury_type_code)
- **Signs** — з `CaseObservation` (vitals)
- **Treatment** — з `CaseMedicationAdministration` + `CaseProcedure`

---

## 4. Triage

| Код | Колір | Опис |
|-----|-------|------|
| RED | #dc2626 | Червоний — критичний |
| YELLOW | #ca8a04 | Жовтий — середній |
| GREEN | #16a34a | Зелений — легкий |
| BLACK | #374151 | Чорний — померлий |
| EXPECTANT | #6b7280 | Очікуваний |

---

## 5. Синхронізація (offline)

- Backend: `/sync/stats`, `/sync/queue`
- Android (якщо буде): SyncWorker, SyncRepository
- Dashboard: сторінка Sync для моніторингу
