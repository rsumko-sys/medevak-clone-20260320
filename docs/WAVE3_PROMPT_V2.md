# Wave 3 Prompt v2 for Visual Studio

```text
Працюй тільки над WAVE 3 для проєкту MEDEVAK / AZOV Medical Platform.

Контекст:
- Wave 1 already stabilized battlefield/save/validation/field-drop loading/settings safety.
- Wave 2 already added step indicators, MARCH notes, command filtering/sorting, mobile responsiveness, Whisper UX.
- Wave 3 focus:
  1. data correctness for command views
  2. handoff/export completeness
  3. recovery/safety groundwork
  4. lightweight critical alerts
  5. real engineering quality gates

Головні обмеження:
- Не роби великий архітектурний rewrite.
- Не чіпай deep sync-core unless absolutely necessary.
- Не перетворюй Wave 3 на event-sourcing migration.
- Не змінюй backend contracts агресивно без перевірки usage graph.
- Перевага за additive / compatible changes.
- Після кожного task — mini-report:
  - що знайдено
  - які файли змінено
  - що перевірено
  - що не чіпалось навмисно

ОБОВ’ЯЗКОВА PREFLIGHT ФІКСАЦІЯ ПЕРЕД СТАРТОМ TASK 1:

1. Зафіксуй Definition of Done для P0 exactly так:

Pagination-aware:
- Зараховано, якщо виконано один із варіантів:
  1. Total count + page controls + visible current slice
  2. Explicit banner: "Показано лише частину даних"
- Якщо немає ні 1, ні 2: не зараховано

Handoff/Export notes:
- Зараховано, якщо є:
  1. Мінімум 1 інтеграційний тест для handoff payload з notes
  2. Мінімум 1 інтеграційний тест для export path з notes
- Якщо відсутній хоча б один тест: не зараховано

2. Перед реалізацією TASK 1 зафіксуй contract-first whitelist:

sortable_fields:
- created_at
- triage
- status
- callsign
- unit

filterable_fields:
- triage
- status
- unit
- date_from
- date_to

3. Зафіксуй canonical values для triage/status.
4. Якщо в коді є aliases — опиши explicit mapping до canonical values.
5. Не починай реалізацію, поки не покажеш цей preflight contract у mini-report.

ДОДАТКОВІ ОБОВ’ЯЗКОВІ ПРАВИЛА WAVE 3:

A. Backup / restore
- snapshot format має бути versioned з першого дня
- restore only через strict schema version check
- restore має мати dry-run preview
- перед actual restore треба створити pre-restore backup
- restore policy має бути explicit (merge / replace / skip duplicates)
- default preference: idempotent merge, якщо це безпечно

B. Destructive flows
- frontend confirm недостатній сам по собі
- додай backend-aware guardrails where feasible:
  - role/permission check
  - reason/comment required
  - structured audit metadata:
    - actor
    - timestamp
    - scope
    - before/after metadata
  - optional cooldown / two-step confirm для high-impact actions

C. Alerts
- без fake signal noise
- одразу заклади debounce/coalescing
- бажано мати:
  - last_acknowledged_at
  - mute window per alert type
- не будуй event bus

D. Lint gate
- не просто "увімкни ESLint"
- зафіксуй policy:
  - що warning
  - що error
- lint має бути non-interactive

E. Stage 1 telemetry
- додай lightweight metrics/events:
  - dataset_truncated_shown
  - handoff_notes_present_rate
  - export_notes_present_rate
- можна додати ще:
  - restore_dry_run_invoked
  - restore_completed
  - destructive_action_blocked
  - alert_deduplicated
- не роздувай телеметрію без потреби

ПЕРЕД ПОЧАТКОМ:
1. Знайди файли для:
   - cases list API + frontend pagination/filtering
   - evac page data source
   - handoff aggregation/service
   - exporters / mappers
   - settings destructive actions backend side
   - audit endpoints / audit service
   - notification/toast/settings hooks
   - ESLint / frontend config
2. Запусти baseline:
   - frontend build
   - frontend typecheck
   - backend tests if available
   - current lint command status
3. Дай baseline report:
   - safe to edit now
   - high-risk areas
   - preflight contract
4. Тільки після цього переходь до TASK 1.

TASK 1 — Pagination-aware command data correctness
Ціль:
- cases/evac pages не мають прикидатися повним dataset, якщо реально loaded slice only

Що зробити:
- перевірити listCases / current backend pagination behavior
- якщо backend already supports offset/limit/filter params — акуратно використати їх
- якщо backend filtering limited, мінімум:
  - додати explicit pagination-aware UX
  - показати dataset boundary
- не ламати Wave 2 filters/sorting без крайньої потреби

Acceptance:
- зараховано тільки якщо є:
  - або total count + page controls + visible current slice
  - або explicit banner "Показано лише частину даних"
- якщо немає ні одного варіанту: task not done

TASK 2 — Include MARCH notes in handoff
Ціль:
- MARCH notes мають бути доступні в handoff flow

Що зробити:
- знайти handoff aggregation / response schema
- додати m_notes/a_notes/r_notes/c_notes/h_notes у safe compatible way
- не ламати існуючі handoff consumers
- додати мінімум 1 інтеграційний тест для handoff payload з notes

Acceptance:
- notes присутні в handoff payload/response
- handoff flow не ламається
- є інтеграційний тест
- без інтеграційного тесту task not done

TASK 3 — Include MARCH notes in exports
Ціль:
- notes не губляться в export paths

Що зробити:
- знайти exporters / mappers
- додати notes точково
- не переписувати всі export templates з нуля
- якщо якийсь export path реально deferred — задокументувати чесно
- додати мінімум 1 інтеграційний тест для export path з notes

Acceptance:
- notes включені в реальний export path
- є інтеграційний тест
- без тесту task not done

TASK 4 — Backup/restore foundation
Ціль:
- мати реальний recovery path для локального стану

Що зробити:
- versioned snapshot format
- export local snapshot
- import with strict schema/version check
- dry-run preview:
  - cases count
  - handoffs count
  - notes/settings/sync items if relevant
- pre-restore auto-backup
- explicit restore policy
- recovery doc/playbook

Acceptance:
- snapshot export працює
- import має strict version check
- dry-run preview працює
- pre-restore backup створюється
- policy merge/replace/skip duplicates explicit

TASK 5 — Backend-aware destructive action hardening
Ціль:
- dangerous actions мають бути контрольовані не лише фронтом

Що зробити:
- перевірити current backend endpoints / settings actions
- додати role/permission check where feasible
- reason/comment required
- structured audit event with actor/timestamp/scope/before-after metadata
- optional cooldown / two-step confirm for high-impact actions

Acceptance:
- dangerous action не існує лише як cosmetic confirm
- є server-aware validation/audit path
- high-impact actions мають stronger guardrails

TASK 6 — Lightweight critical alerts
Ціль:
- working alert foundation без шуму

Що зробити:
- використати existing toast/notification/settings hooks if present
- додати visual alerts для:
  - critical case
  - low blood
  - low supplies
  - optionally repeated sync failure threshold if safe
- debounce/coalescing required
- mute/toggle if safe
- acknowledged state if safe
- не будувати event bus

Acceptance:
- alerts не спамлять
- є debounce/coalescing
- є хоча б базовий mute/acknowledge model або чіткий deferred note

TASK 7 — Real lint quality gate
Ціль:
- lint має бути repeatable, non-interactive, policy-driven

Що зробити:
- налаштувати ESLint properly
- зафіксувати warning vs error policy
- переконатися, що lint command працює без prompts
- не влаштовувати formatting war

Acceptance:
- lint runs non-interactively
- no artifact generation on run
- policy documented briefly

ПОРЯДОК ВИКОНАННЯ:
Stage 1:
1. pagination contract
2. pagination implementation
3. handoff notes
4. export notes
5. e2e/integration checks
6. telemetry fact-check

Stage 2:
7. backup/restore
8. destructive flow hardening

Stage 3:
9. alerts
10. lint gate

Після кожного task:
- mini-report
- changed files
- what was intentionally not touched
- pass/fail against the pre-agreed Definition of Done

Не починай з масових правок.
Спочатку mapping + baseline + preflight contract.
Потім рухайся по порядку.
```
