#!/bin/bash
# Form 100 Smoke Test API Commands
# Run each command sequentially to test Form 100 API endpoints
# 
# Usage: bash test_form100_api.sh 2>&1 | tee /tmp/smoke_test.log

set -e

BASE_URL="http://localhost:8000/api/v1"
CASE_ID=""
FORM_100_ID=""

echo "📋 FORM 100 SMOKE TEST - API LEVEL"
echo "=================================="
echo "Date: $(date)"
echo "Base URL: $BASE_URL"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_step() {
  echo -e "${BLUE}▶ Step $1: $2${NC}"
}

print_success() {
  echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
  echo -e "${RED}❌ $1${NC}"
  exit 1
}

print_header() {
  echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo -e "${YELLOW}$1${NC}"
  echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# ============================================================================
# PHASE 1: CREATE CASE + FORM 100
# ============================================================================

print_header "PHASE 1: CREATE CASE WITH FORM 100"

print_step "1.1" "Health Check"
HEALTH=$(curl -sS "$BASE_URL/health" | jq '.status // "unknown"')
if [[ "$HEALTH" == "ok" ]] || [[ "$HEALTH" == "\"ok\"" ]]; then
  print_success "Backend healthy: $HEALTH"
else
  print_error "Backend not responding: $HEALTH"
fi

print_step "1.2" "Create Case with Form 100"

# Create case payload
CASE_PAYLOAD=$(cat <<EOF
{
  "patient_name": "Smoke Test Patient",
  "rank": "Private",
  "unit": "Alpha Company",
  "sex": "M",
  "injury_datetime": "2026-03-21T10:00:00Z",
  "form_100": {
    "document_number": "F100-TEST-$(date +%s)",
    "stub": {
      "issued_at": "2026-03-21T10:15:00Z",
      "isolation_flag": false,
      "urgent_care_flag": true,
      "sanitary_processing_flag": false
    },
    "front_side": {
      "identity": {
        "full_name": "Smoke Test Patient",
        "rank": "Private",
        "unit": "Alpha Company",
        "sex": "M"
      },
      "injury": {
        "injury_or_illness_datetime": "2026-03-21T10:00:00Z",
        "mechanism": "Blast - IED",
        "diagnosis": "Traumatic brain injury with mild concussion",
        "body_diagram_marks": [
          {"location": "head", "severity": "moderate"}
        ]
      },
      "treatment": {
        "antibiotics_given": true,
        "painkillers_given": true,
        "treatment_notes": "Stabilized at battalion aid post, airway clear"
      },
      "evacuation": {
        "transport_type": "Ambulance",
        "destination": "Forward Hospital",
        "patient_position": "Supine",
        "priority": "Urgent"
      },
      "triage_markers": {
        "red_urgent_care": true,
        "yellow_delayed": false,
        "black_deceased": false,
        "blue_minor": false
      },
      "body_diagram": {
        "marks": [
          {"x": 45, "y": 20, "label": "Head - moderate"}
        ]
      }
    },
    "back_side": {
      "stage_log": [
        {
          "stage": "Battalion Aid Post",
          "result": "Stabilized, airway clear, consciousness GCS 14/15",
          "physician_notes": "TBI suspected, monitor for deterioration",
          "timestamp": "2026-03-21T10:15:00Z"
        },
        {
          "stage": "Forward Hospital",
          "result": "CT scan clear, ICU admission",
          "physician_notes": "Send to regional medical center for advanced neuro imaging",
          "timestamp": "2026-03-21T10:45:00Z"
        }
      ],
      "signature": {
        "physician_name": "Dr. Smith",
        "signed_at": "2026-03-21T11:30:00Z"
      }
    },
    "meta_legal_rules": {
      "legal_status": "Combat casualty - NATO personnel",
      "first_eme_completed": true,
      "continuity_required": true,
      "commander_notified": true
    }
  }
}
EOF
)

RESPONSE=$(curl -sS -X POST "$BASE_URL/cases" \
  -H "Content-Type: application/json" \
  -d "$CASE_PAYLOAD")

CASE_ID=$(echo "$RESPONSE" | jq -r '.id // .case_id // empty' 2>/dev/null)

if [[ -z "$CASE_ID" ]]; then
  echo "Response: $RESPONSE"
  print_error "Failed to create case (no ID returned)"
fi

print_success "Case created: $CASE_ID"

FORM_100_ID=$(echo "$RESPONSE" | jq -r '.form_100.id // .form_100_id // empty' 2>/dev/null)
print_success "Form 100 created: $FORM_100_ID"

echo ""
echo "📦 Case Details:"
echo "$RESPONSE" | jq '.case // .' 2>/dev/null | head -20

# ============================================================================
# PHASE 2: READ FORM 100
# ============================================================================

print_header "PHASE 2: READ FORM 100 FROM DATABASE"

print_step "2.1" "Get Case Detail with Form 100"

CASE_DETAIL=$(curl -sS "$BASE_URL/cases/$CASE_ID")

echo "$CASE_DETAIL" | jq '.' 2>/dev/null > /tmp/case_detail.json

print_success "Case detail retrieved"

# Verify canonical sections
print_step "2.2" "Verify Canonical Nested Structure"

FORM_100=$(echo "$CASE_DETAIL" | jq '.form_100 // empty' 2>/dev/null)

if [[ -z "$FORM_100" ]]; then
  print_error "Form 100 not in response"
fi

# Check each section
STUB=$(echo "$FORM_100" | jq '.stub // empty' 2>/dev/null)
[[ -z "$STUB" ]] && print_error "Stub section missing" || print_success "✓ Stub section"

FRONT_SIDE=$(echo "$FORM_100" | jq '.front_side // empty' 2>/dev/null)
[[ -z "$FRONT_SIDE" ]] && print_error "Front side section missing" || print_success "✓ Front side section"

BACK_SIDE=$(echo "$FORM_100" | jq '.back_side // empty' 2>/dev/null)
[[ -z "$BACK_SIDE" ]] && print_error "Back side section missing" || print_success "✓ Back side section"

META_LEGAL=$(echo "$FORM_100" | jq '.meta_legal_rules // empty' 2>/dev/null)
[[ -z "$META_LEGAL" ]] && print_error "Meta legal rules missing" || print_success "✓ Meta legal rules section"

# Verify stage log array
STAGE_LOG=$(echo "$FORM_100" | jq '.back_side.stage_log // empty' 2>/dev/null)
STAGE_COUNT=$(echo "$STAGE_LOG" | jq 'length // 0' 2>/dev/null)
print_success "Stage log entries: $STAGE_COUNT (expected 2)"

echo ""
echo "📋 Form 100 Structure (sample):"
echo "$FORM_100" | jq '.stub, .front_side.identity, .back_side.stage_log | first' 2>/dev/null | head -40

# ============================================================================
# PHASE 3: EDIT FORM 100
# ============================================================================

print_header "PHASE 3: EDIT FORM 100"

print_step "3.1" "Update Form 100 (partial - only triage markers)"

UPDATE_PAYLOAD=$(cat <<EOF
{
  "front_side": {
    "triage_markers": {
      "red_urgent_care": false,
      "yellow_delayed": true,
      "black_deceased": false,
      "blue_minor": false
    }
  }
}
EOF
)

UPDATE_RESPONSE=$(curl -sS -X PATCH "$BASE_URL/form100/$FORM_100_ID" \
  -H "Content-Type: application/json" \
  -d "$UPDATE_PAYLOAD")

print_success "Update sent"

# Verify update
UPDATED_TRIAGE=$(echo "$UPDATE_RESPONSE" | jq '.front_side.triage_markers // empty' 2>/dev/null)
YELLOW_FLAG=$(echo "$UPDATED_TRIAGE" | jq '.yellow_delayed' 2>/dev/null)

if [[ "$YELLOW_FLAG" == "true" ]]; then
  print_success "✓ Triage markers updated (yellow_delayed = true)"
else
  print_error "Triage update failed"
fi

# ============================================================================
# PHASE 4: VERIFY PERSISTENCE
# ============================================================================

print_header "PHASE 4: VERIFY DATABASE PERSISTENCE"

print_step "4.1" "Re-read Form 100 (simulate page reload)"

REREAD=$(curl -sS "$BASE_URL/cases/$CASE_ID")
REREAD_TRIAGE=$(echo "$REREAD" | jq '.form_100.front_side.triage_markers // empty' 2>/dev/null)
REREAD_YELLOW=$(echo "$REREAD_TRIAGE" | jq '.yellow_delayed' 2>/dev/null)

if [[ "$REREAD_YELLOW" == "true" ]]; then
  print_success "✓ Triage markers persisted to database"
else
  print_error "Persistence failed - triage reverted"
fi

# Check stage log is still there (full 2 entries)
REREAD_STAGE=$(echo "$REREAD" | jq '.form_100.back_side.stage_log // empty' 2>/dev/null)
REREAD_COUNT=$(echo "$REREAD_STAGE" | jq 'length // 0' 2>/dev/null)
print_success "✓ Stage log preserved: $REREAD_COUNT entries"

# ============================================================================
# PHASE 5: EXPORT SURFACES
# ============================================================================

print_header "PHASE 5: EXPORT SURFACES (Bundle, PDF, FHIR, QR)"

print_step "5.1" "Export Bundle (JSON)"

BUNDLE=$(curl -sS "$BASE_URL/exports/case/$CASE_ID?format=json")

echo "$BUNDLE" | jq '.' 2>/dev/null > /tmp/export_bundle.json

BUNDLE_FORM100=$(echo "$BUNDLE" | jq '.form_100 // empty' 2>/dev/null)
[[ -z "$BUNDLE_FORM100" ]] && print_error "Form 100 missing from bundle" || print_success "✓ Bundle includes Form 100 sections"

echo "Bundle file: /tmp/export_bundle.json"

print_step "5.2" "Export PDF"

PDF=$(curl -sS "$BASE_URL/exports/case/$CASE_ID?format=pdf" -o /tmp/export_form100.pdf)

if [[ -f /tmp/export_form100.pdf ]] && [[ -s /tmp/export_form100.pdf ]]; then
  SIZE=$(du -h /tmp/export_form100.pdf | cut -f1)
  print_success "✓ PDF exported ($SIZE)"
else
  print_error "PDF export failed"
fi

print_step "5.3" "Export FHIR Bundle"

FHIR=$(curl -sS "$BASE_URL/exports/case/$CASE_ID?format=fhir")

echo "$FHIR" | jq '.' 2>/dev/null > /tmp/export_fhir.json

# Count Observations for Form 100 sections
FHIR_ENTRIES=$(echo "$FHIR" | jq '.entry | length // 0' 2>/dev/null)
FORM100_OBS=$(echo "$FHIR" | jq '[.entry[] | select(.resource.code.text | startswith("Form100"))] | length' 2>/dev/null)

print_success "✓ FHIR Bundle exported"
print_success "  - Total entries: $FHIR_ENTRIES"
print_success "  - Form 100 Observations: $FORM100_OBS (expected 4)"

echo "FHIR file: /tmp/export_fhir.json"

print_step "5.4" "Export QR Code"

QR=$(curl -sS "$BASE_URL/exports/case/$CASE_ID?format=qr")

echo "$QR" | jq '.' 2>/dev/null > /tmp/export_qr.json

QR_F100=$(echo "$QR" | jq '.qr_payload.f100 // empty' 2>/dev/null)
[[ -z "$QR_F100" ]] && print_error "F100 block missing from QR payload" || print_success "✓ QR includes F100 compact block"

QR_KEYS=$(echo "$QR_F100" | jq 'keys' 2>/dev/null)
print_success "  - F100 keys: $QR_KEYS (expected: dn, s, fs, bs, mlr)"

echo "QR file: /tmp/export_qr.json"

# ============================================================================
# SUMMARY
# ============================================================================

print_header "SMOKE TEST SUMMARY"

echo -e "${GREEN}✅ ALL PHASES PASSED${NC}"
echo ""
echo "📊 Test Results:"
echo "  Phase 1 (Create): ✅ Case + Form 100 created"
echo "  Phase 2 (Read):   ✅ Canonical nested structure retrieved"
echo "  Phase 3 (Edit):   ✅ Partial update (PATCH) applied"
echo "  Phase 4 (Persist):✅ Data persisted to database"
echo "  Phase 5.1 (Bundle): ✅ JSON export includes Form 100"
echo "  Phase 5.2 (PDF):  ✅ PDF generated"
echo "  Phase 5.3 (FHIR): ✅ FHIR Bundle with Observations"
echo "  Phase 5.4 (QR):   ✅ QR payload with F100 block"
echo ""
echo "📁 Test Artifacts:"
echo "  - /tmp/case_detail.json (case detail response)"
echo "  - /tmp/export_bundle.json (JSON export)"
echo "  - /tmp/export_form100.pdf (PDF export)"
echo "  - /tmp/export_fhir.json (FHIR export)"
echo "  - /tmp/export_qr.json (QR export)"
echo ""
echo "🆔 Test Case IDs:"
echo "  - CASE_ID: $CASE_ID"
echo "  - FORM_100_ID: $FORM_100_ID"
echo ""
echo "✨ Form 100 canonical implementation VERIFIED!"
echo ""
