#!/bin/bash
# The day's spare-slot jobs after W3: Paris stage 2 (96), then M1's third coder (325), each through tools/run_requests.py on the
# plain live server, slot 1, behind the natural-step latency guard (the observer's file, limit 17.0 s). A run the guard stops is
# resumed after 60 s; no new call after 20:45. An unknown request (began, no saved end) stops everything for a human.
WSP=/mnt/c/Users/hendr/AppData/Local/Temp/claude/b52770502021644c/ae932ed3-101c-49e5-8ebb-b1be766eff5b/scratchpad
OBS=$WSP/w3-observation.json
cd ~/jobs/main || exit 1
log() { echo "[$(date +%F' '%T)] $*" | tee -a ~/jobs/day.log; }
job() {   # name requests
  local name=$1 req=$2
  log "START $name ($(wc -l < $req) requests)"
  while true; do
    H=$((10#$(date +%H%M))); [ $H -ge 2045 ] && { log "CUTOFF 20:45: $name not complete"; return 1; }
    [ -f $WSP/STOP ] && { log "STOP file: $name"; return 1; }
    env -i HOME=$HOME PATH=/usr/bin:/bin HEGEL_ENV=/dev/null python3 tools/run_requests.py --requests $req --server http://127.0.0.1:8082 \
      --job ~/jobs/$name --out ~/jobs/$name-REPLIES.jsonl --latency-observation $OBS --latency-limit 17.0 > ~/jobs/$name-last.json 2> ~/jobs/$name-last.err
    rc=$?
    if grep -q '"complete": true' ~/jobs/$name-last.json; then log "DONE $name: $(python3 -c "import json;l=json.load(open('$HOME/jobs/$name/LEDGER.json'));print({k:l[k] for k in ('requests','replied','failed','complete','replies_sha256')})")"; return 0; fi
    if grep -q UnknownRequest ~/jobs/$name-last.err; then log "UNKNOWN request in $name: stop for a human"; tail -3 ~/jobs/$name-last.err | tee -a ~/jobs/day.log; return 2; fi
    held=$(python3 -c "import json;l=json.load(open('$HOME/jobs/$name-last.json'));print('yes' if l.get('stopped') and not l.get('failed') else 'no')" 2>/dev/null)
    if [ "$held" != "yes" ]; then log "$name failed rc=$rc: $(tail -c 300 ~/jobs/$name-last.json | tr '\n' ' ') $(tail -1 ~/jobs/$name-last.err)"; return 3; fi
    s=$(python3 -c "import json;l=json.load(open('$HOME/jobs/$name-last.json'));print(l['replied'],'/',l['requests'],'|',l['stopped'],'| failed',len(l['failed']))" 2>/dev/null)
    log "$name held: $s"; sleep 60
  done
}
job paris-stage2 ~/jobs/main/pc/exports/paris-stage2-20261118/REQUESTS.jsonl && job m1-coder ~/jobs/m1-coder-REQUESTS.jsonl
log "DAY JOBS END rc=$?"
