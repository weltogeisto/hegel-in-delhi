"""W22 (pc/INKLING-BAKEOFF.md): one request file against the server on 8082, through tools/run_requests.run, as declared
(--night, one slot, --timeout 900), with one addition: no new call starts after --deadline (HH:MM, local), so the window ends at a
whole request and the rest is resumed another night by the same command. --model only if the server refuses the runner's "qwen".
python3 inkling_run.py ENGINE REQUESTS JOB OUT SLOT DEADLINE [MODEL]   Prints LEDGER {...}; the replies are not printed."""
import json, sys, time
engine, requests, job, out, slot, deadline = sys.argv[1:7]
model = sys.argv[7] if len(sys.argv) > 7 else "qwen"
sys.path.insert(0, engine)
from tools import run_requests as rr
from tools.recorded_llama import TransportError


def guard():
    if time.strftime("%H:%M") >= deadline:
        raise TransportError(f"the window ends at {deadline}: no new call")


if model != "qwen":
    _payload = rr.payload
    rr.payload = lambda row, model_=model: _payload(row, model=model_)
ledger = rr.run(requests, "http://127.0.0.1:8082", job, out, before_request=guard, slot=int(slot), night=True, timeout=900)
print("LEDGER", json.dumps(ledger))
