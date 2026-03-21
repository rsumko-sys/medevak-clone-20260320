# Wave 3 Stage 1a: Canonical Filters/Status Contract

## Purpose

Freeze one canonical contract for triage/status before Task 1 pagination-aware implementation.

## Canonical Contract-Level Values

### Canonical triage values (contract-level)

- IMMEDIATE
- DELAYED
- MINIMAL
- EXPECTANT
- DECEASED

### Canonical status values (contract-level)

- ACTIVE
- STABILIZING
- AWAITING_EVAC
- IN_TRANSPORT
- HANDED_OFF
- CLOSED
- DECEASED
- VOIDED

## Aliases and Mapping to Canonical

### Triage aliases observed

- RED -> IMMEDIATE
- YELLOW -> DELAYED
- GREEN -> MINIMAL
- BLACK -> DECEASED
- EXPECTANT -> EXPECTANT
- ! -> IMMEDIATE
- 300 -> DELAYED
- 400 -> MINIMAL
- + -> EXPECTANT
- 200 -> DECEASED

Notes:
- Aliases are allowed only as input/output mapping at boundaries.
- Internal API/UI filtering/sorting contract must use canonical values only.

### Status aliases observed

- evac_status (legacy/display usage) -> case_status

Notes:
- case_status is the canonical persisted/filterable status.
- evac_status should be treated as compatibility/display alias, not a second source of truth.

## Display-Only vs Contract-Level

### Contract-level fields for filtering/sorting

- triage_code (canonical values)
- case_status (canonical values)
- unit
- created_at
- callsign

### Display-only (non-contract filters)

- Localized labels and badges in UI
- Human-readable wording (for example, "IN TRANSPORT")
- Legacy/reference code lists used for rendering/help text

## Contract-First Whitelist (fixed before Task 1)

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

## Sources Used for Stage 1a Mapping

- frontend/src/lib/types.ts
- frontend/src/app/cases/page.tsx
- frontend/src/app/evac/page.tsx
- backend/app/schemas/unified.py
- backend/app/models/cases.py
- backend/app/api/v1/reference.py
- backend/app/core/fhir_integration.py
- backend/app/api/v1/cases.py
- backend/app/services/military_templates.py

## Recommended API/UI Contract Values

### Triage

- API request/response triage values should be canonical only.
- Any incoming alias must be normalized to canonical at boundary handlers.
- Any outgoing legacy view should map from canonical values only.

### Status

- API request/response status values should use case_status canonical set only.
- Evac workflows should update/filter using case_status as the single contract value.

## Follow-up Chores (must be tracked before/alongside Task 1)

1. Backend tests chore
- Fix missing fixture client in backend/app/tests/test_field_drop_finalize.py
- Ensure pytest baseline is green for field-drop finalize test set.

2. Lint gate chore
- Configure ESLint to run non-interactively.
- Ensure lint command is policy-driven (warning vs error) and does not auto-generate setup artifacts.
