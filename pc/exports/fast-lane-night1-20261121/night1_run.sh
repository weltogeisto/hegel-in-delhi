#!/bin/bash
# WSL: one run, then its health row, then its files into the branch folder.  night1_run.sh NAME DAY ARM SEED BLOCK MAXSECS DEST
# Runs side by side (every slot, DECISIONS 62): each writes only its own folder; runs.jsonl is assembled by the driver from row.json files.
N=$1; D=$2; A=$3; S=$4; BL=$5; MAX=$6; DEST=$7; B=/home/ai/night1
DATE=$(python3 -c "print({50:'2026-11-20',51:'2026-11-21',52:'2026-11-22'}[$D])")
R=runs; [ "$NIGHT1_DRY" = 1 ] && R=runs-dry
cd $B || exit 9
mkdir -p logs
timeout --signal=TERM --kill-after=30 ${MAX}s python3 night1_run.py $N $D $A $S $BL > logs/$N.log 2>&1 &
P=$!
while kill -0 $P 2>/dev/null; do
  echo "$(date +%T) $(curl -s -m 5 http://127.0.0.1:8082/slots | python3 -c 'import sys,json; s=json.load(sys.stdin); print("busy", sum(1 for x in s if x.get("is_processing")), "of", len(s))' 2>/dev/null || echo 'no answer')" >> logs/$N.slots.txt
  sleep 15
done
wait $P; rc=$?
O=$R/$N
if [ -f $O/RUN.json ]; then
  (cd engine && python3 -m world report --health --docs ../$O $DATE) > $O/health.txt 2>&1
  grep -q '^| *[0-9]' $O/health.txt || { echo "(below the floor of 20 thoughts; the row with --floor 1:)" >> $O/health.txt; (cd engine && python3 -m world report --health --floor 1 --docs ../$O $DATE) >> $O/health.txt 2>&1; }
  (cd engine && python3 -m world report --health --json --floor 1 --docs ../$O $DATE) > $O/health.json 2>&1
fi
if [ -n "$DEST" ]; then
  T=$DEST/runs/$N; mkdir -p $T
  cp logs/$N.slots.txt $T/slots.txt 2>/dev/null; cp logs/$N.log $T/run.log 2>/dev/null
  if [ -f $O/RUN.json ]; then
    cp $O/days/$DATE.json $O/RUN.json $O/health.txt $O/health.json $T/
    python3 night1_row.py $O logs/$N.slots.txt > $T/row.json
  else
    echo "{\"name\": \"$N\", \"block\": \"$BL\", \"morning_day\": $D, \"arm\": \"$A\", \"seed\": $S, \"rc\": $rc, \"killed_or_failed\": true, \"end\": \"$(date +%FT%T%z)\"}" > $T/row.json
  fi
fi
echo "run $N rc=$rc: $(tail -1 logs/$N.log | cut -c1-160)"
exit $rc
