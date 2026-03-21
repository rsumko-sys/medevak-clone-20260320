import io
import json
import uuid
import zipfile
from datetime import datetime
from urllib.request import Request, urlopen

BASE = "http://localhost:8000/api/v1"


def req(method, path, payload=None, accept=None):
    url = BASE + path
    headers = {}
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if accept:
        headers["Accept"] = accept
    r = Request(url, data=data, headers=headers, method=method)
    with urlopen(r, timeout=30) as resp:
        return resp.status, resp.headers.get("content-type", ""), resp.read()


def unwrap(body):
    obj = json.loads(body.decode("utf-8"))
    return obj.get("data", obj)


status, _, body = req(
    "POST",
    "/cases",
    {
        "callsign": "SMOKE-F100",
        "triage_code": "IMMEDIATE",
        "case_status": "ACTIVE",
    },
)
case = unwrap(body)
case_id = case["id"]
print("create_case", status, case_id)

create_payload = {
    "document_number": f"F100-SMOKE-{uuid.uuid4().hex[:8]}",
    "injury_datetime": datetime.utcnow().isoformat() + "Z",
    "injury_location": "Sector Smoke",
    "injury_mechanism": "Blast",
    "diagnosis_summary": "Concussion",
    "documented_by": "Medic-01",
    "front_side": {
        "triage_markers": {
            "red_urgent_care": True,
            "yellow_sanitary_processing": False,
            "black_isolation": False,
            "blue_radiation_measures": False,
        }
    },
    "back_side": {
        "stage_log": [
            {"stage_name": "ROLE_1", "result": "stable"},
        ]
    },
    "meta_legal_rules": {"commander_notified": True},
}
status, _, body = req("POST", f"/cases/{case_id}/form100", create_payload)
form = unwrap(body)
print("create_form100", status, form["id"])

status, _, body = req("GET", f"/cases/{case_id}/form100")
form = unwrap(body)
print("read_form100", status, bool(form.get("front_side")))

status, _, body = req(
    "PATCH",
    f"/cases/{case_id}/form100",
    {
        "front_side": {
            "triage_markers": {
                "red_urgent_care": False,
                "yellow_sanitary_processing": True,
                "black_isolation": False,
                "blue_radiation_measures": False,
            }
        }
    },
)
form = unwrap(body)
print(
    "patch_form100",
    status,
    form["front_side"]["triage_markers"]["yellow_sanitary_processing"],
)

status, _, body = req("GET", f"/cases/{case_id}")
case_detail = unwrap(body)
print("read_case_detail", status, bool(case_detail.get("form100")))

for name, path, accept in [
    ("bundle", f"/exports/{case_id}/bundle", None),
    ("pdf", f"/exports/{case_id}/pdf", "application/pdf"),
    ("qr", f"/exports/{case_id}/qr", None),
    ("fhir", f"/exports/{case_id}/fhir", None),
]:
    status, ctype, body = req("GET", path, accept=accept)
    print(f"export_{name}", status, ctype.split(";")[0], len(body))

status, _, body = req("GET", f"/exports/{case_id}/bundle")
zf = zipfile.ZipFile(io.BytesIO(body), "r")
case_json = json.loads(zf.read("case.json").decode("utf-8"))
f100 = case_json.get("form_100") or {}
keys = [
    k
    for k in ["stub", "front_side", "back_side", "meta_legal_rules"]
    if f100.get(k) is not None
]
print("bundle_form100_keys", keys)
print("SMOKE_OK", case_id)
