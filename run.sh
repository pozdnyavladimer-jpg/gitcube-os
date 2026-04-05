#!/usr/bin/env bash

echo "=== GitCube START ==="

if [ -f .env ]; then
  export $(cat .env | xargs)
  echo "[OK] .env loaded"
else
  echo "[WARN] .env not found"
fi

if [ -z "$GITHUB_TOKEN" ] || [ -z "$GITHUB_REPO" ]; then
  echo "[WARN] GitHub not configured"
else
  echo "[OK] GitHub configured"
fi

echo "[STEP] OS SYNC"
PYTHONPATH=. python runtime_experimental/os_sync.py

echo "[STEP] ACTOR"
python actor_executor.py

echo "=== DONE ==="
