# EVACECO Transfer Runbook

Target repository:
- https://github.com/wakkawarpman-oss/EVACECO

This project already has an automation helper:
- scripts/transfer_to_evaceco.sh

## 1) Quick preview (no changes)

From project root:

```bash
bash scripts/transfer_to_evaceco.sh dry-run
```

## 2) Option A: transfer with full git history (recommended)

This keeps all branches and tags.

```bash
bash scripts/transfer_to_evaceco.sh mirror
```

What this does:
- Ensures remote name `evaceco` points to `https://github.com/wakkawarpman-oss/EVACECO.git`.
- Pushes all branches.
- Pushes all tags.

## 3) Option B: clean import without git history

Use when you want a fresh repository state.

```bash
bash scripts/transfer_to_evaceco.sh copy ../EVACECO-import
cd ../EVACECO-import
git init
git checkout -b main
git remote add origin https://github.com/wakkawarpman-oss/EVACECO.git
git add .
git commit -m "Initial import from MEDEVAK_clone"
git push -u origin main
```

## 4) Pre-transfer checklist

- Confirm current branch and uncommitted changes:

```bash
git status
git branch --show-current
```

- Verify target remote access:

```bash
git ls-remote https://github.com/wakkawarpman-oss/EVACECO.git
```

- Ensure sensitive local artifacts are not included:
  - `.venv`, `.venv2`
  - local SQLite files (`medevak.db*`)
  - `node_modules`

## 5) Post-transfer validation

- Open EVACECO repo and verify expected branches and files.
- Run backend startup:

```bash
./run.sh
```

- Run frontend build checks:

```bash
cd frontend && npm run build
cd ../sandbox/medevac-app/frontend && npm run build
```
