"""Part 1 of pc/VOICE-REPAIRS-CHECK.md: the recorded replies of some days put through the routing and the cleaning again, with
HEGEL_VOICE_REPAIRS off and on. No model, no network.

    python3 tools/voice_repairs_replay.py --ref origin/shadow --days 44-49 --out DIR
    python3 tools/voice_repairs_replay.py --docs FOLDER --out DIR        (FOLDER holds the day files; index.json if it has one)

What a day file holds of the facts the reply path reads, and what is rebuilt:
  present            held (the step's `present`, as the people's short names)
  his words          held (decision.says), and decision.speaks_to
  speaker            held (voice.by)
  a beat that fired  held (step.beat is its id); its `needs` come from the beat's data in the repository, not from the file
  a purchase         inferred: the day's `bag` and settling `expense` entries stamped with the step's time
  the greeting       held on days that carry `opened` ("greeting:<id>"); inferred on older days: a `said` entry with `by` that comes
                     first among the entries stamped with the step's time
  who last spoke     inferred: the day's `said` entries stamped before the step, and the segments that began before it
                     (the file keeps the final segments; the place is the one that holds the step's minute)
A step whose off-routing does not give the recorded speaker is "not reproducible" and is left out of every count.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
from world import voices  # noqa: E402
from world.world import World  # noqa: E402


def load_days(ref=None, docs=None, lo=0, hi=10 ** 6):
    """[(day file, as a dict)] for the days numbered lo to hi, in order."""
    out = []
    if ref:
        git = lambda p: subprocess.run(["git", "-C", str(REPO), "show", f"{ref}:{p}"], capture_output=True, text=True, check=True).stdout
        rows = json.loads(git("docs/days/index.json"))["days"]
        for r in rows:
            if lo <= r.get("n", -1) <= hi:
                out.append(json.loads(git(f"docs/days/{r['date']}.json")))
    else:
        for f in sorted(Path(docs).glob("2*.json")):
            d = json.loads(f.read_text(encoding="utf-8"))
            if lo <= d.get("n", -1) <= hi:
                out.append(d)
    return sorted(out, key=lambda d: d["date"])


class Replay:
    def __init__(self, world=None):
        self.w = world or World()
        self.cast = self.w.cast
        self.by_short = {c["short"]: k for k, c in self.cast.items()}
        self.by_name = {c["name"][0].upper() + c["name"][1:]: k for k, c in self.cast.items()}

    def needs(self, beat_id, place):
        b = next((x for x in self.w.beats if x["id"] == beat_id), None)
        if b is None:
            return None
        return (b.get("variants", {}).get(place) or b).get("needs", [])

    def place_at(self, day, t):
        seg = next((s for s in day.get("segments", []) if s["from"] <= t < s["to"]), None)
        return seg.get("at") if seg else None

    def facts(self, day, i):
        """What the reply path would have read at step i, from the file."""
        s = day["steps"][i]
        t = s["t"]
        present = [self.by_short.get(p) for p in s.get("present", [])]
        mine = [e for e in day["entries"] if e.get("t") == t]
        held = "opened" in s
        if held:
            greeter = next((x[len("greeting:"):] for x in s["opened"] if x.startswith("greeting:")), None)
        else:
            greeter = self.by_name.get(mine[0].get("by")) if mine and mine[0].get("k") == "said" and mine[0].get("by") else None
        purchases = [{"item": e["item"], "price": e.get("price", e.get("amount"))} for e in mine
                     if e.get("k") == "bag" or (e.get("k") == "expense" and e.get("settles") is True)]
        place = self.place_at(day, t)
        return dict(
            present=present, greeting=greeter, greeting_held=held, purchases=purchases, place=place,
            needs=self.needs(s["beat"], place) if s.get("beat") else [], beat=s.get("beat"),
            entries=[e for e in day["entries"] if e.get("t", "") < t],
            segments=[g for g in day.get("segments", []) if g["from"] < t])

    def route(self, day, i):
        """The row for one step with a recorded reply, or None."""
        s = day["steps"][i]
        v, dec = s.get("voice"), s.get("decision") or {}
        if not v or not dec.get("says"):
            return None
        f = self.facts(day, i)
        row = dict(day=day["date"], n=day["n"], t=s["t"], says=dec["says"], recorded=v["by"], present=f["present"])
        speaker = self.by_name.get(v["by"])
        if None in f["present"] or speaker is None or not f["present"]:
            return dict(row, reproducible=False, why="a person is not in the cast")
        off = voices.pick(self.cast, dec["says"], f["present"], recipient=dec.get("speaks_to") if dec.get("speaks_to") in f["present"] else None)
        row["off"] = off
        if off != speaker:
            return dict(row, reproducible=False, why=f"off-routing gives {off}, recorded {speaker}")
        on, rule = voices.route_repaired(self.cast, dec["says"], f["present"], False, f["purchases"], f["entries"], f["segments"], f["place"],
                                         dict(greeting=f["greeting"], needs=f["needs"] or []))
        if dec.get("speaks_to") in f["present"]:
            on, rule = dec["speaks_to"], "recipient"
        named = voices.addressed(self.cast, dec["says"], f["present"])
        found = voices.addressed_at(self.cast, dec["says"], f["present"])
        names = [c for c in f["present"] if voices.addressed(self.cast, dec["says"], [c])]
        return dict(row, reproducible=True, speaker=speaker, new=on, changed=on != speaker, rule=rule, names_a_present=bool(names),
                    new_is_named=on in names, recorded_is_named=speaker in names, first_named=named, addressed_names=sorted(found),
                    greeting=f["greeting"], greeting_held=f["greeting_held"], beat=f["beat"], purchases=f["purchases"])

    def dropped(self, day, i):
        s = day["steps"][i]
        v = s.get("voice")
        if not v or not v.get("does"):
            return None
        who = self.by_name.get(v["by"])
        kind = voices.does_flaw(self.cast[who], v["does"]) if who else None
        return dict(day=day["date"], t=s["t"], speaker=v["by"], does=v["does"], kind=kind) if kind else None

    def run(self, days):
        out = dict(days=[], changed=[], dropped=[], unreproducible=[])
        for day in days:
            seen = repro = changed = dropped = greetings = 0
            for i, s in enumerate(day["steps"]):
                if s.get("voice"):
                    seen += 1
                    r = self.route(day, i)
                    if r and r["reproducible"]:
                        repro += 1
                        if r["changed"]:
                            changed += 1
                            out["changed"].append(r)
                    elif r:
                        out["unreproducible"].append({k: r[k] for k in ("day", "t", "recorded", "why")})
                    d = self.dropped(day, i)
                    if d:
                        dropped += 1
                        out["dropped"].append(d)
                if self.facts(day, i)["greeting"]:
                    greetings += 1
            out["days"].append(dict(date=day["date"], n=day["n"], replies=seen, greetings=greetings, reproducible=repro, changed=changed, dropped=dropped))
        return out


def table(res):
    md = ["| Day | Date | Replies | Greetings | Reproducible | Speaker changed | `does` dropped |", "|---|---|---|---|---|---|---|"]
    for d in res["days"]:
        md.append(f"| {d['n']} | {d['date']} | {d['replies']} | {d['greetings']} | {d['reproducible']} | {d['changed']} | {d['dropped']} |")
    tot = {k: sum(d[k] for d in res["days"]) for k in ("replies", "greetings", "reproducible", "changed", "dropped")}
    md.append(f"| all | | {tot['replies']} | {tot['greetings']} | {tot['reproducible']} | {tot['changed']} | {tot['dropped']} |")
    md += ["", f"Not reproducible (left out of the counts): {len(res['unreproducible'])}.", "", "## Speakers that change", ""]
    for r in res["changed"]:
        md += [f"- {r['day']} {r['t']}: recorded {r['recorded']}, now {r['new']} (rule: {r['rule']}). "
               f"His words name a present person: {'yes' if r['names_a_present'] else 'no'}; the new speaker is that person: "
               f"{'yes' if r['new_is_named'] else 'no'}; the recorded speaker was named: {'yes' if r['recorded_is_named'] else 'no'}.",
               f"  Present: {', '.join(r['present'])}. Addressed names found: {', '.join(r['addressed_names']) or 'none'}.",
               f"  His words: {r['says']}"]
    md += ["", "## `does` lines dropped", ""] + [f"- {r['day']} {r['t']}, {r['speaker']} ({r['kind']}): {r['does']}" for r in res["dropped"]]
    if res["unreproducible"]:
        md += ["", "## Not reproducible", ""] + [f"- {r['day']} {r['t']}, {r['recorded']}: {r['why']}" for r in res["unreproducible"]]
    return "\n".join(md) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--ref")
    ap.add_argument("--docs")
    ap.add_argument("--days", default="0-999999")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    if bool(a.ref) == bool(a.docs):
        ap.error("give --ref or --docs")
    m = re.fullmatch(r"(\d+)(?:-(\d+))?", a.days)
    if not m:
        ap.error("--days is N or N-M")
    lo, hi = int(m.group(1)), int(m.group(2) or m.group(1))
    res = Replay().run(load_days(a.ref, a.docs, lo, hi))
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "replay.json").write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    (out / "replay.md").write_text(table(res), encoding="utf-8")
    print(table(res))


if __name__ == "__main__":
    main()
