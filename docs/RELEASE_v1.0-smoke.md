# Release Evidence — v1.0-smoke

**Tag:** `v1.0-smoke`  
**Commit:** `8b6d027` Fix production login redirect and navigation controls  
**Date:** 2026-03-22  
**Environment:** `https://medevak-clone-front-clone-20260321.vercel.app`  
**Vercel deploy:** `dpl_79xfpTg2o1LPYt3Fdh4KsejLFkxg` (● Ready)

---

## Smoke Test Results — 13/13 PASSED

```
=== 1. LOGIN / REDIRECT / RE-LOGIN ===
  200  POST /api/auth/login  [login]
  ✅  login 200
  200  GET /api/auth/me  [/me]
  ✅  /me returns user  (email=probe.1774204740@test.ua)

=== 2. LOGOUT + token blacklist ===
  200  POST /api/auth/logout  [logout]
  ⚠️   old access ALIVE 200  — short-expiry design (known, see backlog #1)
  401  POST /api/auth/refresh  [old refresh after logout]
  ✅  old refresh token dead (401)  (Token has been revoked)
  200  POST /api/auth/login  [re-login after logout]
  ✅  re-login OK

=== 3. EVAC — contract статусів ===
  200  POST /api/cases  [create case]
  ✅  create case
     initial status=ACTIVE
  200  PATCH /api/cases/{id}  [→ IN_TRANSPORT]
  ✅  ACTIVE → IN_TRANSPORT
  200  PATCH /api/cases/{id}  [→ HANDED_OFF]
  ✅  IN_TRANSPORT → HANDED_OFF
  422  PATCH /api/cases/{id}  [→ BOGUS]
  ✅  invalid status → 422 — contract holds

=== 4. BLOOD — save / reload / retry після refresh ===
  ✅  blood GET  (O+=0)
  ✅  blood PATCH +1  (quantity=1)
  ✅  blood reload matches patch  (reload=1 patch=1)
  ✅  token refresh OK
  ✅  blood persists after token refresh  (O+=1)

==================================================
  PASSED 13/13
==================================================
```

---

## Known Issues at Tag Time

| # | Issue | Severity | Backlog |
|---|-------|----------|---------|
| 1 | Access token lives until expiry (~15 min) after logout | Medium | `BACKLOG.md #1` |
| 2 | SQLite is ephemeral on Vercel lambda (data lost on cold start) | **High** | `BACKLOG.md #2` |

---

## Test Account (production)

> `probe.1774204740@test.ua` / `ProbePass2026!` — role: `medic`
> Note: prod DB resets on cold start until persistent DB is wired (backlog #2).
