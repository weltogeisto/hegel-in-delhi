#!/bin/bash
# Natural-step latency observer for the spare-slot jobs (DECISIONS 30). Read-only on the Pi: every 30 s it reads the latest day file and
# writes $SP/w3-observation.json = {observed_unix, latency_s, limit_s, ...} for tools/recorded_llama.LatencyGuard. latency_s is the
# mind latency of his most recent natural step; limit_s is frozen (LIMIT, below). Stops when $SP/STOP exists or after 21:15.
SP=/c/Users/hendr/AppData/Local/Temp/claude/b52770502021644c/ae932ed3-101c-49e5-8ebb-b1be766eff5b/scratchpad
export MSYS_NO_PATHCONV=1
SPW=$(cygpath -m "$SP")
LIMIT=${LIMIT:-17.0}      # Day 49's p90 of his step latency (median 10.2, max 29.1); not changed during the run
PI="ssh -o BatchMode=yes -o ConnectTimeout=15 -o IdentitiesOnly=yes -i $HOME/.ssh/gondolin_key faqts@Gondolin.local"
REMOTE='cd hegel-in-delhi && python3 -c "
import json,glob
fs=sorted(glob.glob(\"docs/days/2026-11-*.json\"))
d=json.load(open(fs[-1])); st=d[\"steps\"]
prev=json.load(open(fs[-2])) if not st else None
src=st if st else prev[\"steps\"]
last=[s for s in src if isinstance(s.get(\"mind\"),dict) and \"latency_s\" in s[\"mind\"] and s[\"mind\"].get(\"source\")==\"mind\"]
l=last[-1] if last else None
print(json.dumps({\"day\":d[\"n\"],\"date\":fs[-1][-15:-5],\"day_steps\":len(st),\"latency_s\":l[\"mind\"][\"latency_s\"] if l else None,\"step_t\":l[\"t\"] if l else None,\"source\":(l[\"mind\"].get(\"source\") if l else None),\"last_source\":(st[-1][\"mind\"].get(\"source\") if st and isinstance(st[-1].get(\"mind\"),dict) else None)}))
"'
log() { echo "[$(date +%FT%T)] $*" >> "$SP/w3-observe.log"; }
log "observer start, limit_s=$LIMIT"
while [ ! -f "$SP/STOP" ]; do
  H=$((10#$(date +%H%M))); [ $H -ge 2115 ] && [ $H -lt 2359 ] && { log "21:15 reached, observer stops"; break; }
  OUT=$($PI "$REMOTE" 2>/dev/null)
  if [ -n "$OUT" ]; then
    echo "$OUT" | python -c "
import sys,json,time,os
o=json.loads(sys.stdin.read());
if o.get('latency_s') is None: sys.exit(1)
o.update(observed_unix=time.time(), limit_s=float('$LIMIT'))
p=r'$SPW/w3-observation.json'; open(p+'.tmp','w').write(json.dumps(o)); os.replace(p+'.tmp',p)
" || log "no usable step in reply: $OUT"
  else
    log "ssh read failed"
  fi
  sleep 30
done
log "observer end"
