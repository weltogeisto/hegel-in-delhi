#!/bin/bash
SP=/mnt/c/Users/hendr/AppData/Local/Temp/claude/b52770502021644c/ae932ed3-101c-49e5-8ebb-b1be766eff5b/scratchpad
rm -rf ~/w3/stubtest ~/w3/job; ls ~/w3/screen | tr '\n' ' '; echo
export W3_SP=$SP W3_LIMIT=17.0 W3_CUTOFF=2045 W3_MIN_STEPS=2
cd ~/w3/main && exec python3 $SP/w3_run.py
