"""Push an unrelated long prompt through each of the server's three slots, so none of them holds a prefix of the world's prompts."""
import json
import urllib.request

URL = "http://127.0.0.1:8082"
for slot in (0, 1, 2):
    body = {"model": "local", "id_slot": slot, "max_tokens": 4, "temperature": 0, "seed": 7,
            "messages": [{"role": "user", "content": f"Slot {slot}. Count slowly from one to forty in words. " * 80}]}
    req = urllib.request.Request(URL + "/v1/chat/completions", data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req, timeout=120).read()
print("flushed slots 0,1,2")
