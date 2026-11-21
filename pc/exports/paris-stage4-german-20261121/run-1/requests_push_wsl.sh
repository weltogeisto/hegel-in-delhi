#!/bin/bash
# Copy a requests job (replies, LEDGER, PLAN, receipts) into a branch worktree folder. Args: TAG WORKTREE_NAME DEST(in repo) OUTNAME
set -e
TAG=$1; WT=$2; DEST=$3; OUT=$4
WSP=/mnt/c/Users/hendr/AppData/Local/Temp/claude/cd74254ce8d0a965/90b4347d-b5da-4fc9-99db-4ff38302b710/scratchpad
R=/home/ai/requests-$TAG
D=$WSP/$WT/$DEST
[ -e "$WSP/$WT/.git" ] || { echo "no branch worktree"; exit 1; }
rm -rf "$D" && mkdir -p "$D"
cp $R/$OUT "$D/"
cp -r $R/job/. "$D/"
cp $R/run.out $R/run.err "$WSP/requests_wsl.sh" "$WSP/requests_push_wsl.sh" "$D/"
ls "$D"; du -sh "$D"; sha256sum "$D/$OUT"
