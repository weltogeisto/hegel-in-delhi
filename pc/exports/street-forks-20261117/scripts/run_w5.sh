#!/bin/bash
# W5, the street's night of forks (pc/STREET-FORKS.md): D = 2026-11-18, Day 48, the first complete shadow day on
# mind/soul-ordinary.md. Ten one-day forks of its morning, seed by seed: S0 (HEGEL_STREET=0) then S1 (HEGEL_STREET=1).
# --seed turns the prompt cache off by itself. No fork starts after CUTOFF (the PC's power guard shuts it down at 23:15).
cd ~/w5/main || exit 1
D=2026-11-18
URL=${MIND:-http://127.0.0.1:8082}           # MIND=stub only for a dry run of this script
DOCS=${DOCS:-$HOME/w5/shadow-docs}
CUTOFF=${CUTOFF:-2240}
SETS="--set HEGEL_DECISION_DRAWS=4 --set HEGEL_CORRESPONDENT=1 --set HEGEL_SOUL_FILE=mind/soul-ordinary.md"
log() { echo "[$(date +%FT%T%z)] $*" | tee -a ~/w5/logs/progress.log; }
curl -s -m 10 $URL/props > ~/w5/logs/server-props.json
nvidia-smi --query-gpu=name,memory.used,memory.total --format=csv > ~/w5/logs/gpu-before.txt 2>&1
log "BEGIN docs=$DOCS sets=$SETS cutoff=$CUTOFF"
for seed in 1831 2718 3141 4253 5167; do
  for arm in 0 1; do
    name=S$arm-$seed
    if [ "$(date +%H%M)" -ge "$CUTOFF" ]; then log "CUTOFF: $name not started"; break 2; fi
    log "START $name"
    rm -rf ~/w5/out/$name
    env -i HOME=$HOME PATH=/usr/bin:/bin HEGEL_ENV=/dev/null /usr/bin/time -v python3 -m world simulate --docs "$DOCS" --date $D --days 1 \
      --mind $URL --seed $seed $SETS --set HEGEL_STREET=$arm --out ~/w5/out/$name > ~/w5/logs/$name.log 2> ~/w5/logs/$name.err
    log "END   $name rc=$? $(grep -m1 '^day 48' ~/w5/logs/$name.log)"
  done
done
log "ALL DONE"
nvidia-smi --query-gpu=name,memory.used,memory.total --format=csv > ~/w5/logs/gpu-after.txt 2>&1
