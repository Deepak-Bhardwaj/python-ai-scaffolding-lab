#!/usr/bin/env bash
# Lab 2-A — one-shot setup. Prefers uv; falls back to python3.12 venv.
set -euo pipefail
cd "$(dirname "$0")"

if command -v uv >/dev/null 2>&1; then
  uv venv --python 3.12 .venv
  uv pip install --python .venv/bin/python -e ".[dev]"
else
  python3.12 -m venv .venv
  ./.venv/bin/python -m pip install --upgrade pip
  ./.venv/bin/python -m pip install -e ".[dev]"
fi

echo "Running tests..."
# Tolerate pytest exit 5 (no tests collected) — tests arrive in later tasks.
# Real failures (exit 1/2/3/4) still abort under set -e.
./.venv/bin/python -m pytest -q || test $? -eq 5
echo "Setup complete. Run ./run.sh to launch the API + Streamlit UI."
