## Wave 3 Data Trust / Recovery / Safety

### Included
- pagination-aware command data correctness
- MARCH notes in handoff
- MARCH notes in exports
- backup/restore foundation
- backend-aware destructive action hardening
- lightweight critical alerts
- non-interactive lint quality gate

### Definition of Done
- pagination-aware accepted only if:
  - total count + page controls + visible current slice
  - or explicit banner: "Показано лише частину даних"
- handoff/export notes accepted only with:
  - at least 1 integration test for handoff payload with notes
  - at least 1 integration test for export path with notes

### Scope Guardrails
- no deep sync-core rewrite
- no event-sourcing migration
- no aggressive backend contract changes without usage verification

### Notes
- contract-first whitelist for filters/sorting fixed before implementation
- recovery format is versioned
- restore requires dry-run preview
- alerts must include debounce/coalescing
- lint gate must be policy-driven and non-interactive
