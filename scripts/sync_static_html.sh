#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PUBLIC_DIR="$ROOT_DIR/frontend/public"

mkdir -p "$PUBLIC_DIR"

FILES=(
  "CCRM_AZOV.html"
  "CCRM_AZOV_OFFLINE.html"
  "CCRM_AZOV_OFFLINE_TEST.html"
  "CCRM_ULF.html"
  "CCRM_ULF_OFFLINE.html"
  "CCRM_ULF_OFFLINE_TEST.html"
  "medevak_os.html"
)

for f in "${FILES[@]}"; do
  cp "$ROOT_DIR/$f" "$PUBLIC_DIR/$f"
done

echo "Synced ${#FILES[@]} static HTML files to frontend/public"
