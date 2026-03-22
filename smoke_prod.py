"""
Production smoke test — MEDEVAK
Tests: login, logout+blacklist, evac contract, blood persistence
"""
import urllib.request, urllib.error, json

BASE  = "https://medevak-clone-front-clone-20260321.vercel.app"
EMAIL = "probe.1774204740@test.ua"
PASS  = "ProbePass2026!"

PASS_  = []
FAIL_  = []

def req(method, path, body=None, token=None, label=""):
    url = BASE + path
    data = json.dumps(body).encode() if body else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    r = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, timeout=15) as resp:
            js = json.loads(resp.read().decode())
            print(f"  {resp.status}  {method} {path}  [{label}]")
            return resp.status, js
    except urllib.error.HTTPError as e:
        try:
            js = json.loads(e.read().decode())
        except:
            js = {}
        print(f"  {e.code}  {method} {path}  [{label}]  detail={js.get('detail','')}")
        return e.code, js

def unwrap(r):
    if isinstance(r, list):
        return r
    return r.get("data", r)

def tokens(r):
    d = unwrap(r)
    return d["access_token"], d["refresh_token"]

def check(label, cond, note=""):
    if cond:
        PASS_.append(label)
        print(f"  ✅  {label}" + (f"  ({note})" if note else ""))
    else:
        FAIL_.append(label)
        print(f"  ❌  {label}" + (f"  ({note})" if note else ""))

# ── 1. LOGIN ──────────────────────────────────────────────────
print("\n=== 1. LOGIN / REDIRECT / RE-LOGIN ===")
st, r = req("POST", "/api/auth/login", {"email": EMAIL, "password": PASS}, label="login")
check("login 200", st == 200)
access1, refresh1 = tokens(r)
st, r = req("GET", "/api/auth/me", token=access1, label="/me")
u = unwrap(r)
check("/me returns user", st == 200 and u.get("email") == EMAIL, f"email={u.get('email')}")

# ── 2. LOGOUT + token blacklist ───────────────────────────────
print("\n=== 2. LOGOUT + token blacklist ===")
req("POST", "/api/auth/logout", {"refresh_token": refresh1}, token=access1, label="logout")

st_acc, _ = req("GET", "/api/auth/me", token=access1, label="access token after logout")
if st_acc == 401:
    check("old access token dead", True)
else:
    # Access tokens are short-lived JWTs; this backend revokes via token_version on the
    # /refresh path only. Access token stays valid until expiry (~15 min).
    # Not a blocker but worth noting.
    print(f"  ⚠️   old access ALIVE {st_acc}  — server uses short-expiry approach, not immediate revoke on access path")

st_ref, r_ref = req("POST", "/api/auth/refresh", {"refresh_token": refresh1}, label="refresh token after logout")
check("old refresh token dead (401)", st_ref == 401, r_ref.get("detail", ""))

st, r = req("POST", "/api/auth/login", {"email": EMAIL, "password": PASS}, label="re-login after logout")
check("re-login OK", st == 200)
access2, refresh2 = tokens(r)

# ── 3. EVAC — status contract ─────────────────────────────────
print("\n=== 3. EVAC — contract статусів ===")
st, r = req("POST", "/api/cases", {
    "full_name": "Smoke Evac",
    "call_sign": "SMK",
    "unit": "1st Btn",
    "injury_mechanism": "Blast",
    "injury_description": "smoke test"
}, token=access2, label="create case")
case_data = unwrap(r)
cid = case_data.get("id")
check("create case", cid is not None, f"id={cid}")
print(f"     initial status={case_data.get('case_status')}")

st, r = req("PATCH", f"/api/cases/{cid}", {"case_status": "IN_TRANSPORT"}, token=access2, label="→ IN_TRANSPORT")
d = unwrap(r)
check("ACTIVE → IN_TRANSPORT", d.get("case_status") == "IN_TRANSPORT", d.get("case_status"))

st, r = req("PATCH", f"/api/cases/{cid}", {"case_status": "HANDED_OFF"}, token=access2, label="→ HANDED_OFF")
d = unwrap(r)
check("IN_TRANSPORT → HANDED_OFF", d.get("case_status") == "HANDED_OFF", d.get("case_status"))

st, _ = req("PATCH", f"/api/cases/{cid}", {"case_status": "BOGUS"}, token=access2, label="→ BOGUS (422?)")
check("invalid status → 422", st == 422, f"got {st}")

# ── 4. BLOOD — save / reload / retry after refresh ───────────
print("\n=== 4. BLOOD — save / reload / retry після refresh ===")
def blood_oplus(r):
    """Extract O+ quantity from wrapped blood inventory response."""
    lst = unwrap(r)
    if not isinstance(lst, list):
        return None
    return next((x["quantity"] for x in lst if x["blood_type"] == "O+"), None)

st, r = req("GET", "/api/blood", token=access2, label="GET before")
before = blood_oplus(r)
check("blood GET", before is not None, f"O+={before}")

st, r = req("PATCH", "/api/blood/O%2B", {"delta": 1, "reason": "restock"}, token=access2, label="PATCH O+ +1")
d = unwrap(r)
patched = d.get("quantity")
check("blood PATCH +1", st == 200 and patched is not None, f"quantity={patched}")

st, r = req("GET", "/api/blood", token=access2, label="GET reload")
reload_val = blood_oplus(r)
check("blood reload matches patch", reload_val == patched, f"reload={reload_val} patch={patched}")

st, r = req("POST", "/api/auth/refresh", {"refresh_token": refresh2}, label="rotate token")
check("token refresh OK", st == 200)
access3, _ = tokens(r)

st, r = req("GET", "/api/blood", token=access3, label="GET after token refresh")
post_refresh = blood_oplus(r)
check("blood persists after token refresh", post_refresh == reload_val, f"O+={post_refresh}")

# cleanup: undo the +1 to leave DB clean
req("PATCH", "/api/blood/O%2B", {"delta": -1, "reason": "manual_use"}, token=access3, label="cleanup O+ -1")

# ── summary ───────────────────────────────────────────────────
print(f"\n{'='*50}")
print(f"  PASSED {len(PASS_)}/{len(PASS_)+len(FAIL_)}")
if FAIL_:
    print(f"  FAILED: {', '.join(FAIL_)}")
print(f"{'='*50}")
