#!/usr/bin/env python3
"""Send a frozen requests file to the plain live server, one call each, with a durable receipt per call.

    python3 tools/run_requests.py --requests REQUESTS.jsonl --server http://127.0.0.1:8082 --job <folder> --out REPLIES.jsonl

Each line of the requests file is {"id", "messages", and "params" or "settings"}: seed, temperature, max_tokens, cache_prompt
(as `tools/paris_stage2.py requests` and `tools/m1_trial.py requests` write them). Calls go to the spare slot only, with
thinking off, through tools/recorded_llama.RecordedClient: a call whose end was not saved is never sent again, so a
stopped run is resumed by running the same command; it reuses every saved reply and asks to reconcile an unknown one.

`--job` holds the receipts and the frozen plan (the requests file's sha256 and its ids); a different requests file
cannot reuse it. `--out` gets {"id", "reply"} lines in the file's order, and `<job>/LEDGER.json` the counts and hashes.
`--latency-observation` (and `--latency-limit`) stop new calls when his own steps are slower than their limit
(recorded_llama.LatencyGuard). `--limit N` sends at most N new calls this run.

Evaluation only: no reply here is ever training data."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from tools.recorded_llama import LatencyGuard, RecordedClient, TransportError, UnknownRequest, freeze_plan, json_bytes  # noqa: E402

KEYS = ("seed", "temperature", "max_tokens", "cache_prompt")


def load(path):
    raw = Path(path).read_bytes()
    rows = [json.loads(l) for l in raw.decode("utf-8").splitlines() if l.strip()]
    ids = [r["id"] for r in rows]
    if len(set(ids)) != len(ids):
        raise ValueError("request ids repeat")
    for r in rows:
        p = r.get("params", r.get("settings"))
        if not isinstance(r.get("messages"), list) or not isinstance(p, dict) or set(p) - set(KEYS) or "max_tokens" not in p:
            raise ValueError(f"request {r.get('id')} needs messages and params of {', '.join(KEYS)}")
    return raw, rows


def payload(row, model="qwen"):
    p = row.get("params", row.get("settings"))
    return {"model": model, "messages": row["messages"], **{k: p[k] for k in KEYS if k in p},
            "chat_template_kwargs": {"enable_thinking": False}}


def text_of(result):
    try:
        text = result["choices"][0]["message"].get("content")
    except (KeyError, IndexError, TypeError, AttributeError) as e:
        raise TransportError("response has no chat choice") from e
    if not isinstance(text, str):
        raise TransportError("chat content is not text")
    return text


def run(requests, server, job, out, limit=None, before_request=None, opener=None):
    raw, rows = load(requests)
    job = Path(job)
    job.mkdir(parents=True, exist_ok=True)
    plan = {"requests_sha256": hashlib.sha256(raw).hexdigest(), "ids": [r["id"] for r in rows], "server": server.rstrip("/"),
            "thinking": False, "slot": 1}
    plan_sha = freeze_plan(job / "PLAN.json", plan)
    client = RecordedClient(server, job / "receipts", before_request=before_request, opener=opener)
    replies, sent, reused, failed, stopped = {}, 0, 0, [], None
    for r in rows:
        done = Path(str(client.stem(r["id"])) + ".done.json").exists()
        if not done and limit is not None and sent >= limit:
            stopped = "limit"
            break
        try:
            result = client.post(r["id"], payload(r))
            replies[r["id"]] = text_of(result)
        except UnknownRequest:
            raise
        except TransportError as e:
            if not done and not Path(str(client.stem(r["id"])) + ".begin.json").exists():
                stopped = f"stopped before {r['id']}: {e}"      # the guard refused: nothing was sent
                break
            failed.append({"id": r["id"], "error": str(e)})
        if done:
            reused += 1
        else:
            sent += 1
    complete = len(replies) == len(rows)
    if complete:
        Path(out).write_bytes(b"".join(json_bytes({"id": r["id"], "reply": replies[r["id"]]}) for r in rows))
    ledger = {"plan_sha256": plan_sha, "requests_sha256": plan["requests_sha256"], "requests": len(rows), "replied": len(replies),
              "sent_this_run": sent, "reused": reused, "failed": failed, "stopped": stopped, "complete": complete,
              "replies_sha256": hashlib.sha256(Path(out).read_bytes()).hexdigest() if complete else None, "training_eligible": False}
    (job / "LEDGER.json").write_bytes(json_bytes(ledger))
    return ledger


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--requests", required=True)
    ap.add_argument("--server", required=True, help="the plain live server, never an adapter's")
    ap.add_argument("--job", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int)
    ap.add_argument("--latency-observation")
    ap.add_argument("--latency-limit", type=float)
    a = ap.parse_args(argv)
    guard = LatencyGuard(a.latency_observation, limit=a.latency_limit) if a.latency_observation else None
    ledger = run(a.requests, a.server, a.job, a.out, limit=a.limit, before_request=guard)
    print(json.dumps(ledger, indent=1))
    return 0 if ledger["complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
