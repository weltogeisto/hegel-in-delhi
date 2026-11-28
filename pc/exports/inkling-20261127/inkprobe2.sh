#!/bin/bash
# Read only, CPU only, port 18803: what reasoning_effort "none" does with Inkling's template (my own test question, not his requests).
NB=b12816; BIN=/home/ai/local-ai/llama/release-$NB/llama-$NB/llama-server; CUDA=/home/ai/local-ai/llama/release-$NB/cudart-llama-$NB-bin-ubuntu-cuda-12.8-x64
INK=/mnt/c/AI/models/Inkling-2-Mini/Inkling-2-Mini-UD-Q4_K_M.gguf; STAMP=$(date +%H%M%S)
su ai -c "tmux new-session -d -s inkling-probe2-$STAMP -c /home/ai 'exec env LD_LIBRARY_PATH=$CUDA $BIN -m $INK --device none -ngl 0 -c 4096 -np 1 --host 127.0.0.1 --port 18803 --alias inkling >>/home/ai/hegel-logs/inkling-probe2-$STAMP.log 2>&1'"
for i in $(seq 1 120); do [ "$(curl -s -m 5 -o /dev/null -w '%{http_code}' http://127.0.0.1:18803/health)" = 200 ] && break; sleep 5; done
echo "== the template's effort handling"
curl -s http://127.0.0.1:18803/props | python3 -c 'import sys,json,re; t=json.load(sys.stdin).get("chat_template",""); [print("   ", l.strip()[:200]) for l in t.splitlines() if re.search(r"effort|enable_thinking|think", l, re.I)]' | head -30
q() {  # LABEL KWARGS MAXTOK
  curl -s -m 900 -o /tmp/p2.json http://127.0.0.1:18803/v1/chat/completions -H 'Content-Type: application/json' \
    -d "{\"model\":\"qwen\",\"messages\":[{\"role\":\"user\",\"content\":\"In two sentences: what did Hegel mean by Sittlichkeit?\"}],\"max_tokens\":$3,\"temperature\":0.7,\"seed\":1,\"cache_prompt\":false,\"chat_template_kwargs\":$2}"
  echo "$1: $(python3 -c 'import json; d=json.load(open("/tmp/p2.json")); c=d["choices"][0]; m=c["message"]; u=d.get("usage",{}); print("finish", c.get("finish_reason"), "| content chars", len(m.get("content") or ""), "| reasoning chars", len(m.get("reasoning_content") or ""), "| completion tokens", u.get("completion_tokens"))' 2>/dev/null || head -c 200 /tmp/p2.json)"
}
q "none + enable_thinking false (as run_requests sends it)" '{"enable_thinking":false,"reasoning_effort":"none"}' 400
q "none alone" '{"reasoning_effort":"none"}' 400
q "medium + enable_thinking false (as run_requests sends it)" '{"enable_thinking":false,"reasoning_effort":"medium"}' 1200
for s in $(su ai -c 'tmux ls -F "#{session_name}" 2>/dev/null' | grep '^inkling-probe2-'); do su ai -c "tmux kill-session -t $s"; done
sleep 2; pgrep -af "release-$NB" || echo "probe server stopped"
