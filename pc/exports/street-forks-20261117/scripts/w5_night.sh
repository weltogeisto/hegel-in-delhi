#!/bin/bash
# W5's night, driven from Git Bash: wait until Day 48 (2026-11-18) has gone to bed on the Pi, copy shadow's docs, run the ten
# forks in WSL, export, commit to codex/street-forks-20261117 and push. Read-only on the Pi.
SP=/c/Users/hendr/AppData/Local/Temp/claude/b52770502021644c/ae932ed3-101c-49e5-8ebb-b1be766eff5b/scratchpad
WSP=/mnt/c/Users/hendr/AppData/Local/Temp/claude/b52770502021644c/ae932ed3-101c-49e5-8ebb-b1be766eff5b/scratchpad
PI="ssh -o BatchMode=yes -o ConnectTimeout=15 -o IdentitiesOnly=yes -i $HOME/.ssh/gondolin_key faqts@Gondolin.local"
export MSYS_NO_PATHCONV=1
log() { echo "[$(date +%FT%T)] $*" | tee -a "$SP/w5-night.log"; }

# 1. Wait for his bedtime step: Day 48's state runs to the next morning. Give up at 22:20 (no time left for ten forks).
until [ "$($PI 'python3 -c "import json;s=json.load(open(\"hegel-in-delhi/docs/days/2026-11-18.json\"))[\"state\"];print(s[\"until\"][:10]>\"2026-11-18\")"' 2>/dev/null)" = "True" ]; do
  [ "$(date +%H%M)" -ge 2220 ] && { log "GAVE UP: Day 48 not in bed by 22:20"; exit 1; }
  sleep 120
done
log "Day 48 is in bed: $($PI 'cd hegel-in-delhi && git log --oneline -1' 2>&1)"

# 2. Shadow's docs as of now (Day 48 final), into WSL.
$PI 'tar -C ~/hegel-in-delhi -c docs/days docs/index.html docs/map docs/og.png 2>/dev/null' > "$SP/w5-docs.tar" || { log "docs copy failed"; exit 1; }
cat > "$SP/w5_docs.sh" <<EOF
rm -rf ~/w5/shadow-docs ~/w5/pre && mkdir ~/w5/pre && tar -C ~/w5/pre -xf $WSP/w5-docs.tar && mv ~/w5/pre/docs ~/w5/shadow-docs && rmdir ~/w5/pre && ls ~/w5/shadow-docs/days | tail -2
EOF
wsl.exe -- bash "$WSP/w5_docs.sh" | tee -a "$SP/w5-night.log"

# 3. The ten forks.
log "forks begin"
wsl.exe -- bash "$WSP/run_w5.sh" >> "$SP/w5-night.log" 2>&1
log "forks end"

# 4. Export, commit, push.
wsl.exe -- bash "$WSP/export_w5.sh" "$WSP/w5-export" >> "$SP/w5-night.log" 2>&1
REPO=$SP/pr1-merge
cd "$REPO" && git fetch -q github && git worktree add -q -B codex/street-forks-20261117 "$SP/w5-branch" github/main 2>>"$SP/w5-night.log" || { log "worktree failed"; exit 1; }
cd "$SP/w5-branch" && mkdir -p pc/exports && rm -rf pc/exports/street-forks-20261117 && cp -r "$SP/w5-export" pc/exports/street-forks-20261117
cp "$SP/w5-PAGE.md" pc/exports/street-forks-20261117/PAGE.md 2>/dev/null
git add pc/exports/street-forks-20261117 && git commit -q -m "W5: the street's night of forks, the raw results (pc/STREET-FORKS.md)

Ten one-day forks of Day 48 (2026-11-18), five seeds with HEGEL_STREET=0 and the same five with
HEGEL_STREET=1, on main bbcb4c9 with shadow's live switches. Day files, fork_diff per pair,
health rows, world_health rows, the cards drawn, logs and scripts. No reading of the bars:
Claude reads the cards' moments and writes the result. Nothing went on shadow.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" && git push -q github codex/street-forks-20261117 2>>"$SP/w5-night.log" && log "PUSHED $(git rev-parse --short HEAD) to codex/street-forks-20261117" || log "commit or push failed"
log "NIGHT DONE"
