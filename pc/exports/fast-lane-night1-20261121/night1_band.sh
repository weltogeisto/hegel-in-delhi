#!/bin/bash
# WSL: the noise band's fork_diff (band-r1 against band-r2) into DEST/band.  night1_band.sh DEST
B=/home/ai/night1; DEST=$1
cd $B || exit 9
mkdir -p $DEST/band
python3 engine/tools/fork_diff.py runs/band-r1 runs/band-r2 > $DEST/band/fork_diff.txt; echo "fork_diff exit $?" >> $DEST/band/fork_diff.txt
python3 engine/tools/fork_diff.py runs/band-r1 runs/band-r2 --json > $DEST/band/fork_diff.json
grep -v 'fork_diff exit' $DEST/band/fork_diff.txt | sed -n '/^identical/,$p;/^first difference/,$p' | awk '!seen[$0]++'
