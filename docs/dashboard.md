# Dashboard — Next.js 14

## 1. Структура

```
dashboard/
├── app/                      # App Router
│   ├── layout.tsx            # Root layout + Sidebar
│   ├── page.tsx              # Головна
│   ├── cases/
│   │   ├── page.tsx          # Список кейсів
│   │   └── [id]/page.tsx     # Деталі кейсу (triage, obs, meds, procs)
│   ├── handoffs/page.tsx     # Handoffs (MIST)
│   ├── handoff/page.tsx      # Redirect → /handoffs
│   ├── medications/page.tsx
│   ├── blood/page.tsx        # Фільтр BLOOD_CODES
│   ├── sync/page.tsx
│   ├── audit/page.tsx
│   └── documents/page.tsx
└── src/
    ├── lib/
    │   ├── api.ts            # API клієнт
    │   ├── types.ts          # TypeScript типи
    │   └── utils.ts          # TRIAGE_*, BLOOD_CODES, isBloodMedication
    └── components/
        ├── layout/
        │   ├── Sidebar.tsx
        │   └── TopBar.tsx
        └── ui/
            ├── Badge.tsx
            └── Table.tsx
```

---

## 2. API клієнт (src/lib/api.ts)

### Обгортки (casesApi, handoffApi, …)

| API | Методи |
|-----|--------|
| casesApi | list, get |
| handoffApi | list, get, generate, update, confirm |
| medicationsApi | list |
| syncApi | stats, queue |
| auditApi | list |
| documentsApi | list |

### Прямі функції (для сторінок)

| Функція | Маршрут | Повертає |
|---------|---------|----------|
| fetchCase(id) | GET /cases/{id} | Case |
| fetchHandoffs(params) | GET /handoffs | Handoff[] |
| fetchMedications(params) | GET /medications | MedicationAdministration[] |
| fetchSyncStats() | GET /sync/stats | SyncStats |
| fetchSyncQueue(params) | GET /sync/queue | SyncQueueItem[] |
| fetchAudit(params) | GET /audit | AuditEntry[] |

**Base URL:** `NEXT_PUBLIC_API_BASE` (default `http://localhost:8000`)

---

## 3. Типи (src/lib/utils.ts, types.ts)

### TriageCode
`RED | YELLOW | GREEN | BLACK | EXPECTANT`

### TRIAGE_COLOR, TRIAGE_LABEL
Маппінг коду → колір hex, українська мітка.

### BLOOD_CODES
`BLOOD`, `PRBC`, `FFP`, `PLT`, `PLATELETS`, `CRYO`, `WHOLE_BLOOD`, `PACKED_RBC`, `FRESH_FROZEN_PLASMA`, `CRYOPRECIPITATE`

### isBloodMedication(code)
Перевірка, чи код відноситься до продуктів крові.

---

## 4. Компоненти

| Компонент | Призначення |
|-----------|-------------|
| Sidebar | Навігація (Головна, Кейси, Handoffs, Медикаменти, Кров, Sync, Аудит, Документи) |
| Badge | Загальний badge |
| TriageBadge | Badge з кольором triage |
| Table | Table, TableHeader, TableBody, TableRow, TableHead, TableCell |

---

## 5. Path alias

`@/*` → `./src/*` (tsconfig.json)
