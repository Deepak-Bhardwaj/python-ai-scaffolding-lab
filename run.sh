#!/usr/bin/env bash
# Lab 2-A — launch the API (background) then the Streamlit UI (foreground).
set -euo pipefail
cd "$(dirname "$0")"

PY="./.venv/bin/python"
[ -x "$PY" ] || { echo "Run ./setup.sh first."; exit 1; }

API_PORT="${API_PORT:-8000}"
export API_BASE_URL="http://localhost:${API_PORT}"

echo "Starting API on ${API_BASE_URL} ..."
"$PY" -m uvicorn api.main:app --port "${API_PORT}" &
API_PID=$!
trap 'kill $API_PID 2>/dev/null || true' EXIT

# Wait for /health before launching the UI.
for _ in $(seq 1 30); do
  if "$PY" -c "import httpx,sys; sys.exit(0 if httpx.get('${API_BASE_URL}/health').status_code==200 else 1)" 2>/dev/null; then
    break
  fi
  sleep 0.5
done

echo "Starting Streamlit on http://localhost:8501 ..."
"$PY" -m streamlit run ui/streamlit_app.py
