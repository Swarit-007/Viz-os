#!/usr/bin/env bash
# VizOS quick start: creates a virtualenv, installs dependencies and runs the server.
set -euo pipefail
cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
    echo "Python 3.9+ is required but python3 was not found." >&2
    exit 1
fi

if [ ! -d .venv ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate
pip install --quiet -r requirements.txt

export PORT="${PORT:-5000}"
echo "VizOS: http://localhost:${PORT}   API: http://localhost:${PORT}/api"
exec python backend/app.py
