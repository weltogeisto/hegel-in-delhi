#!/bin/bash
# Gather W2's results into one folder: day files, the diffs, the health rows, the traces and the scripts. Usage: export.sh DEST
set -e
D=$1
cd ~/w2
mkdir -p "$D/days" "$D/traces" "$D/scripts"
FORKS="s1a s1b s1c s1d s1e n1 n2 s2 s0"
for f in $FORKS; do [ -f out/$f/days/2026-11-16.json ] && cp out/$f/days/2026-11-16.json "$D/days/$f.json"; done
cp logs/trace-?.jsonl logs/trace-d-payload3.json "$D/traces/" 2>/dev/null || true
cp logs/server-props.json "$D/server-props.json"
cp run_w2.sh analyze.py where_parts.py trace_calls.py replay.py flush.py run_nocache.py export.sh "$D/scripts/"

cd ~/w2/main
{
  echo "# fork_diff, pair by pair (tools/fork_diff.py; it compares each day's state and each step's decision, not the stopwatch)"
  for p in "s1a s1b" "s1a s1c" "s1b s1c" "s1d s1e" "s1d s1a" "n1 n2" "s1a s2" "s1a s0" "s2 s0"; do
    set -- $p
    [ -d ~/w2/out/$1 ] && [ -d ~/w2/out/$2 ] || continue
    echo; echo "## $1 / $2"
    python3 tools/fork_diff.py ~/w2/out/$1 ~/w2/out/$2 2>&1 | grep -E "^2026-11-16|first difference|^  [AB]:|^identical" || true
  done
} > "$D/fork-diff.txt"

{
  echo "# where two forks first differ in any field of a step (scripts/where_parts.py), same-seed pairs"
  for p in "s1a s1b" "s1a s1c" "s1d s1e" "n1 n2"; do
    set -- $p
    [ -d ~/w2/out/$1 ] && [ -d ~/w2/out/$2 ] || continue
    echo; python3 ~/w2/where_parts.py $1 $2
  done
} > "$D/where-parts.txt"

{
  echo "# python3 -m world report --health --docs <fork> 2026-11-16"
  for f in $FORKS; do
    [ -d ~/w2/out/$f ] || continue
    echo; echo "## $f"; python3 -m world report --health --docs ~/w2/out/$f 2026-11-16 2>&1 | head -4
  done
} > "$D/health-rows.md"

python3 ~/w2/analyze.py > "$D/tables.md"
echo "exported to $D"
