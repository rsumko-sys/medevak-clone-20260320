# 🎯 Form 100 Smoke Test - READY TO RUN

**Status:** ✅ All Environment Setup Complete  
**Date:** 21 березня 2026 р.  
**Servers:** Backend ✅ 8000 | Frontend ✅ 3000  

---

## 🚀 START HERE (3 Options)

### Option A: Manual Browser Testing (Recommended for UI Verification)
```
1. Open http://localhost:3000 in browser
2. Navigate to Cases
3. Create new case with Form 100 (stub/front/back/meta sections)
4. View/Edit/Export in all 4 formats (JSON/PDF/FHIR/QR)
5. Check Browser DevTools Console for errors

📖 Full guide: docs/SMOKE_TEST_FORM100.md
⚡ Quick version: docs/QUICK_SMOKE_TEST.md (7-step test)
```

### Option B: Automated API Testing (Recommended for Rapid Verification)
```bash
# Run full smoke test (all 5 phases: create/read/edit/persist/export)
bash scripts/test_form100_api.sh 2>&1 | tee /tmp/smoke_test_results.log

# Expected: All phases PASS, creates test case in database
# Results: /tmp/export_*.json (bundle, fhir, qr), /tmp/export_*.pdf
```

### Option C: Quick Health Check (< 30 seconds)
```bash
# Backend health
curl http://localhost:8000/api/v1/health

# Frontend health  
curl http://localhost:3000 | head -5

# Both return 200? → Systems ready
```

---

## 📋 What Gets Tested

### Create Phase
- ✅ POST to create Case with Form 100
- ✅ Canonical nested structure in request body
- ✅ Database persists to form_100_records table
- ✅ Response includes form_100.id

### Read Phase  
- ✅ GET case detail with Form 100
- ✅ Canonical sections retrieve correctly:
  - stub (issued_at, flags)
  - front_side (identity, injury, treatment, evacuation, triage, diagram)
  - back_side (stage_log array, signature)
  - meta_legal_rules (legal status, continuity, etc.)

### Edit Phase
- ✅ PATCH Form 100 with partial updates
- ✅ Triage markers updated
- ✅ Other sections preserved (not cleared)

### Persist Phase
- ✅ Re-read from database confirms changes
- ✅ Stage log array maintained (2+ entries)
- ✅ All canonical sections still populated

### Export Phase
- ✅ **Bundle/JSON:** Response includes form_100 with all sections
- ✅ **PDF:** File generated, "Form 100 Canonical Sections" block rendered
- ✅ **FHIR:** 4 Observation entries (Stub/Front/Back/Meta)
- ✅ **QR:** Compact f100 block (dn/s/fs/bs/mlr keys) + scannable image

---

## 🎯 Quick Test Decision Tree

```
Do you want to...

✅ Verify API works (fastest)?
   → Run: bash scripts/test_form100_api.sh
   ⏱  Time: ~30 seconds
   📊 Output: Phase PASS/FAIL + JSON exports

✅ Check browser UI (most realistic)?
   → Open: http://localhost:3000
   → Navigate: Cases → Create → Edit → Export
   ⏱  Time: ~5 minutes
   👁️ Visual: See canonical sections render + PDF/QR generate

✅ Just confirm servers alive?
   → Run: curl http://localhost:8000/api/v1/health
   ⏱  Time: ~2 seconds
   ✨ Result: {"status": "ok"}
```

---

## 🔗 Quick Reference Links

**Documentation:**
- Full Smoke Test: [docs/SMOKE_TEST_FORM100.md](docs/SMOKE_TEST_FORM100.md)
- Quick Reference: [docs/QUICK_SMOKE_TEST.md](docs/QUICK_SMOKE_TEST.md)
- Project Status: [PROJECT_STATUS.md](PROJECT_STATUS.md)

**Code:**
- Form 100 API: [backend/app/api/v1/form100.py](backend/app/api/v1/form100.py)
- Form 100 Schema: [backend/app/schemas/unified.py](backend/app/schemas/unified.py)
- Frontend Types: [frontend/src/lib/types.ts](frontend/src/lib/types.ts)
- UI Sync Helper: [frontend/src/lib/form100-ui-sync.js](frontend/src/lib/form100-ui-sync.js)
- Case Detail UI: [frontend/src/app/cases/page.tsx](frontend/src/app/cases/page.tsx)

**Test Scripts:**
- Automated API: [scripts/test_form100_api.sh](scripts/test_form100_api.sh) (executable)

---

## 🏗️ Environment Status

| Component | Status | Details |
|-----------|--------|---------|
| **Backend (Port 8000)** | ✅ Running | PID 7530 (uvicorn) |
| **Frontend (Port 3000)** | ✅ Running | PID 40316 (Next.js) |
| **Python** | ✅ 3.11.15 | Ready |
| **Node** | ✅ Installed | npm packages present |
| **TypeScript** | ✅ 5.9.3 | Zero compilation errors |
| **Database** | ✅ Ready | SQLAlchemy ORM + migrations |

### Start Servers (if needed)
```bash
# Terminal 1: Backend
cd backend
python -m pip install -r requirements.txt  # if not already
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Frontend
cd frontend
npm install  # if not already
npm run dev

# Terminal 3: Run tests
bash scripts/test_form100_api.sh
```

