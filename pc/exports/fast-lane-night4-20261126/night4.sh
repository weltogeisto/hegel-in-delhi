#!/bin/bash
# The fast lane, night 4 (W21, pc/FAST-LANE-NIGHT4.md on main): HEGEL_EXITS off and on side by side, plus the think arm (on +
# HEGEL_WRITE_REASONING_TOKENS=2048, seed 1831), simulate --days 14 from the newest saved morning (shadow at "Day 59 begins"), main's
# engine (holds when.after_dues). Ordered for Thursday 26 November; run on Friday 27 November, the first night the PC seat ran it.
# Queue: off-1831 on-1831 think-1831, then off-2718 on-2718, then off-4242 on-4242; three at once, the next in whichever slot frees
# first. Live server never restarted; prompt cache off, phone cache frozen, no feeds, no network but 8082. Night 3's stops: no new
# day after 07:30, all stopped at 07:45. Night 3's GPU rule: 0x40, or the core above 83 C for 10 min -> all futures stop; 0x20/0x40
# 30 min in a row -> no new future starts. Every call timed (logs/SEED.calls.jsonl). The DONE text is written, not posted.
export MSYS_NO_PATHCONV=1
SP=/c/Users/hendr/AppData/Local/Temp/claude/cd74254ce8d0a965/206bd0ad-34b9-4f26-88b8-6e818bc0ce46/scratchpad
WSP=/mnt/c/Users/hendr/AppData/Local/Temp/claude/cd74254ce8d0a965/206bd0ad-34b9-4f26-88b8-6e818bc0ce46/scratchpad
SPW='C:/Users/hendr/AppData/Local/Temp/claude/cd74254ce8d0a965/206bd0ad-34b9-4f26-88b8-6e818bc0ce46/scratchpad'
REPO=/c/AI/projects/hegel-in-delhi; BRANCH=codex/fast-lane-night4-20261126; DEST=pc/exports/fast-lane-night4-20261126
BR=$SP/night4-branch; WDEST=$WSP/night4-branch/$DEST; LOG=$SP/night4.log; DONEF=$SP/night4-done.txt; STOPF=$SP/night4-stopped.txt
STARTF=$SP/night4-started.txt; POSTF=$SP/night4-DONE.md
PI="/c/Windows/System32/OpenSSH/ssh.exe -o BatchMode=yes -o ConnectTimeout=15 -i C:/Users/hendr/.ssh/gondolin_key faqts@gondolin"
MODEL_SHA=322e194ff79741c7baa497c240f677f54b201b0efab44ca8e50f122b39123482
N=59; DATE=2026-11-29; PREV=2026-11-28
QUEUE=(off-1831 on-1831 think-1831 off-2718 on-2718 off-4242 on-4242); MAXRUN=3
W() { wsl.exe -d Ubuntu-24.04 -u ai -- "$@" < /dev/null; }
log() { echo "[$(date +%FT%T)] $*" | tee -a "$LOG"; }
hhmm() { echo $((10#$(date +%H%M))); }
morning_side() { [ "$(hhmm)" -lt 2000 ]; }
blocked() { printf '**BLOCKED, W21 the fast lane night 4 (PC seat, %s Berlin):** %s\n' "$(date +%H:%M)" "$1" > "$POSTF"; log "BLOCKED: $1"; exit 1; }
up() { [ "$(curl -s -m 10 -o /dev/null -w '%{http_code}' http://127.0.0.1:8082/health)" = 200 ]; }
check8082() {
  for t in 1 2 3; do up && return 0; sleep 20; done
  log "8082 does not answer ($1): the Windows starter"
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File 'C:\hegel\scripts\Start-HegelQwen8082.ps1' >> "$LOG" 2>&1
  sleep 120; up && { log "8082 answers after the Windows starter"; return 2; }; log "8082 still down"; return 1; }
maxsecs() { python -c "
import datetime as d
n=d.datetime.now(); s=n.replace(hour=7,minute=50,second=0,microsecond=0)
s = s if n < s else s + d.timedelta(days=1)
print(int((s-n).total_seconds()))"; }
ndays() { W ls /home/ai/night4/$1/futures/$2/days/ 2>/dev/null | grep -c '^2026-'; }
started() { grep -q "^start $1-$2$" "$STARTF" 2>/dev/null; }
running() { started $1 $2 && ! grep -q "^$1-$2 " "$DONEF" 2>/dev/null; }
nrunning() { local n=0 f; for f in "${QUEUE[@]}"; do running ${f%-*} ${f#*-} && n=$((n+1)); done; echo $n; }
stop_future() {
  running $1 $2 || return 0
  grep -q "^$1-$2 " "$STOPF" 2>/dev/null || echo "$1-$2 $3" >> "$STOPF"
  log "stop $1-$2: $3"; W pkill -TERM -f "night4/$1/night4_run.py $2" >/dev/null 2>&1; }
start_future() {  # ARM SEED
  echo "start $1-$2" >> "$STARTF"
  ( W env NIGHT2_BASE=/home/ai/night4/$1 NIGHT2_DATE=$DATE NIGHT2_DAYS=14 bash /home/ai/night4/$1/night4_run.sh $2 $(maxsecs) >> "$SP/night4-runs.log" 2>&1; echo "$1-$2 $?" >> "$DONEF" ) &
  log "start $1 $2"; sleep 20; }
finish_one() {  # ARM SEED
  local how; how=$(grep "^$1-$2 " "$STOPF" 2>/dev/null | head -1 | cut -d' ' -f2-); printf '%s' "$how" > "$SP/night4-how-$1-$2.txt"
  W env NIGHT2_BASE=/home/ai/night4/$1 NIGHT2_DATE=$DATE python3 /home/ai/night4/$1/night4_finish.py $2 "$WDEST/$1" live "$WSP/night4-how-$1-$2.txt" 2>&1 | tail -1 | tee -a "$LOG" | sed -n 's/^FINISH //p' > "$SP/night4-finish-$1-$2.json"; }
days_line() {
  local a o="" f
  for f in "$SP"/night4-finish-*.json; do
    [ -s "$f" ] || continue; a=$(basename "$f" .json); a=${a#night4-finish-}
    o="$o${o:+; }${a%-*} ${a##*-}: $(python -c "import json,sys; d=json.load(open(sys.argv[1])); print(str(d['days_complete'])+' days ('+str(d['first'])+' to '+str(d['last'])+')')" "$(cygpath -m "$f")" 2>/dev/null || echo '?')"
  done; echo "${o:-none yet}"; }
commit_push() {
  cp "$GPULOG" "$BR/$DEST/gpu-log.csv" 2>/dev/null; cp "$LOG" "$BR/$DEST/night.log"
  for a in off on think; do
    mkdir -p "$BR/$DEST/$a"
    for f in MORNING.json SERVER.json SWITCHES.json ENGINE; do W cp /home/ai/night4/$a/$f $WDEST/$a/$f 2>>"$LOG"; done
  done
  cp "$SP"/night4.sh "$SP"/night4_setup.py "$SP"/night4_run.py "$SP"/night4_run.sh "$SP"/night4_finish.py "$BR/$DEST/" 2>/dev/null
  (cd "$BR" && git add $DEST && { git diff --cached --quiet || git -c user.name="Claude on the PC" -c user.email=noreply@anthropic.com commit -q -m "The fast lane, night 4 (W21): $1, unread

pc/FAST-LANE-NIGHT4.md: HEGEL_EXITS off and on side by side, and the think arm (on + HEGEL_WRITE_REASONING_TOKENS=2048, seed
1831), simulate --days 14 from Day $N's saved morning (shadow $MCOMMIT), main's engine $ECOMMIT, every switch as the Pi runs. The
live server, never restarted. Days complete: $(days_line). Evaluation only; nothing here becomes training data or reaches his world.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"; } && git push -q -u github $BRANCH 2>>"$LOG" && log "pushed $(git rev-parse --short HEAD): $1") || log "commit/push failed: $1"; }

GPULOG=$SP/night4-gpu.csv; GSTOPF=$SP/night4-gpustop; ONEF=$SP/night4-one
gpu_logger() {
  local n=0 hot=0 cont=0 line T R b20 b40
  echo "timestamp,temp,power,util,sm,throttle" > "$GPULOG"
  while :; do
    line=$(nvidia-smi --query-gpu=timestamp,temperature.gpu,power.draw,utilization.gpu,clocks.sm,clocks_throttle_reasons.active --format=csv,noheader 2>/dev/null | head -1)
    T=$(echo "$line" | cut -d, -f2 | tr -dc 0-9); R=$(echo "$line" | awk -F, '{print $NF}' | tr -d ' \r')
    [ $((n % 5)) = 0 ] && echo "$line" >> "$GPULOG"
    if [ "${T:-0}" -gt 83 ]; then hot=$((hot+1)); else hot=0; fi
    b20=0; b40=0; case "$R" in 0x*) [ $(( R & 0x20 )) -ne 0 ] && b20=1; [ $(( R & 0x40 )) -ne 0 ] && b40=1;; esac
    if [ $b20 = 1 ] || [ $b40 = 1 ]; then cont=$((cont+1)); else cont=0; fi
    if [ ! -e "$GSTOPF" ]; then
      [ $b40 = 1 ] && echo "0x40 (HW thermal slowdown) at $(date +%H:%M)" > "$GSTOPF"
      [ $hot -ge 10 ] && echo "the core above 83 C for 10 minutes at $(date +%H:%M)" > "$GSTOPF"
      [ -e "$GSTOPF" ] && { echo "$line" >> "$GPULOG"; log "GPU stop: $(cat "$GSTOPF"): $line"; }
    fi
    [ ! -e "$ONEF" ] && [ $cont -gt 30 ] && { echo "$(date +%H:%M)" > "$ONEF"; log "GPU: 0x20/0x40 for 30 minutes in a row: no new future from now"; }
    n=$((n+1)); sleep 60
  done; }

# --- 1. the newest saved morning, the engine
log "armed (pid $$)"; rm -f "$DONEF" "$STOPF" "$GSTOPF" "$ONEF" "$STARTF" "$POSTF" "$SP"/night4-finish-*.json; touch "$DONEF" "$STARTF"
while :; do
  C=$($PI "cd hegel-in-delhi && git log --format=%H -1 --grep='^Day $N begins\$'" 2>/dev/null | tr -d '\r')
  [ -n "$C" ] && break
  morning_side && [ "$(hhmm)" -ge 130 ] && blocked "shadow has no \"Day $N begins\" commit by 01:30, so there is no saved morning. Nothing ran."
  sleep 60
done
MCOMMIT=${C:0:7}; log "Day $N's saved morning: shadow $C"
(cd "$REPO" && GIT_SSH_COMMAND="ssh -o BatchMode=yes -o IdentitiesOnly=yes -i $HOME/.ssh/gondolin_key" git fetch -q origin shadow && git cat-file -e $C) || blocked "could not fetch shadow's \"Day $N begins\" ($MCOMMIT). Nothing ran."
(cd "$REPO" && git archive -o "$SPW/night4-morning.tar" $C) || blocked "git archive of the morning failed. Nothing ran."
(cd "$REPO" && git fetch -q github main) || blocked "could not fetch main. Nothing ran."
ECOMMIT=$(cd "$REPO" && git rev-parse --short=8 github/main)
(cd "$REPO" && git grep -q after_dues github/main -- world) || blocked "main ($ECOMMIT) does not hold when.after_dues. Nothing ran."
(cd "$REPO" && git archive -o "$SPW/night4-engine.tar" github/main) || blocked "git archive of main failed. Nothing ran."
log "engine: main $ECOMMIT"
SET=$(W python3 $WSP/night4_setup.py $C $MODEL_SHA $ECOMMIT $N $DATE $PREV 2>&1); log "setup: $(echo "$SET" | tr '\n' ' ' | cut -c1-600)"
echo "$SET" | grep -q '"pin_matches": true' || blocked "the setup did not finish, or 8082 is not the pinned server: \`$(echo "$SET" | tail -2 | tr '\n' ' ' | cut -c1-300)\`. Nothing ran."
check8082 "before the night"; [ $? = 1 ] && blocked "8082 does not answer, even after the Windows starter. Nothing ran."
if [ ! -d "$BR" ]; then (cd "$REPO" && git worktree add -q -b $BRANCH "$(cygpath -m "$BR")" github/main) || blocked "the branch worktree failed. Nothing ran."; fi
mkdir -p "$BR/$DEST"
gpu_logger & GPUPID=$!; trap 'kill $GPUPID 2>/dev/null' EXIT
T0=$(date +%H:%M)

# --- 2. the futures: the queue, three at once
qi=0
declare -A AT730 FIN
while :; do
  H=$(hhmm); late=no; { morning_side && [ $H -ge 700 ]; } && late=yes
  while [ $qi -lt ${#QUEUE[@]} ] && [ $(nrunning) -lt $MAXRUN ] && [ $late = no ] && [ ! -e "$GSTOPF" ] && [ ! -e "$ONEF" ]; do
    f=${QUEUE[$qi]}; qi=$((qi+1)); start_future ${f%-*} ${f#*-}
  done
  for f in "${QUEUE[@]}"; do
    a=${f%-*}; s=${f#*-}; running $a $s || continue
    [ -e "$GSTOPF" ] && stop_future $a $s "the GPU rule ($(cat "$GSTOPF"))"
    if morning_side && [ $H -ge 730 ]; then
      n=$(ndays $a $s)
      if [ -z "${AT730[$f]}" ]; then AT730[$f]=$n; log "07:30: $f has $n day files; no new day from now"
      elif [ "${n:-0}" -gt "${AT730[$f]}" ]; then stop_future $a $s "07:30: a new day began after 07:30"; fi
    fi
    morning_side && [ $H -ge 745 ] && stop_future $a $s "07:45"
  done
  # a future that has ended: finish it, push
  for f in "${QUEUE[@]}"; do
    a=${f%-*}; s=${f#*-}
    if started $a $s && ! running $a $s && [ -z "${FIN[$f]}" ]; then
      FIN[$f]=1; log "$f ended: $(grep "^$f " "$DONEF")"; finish_one $a $s; commit_push "$a $s"
    fi
  done
  [ $(nrunning) = 0 ] && { [ $qi -ge ${#QUEUE[@]} ] || [ $late = yes ] || [ -e "$GSTOPF" ] || [ -e "$ONEF" ]; } && break
  if [ $(( $(date +%s) - ${LASTCHK:-0} )) -ge 600 ]; then
    LASTCHK=$(date +%s)
    if ! up; then check8082 "during the night"; [ $? = 1 ] && for f in "${QUEUE[@]}"; do stop_future ${f%-*} ${f#*-} "8082 stopped answering"; done; fi
    pr=""; for f in "${QUEUE[@]}"; do running ${f%-*} ${f#*-} && pr="$pr${pr:+, }$f $(ndays ${f%-*} ${f#*-})"; done
    log "progress (day files): ${pr:-nothing running}"
  fi
  sleep 30
done

# --- 3. the end
kill $GPUPID 2>/dev/null
sleep 30; check8082 "after the night"; c=$?
LIVE="8082 answers after the night."
[ $c = 2 ] && LIVE="**8082 had stopped answering; the Windows starter brought it back.**"
[ $c = 1 ] && LIVE="**8082 does not answer after the night: it needs a human before 08:59.**"
TMAX=$(awk -F', ' 'NR>1{if($2+0>m)m=$2+0} END{print m}' "$GPULOG" 2>/dev/null)
HEAD=$(cd "$BR" && git rev-parse --short HEAD); STOPS=$(tr '\n' ';' < "$STOPF" 2>/dev/null)
GR=""; [ -e "$GSTOPF" ] && GR=" **GPU rule:** $(cat "$GSTOPF")."; [ -e "$ONEF" ] && GR="$GR No new future after $(cat "$ONEF") (0x20/0x40 for 30 minutes in a row)."
NOTRUN=""; [ $qi -lt ${#QUEUE[@]} ] && NOTRUN=" Not started: ${QUEUE[*]:$qi}."
printf '%s\n' "**DONE, W21 the fast lane night 4 (PC seat, $(date +%H:%M) Berlin), unread, on \`$BRANCH\` (\`$HEAD\`):** HEGEL_EXITS off and on side by side and the think arm (on + \`HEGEL_WRITE_REASONING_TOKENS=2048\`, seed 1831), \`simulate --days 14\` from Day $N's saved morning (shadow \`$MCOMMIT\`), main \`$ECOMMIT\`, every switch as the Pi runs; $T0 to $(date +%H:%M), the night of Friday 27 November (Thursday's did not run). **Days complete:** $(days_line). How each stopped: ${STOPS:-all ran to their end}.$NOTRUN$GR GPU max ${TMAX} °C. Layout: \`$DEST/{off,on,think}/futures/<seed>/\` with \`days/\`, \`health.jsonl\`, \`RUN.json\`, \`log\`, \`slots.txt\`, \`calls.jsonl\` (every call timed, writing calls by kind); \`gpu-log.csv\`. Live server never restarted. $LIVE" > "$POSTF"
log "done"
