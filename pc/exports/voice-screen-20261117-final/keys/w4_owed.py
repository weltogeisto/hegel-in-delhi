"""W4's three owed items, from the frozen job on the PC (copied, never changed): the two keys, arm P's act records, who answers."""
import json, glob, hashlib, os, re, shutil, sys
JOB = "/home/ai/hegel-eval/codex-tasks-20261117/w4-night-204000"
OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
for name in ("KEY.json", "PAIRS-KEY.json"):
    shutil.copyfile(f"{JOB}/private/{name}", f"{OUT}/{name}")
shutil.copyfile(f"{JOB}/WHO-ANSWERS.json", f"{OUT}/WHO-ANSWERS.json")

def parse(raw):
    try:
        return json.loads(raw)
    except Exception:
        m = re.search(r"\{.*\}", raw or "", re.S)
        try:
            return json.loads(m.group(0)) if m else None
        except Exception:
            return None

rows = []
for f in sorted(glob.glob(f"{JOB}/screen/records/*.json")):
    r = json.load(open(f))
    if r["arm"] != "P":
        continue
    first = parse(r["calls"][0]["raw"]) or {}
    act = first.get("act") if isinstance(first, dict) else None
    row = {"id": r["id"], "seed": r["seed"], "act_made": bool(act), "act": act,
           "act_kind": act.get("kind") if isinstance(act, dict) else None,
           "act_what": act.get("what") if isinstance(act, dict) else None,
           "act_minutes": act.get("minutes") if isinstance(act, dict) else None,
           "refused": len(r["calls"]) > 1, "refusal": None, "second_answer": None, "second_act": None,
           "kept_promises": r["promises"], "first_raw": r["calls"][0]["raw"]}
    if len(r["calls"]) > 1:
        msg = r["calls"][1]["payload"]["messages"][-1]["content"]
        row["refusal"] = msg
        second = parse(r["calls"][1]["raw"]) or {}
        row["second_answer"] = r["calls"][1]["raw"]
        row["second_act"] = second.get("act") if isinstance(second, dict) else None
    rows.append(row)
rows.sort(key=lambda x: (x["id"], x["seed"]))
with open(f"{OUT}/P-ACTS.jsonl", "w") as fh:
    for row in rows:
        fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
summary = {"P_replies": len(rows), "acts_made": sum(r["act_made"] for r in rows), "refused": sum(r["refused"] for r in rows),
           "second_with_act": sum(1 for r in rows if r["refused"] and r["second_act"]), "kept_promises": sum(1 for r in rows if r["kept_promises"])}
sha = {n: hashlib.sha256(open(f"{OUT}/{n}", "rb").read()).hexdigest() for n in ("KEY.json", "PAIRS-KEY.json", "P-ACTS.jsonl", "WHO-ANSWERS.json")}
json.dump({"summary": summary, "sha256": sha, "source": JOB}, open(f"{OUT}/OWED.json", "w"), indent=1)
print(json.dumps(summary)); print(json.dumps(sha, indent=1))
