#!/usr/bin/env bash
set -u

BASE_API="http://127.0.0.1:8000/api"
BASE_UI="http://127.0.0.1:3000"
DURATION=180
END_TS=$(( $(date +%s) + DURATION ))

PASS=0
FAIL=0
CREATED=0
S0=0
S1=0
S2=0
S3=0
S4=0
S5=0
S6=0
S7=0
ERRORS_FILE="/tmp/qa_massive_errors_v2.log"
: > "$ERRORS_FILE"

rand_pick() { echo $((RANDOM % $1)); }

add_pass() { PASS=$((PASS+1)); }
add_fail() {
  FAIL=$((FAIL+1))
  echo "[$(date +%T)] FAIL: $*" >> "$ERRORS_FILE"
}

check_http() {
  local method="$1"; shift
  local url="$1"; shift
  local body="${1-}"
  local code
  if [[ -n "$body" ]]; then
    code=$(curl -sS -o /tmp/qa_resp.json -w "%{http_code}" -X "$method" "$url" -H 'Content-Type: application/json' -d "$body" || echo 000)
  else
    code=$(curl -sS -o /tmp/qa_resp.json -w "%{http_code}" -X "$method" "$url" || echo 000)
  fi
  echo "$code"
}

# Readiness gates
for u in "$BASE_UI/" "$BASE_UI/battlefield" "$BASE_UI/supplies" "http://127.0.0.1:8000/health"; do
  code=$(curl -sS -o /dev/null -w "%{http_code}" "$u" || echo 000)
  if [[ "$code" =~ ^2|3 ]]; then add_pass; else add_fail "readiness $u code=$code"; fi
done

while [[ $(date +%s) -lt $END_TS ]]; do
  scenario=$(rand_pick 8)
  case "$scenario" in
    0)
      S0=$((S0+1))
      for p in / /battlefield /command /cases /supplies /blood /evac /documents /exports /sync /audit /settings; do
        code=$(curl -sS -o /dev/null -w "%{http_code}" "$BASE_UI$p" || echo 000)
        if [[ "$code" =~ ^2|3 ]]; then add_pass; else add_fail "ui $p code=$code"; fi
      done
      ;;
    1)
      S1=$((S1+1))
      payload=$(cat <<JSON
{"callsign":"QA-$RANDOM","full_name":"Тест $RANDOM","unit":"QA-UNIT","triage_code":"IMMEDIATE","tourniquet_applied":true,"incident_time":"$(date -u +%Y-%m-%dT%H:%M:%SZ)","injuries":[{"body_region":"CHEST_ANTERIOR","injury_type":"FRAG_WOUND","severity":"SEVERE","view":"front","penetrating":true}]}
JSON
)
      code=$(check_http POST "$BASE_API/cases" "$payload")
      if [[ "$code" == "200" || "$code" == "201" ]]; then
        add_pass
        cid=$(node -e 'const fs=require("fs");try{const d=JSON.parse(fs.readFileSync("/tmp/qa_resp.json","utf8"));process.stdout.write(((d.data||{}).id||""));}catch{process.stdout.write("")}')
        if [[ -n "$cid" ]]; then
          CREATED=$((CREATED+1))
          for ep_body in \
            "/cases/$cid/vitals::{\"heart_rate\":120,\"respiratory_rate\":28,\"systolic_bp\":90,\"diastolic_bp\":60,\"spo2_percent\":92}" \
            "/cases/$cid/march::{\"m_massive_bleeding\":true,\"m_tourniquets_applied\":1}" \
            "/cases/$cid/evacuation::{\"evacuation_priority\":\"URGENT\",\"transport_type\":\"GROUND\",\"destination\":\"ROLE-2\"}" \
            "/cases/$cid/events::{\"event_type\":\"timeline\",\"payload\":{\"note\":\"qa stress\"}}"
          do
            ep="${ep_body%%::*}"; body="${ep_body##*::}"
            code2=$(check_http POST "$BASE_API$ep" "$body")
            if [[ "$code2" == "200" || "$code2" == "201" ]]; then add_pass; else add_fail "chain $ep code=$code2"; fi
          done
        else
          add_fail "create case parse id failed"
        fi
      else
        add_fail "create case code=$code"
      fi
      ;;
    2)
      S2=$((S2+1))
      for bad in \
        '{"triage_code":123}' \
        '{"callsign":"","triage_code":"NOPE"}' \
        '{"injuries":"boom"}' \
        '{"tourniquet_applied":"yes"}'
      do
        code=$(check_http POST "$BASE_API/cases" "$bad")
        if [[ "$code" =~ ^4 ]]; then add_pass; else add_fail "fuzz expected4xx got $code payload=$bad"; fi
      done
      ;;
    3)
      S3=$((S3+1))
      for p in "/sync/stats" "/sync/queue" "/audit?limit=20" "/reference"; do
        code=$(check_http GET "$BASE_API$p")
        if [[ "$code" == "200" ]]; then add_pass; else add_fail "sync/audit $p code=$code"; fi
      done
      ;;
    4)
      S4=$((S4+1))
      for i in 1 2 3 4 5; do
        (
          check_http POST "$BASE_API/cases" "{\"callsign\":\"B$i-$RANDOM\",\"triage_code\":\"DELAYED\"}" >/tmp/qa_burst_$i.txt
        ) &
      done
      wait
      code=$(check_http GET "$BASE_API/cases")
      if [[ "$code" == "200" ]]; then add_pass; else add_fail "post-burst list cases code=$code"; fi
      ;;
    5)
      S5=$((S5+1))
      fake="00000000-0000-0000-0000-000000000000"
      for p in "/cases/$fake" "/cases/$fake/mist" "/cases/$fake/vitals"; do
        if [[ "$p" == *"/vitals" ]]; then
          code=$(check_http POST "$BASE_API$p" '{"heart_rate":111}')
        else
          code=$(check_http GET "$BASE_API$p")
        fi
        if [[ "$code" =~ ^4 ]]; then add_pass; else add_fail "fake id $p code=$code"; fi
      done
      ;;
    6)
      S6=$((S6+1))
      code=$(check_http GET "$BASE_API/documents")
      if [[ "$code" == "200" ]]; then add_pass; else add_fail "documents list code=$code"; fi
      ;;
    7)
      S7=$((S7+1))
      for i in {1..8}; do
        curl -sS -o /dev/null "$BASE_UI/battlefield" &
        curl -sS -o /dev/null "$BASE_UI/sync" &
        curl -sS -o /dev/null "$BASE_API/sync/stats" &
      done
      wait
      add_pass
      ;;
  esac
  sleep 0.2
done

echo "QA_MASSIVE_SUMMARY pass=$PASS fail=$FAIL created_cases=$CREATED"
echo "QA_SCENARIOS s0=$S0 s1=$S1 s2=$S2 s3=$S3 s4=$S4 s5=$S5 s6=$S6 s7=$S7"
echo "QA_ERRORS_FILE $ERRORS_FILE"
if [[ -s "$ERRORS_FILE" ]]; then
  echo "--- FIRST FAILURES ---"
  sed -n '1,60p' "$ERRORS_FILE"
fi
