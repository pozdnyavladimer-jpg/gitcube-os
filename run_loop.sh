#!/usr/bin/env bash

echo "=== GitCube LOOP START ==="

ITER=1

while true
do
  echo ""
  echo "=== ITERATION $ITER ==="

  ./run.sh

  echo "--- sleeping 60s ---"
  sleep 60

  ITER=$((ITER+1))
done
