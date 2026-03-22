# CCRM АЗОВ — Чеклист виходу в поле

**Версія:** 1.0  
**Дата:** Березень 2026

---

## Кроки перед запуском

### 1. Перевірка змінних середовища (Railway / Render)

Відкрити дашборд хостингу → Variables і переконатись:

| Змінна | Значення | Критично |
|--------|----------|----------|
| `DEV_AUTH_BYPASS` | `false` або відсутня | ✅ обов'язково |
| `SECRET_KEY` | довгий рандомний рядок | ✅ обов'язково |
| `DATABASE_URL` | postgres://... | ✅ обов'язково |
| `ENV` | `production` | рекомендовано |

> ⚠️ Якщо `DEV_AUTH_BYPASS=true` — JWT і RBAC ігноруються повністю. Будь-який запит без токена проходить.

---

### 2. Ініціалізація бази і seed користувачів

```bash
# Локально (SQLite)
cd backend
python init_db.py
python seed_users.py

# На продакшні (PostgreSQL через Railway CLI або SSH)
DATABASE_URL=postgresql://... python seed_users.py
```

Скрипт ідемпотентний — безпечно запускати повторно, вже існуючих користувачів не перезаписує.

---

### 3. Тестові облікові записи

| Email | Пароль | Роль | Призначення |
|-------|--------|------|-------------|
| `admin@azov.ua` | `Admin2026!` | admin | Перевірка адмін-панелі, аудиту, користувачів |
| `medic@azov.ua` | `Medic2026!` | medic | Бойовий дашборд, облік поранень |

> 🔒 Перед реальним розгортанням змінити паролі або видалити тестові акаунти через API / адмін-панель.

---

### 4. E2E перевірка після деплою

```
1. Відкрити /login
2. Ввести: medic@azov.ua / Medic2026!
3. Очікуваний результат: редирект на /dashboard з активною сесією

4. Відкрити /battlefield → заповнити драфт → закрити вкладку → повернутись
5. Очікуваний результат: тост "⚠ Відновлено незбережену чернетку"

6. Відкрити /battlefield → зберегти пацієнта
7. Очікуваний результат: 200 OK, драфт видалено, пацієнт у /cases

8. Відкрити /settings → ввести Whisper API ключ → закрити вкладку → повернутись
9. Очікуваний результат: ключ збережено (localStorage, переживає закриття вкладки)
```

---

### 5. Перевірка захисту без токена

```bash
# Без токена — повинен повернути 401
curl https://YOUR_BACKEND_URL/api/cases

# З токеном — повинен повернути 200
TOKEN=$(curl -s -X POST https://YOUR_BACKEND_URL/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"medic@azov.ua","password":"Medic2026!"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['access_token'])")

curl https://YOUR_BACKEND_URL/api/cases -H "Authorization: Bearer $TOKEN"
```

---

## Відомі обмеження v1.0

- Sync reconfile (`/sync/reconcile`) реалізований на бекенді, але не має UI-кнопки — синхронізація через `/sync/queue` і авто-пуш
- Голосове введення (Whisper) потребує HTTPS — на localhost не працює без self-signed cert
- Офлайн-кеш зашифрований AES через `cachePassphrase` зі sessionStorage — при закритті браузера кеш перестає читатись (навмисно, для безпеки)
