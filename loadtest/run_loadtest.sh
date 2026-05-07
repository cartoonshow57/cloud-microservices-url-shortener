#!/usr/bin/env bash
set -euo pipefail

TARGET="${1:-http://localhost}"
DURATION="${2:-30s}"
CONNECTIONS="${3:-10}"
THREADS="${4:-2}"
RESULTS_DIR="$(dirname "$0")/results"

mkdir -p "$RESULTS_DIR"

if ! command -v wrk &> /dev/null; then
    echo "Installing wrk..."
    sudo apt-get update -qq && sudo apt-get install -y -qq wrk
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "============================================"
echo "Load Test: URL Shortener"
echo "Target:      $TARGET"
echo "Duration:    $DURATION"
echo "Connections: $CONNECTIONS"
echo "Threads:     $THREADS"
echo "============================================"
echo ""

echo "--- Test 1: Health Endpoint (GET /api/health) ---"
wrk -t"$THREADS" -c"$CONNECTIONS" -d"$DURATION" \
    "$TARGET/api/health" \
    | tee "$RESULTS_DIR/health_${TIMESTAMP}.txt"
echo ""

echo "--- Test 2: Shorten Endpoint (POST /shorten) ---"
wrk -t"$THREADS" -c"$CONNECTIONS" -d"$DURATION" \
    -s "$SCRIPT_DIR/shorten.lua" \
    "$TARGET" \
    | tee "$RESULTS_DIR/shorten_${TIMESTAMP}.txt"
echo ""

echo "--- Test 3: Redirect Endpoint (GET /r/{code}) ---"
CODE=$(curl -s -X POST "$TARGET/shorten" \
    -H "Content-Type: application/json" \
    -d '{"url":"https://example.com"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['code'])")

wrk -t"$THREADS" -c"$CONNECTIONS" -d"$DURATION" \
    "$TARGET/r/$CODE" \
    | tee "$RESULTS_DIR/redirect_${TIMESTAMP}.txt"
echo ""

echo "============================================"
echo "Results saved to $RESULTS_DIR/"
echo "============================================"
