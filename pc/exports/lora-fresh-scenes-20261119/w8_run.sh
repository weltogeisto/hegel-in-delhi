#!/bin/bash
# W8's run step in WSL: freeze | run [LIMIT] ; URL and folders overridable for the stub test.
MODE=$1; LIMIT=$2
OUT=${W8_OUT:-$HOME/w8/run}
URL=${W8_URL:-http://127.0.0.1:18802}
cd ~/w8/main || exit 1
case "$MODE" in
freeze)
  bash /mnt/c/Users/hendr/AppData/Local/Temp/claude/b52770502021644c/ae932ed3-101c-49e5-8ebb-b1be766eff5b/scratchpad/w8_refs.sh
  rm -rf $OUT && mkdir -p $OUT
  env -i HOME=$HOME PATH=/usr/bin:/bin HEGEL_ENV=/dev/null python3 tools/lora_scenes.py freeze --ref origin/shadow --days 44-49 --out $OUT/plan.json || exit 1
  sha256sum $OUT/plan.json;;
run)
  env -i HOME=$HOME PATH=/usr/bin:/bin HEGEL_ENV=/dev/null python3 tools/lora_scenes.py run --plan $OUT/plan.json --url $URL --out $OUT ${LIMIT:+--limit $LIMIT};;
*) echo "usage: freeze | run [LIMIT]"; exit 2;;
esac
