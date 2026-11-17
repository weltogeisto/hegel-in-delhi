#!/bin/bash
# W5's same-seed check (pc/STREET-FORKS.md): seed 1831, HEGEL_STREET=0, a second time with exactly the first run's command,
# then fork_diff against S0-1831. Same code (main bbcb4c9), same docs (~/w5/shadow-docs), same switches as run_w5.sh.
cd ~/w5/main || exit 1
D=2026-11-18
URL=http://127.0.0.1:8082
SETS="--set HEGEL_DECISION_DRAWS=4 --set HEGEL_CORRESPONDENT=1 --set HEGEL_SOUL_FILE=mind/soul-ordinary.md"
log() { echo "[$(date +%FT%T%z)] $*" | tee -a ~/w5/logs/progress.log; }
name=CHECK-S0-1831
log "START $name"
rm -rf ~/w5/out/$name
env -i HOME=$HOME PATH=/usr/bin:/bin HEGEL_ENV=/dev/null /usr/bin/time -v python3 -m world simulate --docs "$HOME/w5/shadow-docs" --date $D --days 1 \
  --mind $URL --seed 1831 $SETS --set HEGEL_STREET=0 --out ~/w5/out/$name > ~/w5/logs/$name.log 2> ~/w5/logs/$name.err
log "END   $name rc=$? $(grep -m1 '^day 48' ~/w5/logs/$name.log)"
python3 tools/fork_diff.py ~/w5/out/S0-1831 ~/w5/out/$name > ~/w5/logs/check-fork-diff-full.txt 2>&1
{
  echo "# the same-seed check: seed 1831, HEGEL_STREET=0, twice (S0-1831 and $name), tools/fork_diff.py"
  grep -E "^$D|first difference|^  [AB]:|^identical" ~/w5/logs/check-fork-diff-full.txt || cat ~/w5/logs/check-fork-diff-full.txt
} > ~/w5/logs/check-fork-diff.txt
cat ~/w5/logs/check-fork-diff.txt
