#!/usr/bin/env bash
# End-to-end M1 demo: Python decoder listens, C++ sender transmits.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PORT="${PORT:-5005}"
COUNT="${COUNT:-20}"
RATE="${RATE:-10}"

cd "$ROOT/sender"
if [[ ! -x ./sender ]]; then
  echo "building sender..."
  if command -v make >/dev/null 2>&1; then
    make -s
  else
    g++ -std=c++17 -O2 -Wall -Wextra -o sender main.cpp -lz
  fi
fi

cd "$ROOT/decoder"
python3 test_decode.py

python3 main.py --port "$PORT" --max-packets "$COUNT" &
DECODER_PID=$!
cleanup() { kill "$DECODER_PID" 2>/dev/null || true; }
trap cleanup EXIT
sleep 0.3

"$ROOT/sender/sender" --host 127.0.0.1 --port "$PORT" --count "$COUNT" --rate "$RATE"
wait "$DECODER_PID"
echo "demo ok"
