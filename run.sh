#!/usr/bin/env bash
set -euo pipefail

if [ ! -d ".venv" ]; then
    echo "Virtual environment not found. Run ./install.sh first."
    exit 1
fi

echo "Starting MarkText-Py on http://localhost:8080"
uv run python main.py
