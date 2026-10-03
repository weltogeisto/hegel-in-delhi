#!/usr/bin/env python3
"""Hegel in Delhi: mind bake-off.

Sends the 20 test situations to one llama-server endpoint, checks every answer
against the world's rules and saves the results. Standard library only.

    python3 mind/bakeoff.py --url http://PC:8081 --label bonsai
    python3 mind/bakeoff.py --url http://PC:8080 --label qwen
    python3 mind/bakeoff.py --compare bonsai qwen     # writes mind/results/bakeoff.md
    python3 mind/bakeoff.py --url http://PC:8081 --label smoke --only s01
"""
import argparse
import json
import statistics
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
sys.path.insert(0, str(HERE.parent))
from world.contract import SCHEMA, check, extract_json, render  # noqa: E402  (one contract for bake-off and the world)


def post(url, payload, timeout):
    req = urllib.request.Request(url.rstrip("/") + "/v1/chat/completions",
                                 data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def ask(url, system, user, model, timeout, constrained=True):
    payload = {
        "model": model,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "temperature": 0.7,
        "max_tokens": 700,
        "chat_template_kwargs": {"enable_thinking": False},
    }
    if constrained:
        payload["response_format"] = {"type": "json_schema", "json_schema": {"name": "decision", "schema": SCHEMA}}
    try:
        data = post(url, payload, timeout)
    except urllib.error.HTTPError as e:
        if constrained and e.code in (400, 422, 500):
            return ask(url, system, user, model, timeout, constrained=False)
        raise
    msg = data["choices"][0]["message"]
    return (msg.get("content") or "").strip(), constrained


def run(args):
    system = (HERE / "soul.md").read_text(encoding="utf-8")
    situations = json.loads((HERE / "situations.json").read_text(encoding="utf-8"))["situations"]
    if args.only:
        situations = [s for s in situations if s["id"] in args.only.split(",")]
    RESULTS.mkdir(exist_ok=True)
    out = {"label": args.label, "url": args.url, "started": datetime.now().isoformat(timespec="seconds"), "answers": []}
    for s in situations:
        t0 = time.time()
        try:
            raw, constrained = ask(args.url, system, render(s), args.model, args.timeout)
            ans = extract_json(raw)
            errors, warnings = check(ans, s)
        except Exception as e:  # report every failure, keep going
            raw, constrained, ans, errors, warnings = "", False, None, [f"request failed: {e}"], []
        dt = round(time.time() - t0, 1)
        out["answers"].append({"id": s["id"], "title": s["title"], "latency_s": dt, "constrained": constrained,
                               "ok": not errors, "errors": errors, "warnings": warnings, "answer": ans, "raw": raw})
        mark = "OK " if not errors else "ERR"
        print(f"{mark} {s['id']} {dt:6.1f}s  {s['title']}" + (f"  ({'; '.join(errors)})" if errors else ""), flush=True)
    path = RESULTS / f"{args.label}.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    ok = sum(a["ok"] for a in out["answers"])
    lat = [a["latency_s"] for a in out["answers"]]
    print(f"\n{args.label}: {ok}/{len(lat)} valid, median {statistics.median(lat):.1f}s, max {max(lat):.1f}s -> {path}")
    return 0 if ok == len(lat) else 1


def compare(labels):
    runs = [json.loads((RESULTS / f"{l}.json").read_text(encoding="utf-8")) for l in labels]
    situations = {s["id"]: s for s in json.loads((HERE / "situations.json").read_text(encoding="utf-8"))["situations"]}
    lines = ["# Bake-off: " + " vs ".join(labels), ""]
    for r in runs:
        a = r["answers"]; lat = [x["latency_s"] for x in a]
        warn = sum(len(x["warnings"]) for x in a)
        lines.append(f"- **{r['label']}**: {sum(x['ok'] for x in a)}/{len(a)} valid, {warn} warnings, "
                     f"median {statistics.median(lat):.1f}s, max {max(lat):.1f}s")
    lines += ["", "Read the thoughts, not just the numbers: which one sounds like Hegel?", ""]
    by_id = [{x["id"]: x for x in r["answers"]} for r in runs]
    for sid in [x["id"] for x in runs[0]["answers"]]:
        s = situations.get(sid, {})
        lines += [f"## {sid} {s.get('title', '')}", "", f"_{s.get('event', '')}_", ""]
        for r, idx in zip(runs, by_id):
            x = idx.get(sid)
            if not x:
                continue
            a = x["answer"] or {}
            head = f"**{r['label']}** ({x['latency_s']}s)"
            if x["errors"]:
                head += " ❌ " + "; ".join(x["errors"])
            elif x["warnings"]:
                head += " ⚠️ " + "; ".join(x["warnings"])
            lines.append(head)
            if a:
                lines.append(f"{a.get('action')} → {a.get('place')}, {a.get('minutes')} min")
                lines.append(f"> {a.get('thought', '')}")
                if a.get("says"):
                    lines.append(f"Says: “{a['says']}”")
                if a.get("buys"):
                    lines.append("Buys: " + ", ".join(f"{b.get('item')} ₹{b.get('price_inr')}" for b in a["buys"]))
                if a.get("revision"):
                    lines.append(f"Revision: {a['revision']}")
            else:
                lines.append("> (no usable answer) " + (x["raw"][:300] if x["raw"] else ""))
            lines.append("")
    path = RESULTS / "bakeoff.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {path}")
    return 0


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--url", help="llama-server base URL, e.g. http://192.168.178.50:8081")
    p.add_argument("--label", help="name for this run, e.g. bonsai or qwen")
    p.add_argument("--model", default="local", help="model name sent to the server (llama-server ignores it)")
    p.add_argument("--only", help="comma-separated situation ids, e.g. s01,s17")
    p.add_argument("--timeout", type=int, default=300)
    p.add_argument("--compare", nargs="+", metavar="LABEL", help="compare saved runs")
    args = p.parse_args()
    if args.compare:
        return compare(args.compare)
    if not args.url or not args.label:
        p.error("--url and --label are required (or use --compare)")
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
