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

# --- System libs for weasyprint (PDF export) ---
case "$(uname)" in
    Darwin)
        if ! command -v brew &>/dev/null; then
            echo "WARNING: Homebrew not found. PDF export requires pango/glib from Homebrew."
            echo "Install Homebrew: https://brew.sh"
        elif ! brew list pango &>/dev/null 2>&1; then
            echo "Installing pango (required by weasyprint for PDF export)..."
            brew install pango
        else
            echo "pango: already installed"
        fi
        ;;
    Linux)
        if command -v apt-get &>/dev/null; then
            if ! dpkg -s libpango-1.0-0 &>/dev/null 2>&1; then
                echo "Installing system libraries for weasyprint..."
                sudo apt-get install -y libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz0b libffi-dev
            else
                echo "pango: already installed"
            fi
        elif command -v dnf &>/dev/null; then
            if ! rpm -q pango &>/dev/null 2>&1; then
                echo "Installing system libraries for weasyprint..."
                sudo dnf install -y pango pango-devel
            else
                echo "pango: already installed"
            fi
        else
            echo "WARNING: Could not detect package manager. PDF export requires pango."
            echo "Install pango/pangoft2 using your distro's package manager."
        fi
        ;;
esac

# --- make scripts executable ---
chmod +x install.sh run.sh 2>/dev/null || true

echo ""
echo "Done! Run ./run.sh to start MarkText-Py."
