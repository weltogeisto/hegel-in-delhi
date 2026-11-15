import json, secrets, sys, hashlib
src, sheet, key = sys.argv[1:4]
rows = [json.loads(l) for l in open(src, encoding="utf-8")]
rng = secrets.SystemRandom()
out, k = [], {}
for r in rows:
    arms = ["control-plain", "adapter-training1"]
    rng.shuffle(arms)
    k[r["id"]] = {"A": arms[0], "B": arms[1]}
    out.append({"id": r["id"], "input": r["input"],
                "A": r["arms"][arms[0]]["output"], "B": r["arms"][arms[1]]["output"]})
open(sheet, "w", encoding="utf-8").write("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in out))
raw = json.dumps(k, sort_keys=True).encode()
open(key, "wb").write(raw)
print("sheet", len(out), "cases; key sha256", hashlib.sha256(raw).hexdigest())
