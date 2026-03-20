# Інтеграція Linear з MEDEVAK

**Linear issue:** [DEA-5](https://linear.app/death-note/issue/DEA-5/medevak)  
**Workspace:** death-note | **Team:** DEA

---

## 1. Linear MCP (Cursor)

Щоб Cursor міг працювати з Linear (створювати issues, шукати, оновлювати):

### Варіант A: Один клік

1. Відкрийте [Cursor MCP Directory](https://cursor.com/docs/context/mcp/directory)
2. Знайдіть **Linear** → **Add to Cursor**
3. Пройдіть OAuth (увійдіть у Linear)

### Варіант B: Через проект

Проект вже має `.cursor/mcp.json` з Linear MCP. Після перезапуску Cursor:

1. **Settings** → **MCP** → перевірте, що Linear у списку
2. Якщо потрібна авторизація — натисніть **Connect** і увійдіть у Linear

### Що дає MCP

- `create_issue` — створення issues
- `search_issues` — пошук за team, assignee, label, priority
- `read_issue` — деталі issue
- `update_issue` — оновлення опису, статусу
- Projects, initiatives, milestones

---

## 2. GitHub Integration

Якщо репозиторій на GitHub:

1. **Linear** → **Settings** → **Integrations** → **GitHub**
2. Підключіть організацію/репо
3. Оберіть команду **DEA**
4. PR будуть зв’язуватися з issues (наприклад, `DEA-5` у commit/PR)

---

## 3. API Script (без MCP)

Для CI/CD або терміналу:

```bash
export LINEAR_API_KEY=lin_api_xxx  # https://linear.app/settings/api
python3 scripts/linear_sync.py
```

Оновлює DEA-5 і створює sub-issues.

---

## 4. Файли проекту

| Файл | Призначення |
|------|-------------|
| `.cursor/mcp.json` | Linear MCP config |
| `docs/linear_import/DEA-5_DESCRIPTION.md` | Опис для DEA-5 |
| `docs/linear_import/DEA-5_SUB_ISSUES.md` | Sub-issues |
| `scripts/linear_sync.py` | API sync script |

---

## 5. Посилання

- [Linear MCP Docs](https://linear.app/docs/mcp)
- [Linear API](https://developers.linear.app/)
- [GitHub ↔ Linear](https://linear.app/docs/github)
