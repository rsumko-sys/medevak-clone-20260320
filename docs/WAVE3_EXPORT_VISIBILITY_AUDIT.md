# Wave 3 Task 3.1: Export Visibility Audit (MARCH Notes)

## Scope

Audit of visible export formats after Task 3 export assembly propagation.

MARCH notes fields in scope:
- m_notes
- a_notes
- r_notes
- c_notes
- h_notes

## Source of truth in export assembly

MARCH notes are now present in export input payload as:
- case_dict.march_notes.m_notes
- case_dict.march_notes.a_notes
- case_dict.march_notes.r_notes
- case_dict.march_notes.c_notes
- case_dict.march_notes.h_notes

Assembly point:
- backend/app/api/v1/exports.py

## Format status

### PDF rendering
Status: EXPOSED

Evidence:
- Input includes march_notes in backend/app/api/v1/exports.py
- PDF renderer includes a dedicated `MARCH Notes` section in backend/app/exporters/pdf_exporter.py
- Section is rendered when at least one MARCH note is present.

### FHIR mapping/export
Status: EXPOSED

Evidence:
- Input includes march_notes in backend/app/api/v1/exports.py
- FHIR export passes case dict into backend/app/exporters/fhir_exporter.py
- Mapping in backend/app/core/fhir_integration.py appends an `Observation` entry with code text `MARCH Notes` and aggregated note content.

### QR payload
Status: EXPOSED

Evidence:
- Input includes march_notes in backend/app/api/v1/exports.py
- QR payload mapper in backend/app/mappers/case_to_qr.py includes compact `mn` block for M/A/R/C/H notes.

## Summary

Current state after Task 3:
- Export assembly propagation: DONE
- Bundle integration coverage for case.json: DONE

Current state after Task 3.1:
- Visible rendering/mapping in PDF/FHIR/QR: DONE

## Recommended next patches (point fixes)

1. PDF: add MARCH notes section in backend/app/exporters/pdf_exporter.py.
2. FHIR: map MARCH notes into a stable FHIR location (for example Observation or Encounter extension) in backend/app/core/fhir_integration.py.
3. QR: add compact march_notes structure in backend/app/mappers/case_to_qr.py with backward-compatible keys.
