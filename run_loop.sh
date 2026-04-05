#!/usr/bin/env bash

for i in 1 2 3 4 5
do
  echo "=== ITERATION $i ==="
  ./run.sh
  sleep 10
done
