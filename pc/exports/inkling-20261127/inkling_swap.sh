#!/bin/bash
# W22, the Inkling bake-off's night part (pc/INKLING-BAKEOFF.md, steps 3 to 6), run after night 4 has stopped:
# stop the live Qwen on 8082, start Inkling 2 Mini (llama.cpp b12816, -np 2, alias inkling, 127.0.0.1 only) on 8082, check one short
# call, run REQUESTS-inkling-A on slot 0 and -D on slot 1 (--night, --timeout 900) until done or the window ends (no new call after
# DEADLINE; a call still running at HARD is cut), stop Inkling, start Qwen again through the Windows starter (its exact pinned
# command), check the pin, /health and the model's sha256, push to codex/inkling-20261127. The DONE text is written, not posted.
# Whatever fails after the live server was stopped, Qwen is started again (trap).
export MSYS_NO_PATHCONV=1
SP=/c/Users/hendr/AppData/Local/Temp/claude/cd74254ce8d0a965/206bd0ad-34b9-4f26-88b8-6e818bc0ce46/scratchpad
WSP=/mnt/c/Users/hendr/AppData/Local/Temp/claude/cd74254ce8d0a965/206bd0ad-34b9-4f26-88b8-6e818bc0ce46/scratchpad
SPW='C:/Users/hendr/AppData/Local/Temp/claude/cd74254ce8d0a965/206bd0ad-34b9-4f26-88b8-6e818bc0ce46/scratchpad'
REPO=/c/AI/projects/hegel-in-delhi; BRANCH=codex/inkling-20261127; DEST=pc/exports/inkling-20261127
BR=$SP/inkling-branch; WBR=$WSP/inkling-branch; LOG=$SP/inkling.log; POSTF=$SP/inkling-DONE.md
DEADLINE=${DEADLINE:-08:15}; HARD=${HARD:-825}; LATEST_START=${LATEST_START:-805}
H=/home/ai/inkling-20261127; QWEN_SHA=322e194ff79741c7baa497c240f677f54b201b0efab44ca8e50f122b39123482
R() { wsl.exe -d Ubuntu-24.04 -u root -- "$@" < /dev/null; }
A() { wsl.exe -d Ubuntu-24.04 -u ai -- "$@" < /dev/null; }
SRV="$WSP/inkling_srv.sh"
log() { echo "[$(date +%FT%T)] $*" | tee -a "$LOG"; }
hhmm() { echo $((10#$(date +%H%M))); }
health() { curl -s -m 10 -o /dev/null -w '%{http_code}' http://127.0.0.1:8082/health; }
note() { printf '%s\n' "$1" > "$POSTF"; log "NOTE: $1"; }
STOPPED=no; RESTORED=no
restore() {
  [ $STOPPED = yes ] && [ $RESTORED = no ] || return 0
  RESTORED=trying
  R bash $SRV stop-inkling >> "$LOG" 2>&1
  for t in 1 2; do
    log "restore: the Windows starter (try $t)"
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File 'C:\hegel\scripts\Start-HegelQwen8082.ps1' >> "$LOG" 2>&1
    for i in $(seq 1 40); do [ "$(health)" = 200 ] && break; sleep 5; done
    if [ "$(health)" = 200 ] && R bash $SRV argvcheck >> "$LOG" 2>&1; then RESTORED=yes; log "restore: Qwen answers on 8082, the pinned argv"; return 0; fi
  done
  RESTORED=FAILED; log "restore FAILED: 8082 is not the pinned Qwen"; }
trap restore EXIT

log "swap armed (pid $$), window: no new call after $DEADLINE, cut at $HARD"
[ "$(hhmm)" -ge $LATEST_START ] && [ "$(hhmm)" -lt 1200 ] && { note "**W22 not run this morning (PC seat, $(date +%H:%M) Berlin):** night 4 ended too late for the window; nothing touched. It runs the next night."; exit 0; }
[ -e "$SP/inkling-cpucheck-ok" ] || { note "**W22 not run (PC seat, $(date +%H:%M) Berlin):** the CPU check of the new build and file did not pass before the night; nothing touched."; exit 0; }
A pgrep -f night4_run.py >/dev/null && { note "**W22 not run (PC seat, $(date +%H:%M) Berlin):** night 4's futures were still running; nothing touched."; exit 0; }
R bash $SRV argvcheck >> "$LOG" 2>&1 || { note "**W22 not run (PC seat, $(date +%H:%M) Berlin):** 8082 is not the pinned Qwen before the swap; nothing touched."; exit 0; }
# the runner's checkout (main, which holds tools/ and the request files), and the branch
A bash -c "mkdir -p $H/engine && [ -e $H/engine/tools/run_requests.py ] || tar -xf $WSP/night4-engine.tar -C $H/engine" || { note "**W22 not run:** could not unpack main for the runner; nothing touched."; exit 0; }
if [ ! -d "$BR" ]; then (cd "$REPO" && git fetch -q github main && git worktree add -q -b $BRANCH "$(cygpath -m "$BR")" github/main) || { note "**W22 not run:** the branch worktree failed; nothing touched."; exit 0; }; fi
mkdir -p "$BR/$DEST"
T0=$(date +%H:%M)

# 3. stop the live server; 4. Inkling on 8082
R bash $SRV stop-live $LATEST_START >> "$LOG" 2>&1 || { note "**W22 not run (PC seat, $(date +%H:%M) Berlin):** the live server did not stop (busy or not the pinned one); untouched."; exit 0; }
STOPPED=yes; log "live stopped"
CTX=""; for c in 32768 24576 16384; do R bash $SRV start-inkling $c >> "$LOG" 2>&1 && { CTX=$c; break; }; done
[ -n "$CTX" ] || { note "**BLOCKED, W22 (PC seat, $(date +%H:%M) Berlin):** Inkling did not start on 8082 with b12816 (contexts 32768, 24576, 16384); Qwen restored. Log: \`inkling.log\`."; exit 1; }
MODEL=qwen
P=$(R bash $SRV probe qwen none 24); log "probe qwen/none: $P"
case "$P" in 200*finish*) ;; *) P=$(R bash $SRV probe inkling none 24); log "probe inkling/none: $P"; case "$P" in 200*finish*) MODEL=inkling;; *) note "**BLOCKED, W22 (PC seat, $(date +%H:%M) Berlin):** Inkling on 8082 does not answer a short call: \`$P\`; Qwen restored."; exit 1;; esac;; esac
P2=$(R bash $SRV probe $MODEL medium 200); log "probe $MODEL/medium: $P2"
case "$P2" in 200*) ;; *) note "**BLOCKED, W22 (PC seat, $(date +%H:%M) Berlin):** the template refuses reasoning_effort \"medium\": \`$P2\`; Qwen restored."; exit 1;; esac
R bash $SRV server-json $WBR/$DEST/SERVER-inkling.json >> "$LOG" 2>&1

