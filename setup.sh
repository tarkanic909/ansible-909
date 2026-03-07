#!/usr/bin/env bash
# Setup Python venv and install dependencies for Ansible dynamic inventory
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"

echo "→ Creating venv at $VENV_DIR"
python3 -m venv "$VENV_DIR"

echo "→ Installing dependencies"
"$VENV_DIR/bin/pip" install --quiet --upgrade pip
"$VENV_DIR/bin/pip" install --quiet ansible

echo "✓ Done. Run: source $VENV_DIR/bin/activate"
