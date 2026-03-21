# Quick Smoke Test Survival Kit

**Status:** 🟢 All systems GO  
**Timestamp:** 21 березня 2026 р. 06:15 UTC

---

## ✅ Environment Status

| Component | Status | Details |
|-----------|--------|---------|
| **Python** | ✅ Ready | 3.11.15 (`/opt/homebrew/opt/python@3.11`) |
| **Backend** | ✅ Running | PID 7530 on port 8000 (uvicorn) |
| **Frontend** | ✅ Running | Port 3000 (Next.js localhost:3000) |
| **Database** | ✅ Ready | SQLAlchemy ORM + SQLite/PostgreSQL |
| **TypeScript** | ✅ Ready | 5.9.3 in node_modules |
| **Node** | ✅ Ready | Latest (npm packages installed) |
| **Git** | ✅ Ready | Branch: `wave2-ux-hardening` |

---

## 🎯 3-Minute Quick Test (For Impatient Users)

### Step 1: Open Browser
```
→ http://localhost:3000
Expected: Page loads with "Медичний модуль АЗОВ" (Ukrainian title)
```

### Step 2: Navigate to Cases
```
→ Click "Cases" in left sidebar or top menu
Expected: Cases list shows (empty or with existing cases)
```

### Step 3: Create Test Form 100
```
→ Click "+ New Case" or "Create"
→ Fill minimal fields:
  - Name: "Test Patient"
  - Rank: "Private" 
  - Injury time: "2026-03-21 10:00"
  - Form 100 → Stub → Urgent care: ☑

→ Click "Save"
Expected: Case created, redirects to detail page
```

### Step 4: Verify Canonical Sections
```
→ Look for Form 100 section tabs or nested field groups
Expected: See "Stub", "Front Side", "Back Side", "Meta Legal Rules" 
         (not legacy flat summary)
```

### Step 5: Export JSON Bundle
```
→ Click "Export" → "Download as JSON" or "Bundle"
→ Save file, open in text editor or online JSON viewer
Expected: Response includes:
{
  "form_100": {
    "stub": {...},
    "front_side": {...},
    "back_side": {...},
    "meta_legal_rules": {...}
  }
}
```

### Step 6: Export PDF
```
→ Click "Export" → "Download as PDF"
Expected: PDF downloads, contains "Form 100 Canonical Sections" block
```

### Step 7: Export QR Code
```
→ Click "Export" → "Generate QR" or "QR Code"
Expected: QR image displayed with payload containing "f100" compact block
         (keys: dn, s, fs, bs, mlr)
```

### ✅ If ALL 7 steps pass: Form 100 canonical implementation is working!

---

## 🔧 URL Quick Reference

| Purpose | URL | Method |
|---------|-----|--------|
| **Home** | http://localhost:3000 | GET |
| **Cases** | http://localhost:3000/cases | GET |
| **Case Detail** | http://localhost:3000/cases/{id} | GET |
| **API Health** | http://localhost:8000/api/v1/health | GET |
| **Form 100 List** | http://localhost:8000/api/v1/form100 | GET |
| **Create Form 100** | http://localhost:8000/api/v1/form100 | POST |
| **Get Form 100** | http://localhost:8000/api/v1/form100/{id} | GET |
| **Update Form 100** | http://localhost:8000/api/v1/form100/{id} | PATCH |
| **Case Detail** | http://localhost:8000/api/v1/cases/{id} | GET |
| **Export Bundle** | http://localhost:8000/api/v1/exports/case/{id}?format=json | GET |
| **Export PDF** | http://localhost:8000/api/v1/exports/case/{id}?format=pdf | GET |
| **Export FHIR** | http://localhost:8000/api/v1/exports/case/{id}?format=fhir | GET |
| **Export QR** | http://localhost:8000/api/v1/exports/case/{id}?format=qr | GET |

---

## 🐛 If Something Breaks

### Frontend Won't Load (404 / Blank Page)
```bash
# Check if server is still running
lsof -nP -iTCP:3000 -sTCP:LISTEN

# Restart if needed
pkill -f "next dev" || true
cd frontend && npm run dev &
```

