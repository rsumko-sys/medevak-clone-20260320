# Wave 3 Preflight Contract

## Definition of Done for P0

### Pagination-aware

Count as done only if **one** of the options is implemented:

1. **Total count + page controls + visibility of current slice**
2. **Explicit banner:** `Показано лише частину даних`

If neither option 1 nor 2 exists, this is **not done**.

### Handoff / Export notes

Count as done only if **both** points are implemented:

1. At least **1 integration test** for `handoff payload` with notes
2. At least **1 integration test** for `export path` with notes

If at least one test is missing, this is **not done**.

---

## Contract-first for filters / sorting

Whitelist must be fixed before implementation starts:

```yaml
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
```

Additional constraints:

- `triage` and `status` must use **canonical values**.
- Aliases are allowed only as **mapping**, not as a second parallel source of truth.
