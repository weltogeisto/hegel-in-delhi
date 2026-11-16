"""Replay one captured request against the server, several ways, and print the first words of each reply.
    python3 replay.py PAYLOAD.json
Each variant sends exactly the captured request (same seed) unless it says otherwise."""
import json
import sys
import urllib.request

URL = "http://127.0.0.1:8082"
base = json.load(open(sys.argv[1], encoding="utf-8"))


def ask(extra=None, payload=None):
    p = dict(payload or base)
    p.update(extra or {})
    req = urllib.request.Request(URL + "/v1/chat/completions", data=json.dumps(p).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        d = json.loads(r.read())
    return (d["choices"][0]["message"].get("content") or "").replace("\n", " ")


def show(label, text):
    print(f"{label:<44} {text[:78]}")


print("seed", base.get("seed"), "| max_tokens", base["max_tokens"])
for i in range(3):
    show(f"default (cache on), try {i + 1}", ask())
for i in range(3):
    show(f"cache_prompt=false, try {i + 1}", ask({"cache_prompt": False}))
# flush the three slots with unrelated long prompts, then the same request again
filler = {"model": "local", "messages": [{"role": "user", "content": "Count slowly from one to forty in words. " * 60}], "max_tokens": 8, "temperature": 0, "seed": 7}
for slot in (0, 1, 2):
    ask({"id_slot": slot}, filler)
show("default after flushing slots 0,1,2", ask())
show("default again", ask())
