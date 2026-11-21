#!/bin/bash
# A frozen requests file from main to the plain live server, spare slot, via that main's tools/run_requests.py; job outside the repo.
# Args: TAG MAIN_SHA REQUESTS_PATH(in repo) REQUESTS_SHA256 OUTNAME   (main's tree must be at $WSP/main-<MAIN_SHA>.tar)
set -e
TAG=$1; MAIN=$2; REL=$3; WANT=$4; OUT=$5
WSP=/mnt/c/Users/hendr/AppData/Local/Temp/claude/cd74254ce8d0a965/90b4347d-b5da-4fc9-99db-4ff38302b710/scratchpad
R=/home/ai/requests-$TAG
H=$((10#$(date +%H%M))); [ $H -ge 800 ] && [ $H -lt 2100 ] && { echo "REFUSED: after 08:00, GPU work stops by 08:30"; exit 1; }
bash /home/ai/fork59/fork59_server.sh argvcheck      # the plain live server as pinned, no adapter
[ -e $R ] && { echo "REFUSED: $R exists"; exit 1; }
mkdir -p $R/main && tar -xf $WSP/main-$MAIN.tar -C $R/main
REQ=$R/main/$REL
[ "$(sha256sum $REQ | cut -c1-64)" = "$WANT" ] || { echo "REFUSED: requests sha256 $(sha256sum $REQ | cut -c1-64)"; exit 1; }
cd $R/main
set +e
python3 tools/run_requests.py --requests $REQ --server http://127.0.0.1:8082 --job $R/job --out $R/$OUT > $R/run.out 2> $R/run.err
rc=$?
echo "rc=$rc"; tail -3 $R/run.err
python3 -c "import json;d=json.load(open('$R/job/LEDGER.json'));print({k:d.get(k) for k in ('complete','requests','replied','failed','reused','sent_this_run','stopped','requests_sha256','replies_sha256')})"
sha256sum $R/$OUT; wc -l < $R/$OUT
exit $rc
