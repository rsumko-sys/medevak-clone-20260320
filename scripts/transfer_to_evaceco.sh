#!/usr/bin/env bash
set -euo pipefail

TARGET_REMOTE_NAME="evaceco"
TARGET_REMOTE_URL="https://github.com/wakkawarpman-oss/EVACECO.git"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

usage() {
  cat <<'EOF'
Usage:
  scripts/transfer_to_evaceco.sh dry-run
  scripts/transfer_to_evaceco.sh mirror
  scripts/transfer_to_evaceco.sh copy <destination_path>

Modes:
  dry-run
    Print what would be executed.

  mirror
    Push all local branches and tags to EVACECO remote.
    Keeps commit history.

  copy <destination_path>
    Copy project files to another folder for a fresh repository import
    (without .git metadata and without heavy local artifacts).
EOF
}

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

ensure_git_repo() {
  if ! git -C "$PROJECT_ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "Not a git repository: $PROJECT_ROOT" >&2
    exit 1
  fi
}

ensure_remote() {
  if git -C "$PROJECT_ROOT" remote get-url "$TARGET_REMOTE_NAME" >/dev/null 2>&1; then
    local current_url
    current_url="$(git -C "$PROJECT_ROOT" remote get-url "$TARGET_REMOTE_NAME")"
    if [[ "$current_url" != "$TARGET_REMOTE_URL" ]]; then
      echo "Remote '$TARGET_REMOTE_NAME' points to a different URL:" >&2
      echo "  current: $current_url" >&2
      echo "  expected: $TARGET_REMOTE_URL" >&2
      echo "Fix the remote URL manually, then rerun." >&2
      exit 1
    fi
  else
    git -C "$PROJECT_ROOT" remote add "$TARGET_REMOTE_NAME" "$TARGET_REMOTE_URL"
  fi
}

run_dry() {
  echo "Project root: $PROJECT_ROOT"
  echo "Target remote: $TARGET_REMOTE_NAME -> $TARGET_REMOTE_URL"
  echo
  echo "Mirror flow preview:"
  echo "  git -C \"$PROJECT_ROOT\" remote add $TARGET_REMOTE_NAME $TARGET_REMOTE_URL"
  echo "  git -C \"$PROJECT_ROOT\" push $TARGET_REMOTE_NAME --all"
  echo "  git -C \"$PROJECT_ROOT\" push $TARGET_REMOTE_NAME --tags"
  echo
  echo "Copy flow preview:"
  echo "  scripts/transfer_to_evaceco.sh copy ../EVACECO-import"
}

run_mirror() {
  require_cmd git
  ensure_git_repo
  ensure_remote

  echo "Pushing branches to $TARGET_REMOTE_NAME..."
  git -C "$PROJECT_ROOT" push "$TARGET_REMOTE_NAME" --all

  echo "Pushing tags to $TARGET_REMOTE_NAME..."
  git -C "$PROJECT_ROOT" push "$TARGET_REMOTE_NAME" --tags

  echo "Mirror transfer completed."
}

run_copy() {
  require_cmd rsync

  local destination="${1:-}"
  if [[ -z "$destination" ]]; then
    echo "Missing destination path for copy mode." >&2
    usage
    exit 1
  fi

  mkdir -p "$destination"

  rsync -a --delete \
    --exclude='.git/' \
    --exclude='.venv/' \
    --exclude='.venv2/' \
    --exclude='node_modules/' \
    --exclude='frontend/node_modules/' \
    --exclude='frontend/.next/' \
    --exclude='frontend/out/' \
    --exclude='frontend/out 2/' \
    --exclude='sandbox/medevac-app/frontend/node_modules/' \
    --exclude='sandbox/medevac-app/frontend/dist/' \
    --exclude='backend/__pycache__/' \
    --exclude='backend/app/**/__pycache__/' \
    --exclude='medevak.db' \
    --exclude='medevak.db-shm' \
    --exclude='medevak.db-wal' \
    "$PROJECT_ROOT/" "$destination/"

  echo "Project files copied to: $destination"
  echo "Next steps:"
  echo "  cd \"$destination\""
  echo "  git init"
  echo "  git remote add origin $TARGET_REMOTE_URL"
  echo "  git add . && git commit -m 'Initial import from MEDEVAK_clone'"
  echo "  git push -u origin main"
}

main() {
  local mode="${1:-dry-run}"
  case "$mode" in
    dry-run)
      run_dry
      ;;
    mirror)
      run_mirror
      ;;
    copy)
      run_copy "${2:-}"
      ;;
    -h|--help|help)
      usage
      ;;
    *)
      echo "Unknown mode: $mode" >&2
      usage
      exit 1
      ;;
  esac
}

main "$@"