# BACKLOG

Відкрито після `v1.0-smoke` — 2026-03-22.

---

## #1 — Access token живе після logout (short-TTL design)

**Стан зараз:**  
При logout `token_version` інкрементується в БД → старий `refresh_token` → 401 ✅  
Але старий `access_token` (JWT, stateless) живе до expiry (~15 хв).

**Чому це важливо:**  
Якщо пристрій захоплений або токен вкрадений — атакер має вікно ~15 хв доступу після того, як справжній користувач вийшов.

**Два варіанти виправлення:**

| Варіант | Зміни | Trade-off |
|---------|-------|-----------|
| Скоротити `ACCESS_TOKEN_EXPIRE_MINUTES` до 5 | 1 env var | Вікно ~5 хв, але не нуль |
| Upstash Redis JTI blacklist | ~50 рядків коду + Upstash free tier | Миттєва ревокація, +1 залежність, +~1ms latency |

**Рекомендація для бойового розгортання:** Redis JTI blacklist.  
**До першого бойового:** достатньо TTL=5хв.

**Файли до зміни:** `backend/app/core/security.py`, `backend/app/api/v1/auth.py`

---

## #2 — Ephemeral SQLite (hard blocker для production)

**Стан зараз:**  
`DATABASE_URL` → SQLite у `/tmp` або bundle на Vercel. Дані вмирають на cold start / між інстансами.

**Симптом:** після кожного deploy або ~5 хв idle — всі користувачі, кейси, кров зникають.

**Виправлення:**  
1. Створити БД на **Neon** (serverless PostgreSQL, free tier): `https://neon.tech`
2. Додати в Vercel env: `DATABASE_URL=postgresql+asyncpg://user:pass@ep-xxx.neon.tech/medevak`
3. `requirements.txt`: замінити `aiosqlite` → `asyncpg`
4. `alembic upgrade head` проти нової БД

**Файли до зміни:** `backend/requirements.txt`, Vercel env vars, Alembic migration (якщо є SQLite-specific типи).

**Нічого в логіці не змінюється** — SQLAlchemy async abstraction уже є.

---

## #3 — E2E через UI-кліки (не тільки API)

**Стан зараз:**  
Smoke test покриває API contract (HTTP рівень). UI взаємодія — тільки ручна перевірка.

**Що не покрито автоматично:**
- Форма логіна: введення, сабміт, redirect
- Evac: кнопки "Прийняти" / "Передати", confirm dialog
- Blood: кнопки +/−, toast повідомлення, optimistic update
- Sidebar navigation, back button, logout button

**Варіанти:**
- **Playwright** (рекомендовано для Next.js static export) — headless Chromium, TypeScript
- **Cypress** — альтернатива, більш відомий

**Мінімальний набір тестів:**
```
login.spec.ts       — form submit → /dashboard redirect
evac.spec.ts        — status change modal → confirm → API call
blood.spec.ts       — +/- buttons → inventory update → persist after reload
auth.spec.ts        — logout → /login, no protected routes accessible
```

---

## Пріоритетність

| Пріоритет | Item | Блокер |
|-----------|------|--------|
| 🔴 P0 | #2 Persistent DB | Так — без цього prod непридатний |
| 🟡 P1 | #1 Access token revocation | Ні — TTL=5хв як проміжне рішення |
| 🟢 P2 | #3 UI E2E tests | Ні — ручна перевірка поки достатня |