# 5. the two files, one a slot
rm -f "$SP/inkling-runs-done.txt"; touch "$SP/inkling-runs-done.txt"
for s in A:0 D:1; do f=${s%:*}; slot=${s#*:}
  ( A python3 $WSP/inkling_run.py $H/engine $H/engine/$DEST/REQUESTS-inkling-$f.jsonl $H/job-$f $H/replies-$f.jsonl $slot $DEADLINE $MODEL > "$SP/inkling-run-$f.log" 2>&1; echo "$f rc=$?" >> "$SP/inkling-runs-done.txt" ) &
done
log "runs started (model name in the payload: $MODEL, ctx $CTX)"
CUT=no
while [ $(grep -c rc= "$SP/inkling-runs-done.txt") -lt 2 ]; do
  sleep 30
  n=$(A bash -c "ls $H/job-A/receipts/*.done.json $H/job-D/receipts/*.done.json 2>/dev/null | wc -l"); log "progress: $n of 88 calls done"
  if [ $(hhmm) -ge $HARD ] && [ $CUT = no ]; then CUT=yes; log "cut at $HARD: the runners are stopped"; A pkill -TERM -f inkling_run.py; sleep 10; fi
done
log "runs ended: $(tr '\n' ' ' < "$SP/inkling-runs-done.txt")"

# 6. Qwen back, with the exact saved command
restore
QS=$(R sha256sum /mnt/c/AI/models/Qwen3.8-27B/Qwen3.8-27B-UD-Q4_K_M.gguf | cut -c1-64); log "Qwen model sha256 $QS"
ARGV=$(R bash $SRV argvcheck 2>&1 | tail -1)
python -c "
import json,sys
json.dump({'restored': sys.argv[1], 'by': 'C:/hegel/scripts/Start-HegelQwen8082.ps1 (the pinned starter)', 'argvcheck': sys.argv[2], 'argv_sha256_expected': '1944b782a1c3557851d1c3639e04e43072e6c2a6e8eff6e96978f96d6e48d6b0',
 'model_sha256': sys.argv[3], 'model_sha256_matches': sys.argv[3] == sys.argv[4], 'health': sys.argv[5]}, open(sys.argv[6], 'w'), indent=1)" \
  "$RESTORED" "$ARGV" "$QS" "$QWEN_SHA" "$(health)" "$(cygpath -m "$BR/$DEST/RESTORE.json")"

# push: replies, ledgers, receipts, the server and restore records, the scripts and the log; the replies are not read
A cp -r $H/job-A $H/job-D $WBR/$DEST/
for f in A D; do A test -e $H/replies-$f.jsonl && A cp $H/replies-$f.jsonl $WBR/$DEST/; done
cp "$SP"/inkling_swap.sh "$SP"/inkling_srv.sh "$SP"/inkling_run.py "$SP"/inkling_prep.sh "$SP"/inkling_count.py "$SP"/inkprobe2.sh "$SP"/inkling-cpucheck-ok "$BR/$DEST/" 2>/dev/null; cp "$LOG" "$BR/$DEST/swap.log"
cp "$SP"/inkling-run-A.log "$SP"/inkling-run-D.log "$BR/$DEST/" 2>/dev/null
LA=$(grep '^LEDGER' "$SP/inkling-run-A.log" | sed 's/^LEDGER //'); LD=$(grep '^LEDGER' "$SP/inkling-run-D.log" | sed 's/^LEDGER //')
cnt() { python -c "import json,sys; d=json.loads(sys.argv[1]) if sys.argv[1] else {}; print(f\"{d.get('replied','?')}/{d.get('requests','?')} replied, {len(d.get('failed',[]))} failed{', stopped: '+d['stopped'] if d.get('stopped') else ''}\")" "$1"; }
(cd "$BR" && git add $DEST && git -c user.name="Claude on the PC" -c user.email=noreply@anthropic.com commit -q -m "Inkling 2 Mini against Qwen (W22): the night's run, unread

pc/INKLING-BAKEOFF.md steps 3 to 6: Inkling-2-Mini-UD-Q4_K_M (sha256 78fcedcf...) on llama.cpp b12816, -np 2, ctx $CTX, on 8082
(127.0.0.1 only) in place of the live Qwen, $T0 to $(date +%H:%M); IA $(cnt "$LA"); ID $(cnt "$LD"). Qwen restored by the pinned
Windows starter ($RESTORED). Evaluation only; nothing here is training data.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" && git push -q -u github $BRANCH 2>>"$LOG" && log "pushed $(git rev-parse --short HEAD)") || log "commit/push failed"
HEAD=$(cd "$BR" && git rev-parse --short HEAD)
CA=$(A python3 $WSP/inkling_count.py $H/job-A 2>&1 | tail -1); CD=$(A python3 $WSP/inkling_count.py $H/job-D 2>&1 | tail -1); log "counts A: $CA | D: $CD"
EFF="Before the night, on the CPU and with a test question of my own: the template accepts \`reasoning_effort\` and turns it into a line \"Thinking effort level: 0.0\" for \"none\"; it is a hint, not an off switch, and Inkling still reasoned about 150 tokens at \"none\" as at \"medium\". IA's \`max_tokens\` of 1100 holds that reasoning too. From the receipts' metadata only, IA: $CA. ID: $CD."
REST="Qwen restored by the pinned Windows starter: argv pin $( [ "$RESTORED" = yes ] && echo matches || echo "**$RESTORED**" ), model sha256 $( [ "$QS" = "$QWEN_SHA" ] && echo matches || echo "**$QS**" ), /health $(health)."
note "**DONE, W22 Inkling 2 Mini against Qwen, the night part (PC seat, $(date +%H:%M) Berlin), unread, on \`$BRANCH\` (\`$HEAD\`):** llama.cpp b12816 in its own folder, \`Inkling-2-Mini-UD-Q4_K_M.gguf\` sha256 \`78fcedcf…\`; on 8082 from $T0, \`-np 2\`, ctx $CTX, alias \`inkling\`, bound to 127.0.0.1; one short call answered, \`reasoning_effort\` accepted. **IA** (slot 0): $(cnt "$LA"). **ID** (slot 1): $(cnt "$LD"). $REST Layout: \`$DEST/{job-A,job-D}/\` (receipts with each call's seconds, \`LEDGER.json\`), \`replies-*.jsonl\` where complete, \`SERVER-inkling.json\`, \`RESTORE.json\`, \`swap.log\`. $EFF Replies not read."
log "done"
