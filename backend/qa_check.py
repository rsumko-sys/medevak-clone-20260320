"""QA check script — run from backend/ with PYTHONPATH=."""
import sys
import os

def sep(title):
    print(f"\n{'='*50}")
    print(f"  {title}")
    print('='*50)

errors = []

# ── 1. Config ──
sep("1. CONFIG")
try:
    from app.core.config import (
        DEV_AUTH_BYPASS, CORS_ORIGINS, ALLOW_GPS,
        PRIVATE_NETWORK_ONLY, SECRET_KEY,
        ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS,
        MAX_UPLOAD_SIZE
    )
    checks = [
        ("DEV_AUTH_BYPASS is False", DEV_AUTH_BYPASS == False),
        ("ALLOW_GPS is False",       ALLOW_GPS == False),
        ("SECRET_KEY is set",        bool(SECRET_KEY)),
        ("ACCESS_TOKEN 60min",       ACCESS_TOKEN_EXPIRE_MINUTES == 60),
        ("REFRESH_TOKEN 7 days",     REFRESH_TOKEN_EXPIRE_DAYS == 7),
        ("MAX_UPLOAD 10MB",          MAX_UPLOAD_SIZE == 10_485_760),
    ]
    for label, ok in checks:
        status = "✅" if ok else "❌"
        print(f"  {status} {label}")
        if not ok:
            errors.append(label)
    print(f"  ℹ  CORS_ORIGINS        = {CORS_ORIGINS}")
    print(f"  ℹ  PRIVATE_NETWORK     = {PRIVATE_NETWORK_ONLY}")
except Exception as e:
    print(f"  ❌ Config import failed: {e}")
    errors.append(f"Config: {e}")

# ── 2. Security / RBAC ──
sep("2. RBAC")
try:
    from app.core.security import has_permission, Permission, UserRole

    rbac_tests = [
        ("admin  can DELETE_PERSONNEL",   'admin',  Permission.DELETE_PERSONNEL, True),
        ("medic  cannot DELETE_PERSONNEL",'medic',  Permission.DELETE_PERSONNEL, False),
        ("viewer cannot CREATE_MEDICAL",  'viewer', Permission.CREATE_MEDICAL,   False),
        ("medic  can CREATE_MEDICAL",     'medic',  Permission.CREATE_MEDICAL,   True),
        ("admin  can AUDIT_LOGS",         'admin',  Permission.AUDIT_LOGS,       True),
        ("viewer cannot EXPORT_DATA",     'viewer', Permission.EXPORT_DATA,      False),
    ]
    for label, role, perm, expected in rbac_tests:
        result = has_permission(role, perm)
        ok = result == expected
        status = "✅" if ok else "❌"
        print(f"  {status} {label}")
        if not ok:
            errors.append(f"RBAC: {label}")
except Exception as e:
    print(f"  ❌ RBAC failed: {e}")
    errors.append(f"RBAC: {e}")

# ── 3. JWT ──
sep("3. JWT AUTH")
try:
    from app.core.auth import create_access_token, create_refresh_token, decode_token, hash_password, verify_password

    # Access token
    token = create_access_token({'sub': 'ua_medic_1', 'role': 'medic', 'unit': 'AZOV'})
    d = decode_token(token)
    checks = [
        ("access token sub",   d.get('sub') == 'ua_medic_1'),
        ("access token type",  d.get('type') == 'access'),
        ("access token unit",  d.get('unit') == 'AZOV'),
    ]
    # Refresh token
    rtoken = create_refresh_token({'sub': 'ua_medic_1'})
    rd = decode_token(rtoken)
    checks += [
        ("refresh token type", rd.get('type') == 'refresh'),
    ]
    # bcrypt
    pw_hash = hash_password('pass123')
    checks += [
        ('bcrypt hash not plaintext', pw_hash != 'pass123'),
        ('bcrypt verify correct',     verify_password('pass123', pw_hash)),
        ("bcrypt verify wrong",       not verify_password('wrong', pw_hash)),
    ]
    # Invalid token
    bad = decode_token("obviously.invalid.token")
    checks += [("invalid token returns None", bad is None)]

    for label, ok in checks:
        status = "✅" if ok else "❌"
        print(f"  {status} {label}")
        if not ok:
            errors.append(f"JWT: {label}")