---

## 🎓 Expected Results

### If ALL Tests Pass ✅
```
✓ Form 100 CRUD fully functional
✓ Canonical nested structure persisted
✓ All 4 export formats working (Bundle/PDF/FHIR/QR)
✓ Round-trip data integrity maintained
✓ TypeScript types correct
✓ No console errors

→ Ready for staging/production deployment
```

### If Tests Fail ❌
```
❌ API returns 500 error
  → Check backend logs: tail -50 /tmp/backend.log
  → Verify Phase B/C code applied to backend/app/api/v1/form100.py

❌ Frontend shows undefined fields
  → Check browser DevTools Console
  → Verify Phase D types imported in frontend/src/lib/types.ts
  → Run: npx tsc --noEmit (check TypeScript errors)

❌ Export fails (PDF/FHIR/QR)
  → Check specific exporter file:
    * PDF: backend/app/exporters/pdf_exporter.py
    * FHIR: backend/app/core/fhir_integration.py
    * QR: backend/app/mappers/case_to_qr.py
  → Verify Phase C code applied to these files
```

---

## 📊 Success Metrics

| Metric | Pass Criteria |
|--------|---------------|
| **Create Form 100** | POST returns 201 + form_100.id |
| **Canonical in DB** | 10 JSON columns populated |
| **UI Display** | Nested sections visible (not legacy summary) |
| **CRUD Roundtrip** | Edit → Save → Reload shows changes |
| **Export Formats** | Bundle/PDF/FHIR/QR all include canonical |
| **Data Integrity** | All fields match between UI ↔ API ↔ DB ↔ Exports |
| **Type Safety** | TypeScript: 0 errors |
| **Console Warnings** | 0 "undefined" errors re: form_100 |

---

## 🚀 Next: Deployment

### If Smoke Test Passes
```bash
# 1. Verify all tests pass again
bash scripts/test_form100_api.sh

# 2. Check TypeScript
cd frontend && npx tsc --noEmit
cd backend && python -m pytest -q

# 3. Commit
git add docs/ PROJECT_STATUS.md scripts/test_form100_api.sh
git commit -m "docs(form100): smoke test guide + automation script"
git push origin wave2-ux-hardening

# 4. Deploy (Vercel auto-builds on push)
# OR manual deploy to staging:
cd backend && alembic upgrade head
cd frontend && npm run build && npm start
```

### If Smoke Test Fails
```bash
# Review logs
tail -100 /tmp/backend.log
tail -100 /tmp/frontend.log

# Check specific test output
bash scripts/test_form100_api.sh 2>&1 | grep -A5 "❌\|ERROR\|FAILED"

# Fix issues, then re-test
bash scripts/test_form100_api.sh
```

---

## 🎯 Current Milestones

✅ **Phase B (Week 1):** Backend contract sync (bc1100f)
- Form 100 DTO with canonical nested structure
- Router + bidirectional mappers
- Migration with 10 JSON columns
- Tests: 11 passing

✅ **Phase C (Week 2):** Export surfaces sync (c101c71)
- Cases detail exposes canonical sections
- PDF/FHIR/QR exporters updated
- Tests: 14 passing (export suite)

✅ **Phase D (Week 3):** Frontend UI sync (e0e9ec5)
- Types extended with canonical nested
- Cases page UI editor for Form 100
- form100-ui-sync.js helper (draft ↔ payload mapping)
- Test: 1 roundtrip passing, TypeScript clean

🔄 **NOW:** Manual smoke test + deployment prep
- UI/API verification in browser
- Automated test script validation
- Ready for staging environment

---

## 💡 Pro Tips

**For Fastest Results:**
```bash
# Just run the API test (30 seconds)
bash scripts/test_form100_api.sh

# If it passes, smoke test complete!
# Results saved to: /tmp/export_*.{json,pdf}
```

**For Most Thorough Testing:**
```bash
# Open browser to http://localhost:3000/cases
# Follow 7-step quick test from docs/QUICK_SMOKE_TEST.md
# Manually verify each export format opens/downloads
```

**To Debug Individual Endpoints:**
```bash
# Test specific API via curl
curl -X GET http://localhost:8000/api/v1/form100 | jq

# Test export
curl http://localhost:8000/api/v1/exports/case/1?format=json | jq .form_100

# Check raw PDF binary
curl http://localhost:8000/api/v1/exports/case/1?format=pdf > /tmp/test.pdf && file /tmp/test.pdf
```

---

## 📞 Ready!

✨ **Everything is prepared for smoke testing!**

**Choose your path:**
1. **Quick API Test** → `bash scripts/test_form100_api.sh`
2. **Browser Test** → Open http://localhost:3000, follow the 7-step guide
3. **Manual Verification** → Curl individual endpoints from QUICK_SMOKE_TEST.md

**Expected duration:** 5-15 minutes for full verification

**Expected result:** ✅ Form 100 canonical implementation VERIFIED across all surfaces

---

Generated: 21 березня 2026 р. 06:45 UTC  
Status: 🟢 READY
