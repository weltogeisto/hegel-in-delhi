#!/bin/bash
# W22 (pc/INKLING-BAKEOFF.md): the server switch for the Inkling bake-off, after fork59_server.sh. Run as root in WSL; every server
# runs as user ai. The live Qwen is never started from here: the Windows starter does that (C:\hegel\scripts\Start-HegelQwen8082.ps1).
#   argvcheck | status | cpucheck | stop-live | start-inkling CTX | probe MODEL EFFORT | stop-inkling | server-json OUT
NB=b12816
BIN=/home/ai/local-ai/llama/release-$NB/llama-$NB/llama-server
CUDA=/home/ai/local-ai/llama/release-$NB/cudart-llama-$NB-bin-ubuntu-cuda-12.8-x64/cudart-llama-$NB-bin-ubuntu-cuda-12.8-x64   # the tarball nests its folder (28 Nov 07:07: without this, the CPU)
LIVEBIN=/home/ai/local-ai/llama/release-b11429/llama-b11429/llama-server
INK=/mnt/c/AI/models/Inkling-2-Mini/Inkling-2-Mini-UD-Q4_K_M.gguf
INK_SHA=78fcedcf93c5d1bfe83e225513b71392bb52259be0eaa5f8899c856a2e5834ae
STAMP=$(date +%Y%m%d-%H%M%S)
asai() { su ai -c "$1"; }
health() { curl -s -m 5 -o /dev/null -w '%{http_code}' http://127.0.0.1:$1/health; }
gpu() { nvidia-smi --query-gpu=memory.used --format=csv,noheader 2>/dev/null; }
servers() { pgrep -af "llama-server" | grep -v pgrep; }
inkpids() { pgrep -f "^$BIN" ; }
argvcheck() {
  python3 - <<'EOF'
import hashlib, os, sys
from pathlib import Path
EXPECTED = '1944b782a1c3557851d1c3639e04e43072e6c2a6e8eff6e96978f96d6e48d6b0'   # /home/ai/.local/bin/hegel-qwen-8082-start.py
found = []
for p in Path('/proc').iterdir():
    try:
        if p.name.isdigit() and (p/'comm').read_text().strip() == 'llama-server':
            raw = (p/'cmdline').read_bytes()
            found.append((hashlib.sha256(raw).hexdigest(), os.readlink(p/'cwd'), b'--lora' in raw))
    except OSError:
        pass
print('servers', found)
sys.exit(0 if found == [(EXPECTED, '/home/ai/hegel-in-delhi', False)] else 1)
EOF
}
probe() {  # PORT MODEL EFFORT MAXTOK: one short call; prints the HTTP code, the finish reason and whether reasoning came back (no text)
  curl -s -m 600 -o /tmp/inkprobe.json -w '%{http_code}' http://127.0.0.1:$1/v1/chat/completions -H 'Content-Type: application/json' \
    -d "{\"model\":\"$2\",\"messages\":[{\"role\":\"user\",\"content\":\"Name one German philosopher of the nineteenth century, in one word.\"}],\"max_tokens\":$4,\"temperature\":0.7,\"seed\":1,\"cache_prompt\":false,\"chat_template_kwargs\":{\"enable_thinking\":false,\"reasoning_effort\":\"$3\"}}"
  echo " $(python3 -c 'import json; d=json.load(open("/tmp/inkprobe.json")); c=d.get("choices",[{}])[0]; m=c.get("message",{}); print("finish", c.get("finish_reason"), "content_chars", len(m.get("content") or ""), "reasoning_chars", len(m.get("reasoning_content") or ""), "error", d.get("error"))' 2>/dev/null || head -c 300 /tmp/inkprobe.json)"
}
case "$1" in
argvcheck) argvcheck && echo ARGV-MATCH;;
status) echo "servers:"; servers; echo "gpu: $(gpu)"; echo "8082: $(health 8082)  18803: $(health 18803)"; echo "tmux: $(asai 'tmux ls 2>/dev/null' | tr '\n' ' ')";;
cpucheck)   # before the night: the new build loads the file and the template takes reasoning_effort, on the CPU only, port 18803
  got=$(cat ${INK}.sha256 2>/dev/null | cut -c1-64); [ "$got" = "$INK_SHA" ] || { echo "REFUSED: model sha256 not confirmed ($got)"; exit 1; }
  asai "tmux new-session -d -s inkling-cpucheck-$STAMP -c /home/ai 'exec env LD_LIBRARY_PATH=$CUDA $BIN -m $INK --device none -ngl 0 -c 4096 -np 1 --host 127.0.0.1 --port 18803 --alias inkling >>/home/ai/hegel-logs/inkling-cpucheck-$STAMP.log 2>&1'"
  for i in $(seq 1 120); do [ "$(health 18803)" = "200" ] && break; sleep 5; done
  echo "health 18803: $(health 18803)"; grep -iE 'error|failed|unknown|template' /home/ai/hegel-logs/inkling-cpucheck-$STAMP.log | head -8
  if [ "$(health 18803)" = "200" ]; then
    echo "props: $(curl -s http://127.0.0.1:18803/props | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d.get("model_alias"), d.get("total_slots"), d.get("build_info"), "template", len(d.get("chat_template") or ""))' 2>/dev/null)"
    echo "probe qwen/none:   $(probe 18803 qwen none 24)"
    echo "probe qwen/medium: $(probe 18803 qwen medium 200)"
  fi
  for s in $(asai 'tmux ls -F "#{session_name}" 2>/dev/null' | grep '^inkling-cpucheck-'); do asai "tmux kill-session -t $s"; done
  sleep 3; echo "gpu after: $(gpu)"; servers;;