### API Returns 500 Error
```bash
# Check backend logs
tail -50 /tmp/backend.log

# Restart backend
pkill -f "uvicorn backend.main:app" || true
cd backend && uvicorn backend.main:app --reload &
```

### Form 100 Not Showing Canonical Sections
```
DevTools → Console → Check for errors
DevTools → Network → Check API response includes "form_100" key with nested structure
```

### Export Failing (PDF/FHIR/QR)
```bash
# Test export API directly
curl http://localhost:8000/api/v1/exports/case/{case_id}?format=json | jq

# If 500 error, check backend logs
# If missing sections, verify Phase C code applied
```

---

## 📂 Key Files for Reference

| File | Purpose |
|------|---------|
| [docs/SMOKE_TEST_FORM100.md](../docs/SMOKE_TEST_FORM100.md) | Full smoke test guide (6 phases) |
| [PROJECT_STATUS.md](../PROJECT_STATUS.md) | Project overview & status |
| [backend/app/api/v1/form100.py](../backend/app/api/v1/form100.py) | Form 100 API endpoints + mappers |
| [backend/app/schemas/unified.py](../backend/app/schemas/unified.py) | Form 100 DTO (canonical structure) |
| [frontend/src/lib/types.ts](../frontend/src/lib/types.ts) | TypeScript types (canonical nested) |
| [frontend/src/lib/form100-ui-sync.js](../frontend/src/lib/form100-ui-sync.js) | UI ↔ API mapping helper |
| [frontend/src/app/cases/page.tsx](../frontend/src/app/cases/page.tsx) | Case detail UI (Form 100 editor) |

---

## 🚀 Deploy to Staging / Production

### Prerequisites
```bash
# Verify all tests pass
cd backend && python -m pytest -q
cd frontend && npm run lint && npx tsc --noEmit
```

### Staging Deploy (Local or Cloud)
```bash
# 1. Run migrations
cd backend && alembic upgrade head

# 2. Install/update dependencies
python -m pip install -r requirements.txt
npm install

# 3. Build frontend
cd frontend && npm run build

# 4. Start services (production mode)
cd backend && gunicorn -w 4 -b 0.0.0.0:8000 backend.main:app
cd frontend && npm start
```

### Cloud Deploy (Vercel/Docker)
```bash
# Option 1: Vercel (automatic on git push)
git add .
git commit -m "feat(form100): phase B/C/D smoke test verified"
git push origin wave2-ux-hardening
# → Vercel auto-deploys frontend

# Option 2: Docker
docker build -t medevak:form100 .
docker push {registry}/medevak:form100
kubectl apply -f deployment.yaml  # or similar
```

---

## ✨ After Smoke Test: Commit & Close Phase

```bash
# Stage smoke test documentation
git add docs/SMOKE_TEST_FORM100.md PROJECT_STATUS.md

# Commit (optional - only needed if findings require fixes)
git commit -m "docs(form100): add smoke test guide and status report"

# OR if all tests pass without fixes needed, just document in WAVE_STATUS:
echo "✅ Form 100 Phase B/C/D smoke test PASSED $(date)" >> docs/WAVE_STATUS.md

# Push to main branch
git push origin wave2-ux-hardening
```

---

## 📊 Success = ✅ All Export Formats Work

- ✅ **Bundle/JSON:** Case + Form 100 nested sections + MARCH notes
- ✅ **PDF:** Readable "Form 100 Canonical Sections" block
- ✅ **FHIR:** 4 Observation entries per section (Stub/Front/Back/Meta)
- ✅ **QR:** Compact f100 block (dn/s/fs/bs/mlr keys) + scannable image

---

**Status:** 🟢 Ready to smoke test!  
**Next:** Open http://localhost:3000 and follow the 7-step quick test above  
**Questions?** See [docs/SMOKE_TEST_FORM100.md](../docs/SMOKE_TEST_FORM100.md) for full guide
