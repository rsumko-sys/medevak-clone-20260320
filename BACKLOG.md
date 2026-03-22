# BACKLOG

Відкрито після `v1.0-smoke` — 2026-03-22.  
Оновлено після `v1.2-neon` — 2026-03-22.

**Поточний канон:** `v1.2-neon` (`f3cc626`) — Neon PostgreSQL = source of truth.

---

## #1 — Access token живе після logout ~~(short-TTL design)~~ ✅ ЧАСТКОВО ЗАКРИТО

**Закрито (TTL частина) в `2508d82` (2026-03-23).**  
`ACCESS_TOKEN_EXPIRE_MINUTES` знижено 60 → 5. Вікно атаки: ~5 хв.

**Залишок — Redis JTI blacklist (P2, окрема задача):**  
Миттєва ревокація при logout. Потребує Upstash + ~50 рядків коду. Відкладено до першого бойового розгортання.

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

## #4 — Прибрати cold-start guard зі smoke_prod.py (техборг)

**Стан зараз:**  
`smoke_prod.py` має auto-register guard і mid-test re-register block — костилі під ephemeral SQLite.  
З Neon ці гілки не тригеряться, але засмічують код і маскують реальні помилки.

**Дія:** видалити або зробити опціональним `--force-init` флаг; зберегти лише базовий 401-guard як safety net.  
**Файли:** `smoke_prod.py`

---

## #5 — Винести `alembic upgrade head` в release step ✅ ЗАКРИТО

**Закрито в `2508d82` (2026-03-23).**  
`nixpacks.toml` і `Procfile` вже мали `alembic upgrade head && uvicorn` — release step існував.  
`main.py` lifespan тепер запускає alembic **тільки на Vercel** (`os.getenv("VERCEL")`).  
На nixpacks/Railway/Heroku — lifespan пропускає alembic, довіряє release step. ~300ms cold start зекономлено.

---

## #6 — Оновити `run.md` і `architecture.md` під Neon як source of truth

**Стан зараз:**  
Документація ще описує SQLite як робочу БД, не згадує Neon.  
**Дія:** оновити секції про DATABASE_URL, описати Neon як єдину production БД, прибрати згадки про `/tmp/medevak.db` з prod-flow.  
**Файли:** `docs/run.md`, `docs/architecture.md`

---

## Пріоритетність

| Пріоритет | Item | Блокер |
|-----------|------|--------|
| ✅ ЗАКРИТО | #2 Persistent DB | Neon verified, v1.2-neon |
| ✅ ЗАКРИТО | #1 Token TTL=5хв | `2508d82` — вікно 60→5 хв |
| ✅ ЗАКРИТО | #5 Alembic release step | `2508d82` — lifespan only on Vercel |
| 🟢 P2 | #1 Redis JTI blacklist | Ні — миттєва ревокація, після бойового |
| 🟢 P2 | #4 Cold-start guard у smoke | Ні — косметика |
| 🟢 P2 | #6 Docs update (Neon) | Ні — актуалізація |
| 🟢 P2 | #3 UI E2E tests | Ні — ручна перевірка поки достатня |