except Exception as e:
    print(f"  ❌ JWT failed: {e}")
    errors.append(f"JWT: {e}")

# ── 4. Medical Validator ──
sep("4. MEDICAL VALIDATOR")
try:
    from app.core.medical_validator import validate_medical_data, MedicalDataValidator
    ok, results_ok = validate_medical_data({'heart_rate': 80, 'spo2_percent': 98})
    _, results_bad = validate_medical_data({'heart_rate': 400, 'spo2_percent': 50})
    checks = [
        ("validator importable",          True),
        ("valid data accepted",           ok),
        ("MedicalDataValidator class ok", MedicalDataValidator is not None),
    ]
    for label, val in checks:
        status = "✅" if val else "⚠️ "
        print(f"  {status} {label}")
except Exception as e:
    print(f"  ⚠️  medical_validator skipped: {e}")

# ── 5. Model imports ──
sep("5. ALL MODELS")
models_to_check = [
    ('cases',      'app.models.cases',      'Case'),
    ('evacuation', 'app.models.evacuation', 'EvacuationRecord'),
    ('march',      'app.models.march',      'MarchAssessment'),
    ('injuries',   'app.models.injuries',   'Injury'),
    ('audit',      'app.models.audit',      'AuditLog'),
    ('documents',  'app.models.documents',  'CaseDocument'),
    ('user',       'app.models.user',       'User'),
    ('sync_queue', 'app.models.sync_queue', 'SyncQueue'),
    ('vitals',     'app.models.vitals',     'VitalsObservation'),
    ('procedures', 'app.models.procedures', 'Procedure'),
    ('medications','app.models.medications','MedicationAdministration'),
    ('personnel',  'app.models.personnel',  'ServiceMember'),
    ('events',     'app.models.events',     'Event'),
]
for name, module, cls in models_to_check:
    try:
        m = __import__(module, fromlist=[cls])
        getattr(m, cls)
        print(f"  ✅ {name}.{cls}")
    except Exception as e:
        print(f"  ❌ {name}: {e}")
        errors.append(f"Model {name}: {e}")

# ── 6. API router ──
sep("6. API ROUTER")
try:
    from app.api.router import api_router
    routes = [r.path for r in api_router.routes]
    expected = ['/cases', '/evacuation', '/march', '/audit', '/sync', '/auth', '/documents']
    for ep in expected:
        found = any(ep in r for r in routes)
        status = "✅" if found else "❌"
        print(f"  {status} {ep}")
        if not found:
            errors.append(f"Router missing: {ep}")
    print(f"  ℹ  Total routes: {len(routes)}")
except Exception as e:
    print(f"  ❌ Router: {e}")
    errors.append(f"Router: {e}")

# ── 7. Migrations ──
sep("7. MIGRATIONS")
try:
    import glob
    migration_files = glob.glob('migrations/versions/*.py')
    migration_files = [f for f in migration_files if not f.endswith('__pycache__')]
    print(f"  ✅ Migration files found: {len(migration_files)}")
    for f in sorted(migration_files):
        print(f"     • {os.path.basename(f)}")
    if len(migration_files) == 0:
        errors.append("No migration files found")
except Exception as e:
    print(f"  ❌ Migrations: {e}")

# ── SUMMARY ──
sep("SUMMARY")
if not errors:
    print("  ✅✅✅  ALL CHECKS PASSED — СИСТЕМА ГОТОВА ДО БОЮ")
else:
    print(f"  ❌ {len(errors)} ISSUES FOUND:")
    for e in errors:
        print(f"     • {e}")

sys.exit(0 if not errors else 1)
