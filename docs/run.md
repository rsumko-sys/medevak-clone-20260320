# Запуск MEDEVAK

## 1. Передумови

- Python 3.10+
- Node.js 18+
- npm або yarn

---

## 2. Backend

```bash
cd /Users/admin/Desktop/MEDEVAK_clone

# Віртуальне середовище (опційно)
python3 -m venv .venv
source .venv/bin/activate   # Linux/macOS

# Залежності
pip install -r backend/requirements.txt

# Міграції
cd backend && python3 -m alembic upgrade head && cd ..

# Запуск (через кореневий скрипт)
./run.sh
```

**URL:** http://localhost:8000  
**Auth:** За замовчуванням auth вимкнено лише при `DEV_AUTH_BYPASS=true`. Продакшн — без bypass.  
**Docs:** http://localhost:8000/docs

---

## 3. Dashboard

```bash
cd /Users/admin/Desktop/MEDEVAK_clone/frontend

# Залежності
npm install

# Запуск
npm run dev
```

**URL:** http://localhost:3000

---

## 4. Змінні середовища

### Dashboard (.env.local)

```
NEXT_PUBLIC_API_BASE=http://localhost:8000/api
```
(Якщо не вказано, використовується значення за замовчуванням.)

### Backend

```
DATABASE_URL=sqlite+aiosqlite:///./medevak.db   # default
DEV_AUTH_BYPASS=true   # лише для локальної розробки; продакшн — false
SECRET_KEY=...         # обовʼязково змінити для продакшну
PRIVATE_NETWORK_ONLY=true  # тільки LAN/VPN (блокує публічні мережі)
ALLOW_GPS=false            # забороняє geo_lat/geo_lon у кейсах
```

---

## 5. Перевірка

```bash
./scripts/verify_mvp.sh
```

---

## 6. Типові проблеми

| Проблема | Рішення |
|----------|---------|
| `pip` not found | Використовувати `python3 -m pip` |
| `alembic` not found | Використовувати `python3 -m alembic` |
| Dashboard ERR_CONNECTION_REFUSED | Запустити backend на порту 8000 |
| `@next/env` missing | `npm install` у dashboard |
| Міграції не застосовуються | Перевірити `alembic.ini` та `env.py` — sqlite:///./medevak.db |
