#!/bin/bash
# W8's server switch, run as root in WSL; every server runs as user ai, as the live one does.
#   status | stop-live | start-trial | stop-trial | start-live
BIN=/home/ai/local-ai/llama/release-b11429/llama-b11429/llama-server
CUDA=/home/ai/local-ai/llama/release-b11429/cudart-llama-b11429-bin-ubuntu-cuda-12.8-x64
MODEL=/mnt/c/AI/models/Qwen3.8-27B/Qwen3.8-27B-UD-Q4_K_M.gguf
ADAPTER=/home/ai/hegel-eval/codex-tasks-20261106/training1-real-day-083650/converted/adapter-f16.gguf
ADAPTER_SHA=5bd5520fa6a8acd3ff48329e877fc7ee6bfc29e1964b93311091c5a87513cbfd   # pc/exports/training1-20261106/MODEL-PROMPT-CHECKPOINT-MANIFEST.json
TRIAL_PORT=18802
STAMP=$(date +%Y%m%d-%H%M%S)
asai() { su ai -c "$1"; }
health() { curl -s -m 5 -o /dev/null -w '%{http_code}' http://127.0.0.1:$1/health; }
gpu() { nvidia-smi --query-gpu=memory.used --format=csv,noheader 2>/dev/null; }
servers() { pgrep -af "^$BIN" ; }

case "$1" in
status)
  echo "servers:"; servers; echo "gpu: $(gpu)"; echo "live 8082: $(health 8082)  trial $TRIAL_PORT: $(health $TRIAL_PORT)"
  echo "tmux: $(asai 'tmux ls 2>/dev/null' | tr '\n' ' ')";;
stop-live)
  # Another seat may be using the live server tonight: wait while any live slot is processing; free means three clear checks
  # in a row, 20 s apart. (Astra's voice-perspective job of 19 November waits for W8's handover and sends nothing before it,
  # so a waiting job of user ai is not counted: counting it would deadlock the two.) Give up at 01:30, live server untouched.
  clear=0
  while [ $clear -lt 3 ]; do
    busy=$(curl -s -m 5 http://127.0.0.1:8082/slots | python3 -c 'import sys,json;print(any(s.get("is_processing") for s in json.load(sys.stdin)))' 2>/dev/null)
    if [ "$busy" = "False" ]; then clear=$((clear+1)); else
      clear=0; echo "[$(date +%T)] waiting: live slots busy=$busy"
      H=$((10#$(date +%H%M))); [ $H -ge 130 ] && [ $H -lt 1200 ] && { echo "REFUSED: the live server was still in use at 01:30; untouched"; exit 1; }
    fi
    sleep 20
  done
  for s in $(asai 'tmux ls -F "#{session_name}" 2>/dev/null' | grep '^hegel-server-'); do echo "kill tmux $s"; asai "tmux kill-session -t $s"; done
  for i in $(seq 1 30); do servers >/dev/null || break; sleep 1; done
  servers && { echo "FAILED: a llama-server still runs"; exit 1; }
  sleep 3; echo "live stopped; gpu $(gpu)";;
start-trial)
  servers && { echo "REFUSED: a llama-server already runs"; exit 1; }
  got=$(sha256sum $ADAPTER | cut -c1-64); [ "$got" = "$ADAPTER_SHA" ] || { echo "REFUSED: adapter sha256 $got"; exit 1; }
  echo "adapter sha256 ok"
  asai "tmux new-session -d -s w8-trial-$STAMP -c /home/ai/hegel-in-delhi 'exec env LD_LIBRARY_PATH=$CUDA $BIN -m $MODEL -ngl 99 -c 49152 -np 3 --host 127.0.0.1 --port $TRIAL_PORT --alias qwen --lora-scaled $ADAPTER:0 >>/home/ai/hegel-logs/w8-trial-$STAMP.log 2>&1'"
  for i in $(seq 1 60); do [ "$(health $TRIAL_PORT)" = "200" ] && break; sleep 5; done
  [ "$(health $TRIAL_PORT)" = "200" ] || { echo "FAILED: trial not healthy in 300 s"; tail -5 /home/ai/hegel-logs/w8-trial-$STAMP.log; exit 1; }
  echo "trial ready: $(curl -s http://127.0.0.1:$TRIAL_PORT/lora-adapters)"; echo "gpu $(gpu)";;
stop-trial)
  for s in $(asai 'tmux ls -F "#{session_name}" 2>/dev/null' | grep '^w8-trial-'); do echo "kill tmux $s"; asai "tmux kill-session -t $s"; done
  for i in $(seq 1 30); do servers >/dev/null || break; sleep 1; done
  servers && { echo "FAILED: a llama-server still runs"; exit 1; }
  sleep 3; echo "trial stopped; gpu $(gpu)";;
start-live)
  servers | grep -q -- "--port $TRIAL_PORT" && { echo "REFUSED: the trial server still runs"; exit 1; }
  asai "python3 /home/ai/.local/bin/hegel-qwen-8082-start.py" 2>&1 | tail -3
  [ "$(health 8082)" = "200" ] || { echo "FAILED: live not healthy"; exit 1; }
  curl -s http://127.0.0.1:8082/props | python3 -c 'import sys,json;d=json.load(sys.stdin);print("live props:",d.get("model_path"),"slots",d.get("total_slots"))'
  echo "live adapters: $(curl -s http://127.0.0.1:8082/lora-adapters)"; servers;;
*) echo "usage: $0 status|stop-live|start-trial|stop-trial|start-live"; exit 2;;
esac
