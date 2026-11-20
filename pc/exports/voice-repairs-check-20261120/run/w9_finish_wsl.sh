#!/bin/bash
# W9, after the calls: the job folder (records, receipts, plan) into the branch worktree, unread.
set -e
WSP=/mnt/c/Users/hendr/AppData/Local/Temp/claude/cd74254ce8d0a965/90b4347d-b5da-4fc9-99db-4ff38302b710/scratchpad
D=$WSP/w9-branch/pc/exports/voice-repairs-check-20261120/run
[ -e "$WSP/w9-branch/.git" ] || { echo "no branch worktree"; exit 1; }
rm -rf "$D" && mkdir -p "$D"
cp -r /home/ai/w9/job/. "$D/"
cp /home/ai/w9/run.out /home/ai/w9/run.err "$D/"
cp "$WSP/w9_night.sh" "$WSP/w9_finish_wsl.sh" "$D/"
ls "$D"; ls "$D/records" | wc -l; du -sh "$D"
