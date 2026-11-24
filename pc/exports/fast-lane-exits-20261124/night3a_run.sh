#!/bin/bash
# WSL: one future of one arm, under a hard backstop, slots sampled every 30 s.  NIGHT2_BASE=<arm base> night3a_run.sh SEED MAXSECS
S=$1; MAX=$2; B=${NIGHT2_BASE:?}
cd $B || exit 9
mkdir -p logs
timeout --signal=TERM --kill-after=30 ${MAX}s python3 $B/night3a_run.py $S > logs/$S.log 2>&1 &
P=$!
echo $P > logs/$S.pid
while kill -0 $P 2>/dev/null; do
  echo "$(date +%T) $(curl -s -m 5 http://127.0.0.1:8082/slots | python3 -c 'import sys,json; s=json.load(sys.stdin); print("busy", sum(1 for x in s if x.get("is_processing")), "of", len(s))' 2>/dev/null || echo 'no answer')" >> logs/$S.slots.txt
  sleep 30
done
wait $P; rc=$?
echo "future $B $S rc=$rc: $(tail -1 logs/$S.log | cut -c1-200)"
exit $rc
