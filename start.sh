#!/bin/zsh
# Start the Interview Prep app: backend (FastAPI :8000) + frontend (Vite :5173).
# Usage: ./start.sh    (Ctrl+C stops both)
cd "$(dirname "$0")"

.venv/bin/uvicorn app.backend.main:app --port 8000 &
BACK=$!
(cd app/frontend && npm run dev) &
FRONT=$!

sleep 2 && open http://localhost:5173

trap "kill $BACK $FRONT 2>/dev/null" EXIT
wait
