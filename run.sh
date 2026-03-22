#!/bin/bash

# Standardized MEDEVAK Startup Script
# Use this to ensure correct import paths and environment activation.

set -e

# Resolve the project root (directory where the script is located)
PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$PROJECT_ROOT"

echo "🔧 Activating venv from $PROJECT_ROOT/.venv..."
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
else
    echo "❌ Error: .venv not found. Please run 'uv venv' or 'python3 -m venv .venv' first."
    exit 1
fi

# Security Assertion: Verify SSL availability before execution
if ! python3 -c "import ssl" >/dev/null 2>&1; then
    echo "❌ CRITICAL SECURITY ERROR: The 'ssl' module is missing."
    echo "Aborting execution. SSL is required."
    exit 1
fi

echo "🚀 Starting backend (local-only mode)..."
# Respect the value from .env if already set; default to false (secure default).
export DEV_AUTH_BYPASS="${DEV_AUTH_BYPASS:-false}"
# Using the module path 'backend.main:app' allows uvicorn to resolve imports relative to root.
exec uvicorn backend.main:app \
  --host 127.0.0.1 \
  --port 8000
