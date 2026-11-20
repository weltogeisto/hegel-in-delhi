#!/bin/bash
# fork59, after the live server is back: fork_diff per seed and the health rows, then the runs into the branch folder.
# (A script file, because wsl.exe -- bash -c "..." expands $ once more in its own shell.)
set -e
WSP=/mnt/c/Users/hendr/AppData/Local/Temp/claude/cd74254ce8d0a965/90b4347d-b5da-4fc9-99db-4ff38302b710/scratchpad
D=$WSP/fork59-branch/pc/exports/adapter-fork-20261121
cd /home/ai/fork59
rm -rf report && mkdir report
for S in 1831 2718 3141; do
  [ -f runs/seed$S-A/FORK-RUN.json ] && [ -f runs/seed$S-B/FORK-RUN.json ] || { echo "seed $S incomplete"; continue; }
  python3 engine/tools/fork_diff.py runs/seed$S-A runs/seed$S-B > report/fork_diff-seed$S.txt || true
  python3 engine/tools/fork_diff.py runs/seed$S-A runs/seed$S-B --json > report/fork_diff-seed$S.json || true
  for A in A B; do (cd engine && python3 -m world report --health --docs ../runs/seed$S-$A 2026-11-21) > report/health-seed$S-$A.txt 2>&1 || true; done
done
ls report
[ -d "$WSP/fork59-branch/.git" ] || [ -f "$WSP/fork59-branch/.git" ] || { echo "no branch worktree"; exit 1; }
rm -rf "$D" && mkdir -p "$D/runs"
for r in runs/*/; do
  n=$(basename "$r"); mkdir -p "$D/runs/$n"; cp -r "$r/days" "$r/FORK-RUN.json" "$D/runs/$n/"
  [ -f "$r/index.html" ] && cp "$r/index.html" "$D/runs/$n/" || true
done
cp -r report logs "$D/"
cp fork59_arm.py fork59_server.sh ENGINE MORNING "$D/"
cp "$WSP/fork59_night.sh" "$WSP/fork59_finish_wsl.sh" "$WSP/fork59-night.log" "$D/"
du -sh "$D"; find "$D" -type f | wc -l
