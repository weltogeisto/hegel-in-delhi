#!/bin/bash
# W9, the voices' repairs, Part 2 (pc/VOICE-REPAIRS-CHECK.md), on the plain live server, spare slot 1, cache off (the tool's own payload).
# The freeze of codex/voice-repairs-check-20261120 fbedd93 (manifest daffde05...b0a5, 29 moments, 174 calls); the cloud's order of
# 20 Nov 23:45 accepts the two departures (set A replies only; R02 kept). Records pushed unread to the same branch.
SP=/c/Users/hendr/AppData/Local/Temp/claude/cd74254ce8d0a965/90b4347d-b5da-4fc9-99db-4ff38302b710/scratchpad
WSP=/mnt/c/Users/hendr/AppData/Local/Temp/claude/cd74254ce8d0a965/90b4347d-b5da-4fc9-99db-4ff38302b710/scratchpad
WSPW='C:/Users/hendr/AppData/Local/Temp/claude/cd74254ce8d0a965/90b4347d-b5da-4fc9-99db-4ff38302b710/scratchpad'
export MSYS_NO_PATHCONV=1
REPO=/c/AI/projects/hegel-in-delhi
BRANCH=codex/voice-repairs-check-20261120
DEST=pc/exports/voice-repairs-check-20261120/run
LOG=$SP/w9-night.log
log() { echo "[$(date +%FT%T)] $*" | tee -a "$LOG"; }
log "W9 start"
wsl.exe -- bash /home/ai/fork59/fork59_server.sh argvcheck >> "$LOG" 2>&1 || { log "the live server is not the plain one as pinned; W9 not run"; exit 1; }
[ "$(wsl.exe -- bash -c 'sha256sum /home/ai/w9/main/pc/exports/voice-repairs-check-20261120/MANIFEST.json' | cut -c1-64)" = "daffde0570f0b61952dff7d660d2e28aa1646923d3c12047212ad36ff7d3b0a5" ] || { log "manifest differs"; exit 1; }
wsl.exe -- bash -c "cd /home/ai/w9 && python3 main/tools/voice_repairs_check.py run --tools /home/ai/w9/main --dir /home/ai/w9/main/pc/exports/voice-repairs-check-20261120 --server http://127.0.0.1:8082 --job /home/ai/w9/job > /home/ai/w9/run.out 2> /home/ai/w9/run.err; echo rc=\$?; tail -1 /home/ai/w9/run.out; tail -3 /home/ai/w9/run.err" >> "$LOG" 2>&1
grep -q '"records": 174' "$LOG" || { log "W9 run did not finish with 174 records (see log)"; exit 2; }
cd "$REPO" && git fetch -q github $BRANCH && rm -rf "$SP/w9-branch" && git worktree prune && git worktree add -q -B $BRANCH "$WSPW/w9-branch" FETCH_HEAD || { log "worktree failed"; exit 3; }
wsl.exe -- bash -c "set -e; D=$WSP/w9-branch/$DEST; mkdir -p \$D; cp -r /home/ai/w9/job/. \$D/; cp /home/ai/w9/run.out /home/ai/w9/run.err \$D/; cp $WSP/w9_night.sh \$D/; du -sh \$D" >> "$LOG" 2>&1
cd "$SP/w9-branch" && git add $DEST && git commit -q -m "W9: the voices' repairs, Part 2, the calls (records and receipts), unread

On the plain live server, spare slot 1, prompt cache off, after the fork; freeze fbedd93 (manifest daffde05...b0a5).
Departures accepted by the cloud's order of 20 Nov 23:45: set A replies only (greetings out); R02 kept.
Evaluation only, never training data.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" && git push -q github $BRANCH 2>>"$LOG" && log "pushed $BRANCH $(git rev-parse --short HEAD)" || { log "push failed"; exit 4; }
log "W9 finished"
