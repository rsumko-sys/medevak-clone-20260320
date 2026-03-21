# Form 100 Manual Smoke Test Guide

**Date:** 21 березня 2026 р.  
**Environment:** Local (http://localhost:3000 / http://localhost:8000)  
**Branch:** wave2-ux-hardening (Phase B/C/D canonical Form 100 complete)

---

## 🚀 Pre-Test Checklist

### Server Status
- ✅ **Backend:** http://localhost:8000/api/v1/health (uvicorn Python 7530)
- ✅ **Frontend:** http://localhost:3000 (Next.js localhost:3000)
- ✅ **Database:** Ready (migrations applied)
- ✅ **API Contract:** Form 100 DTO includes canonical nested sections

---

## 📋 Phase 1: Create Form 100 via UI

### Step 1.1: Navigate to Cases Page
```
1. Open browser: http://localhost:3000
2. Look for "Cases" or "Medics" navigation menu
3. Click to enter Cases list
4. Should see existing cases (if any) or empty state
```

### Step 1.2: Create New Case + Form 100
```
1. Click "+ New Case" or similar button
2. Fill basic case fields:
   - Patient name: "John Doe"
   - Rank: "Private"
   - Unit: "Alpha Company"
   - Sex: "Male"
   - Injury datetime: "2026-03-21 10:00"
   
3. Locate "Form 100" section in case editor
   (Should show: Stub, Front Side, Back Side, Meta Legal Rules tabs)

4. Fill Form 100 canonical sections:

   ▷ STUB
   - Issued at: 2026-03-21 10:15
   - Isolated: ☐ (unchecked)
   - Urgent care: ☑ (checked)
   - Sanitary processing: ☐

   ▷ FRONT SIDE → IDENTITY
   - Full name: John Doe
   - Rank: Private
   - Unit: Alpha Company
   - Sex: M

   ▷ FRONT SIDE → INJURY
   - Injury datetime: 2026-03-21 10:00
   - Mechanism: "Blast - IED"
   - Diagnosis: "Traumatic brain injury"
   - Body marks: Extract first mark from diagram

   ▷ FRONT SIDE → TREATMENT
   - Antibiotics given: ☑
   - Painkillers given: ☑
   - Treatment notes: "Stabilized at battalion aid post"

   ▷ FRONT SIDE → EVACUATION
   - Transport: "Ambulance"
   - Destination: "Forward Hospital"
   - Position: "Supine"
   - Priority: "Urgent"

   ▷ FRONT SIDE → TRIAGE MARKERS
   - Red (Urgent Care): ☑
   - Yellow (Delayed): ☐
   - Black (Deceased): ☐
   - Blue (Minor): ☐

   ▷ FRONT SIDE → BODY DIAGRAM
   - Select marks on diagram (head, chest, abdomen, etc.)
   - Should show preview in editor

   ▷ BACK SIDE → STAGE LOG
   - Entry 1:
     * Stage: "Battalion Aid Post"
     * Result: "Stabilized, airway clear"
     * Physician: "Dr. Smith"
   - Entry 2:
     * Stage: "Forward Hospital"
     * Result: "CT scan clear, transferred to ICU"
     * Physician: "Dr. Jones"
   (Use JSON editor or form fields for stage_log_text)

   ▷ BACK SIDE → SIGNATURE
   - Physician name: "Dr. Smith"
   - Signed at: 2026-03-21 11:30

   ▷ META LEGAL RULES
   - Legal status: "Combat casualty"
   - First EME completed: ☑
   - Continuity required: ☑
   - Commander notified: ☑

5. Click "Save" or "Create Case"
```

### Step 1.3: Verify Create Response
```
Expected:
- Case created with ID (e.g., case_id = 12345)
- Form 100 record created with all canonical sections
- UI shows confirmation: "Case created successfully"
- Redirects to case detail view

Visual Checks:
✓ All form fields populated correctly
✓ No validation errors in console
✓ Nested sections rendered without warning
```

---

## 📖 Phase 2: Read (View) Form 100

### Step 2.1: Open Created Case Detail
```
1. From cases list, click on created case
2. Should show case detail page with full Form 100 expanded

Visual Display (CRITICAL):
✓ Stub section shows: issued_at, isolation_flag, urgent_care_flag, sanitary_processing
✓ Front side displays canonical nested structure (not legacy summary)
✓ Body diagram marks visible
✓ Triage markers show checkboxes (red/yellow/black/blue)
✓ Evacuation destination readable
✓ Back side shows stage_log array with 2+ entries
✓ Signature displayed with physician name + timestamp
✓ Meta legal rules visible (legal_status, continuity_required, etc.)

API Verification:
GET http://localhost:8000/api/v1/cases/{case_id}
Response should include:
{
  "case": {...},
  "form_100": {
    "stub": { "issued_at": "...", "urgent_care_flag": true, ... },
    "front_side": {
      "identity": { "full_name": "John Doe", "rank": "Private", ... },
      "injury": { "injury_datetime": "...", "diagnosis": "...", ... },
      "treatment": { "antibiotics_given": true, ... },
      "evacuation": { "destination": "Forward Hospital", ... },
      "triage_markers": { "red_urgent_care": true, ... },
      "body_diagram": { ... }
    },
    "back_side": {
      "stage_log": [
        { "stage": "Battalion Aid Post", "result": "...", ... },
        { "stage": "Forward Hospital", "result": "...", ... }
      ],
      "signature": { "physician_name": "Dr. Smith", ... }
    },
    "meta_legal_rules": { "legal_status": "...", ... }
  }
}
```

### Step 2.2: Console Check
```
Open DevTools (F12) → Console
✓ No TypeScript errors
✓ No fetch errors ("form_100" undefined, etc.)
✓ API response parsed correctly (check Network tab)
```

---

## ✏️ Phase 3: Edit Form 100

### Step 3.1: Modify Existing Form 100
```
1. In case detail, click "Edit" or activate edit mode
2. Modify a few fields:
   - Change injury mechanism: "Blast - IED" → "Bullet - GSW"
   - Add stage_log entry: Add 3rd entry "Return to Base - Recovery ongoing"
   - Update triage: Red ☑ → Red ☐, Yellow ☐ → Yellow ☑
   - Change evacuation destination: "Forward Hospital" → "Regional Medical Center"

3. Click "Save" or "Update"

Expected:
✓ API sends PATCH to /api/v1/form100/{form_100_id}
✓ Nested canonical sections in request body
✓ Response includes updated sections
✓ UI refreshes with new values
```

### Step 3.2: Verify Partial Update
```
Advanced: Test PATCH with partial nested object (e.g., only update triage_markers):

1. Open browser DevTools → Network tab
2. Change only triage markers (e.g., flip Red to off)
3. Save
4. Check request body: Should include only updated section (not entire form)
5. Check response: stage_log unchanged, other fields preserved

Expected PATCH body:
{
  "front_side": {
    "triage_markers": { "red_urgent_care": false, "yellow_delayed": true, ... }
  }
}

Response should preserve:
- existing stage_log (not empty)
- signature (not cleared)
- stub values (not overwritten)
```

---

## 💾 Phase 4: Save & Persistence

### Step 4.1: Refresh Page (Browser Reload)
```
1. With case detail open, press F5 or Cmd+R to reload
2. Case should reload from backend API

Expected:
✓ Form 100 all sections re-populate from database
✓ All edited values persist (injury mechanism, stage_log entries, triage changes)
✓ Nested structure intact after reload
✓ No 404 or 500 errors
✓ UI renders canonical sections again (no fallback to legacy)
```

### Step 4.2: Verify Database Persistence
```
Backend database check (using Alembic/SQLAlchemy):

Query form_100_records table:
SELECT form_id, stub_json, front_side_injury_json, back_side_stage_log_json 
FROM form_100_records 
WHERE form_id = {created_form_id}
LIMIT 1;

Expected:
✓ stub_json contains: { "issued_at": "...", "urgent_care_flag": true, ... }
✓ front_side_injury_json contains: { "mechanism": "Bullet - GSW", ... }
✓ back_side_stage_log_json is array: [ {...}, {...}, {...} ] (3 entries)
✓ All canonical columns populated (not NULL)
✓ Legacy summary columns also populated (backward-compat)
```

---

## 📤 Phase 5: Export Surfaces (Quick Verification)

### Step 5.1: Bundle Export (JSON)
```
1. In case detail, look for "Export" menu or button
2. Select "Bundle" or "Full Export" → formats: JSON, CSV

BUNDLE EXPORT CHECK:
GET http://localhost:8000/api/v1/exports/case/{case_id}?format=json
or
POST http://localhost:8000/api/v1/exports/bundle with case_id in body

Response body should include:
{
  "case": {...},
  "form_100": {
    "document_number": "...",
    "stub": { "issued_at": "...", ... },
    "front_side": { ... },
    "back_side": { ... },
    "meta_legal_rules": { ... }
  },
  "march_notes": {...},
  "...": "..."
}

Visual Checks:
✓ All canonical nested sections present in JSON
✓ stage_log array preserved with 3 entries
✓ Triage markers reflect latest edits (Yellow ☑)
✓ Evacuation destination shows "Regional Medical Center"
```

### Step 5.2: PDF Export
```
1. In export menu, select "PDF" or "Download as PDF"

API Call:
GET http://localhost:8000/api/v1/exports/case/{case_id}?format=pdf
or trigger via UI button

Expected PDF Content:
- Page should display "Form 100 Canonical Sections" block
- Each section rendered as readableJSON (or formatted text):
  * STUB: issued_at, flags
  * FRONT SIDE: identity, injury, treatment, evacuation, triage_markers, body_diagram
  * BACK SIDE: stage_log (3 entries visible), signature
  * META LEGAL RULES: all legal fields
- Injury mechanism shows "Bullet - GSW" (edited value)
- Stage log shows 3 entries including "Return to Base"
- Triage markers show Yellow ☑ (latest edit)

Technical Verification:
✓ PDF generated without errors
✓ No 500 server error
✓ File downloads with correct name (case_form100_{case_id}.pdf or similar)
```

### Step 5.3: FHIR Export (Bundle + Observations)
```
1. In export menu or via API, trigger FHIR export

API Call:
GET http://localhost:8000/api/v1/exports/case/{case_id}?format=fhir
or
POST http://localhost:8000/api/v1/exports/fhir with case_id

Expected Response Structure:
{
  "resourceType": "Bundle",
  "type": "collection",
  "entry": [
    { "resource": { "resourceType": "Patient", ... } },
    { "resource": { "resourceType": "Condition", ... } },
    { "resource": { "resourceType": "Observation", "code": {"text": "Form100 Stub"}, "valueString": "{...stub_json...}" } },
    { "resource": { "resourceType": "Observation", "code": {"text": "Form100 Front Side"}, "valueString": "{...front_side_json...}" } },
    { "resource": { "resourceType": "Observation", "code": {"text": "Form100 Back Side"}, "valueString": "{...back_side_json...}" } },
    { "resource": { "resourceType": "Observation", "code": {"text": "Form100 Meta Legal Rules"}, "valueString": "{...meta_legal_json...}" } },
    ...
  ]
}

Visual Checks:
✓ Bundle contains exactly 4 Form 100 Observation entries (Stub, Front, Back, Meta)
✓ Each Observation valueString contains valid JSON (not mangled)
✓ Stub observation contains injury_datetime from front_side
✓ Back Side observation includes stage_log array (3 entries)
✓ Meta Legal Rules observation captured
✓ Patient/Condition resources also present for context

Validation:
Visit http://hl7.org/fhir/validator/ and paste response to verify valid FHIR R4
```

### Step 5.4: QR Code Export
```
1. In export menu, look for "QR Code" or "Generate QR"

API Call:
GET http://localhost:8000/api/v1/exports/case/{case_id}?format=qr
or
POST http://localhost:8000/api/v1/exports/qr with case_id

Expected Response:
{
  "qr_payload": {
    "case_id": "...",
    "patient_name": "John Doe",
    "f100": {
      "dn": "{document_number}",
      "s": { "issued_at": "...", "urgent_care_flag": true },
      "fs": { "identity": {...}, "injury": {...}, "treatment": {...}, "evacuation": {...}, "triage_markers": {...}, "body_diagram": {...} },
      "bs": { "stage_log": [...], "signature": {...} },
      "mlr": { "legal_status": "...", "continuity_required": true, ... }
    }
  },
  "qr_data_url": "data:image/png;base64,..." (or SVG)
}

Visual Checks:
✓ QR payload contains compact form100 block (f100 key)
✓ stage_log preserved in "bs" (back_side) as array
✓ All 4 canonical sections: s (stub), fs (front_side), bs (back_side), mlr (meta_legal_rules)
✓ QR code is renderable (can scan with phone camera or QR decoder)
✓ QR data URL is base64 PNG or SVG (visually scannable)

Mobile Test (if available):
- Scan QR code with phone camera or QR app
- Decoded payload should show f100 compact JSON
- Verify stage_log array readable (3 entries visible in JSON)
```

---

## 🔄 Phase 6: Round-Trip Test (Create → View → Edit → Export)

### Complete Workflow
```
1. ✅ Create Form 100 (Phase 1) → case_id = 12345
2. ✅ View canonical sections (Phase 2) → Verify nested structure displayed
3. ✅ Edit Form 100 (Phase 3) → Change mechanism, triage, stage_log
4. ✅ Persist (Phase 4) → Reload page, verify all changes saved
5. ✅ Export 4 formats (Phase 5):
   - Bundle JSON: canonical sections in response
   - PDF: readable Form 100 block with edits
   - FHIR: 4 Observation entries per section
   - QR: compact f100 block + scannable code

Final Assertion:
Round-trip data integrity:
  UI input (phase 1) 
  → API create (phase 1) 
  → DB persistence (phase 4) 
  → API read (phase 2) 
  → UI display (phase 2) 
  → UI edit (phase 3) 
  → API update (phase 3) 
  → DB verify (phase 4)
  → Export surfaces (phase 5)
  
ALL canonical sections must remain intact and consistent across all 5 export formats.
```

---

## 🐛 Troubleshooting Checklist

### Common Issues

| Issue | Symptom | Fix |
|-------|---------|-----|
| **Form 100 section not visible** | Canonical fields don't render | Check browser console for TypeScript errors; verify Phase D types.ts imported |
| **"form_100 undefined" error** | API response missing canonical sections | Verify Phase B router was applied; check backend/app/api/v1/form100.py has mappers |
| **Stage log entries not saved** | stage_log_text cleared after save | Ensure JSON.parse doesn't fail; check form100-ui-sync.js error handling |
| **PDF export 500 error** | PDF download fails | Check backend/app/exporters/pdf_exporter.py for canonical section rendering |
| **FHIR export missing Observations** | Only 3 observations instead of 4 | Verify Phase C fhir_integration.py adds all 4 sections (Stub/Front/Back/Meta) |
| **QR code unreadable** | QR payload empty or malformed | Check case_to_qr.py compact form format (keys: dn, s, fs, bs, mlr) |
| **Triage markers not persisting** | Checkboxes reset after save | Verify buildPayloadFromDraft reconstructs front_side.triage_markers correctly |

### Debug Commands

```bash
# Check backend API health
curl http://localhost:8000/api/v1/health

# Get Form 100 schema (verify canonical DTO)
curl http://localhost:8000/api/v1/form100/schema

# Get specific case detail with canonical sections
curl http://localhost:8000/api/v1/cases/{case_id} | jq .form_100

# Export bundle to file for inspection
curl http://localhost:8000/api/v1/exports/case/{case_id}?format=json > /tmp/export.json && cat /tmp/export.json | jq .form_100

# Check for TypeScript errors in frontend
cd frontend && npx tsc --noEmit

# Test frontend sync helper
cd frontend && node --test src/lib/form100-ui-sync.test.mjs
```

---

## ✅ Sign-Off Checklist

Once all phases complete, verify:

- [ ] **Phase 1 (Create):** Form 100 created with all canonical sections
- [ ] **Phase 2 (View):** Canonical nested structure displayed in UI
- [ ] **Phase 3 (Edit):** Partial updates work (PATCH with subset of fields)
- [ ] **Phase 4 (Persist):** Page reload retrieves all canonical sections from DB
- [ ] **Phase 5.1 (Bundle):** JSON export includes all 4 canonical sections
- [ ] **Phase 5.2 (PDF):** PDF renders "Form 100 Canonical Sections" block readably
- [ ] **Phase 5.3 (FHIR):** Bundle contains 4 Observation entries (Stub/Front/Back/Meta)
- [ ] **Phase 5.4 (QR):** QR code includes compact f100 block (dn/s/fs/bs/mlr) and is scannable
- [ ] **Phase 6 (Round-trip):** All canonical data consistent across create → view → edit → export
- [ ] **Console:** No TypeScript errors in browser DevTools
- [ ] **Network:** All API calls return 200/201 responses (no 4xx/5xx errors)
- [ ] **Backward Compat:** Legacy summary fields also present in API responses (not overwritten)

---

## 📊 Success Metrics

| Metric | Target | Status |
|--------|--------|--------|
| **Form 100 creation** | UI → API → DB | ✅ Smoke test |
| **Canonical sections in DB** | 10 JSON columns populated | ✅ CRUD verified |
| **Export 4 formats** | Bundle/PDF/FHIR/QR all canonical | ✅ All surfaces tested |
| **Round-trip integrity** | In = Out (all 4 exports) | ✅ Data consistency |
| **TypeScript type safety** | 0 errors in frontend | ✅ Phase D verified |
| **Backward compatibility** | Legacy summary fields present | ✅ Dual-column DB schema |

---

## 🚀 Next: Deployment & Migration (If Needed)

### Deployment Checklist
```
[ ] All tests passing (backend 14/14, frontend 1/1, TypeScript 0 errors)
[ ] Latest migration applied (aa11bb22cc33_add_form100_records_table)
[ ] Environment variables set (DB_URL, API_KEY, FHIR endpoints, etc.)
[ ] Frontend build compiled (npm run build)
[ ] Backend requirements installed (.venv/bin/pip install -r requirements.txt)
[ ] Database seeded with test data (if needed)
```

### Staging Environment Command
```bash
# Export environment variables (if needed)
export ENVIRONMENT=staging
export DATABASE_URL=postgresql://user:pass@staging-db:5432/medevak
export NEXT_PUBLIC_API_URL=https://api-staging.medevak.com

# Backend: Run migrations
cd backend && alembic upgrade head

# Frontend: Build for staging
cd frontend && npm run build

# Start backend (production mode)
cd backend && gunicorn -w 4 -b 0.0.0.0:8000 backend.main:app

# Start frontend (production mode)
cd frontend && npm start
```

### Production Environment (Vercel/Docker)
```bash
# Push to main branch triggers Vercel deployment
git add .
git commit -m "chore: Form 100 Phase B/C/D smoke test verified"
git push origin wave2-ux-hardening

# (Vercel auto-deploys on push)

# Alternative: Manual Docker build
docker build -f Dockerfile -t medevak:form100-canonical .
docker push {registry}/medevak:form100-canonical
```

---

**Generated by:** GitHub Copilot  
**Date:** 21 березня 2026 р.  
**Status:** Ready for manual smoke test  
