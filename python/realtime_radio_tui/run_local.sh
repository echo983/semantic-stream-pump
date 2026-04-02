#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PYTHON="$ROOT_DIR/.venv/bin/python"

if [[ ! -x "$VENV_PYTHON" ]]; then
  echo "Missing virtualenv Python at $VENV_PYTHON" >&2
  echo "Create it first with: python3 -m venv python/realtime_radio_tui/.venv" >&2
  exit 1
fi

cd "$ROOT_DIR"
PYTHONPATH="$ROOT_DIR/src" exec "$VENV_PYTHON" -m realtime_radio_tui.app "$@"