stop-live)  # waits for idle slots; refuses after DEADLINE (HH:MM as a number, e.g. 810)
  DL=${2:-810}; clear=0
  while [ $clear -lt 3 ]; do
    busy=$(curl -s -m 5 http://127.0.0.1:8082/slots | python3 -c 'import sys,json;print(any(s.get("is_processing") for s in json.load(sys.stdin)))' 2>/dev/null)
    if [ "$busy" = "False" ]; then clear=$((clear+1)); else
      clear=0; echo "[$(date +%T)] waiting: live slots busy=$busy"
      [ $((10#$(date +%H%M))) -ge $DL ] && { echo "REFUSED: the live server still in use at $DL; untouched"; exit 1; }
    fi
    sleep 15
  done
  argvcheck >/dev/null || { echo "REFUSED: 8082 is not the pinned live server"; exit 1; }
  for s in $(asai 'tmux ls -F "#{session_name}" 2>/dev/null' | grep '^hegel-server-'); do echo "kill tmux $s"; asai "tmux kill-session -t $s"; done
  for i in $(seq 1 30); do pgrep -f "^$LIVEBIN" >/dev/null || break; sleep 1; done
  pgrep -af "^$LIVEBIN" && { echo "FAILED: the live server still runs"; exit 1; }
  sleep 3; echo "live stopped $(date +%T); gpu $(gpu)";;
start-inkling)
  CTX=${2:-32768}
  servers && { echo "REFUSED: a llama-server already runs"; exit 1; }
  asai "tmux new-session -d -s inkling-$STAMP -c /home/ai 'exec env LD_LIBRARY_PATH=$CUDA $BIN -m $INK -ngl 99 -c $CTX -np 2 --host 127.0.0.1 --port 8082 --alias inkling >>/home/ai/hegel-logs/inkling-$STAMP.log 2>&1'"
  for i in $(seq 1 90); do [ "$(health 8082)" = "200" ] && break; inkpids >/dev/null || break; sleep 4; done
  if [ "$(health 8082)" != "200" ]; then echo "FAILED: Inkling not healthy (ctx $CTX)"; tail -6 /home/ai/hegel-logs/inkling-$STAMP.log; for s in $(asai 'tmux ls -F "#{session_name}" 2>/dev/null' | grep '^inkling-'); do asai "tmux kill-session -t $s"; done; exit 1; fi
  used=$(gpu | tr -dc 0-9); if [ "${used:-0}" -lt 10000 ]; then echo "FAILED: Inkling answers but is not on the GPU (gpu $(gpu))"; for s in $(asai 'tmux ls -F "#{session_name}" 2>/dev/null' | grep '^inkling-'); do asai "tmux kill-session -t $s"; done; exit 1; fi
  echo "inkling ready $(date +%T) ctx $CTX; gpu $(gpu); log /home/ai/hegel-logs/inkling-$STAMP.log";;
probe) echo "$(probe 8082 ${2:-qwen} ${3:-none} ${4:-24})";;
stop-inkling)
  for s in $(asai 'tmux ls -F "#{session_name}" 2>/dev/null' | grep '^inkling-'); do echo "kill tmux $s"; asai "tmux kill-session -t $s"; done
  for i in $(seq 1 30); do inkpids >/dev/null || break; sleep 1; done
  inkpids && { pkill -TERM -f "^$BIN"; sleep 5; }
  inkpids && { echo "FAILED: Inkling still runs"; exit 1; }
  sleep 3; echo "inkling stopped $(date +%T); gpu $(gpu)";;
server-json)  # OUT: Inkling's SERVER.json, from /proc and /props
  python3 - "$2" "$INK_SHA" "$NB" <<'EOF'
import hashlib, json, os, sys, urllib.request
from pathlib import Path
out, sha, nb = sys.argv[1:4]
srv = []
for p in Path('/proc').iterdir():
    try:
        if p.name.isdigit() and (p/'comm').read_text().strip() == 'llama-server':
            raw = (p/'cmdline').read_bytes()
            srv.append({"pid": int(p.name), "argv": [a.decode() for a in raw.rstrip(b"\0").split(b"\0")], "argv_sha256": hashlib.sha256(raw).hexdigest(), "cwd": os.readlink(p/'cwd')})
    except OSError:
        pass
props = json.loads(urllib.request.urlopen("http://127.0.0.1:8082/props", timeout=10).read())
rec = {"servers": srv, "model_file": "unsloth/Inkling-2-Mini-GGUF / Inkling-2-Mini-UD-Q4_K_M.gguf", "model_sha256": sha, "llama_cpp_build": nb,
       "build_info": props.get("build_info"), "total_slots": props.get("total_slots"), "model_alias": props.get("model_alias"),
       "n_ctx": (props.get("default_generation_settings") or {}).get("n_ctx"), "host": "127.0.0.1 only: the Pi cannot reach it"}
Path(out).write_text(json.dumps(rec, indent=1) + "\n")
print("SERVER-JSON", json.dumps({k: rec[k] for k in ("llama_cpp_build", "build_info", "total_slots", "model_alias", "n_ctx")}))
EOF
  ;;
*) echo "usage: $0 argvcheck|status|cpucheck|stop-live [HHMM]|start-inkling CTX|probe MODEL EFFORT MAXTOK|stop-inkling|server-json OUT"; exit 2;;
esac
