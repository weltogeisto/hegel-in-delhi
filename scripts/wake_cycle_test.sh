#!/usr/bin/env bash
# Wakes the PC N times, asks the mind one tiny question, then waits for the PC to sleep again.
# Usage: bash scripts/wake_cycle_test.sh 10
set -uo pipefail
N="${1:-10}"
source "${HEGEL_ENV:-$HOME/.config/hegel/env}"
PORT="${MIND_PORT:-8081}"
IDLE="${WATCHDOG_IDLE_MIN:-3}"
here="$(cd "$(dirname "$0")" && pwd)"
ask='{"messages":[{"role":"user","content":"Reply with one word: Namaste."}],"max_tokens":8,"chat_template_kwargs":{"enable_thinking":false}}'
printf "cycle\twake_s\tanswer_s\tasleep_after_s\n"
for i in $(seq 1 "$N"); do
  t0=$(date +%s)
  if ! "$here/wake_pc.sh" >/dev/null; then printf "%s\tFAIL\t-\t-\n" "$i"; continue; fi
  t1=$(date +%s)
  if ! curl -fsS -m 180 "http://$PC_HOST:$PORT/v1/chat/completions" -H 'Content-Type: application/json' -d "$ask" >/dev/null; then
    printf "%s\t%s\tFAIL\t-\n" "$i" "$((t1 - t0))"; continue
  fi
  t2=$(date +%s)
  asleep="-"
  limit=$(( (IDLE + 6) * 60 ))
  while (( $(date +%s) - t2 < limit )); do
    sleep 30
    if ! curl -fsS -m 3 "http://$PC_HOST:$PORT/health" >/dev/null 2>&1; then asleep=$(( $(date +%s) - t2 )); break; fi
  done
  printf "%s\t%s\t%s\t%s\n" "$i" "$((t1 - t0))" "$((t2 - t1))" "$asleep"
  sleep 20
done
