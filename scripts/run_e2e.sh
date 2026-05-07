#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-mock}"

echo "=== Unit + Integration Tests ==="
python3 -m pytest tests/ --ignore=tests/e2e -q

echo ""
echo "=== Playwright E2E Tests (${MODE} mode) ==="

if [ "$MODE" = "live" ]; then
    python3 -m pytest tests/e2e/ -v -m live
elif [ "$MODE" = "all" ]; then
    python3 -m pytest tests/e2e/ -v
else
    python3 -m pytest tests/e2e/ -v -m "not live"
fi

echo ""
echo "Videos saved to tests/e2e/videos/"
