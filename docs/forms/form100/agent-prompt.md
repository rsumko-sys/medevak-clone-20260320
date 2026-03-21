# Agent Prompt: Form 100 Official Implementation Guardrails

Use the official Form 100 source as the single source of truth.

Files:
- docs/forms/form100/form100-original.docx
- docs/forms/form100/form100-spec.md
- docs/forms/form100/form100-field-map.json

Important:
- Existing backend Form 100 implementation may be simplified.
- Do not treat simplified schema as the full official Form 100.
- Extend implementation to preserve official structure and semantics from the original document.

Must preserve exactly:
1. Front side, back side, and stub/root as separate logical parts.
2. Legal meaning: official injury/illness registration and continuity of care.
3. Treatment entries with administered substances and doses.
4. Sanitary loss classification and coded injury categories.
5. Tourniquet timestamp, evacuation method, destination, and priority.
6. Body diagram / wound marking model semantics.
7. Colored edge indicators:
   - urgent care
   - sanitary processing
   - isolation
   - radiation measures
8. Back-side repeated stage log across multiple EME stages.
9. Physician signature/date and official output compatibility.

Implementation rules:
- Do not overwrite or collapse fields into summary-only schema.
- Introduce/keep a normalized internal data model that can represent full official form.
- Preserve backward compatibility where possible by mapping legacy simplified fields.
- Add DB migration for schema changes.
- Add tests for:
  - create/read/update full Form 100 structure
  - export bundle contains full Form 100 structure
  - PDF output renders official sections
  - repeated back-side stage entries
  - colored flags and evacuation metadata
- If body diagram cannot be fully implemented now, add explicit placeholder model and TODO (no silent omission).

Deliverables required from implementation step:
1. Canonical schema proposal
2. Migration plan
3. Changed files
4. Tests and results
5. Remaining gaps vs official original
