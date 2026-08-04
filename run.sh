#!/usr/bin/env bash
set -euo pipefail

# Keep the venv out of ~/Documents (iCloud Drive) — iCloud evicts venv files
# to cloud-only placeholders, which makes imports hang forever reading them.
export UV_PROJECT_ENVIRONMENT="$HOME/.venvs/marktext-py"

if [ ! -d "$UV_PROJECT_ENVIRONMENT" ]; then
    echo "Virtual environment not found. Run ./install.sh first."
    exit 1
fi

echo "Starting MarkText-Py on http://localhost:8080"
uv run python main.py
