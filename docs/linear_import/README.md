# Імпорт MEDEVAK в Linear

Проект **MEDEVAK (CCRM)** — Combat Casualty Record Module для медичної евакуації.  
Контекст: [Вовки Да Вінчі](https://vovkydavinci.army/) — батальйон ЗСУ.

**Issue:** [DEA-5](https://linear.app/death-note/issue/DEA-5/medevak)

---

## Що є в імпорті

- **1 Epic/Project** — MEDEVAK (CCRM)
- **10 Breaking Issues** — з REAL_AUDIT_REPORT.md
- **6 Backlog items** — з PROJECT_STATUS.md

Файл: `MEDEVAK_linear_import.csv`

---

## Як імпортувати в Linear

### Варіант 1: Через Linear UI (рекомендовано)

1. Увійдіть у [Linear](https://linear.app/login).
2. Перейдіть: **Settings → Administration → Import/Export**  
   (потрібна роль Admin).
3. Натисніть **Export CSV**, щоб отримати шаблон.
4. Відкрийте `MEDEVAK_linear_import.csv` і скопіюйте потрібні рядки в шаблон Linear (або збережіть як експорт).
5. Оберіть **Import** → **Linear CSV** і завантажте файл.
6. Виберіть команду (team) для імпорту.
7. Завершіть імпорт.

### Варіант 2: CLI Importer

1. Встановіть [Linear CLI importer](https://github.com/linear/linear/tree/master/packages/import).
2. Експортуйте шаблон з Linear: **Settings → Import/Export → Export CSV**.
3. Підставте дані з `MEDEVAK_linear_import.csv` у формат Linear.
4. Запустіть імпорт згідно з [документацією](https://linear.app/docs/import-issues#trello-or-pivotal-tracker).

### Варіант 3: Створити issues вручну

1. Створіть проект **MEDEVAK** у Linear.
2. Створюйте issues по одному, копіюючи з CSV (Title, Description, Labels, Priority).

---

## Поля в CSV

| Поле       | Опис                          |
|------------|-------------------------------|
| Title      | Назва issue                   |
| Description| Опис (Markdown)               |
| Estimate   | Оцінка (points)               |
| Labels     | Bug, Feature, Chore, Project  |
| Status     | Backlog                       |
| Priority   | 1=Urgent, 2=High, 3=Medium, 4=Low |

---

## Автоматичний sync (Linear API)

```bash
# Отримати API key: https://linear.app/settings/api
export LINEAR_API_KEY=lin_api_xxx
python3 scripts/linear_sync.py
```

Скрипт оновить опис DEA-5 і створить sub-issues.

---

## Файли

| Файл | Призначення |
|------|-------------|
| `DEA-5_DESCRIPTION.md` | Опис для copy-paste в DEA-5 |
| `DEA-5_SUB_ISSUES.md` | Список sub-issues для ручного додавання |
| `MEDEVAK_linear_import.csv` | CSV для імпорту через Linear UI |

---

## Посилання

- **Сайт Вовки Да Вінчі:** https://vovkydavinci.army/
- **Linear Import Docs:** https://linear.app/docs/import-issues
- **Linear API:** https://developers.linear.app/
