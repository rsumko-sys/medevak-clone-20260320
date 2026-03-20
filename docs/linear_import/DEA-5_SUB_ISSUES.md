# Sub-issues для DEA-5 (MEDEVAK)

Додати як sub-issues до [DEA-5](https://linear.app/death-note/issue/DEA-5/medevak).

---

## Breaking (пріоритет 1–2)

| Title | Description | Priority |
|-------|-------------|----------|
| Sync is fake — stats 0,0,0 and empty queue | sync.py returns hardcoded pending:0, synced:0, failed:0; queue:[]. No offline/retry logic. | 1 |
| Auth is mock — any client can access | deps.py:10-12 returns mock user. No production auth. | 1 |
| PDF export returns JSON, not PDF | exports.py returns JSON envelope, NOT PDF. pdf_exporter returns b"" | 2 |
| Dashboard has no document upload UI | documents/page.tsx — list only. API exists but unusable from UI. | 2 |
| documentsApi has no upload method | api.ts has list only. No upload() for dashboard. | 2 |

---

## Medium/Low

| Title | Description | Priority |
|-------|-------------|----------|
| March, Evacuation, Tourniquets return empty | march.py, evacuation.py, tourniquets.py return []. No data model. | 3 |
| pdf_exporter dead code | API uses map_case_to_pdf_data. pdf_exporter returns b"" — unused. | 3 |
| Procedures comment says stub but implemented | procedures.py comment wrong. Actually returns real DB data. | 3 |
| handoff.py bare pass in except blocks | handoff.py:49,60,73,86 — swallows errors. | 3 |
| Android app absent | android-app folder not restored. | 4 |

---

## Backlog (features)

| Title | Description |
|-------|-------------|
| Поля пацієнта: patient_name, call_sign, unit, time_of_injury | Додати до моделі Case |
| Модель Tourniquet, час накладення | Модель для турнікетів |
| Body map UI (схема тіла) | UI для позначення поранень |
| Голосовий ввід (Whisper API) | Інтеграція Whisper |
| Inventory (склад медикаментів/крові) | Модуль складу |
| Окремий польовий екран (/field або /intake) | Екран польового введення |
