#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [ ! -d .venv ]; then
  echo "Creating Python venv and installing backend deps..."
  python3 -m venv .venv
  .venv/bin/pip install -r requirements.txt
fi

if [ ! -d frontend/node_modules ]; then
  echo "Installing frontend deps..."
  (cd frontend && npm install)
fi

echo "Starting backend on http://localhost:8000 ..."
.venv/bin/uvicorn api.main:app --reload --port 8000 &
BACKEND_PID=$!

echo "Starting website on http://localhost:3000 ..."
(cd frontend && npm run dev) &
FRONTEND_PID=$!

cleanup() {
  echo
  echo "Stopping servers..."
  kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo
echo "Website ready:  http://localhost:3000"
echo "Backend API:    http://localhost:8000 (press Ctrl+C to stop both)"
wait