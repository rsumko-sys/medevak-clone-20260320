# Combat Dashboard — зʼєднання з backend

## Маппінг

| Combat (patients) | Backend (cases) |
|------------------|-----------------|
| id | cases.id |
| callsign | notes \|\| mechanism_of_injury \|\| mechanism |
| triage (!, 200, 300, 400, +) | triage_code (RED→!, YELLOW→300, GREEN→400, BLACK→200, EXPECTANT→+) |
| evacStatus | — (за замовчуванням "очікує") |
| synced | !pendingIds.has(id) з sync/queue |
| vitals (pulse, spo2) | observations (HR/PULSE, SPO2) |
| tourniquets | — (backend повертає []) |

## API endpoints

| Дія | Endpoint |
|-----|----------|
| Список пацієнтів | GET /cases, GET /cases/{id}, GET /sync/queue |
| Видалити | DELETE /cases/{id} |
| Новий кейс | POST /cases |

## Сторінки

| URL | Опис |
|-----|------|
| /combat | CombatDashboard (список) |
| /combat/new | Створення кейсу → redirect /combat/{id} |
| /combat/[id] | Redirect → /cases/[id] |

## Змінні середовища

```
NEXT_PUBLIC_API_BASE=http://localhost:8000/api
```

Backend потребує `DEV_AUTH_BYPASS=true` для локальної розробки (без JWT).
Для мережевої ізоляції рекомендовано `PRIVATE_NETWORK_ONLY=true` та `ALLOW_GPS=false`.
