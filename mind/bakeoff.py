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
import re
import statistics
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
PLACES = ["home", "lodhi", "safdarjung", "khan", "gandhi", "gym", "iic", "estates"]
ACTIONS = ["stay", "walk", "read", "write", "talk", "buy", "eat", "rest", "sleep"]
NULLABLE_STR = {"anyOf": [{"type": "string"}, {"type": "null"}]}
SCHEMA = {
    "type": "object",
    "properties": {
        "thought": {"type": "string"},
        "action": {"type": "string", "enum": ACTIONS},
        "place": {"type": "string", "enum": PLACES},
        "minutes": {"type": "integer", "minimum": 5, "maximum": 240},
        "says": NULLABLE_STR,
        "buys": {"type": "array", "items": {
            "type": "object",
            "properties": {"item": {"type": "string"}, "price_inr": {"type": "integer", "minimum": 0}},
            "required": ["item", "price_inr"]}},
        "revision": NULLABLE_STR,
    },
    "required": ["thought", "action", "place", "minutes", "says", "buys", "revision"],
}


def render(s):
    present = ", ".join(s["present"]) if s["present"] else "nobody"
    return (
        f"{s['day']}, {s['time']} Delhi time. You are at: {s['place']}.\n"
        f"Weather: {s['weather']}. Air quality index: {s['aqi']}.\n"
        f"Wearing: {s['outfit']}. Imprest left: ₹{s['imprest_left']:,}.\n"
        f"Present: {present}.\n"
        f"Open now: {', '.join(s['open_now'])}.\n\n"
        f"What happens: {s['event']}\n\n"
        "Decide your next step. Answer with the JSON object only."
    )


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


def extract_json(text):
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S).strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, flags=re.S)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                return None
    return None


def check(ans, s):
    errors, warnings = [], []
    if not isinstance(ans, dict):
        return ["answer is not a JSON object"], warnings
    for k in SCHEMA["required"]:
        if k not in ans:
            errors.append(f"missing '{k}'")
    if errors:
        return errors, warnings
    if ans["action"] not in ACTIONS:
        errors.append(f"unknown action '{ans['action']}'")
    if ans["place"] not in PLACES:
        errors.append(f"unknown place '{ans['place']}'")
    elif ans["place"] not in s["open_now"]:
        errors.append(f"'{ans['place']}' is closed now")
    if not isinstance(ans["minutes"], int) or not 5 <= ans["minutes"] <= 240:
        errors.append(f"minutes out of range: {ans['minutes']}")
    try:
        spent = sum(int(b.get("price_inr", 0)) for b in ans["buys"])
    except (TypeError, ValueError, AttributeError):
        spent = 0
        errors.append("buys is malformed")
    if spent > s["imprest_left"]:
        errors.append(f"spends ₹{spent} with ₹{s['imprest_left']} left")
    thought = ans["thought"] if isinstance(ans["thought"], str) else ""
    if len(thought) < 20:
        errors.append("thought is empty or too short")
    elif len(thought) > 700:
        warnings.append("thought is very long")
    if ans["says"] and not s["present"]:
        warnings.append("talks although nobody is present")
    if ans["action"] == "walk" and ans["place"] == s["place"]:
        warnings.append("walks to where he already is")
    return errors, warnings


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
