#!/bin/bash
# Gather W5's results into DEST: the fork days, fork_diff per seed pair, the health rows, world_health's rows, the cards,
# the logs and the scripts. Facts only: Claude reads the cards' moments and writes the result. Usage: export_w5.sh DEST
D=2026-11-18
DEST=$1
SP=/mnt/c/Users/hendr/AppData/Local/Temp/claude/b52770502021644c/ae932ed3-101c-49e5-8ebb-b1be766eff5b/scratchpad
rm -rf "$DEST"; mkdir -p "$DEST/days" "$DEST/logs" "$DEST/scripts" "$DEST/world-health"
cd ~/w5/main || exit 1
FORKS=$(cd ~/w5/out && ls -d S?-* 2>/dev/null | sort -t- -k2,2 -k1,1)
for f in $FORKS; do [ -f ~/w5/out/$f/days/$D.json ] && cp ~/w5/out/$f/days/$D.json "$DEST/days/$f.json"; done
cp ~/w5/shadow-docs/days/$D.json "$DEST/days/shadow-D.json" 2>/dev/null
cp ~/w5/logs/* "$DEST/logs/" 2>/dev/null
cp "$SP/run_w5.sh" "$SP/export_w5.sh" "$SP/w5_night.sh" "$SP/w5_cards.py" "$DEST/scripts/"

{
  echo "# fork_diff, S0 against S1 of each seed (tools/fork_diff.py): where the two days part"
  for seed in 1831 2718 3141 4253 5167; do
    [ -d ~/w5/out/S0-$seed ] && [ -d ~/w5/out/S1-$seed ] || continue
    echo; echo "## seed $seed: S0 / S1"
    python3 tools/fork_diff.py ~/w5/out/S0-$seed ~/w5/out/S1-$seed 2>&1 | grep -E "^$D|first difference|^  [AB]:|^identical" || true
  done
} > "$DEST/fork-diff.txt"

{
  echo "# python3 -m world report --health --docs <fork> $D"
  for f in $FORKS; do echo; echo "## $f"; python3 -m world report --health --docs ~/w5/out/$f $D 2>&1 | head -6; done
} > "$DEST/health-rows.md"

for f in $FORKS; do
  python3 tools/world_health.py --days ~/w5/out/$f/days --json "$DEST/world-health/$f.json" > "$DEST/world-health/$f.txt" 2>&1
done

{ echo "# street cards drawn (the street: kinds of each step's opened), empty moments, cards spent"
  for f in $FORKS; do [ -f "$DEST/days/$f.json" ] && python3 "$SP/w5_cards.py" "$DEST/days/$f.json"; done
} > "$DEST/cards.txt"
echo "exported to $DEST: $(ls "$DEST/days" | wc -l) day files"
