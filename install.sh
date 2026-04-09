#!/usr/bin/env bash
set -euo pipefail

echo "=== MarkText-Py installer ==="

# --- uv ---
if ! command -v uv &>/dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi
echo "uv: $(uv --version)"

# --- Python deps ---
echo "Installing Python dependencies..."
uv sync

# --- macOS: Homebrew libs for weasyprint (PDF export) ---
if [[ "$(uname)" == "Darwin" ]]; then
    if ! command -v brew &>/dev/null; then
        echo "WARNING: Homebrew not found. PDF export requires pango/glib from Homebrew."
        echo "Install Homebrew: https://brew.sh"
    elif ! brew list pango &>/dev/null 2>&1; then
        echo "Installing pango (required by weasyprint for PDF export)..."
        brew install pango
    else
        echo "pango: already installed"
    fi
fi

# --- make scripts executable ---
chmod +x install.sh run.sh 2>/dev/null || true

echo ""
echo "Done! Run ./run.sh to start MarkText-Py."
