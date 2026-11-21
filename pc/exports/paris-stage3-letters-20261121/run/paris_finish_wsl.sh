#!/bin/bash
set -e
WSP=/mnt/c/Users/hendr/AppData/Local/Temp/claude/cd74254ce8d0a965/90b4347d-b5da-4fc9-99db-4ff38302b710/scratchpad
D=$WSP/paris-branch/pc/exports/paris-stage3-letters-20261121/run
[ -e "$WSP/paris-branch/.git" ] || { echo "no branch worktree"; exit 1; }
rm -rf "$D" && mkdir -p "$D"
cp /home/ai/paris3/REPLIES.jsonl "$D/"
cp -r /home/ai/paris3/job/. "$D/"
cp /home/ai/paris3/run.out /home/ai/paris3/run.err "$WSP/paris_wsl.sh" "$WSP/paris_finish_wsl.sh" "$D/"
ls "$D"; du -sh "$D"; sha256sum "$D/REPLIES.jsonl"
