#!/bin/bash
# Start the IA2 swap right after Hegel's next decision is committed (so his new step runs while we test). Window: no new call after
# +35 min, a running call cut at +45, the live server not stopped if still busy at +20.
SP=/c/Users/hendr/AppData/Local/Temp/claude/cd74254ce8d0a965/206bd0ad-34b9-4f26-88b8-6e818bc0ce46/scratchpad
PI="/c/Windows/System32/OpenSSH/ssh.exe -o BatchMode=yes -o ConnectTimeout=15 -i C:/Users/hendr/.ssh/gondolin_key faqts@gondolin"
OLD=$($PI 'cd hegel-in-delhi && git log --format=%h -1' | tr -d '\r')
echo "[$(date +%FT%T)] waiting for Hegel's next decision after $OLD" >> $SP/inkling2.log
for i in $(seq 1 60); do
  NEW=$($PI 'cd hegel-in-delhi && git log --format="%h %s" -1' | tr -d '\r')
  [ "${NEW%% *}" != "$OLD" ] && break; sleep 20
done
echo "[$(date +%FT%T)] his step: $NEW" >> $SP/inkling2.log
sleep 20
DEADLINE=$(date -d '+35 min' +%H:%M) HARD=$((10#$(date -d '+45 min' +%H%M))) LATEST_START=$((10#$(date -d '+20 min' +%H%M))) bash $SP/inkling_swap2.sh > $SP/inkling2.out 2>&1
echo "[$(date +%FT%T)] IA2 swap ended rc=$?" >> $SP/inkling2.log
