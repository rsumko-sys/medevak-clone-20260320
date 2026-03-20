# Звіт глибокого дебагу MEDEVAK

**Дата:** 2025-03-17  
**Методологія:** systematic-debug (Reproduce → Isolate → Hypothesize → Fix)

---

## 1. Systematic-debug скіл

Встановлено скіл **systematic-debug** у `~/.cursor/skills-cursor/systematic-debug/`:
- Структурований root-cause аналіз
- Гіпотези з пріоритетом
- Без фіксів до з’ясування причини

---

## 2. Reproduce — відтворення

| Перевірка | Результат |
|-----------|-----------|
| Backend pytest | 8/8 passed |
| API GET /cases | 200 OK |
| API POST /cases | 200 OK, case створено |
| API GET /cases/{id} | 200 OK |
| API GET /cases/000... (404) | 404, `{"detail":"Case not found"}` |
| API GET /handoffs | 200 OK |
| API GET /medications | 200 OK |
| Dashboard build | ✓ Compiled |

**Висновок:** Критичних збоїв не виявлено. Є потенційні проблеми цілісності даних.

---

## 3. Isolate — ізоляція

### 3.1 Trace code paths

- **API envelope:** Backend повертає `{ data, request_id }` — dashboard очікує саме це ✓
- **Error handling:** 404 → `err.detail` — api.ts коректно обробляє ✓
- **fetchHandoffs:** `(json.data ?? json)` — коректно для `{ data: [] }` ✓

### 3.2 Виявлені проблеми

| # | Проблема | Локація | Severity |
|---|----------|---------|----------|
| 1 | **CaseDocument не видаляється при delete case** | `cases.py` delete_case | HIGH |
| 2 | `datetime.utcnow` deprecated (Python 3.12) | models/*.py | LOW |
| 3 | Pytest cache timeout warning | .pytest_cache | LOW |
| 4 | Next.js 14.2.0 security vulnerability | package.json | MEDIUM |

---

## 4. Hypothesize — гіпотези

**H1 (підтверджено):** При видаленні кейсу `CaseDocument` залишаються в БД → порушення FK при подальших операціях, orphan records.

**H2:** `datetime.utcnow` може бути видалено в майбутніх версіях Python — поки що працює.

**H3:** Pytest cache — можлива проблема з правами/шляхом у sandbox.

---

## 5. Fix — виправлення

### Застосовано

**CaseDocument при delete case:**
- Додано `CaseDocument` до списку моделей, що видаляються разом із кейсом
- Файли в `backend/uploads/` залишаються (орфанні) — окремий cleanup при потребі

```python
# backend/app/api/v1/cases.py
for model in (..., CaseDocument):
    ...
```

### Не застосовувалось (низький пріоритет)

- Заміна `datetime.utcnow` → `datetime.now(timezone.utc)` — потребує міграції
- Оновлення Next.js — потребує перевірки сумісності
- Pytest cache — не впливає на роботу тестів

---

## 6. Підсумок

| Категорія | Статус |
|-----------|--------|
| Критичні баги | 0 (після фіксу) |
| Виправлено | 1 (CaseDocument cascade delete) |
| Рекомендації | 3 (datetime, Next.js, pytest cache) |

**Проект готовий до подальшої розробки.** Скіл systematic-debug доступний для майбутніх дебаг-сесій.
