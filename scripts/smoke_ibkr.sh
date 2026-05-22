#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-$ROOT_DIR/.venv/bin/python}"

if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "Python environment not found at $PYTHON_BIN. Run: uv sync" >&2
  exit 2
fi

cd "$ROOT_DIR"
export PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"

"$PYTHON_BIN" scripts/check_ibkr_setup.py
"$PYTHON_BIN" -m modules.historical_data forex EURUSD --client-id 11
"$PYTHON_BIN" -m modules.historical_data stock AAPL --streams TRADES --client-id 12
