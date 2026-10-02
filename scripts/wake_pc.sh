#!/usr/bin/env bash
# Wakes the PC and waits until Hegel's mind answers. Prints "awake <seconds>s".
set -euo pipefail
source "${HEGEL_ENV:-$HOME/.config/hegel/env}"
: "${PC_MAC:?set PC_MAC}" "${PC_HOST:?set PC_HOST}"
PORT="${MIND_PORT:-8081}"
health() { curl -fsS -m 3 "http://$PC_HOST:$PORT/health" >/dev/null 2>&1; }
wake() { if [ -n "${PC_BCAST:-}" ]; then wakeonlan -i "$PC_BCAST" "$PC_MAC" >/dev/null; else wakeonlan "$PC_MAC" >/dev/null; fi; }
start=$(date +%s)
if health; then echo "awake 0s"; exit 0; fi
wake
for i in $(seq 1 60); do        # up to three minutes
  sleep 3
  if health; then echo "awake $(( $(date +%s) - start ))s"; exit 0; fi
  if (( i % 10 == 0 )); then wake; fi
done
echo "no answer after $(( $(date +%s) - start ))s" >&2
exit 1
