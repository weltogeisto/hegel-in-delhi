#!/bin/bash
# W2 · the band of noise. D = 2026-11-16 (Day 46, the latest complete shadow day). Four one-day forks of one saved morning.
cd ~/w2/main
URL=http://127.0.0.1:8082
SETS='--set HEGEL_DECISION_DRAWS=4 --set HEGEL_CORRESPONDENT=1'
mkdir -p ~/w2/logs ~/w2/out
curl -s -m 10 $URL/props > ~/w2/logs/server-props.json
nvidia-smi --query-gpu=name,memory.used,memory.total --format=csv > ~/w2/logs/gpu-before.txt
run() {  # name, extra args
  name=$1; shift
  echo "[$(date -u +%FT%TZ)] START $name $*" | tee -a ~/w2/logs/progress.log
  rm -rf ~/w2/out/$name
  /usr/bin/time -v python3 -m world simulate --docs ~/w2/shadow-docs --date 2026-11-16 --days 1 --mind $URL $SETS "$@" --out ~/w2/out/$name > ~/w2/logs/$name.log 2> ~/w2/logs/$name.err
  rc=$?
  echo "[$(date -u +%FT%TZ)] END   $name rc=$rc" | tee -a ~/w2/logs/progress.log
  return $rc
}
run s1a --seed 1 && run s1b --seed 1 && run s2 --seed 2 && run s0
echo "[$(date -u +%FT%TZ)] ALL DONE" | tee -a ~/w2/logs/progress.log
nvidia-smi --query-gpu=name,memory.used,memory.total --format=csv > ~/w2/logs/gpu-after.txt
