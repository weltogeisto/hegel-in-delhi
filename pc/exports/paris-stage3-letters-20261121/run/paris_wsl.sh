#!/bin/bash
# Paris stage-3 letters re-test (the cloud's order of 20 Nov, item 3): main 814e0a3's frozen REQUESTS.jsonl to the plain live server,
# spare slot, through tools/run_requests.py; the job outside the repo. Replies unread.
set -e
WSP=/mnt/c/Users/hendr/AppData/Local/Temp/claude/cd74254ce8d0a965/90b4347d-b5da-4fc9-99db-4ff38302b710/scratchpad
R=/home/ai/paris3
bash /home/ai/fork59/fork59_server.sh argvcheck      # the plain live server as pinned, no adapter
mkdir -p $R/main && tar -xf $WSP/main-814e0a3.tar -C $R/main
REQ=$R/main/pc/exports/paris-stage3-letters-20261121/REQUESTS.jsonl
[ "$(sha256sum $REQ | cut -c1-64)" = 50bf9c1c2c3e5707f183a541f0f8c5505847a1dcaca3e8e5e0aec6d3c9ea03a9 ] || { echo "requests sha differs"; exit 1; }
cd $R/main
python3 tools/run_requests.py --requests $REQ --server http://127.0.0.1:8082 --job $R/job --out $R/REPLIES.jsonl > $R/run.out 2> $R/run.err
echo "rc=$?"; tail -3 $R/run.out; tail -3 $R/run.err
wc -l < $R/REPLIES.jsonl; sha256sum $R/REPLIES.jsonl; ls $R/job
