#!/usr/bin/env python3
"""The world's score, by week, from a night's futures (WORLD-3.md, "The score: the instrument first").

    python3 tools/world_score.py --futures <folder>/futures --from 2026-11-25 --out <folder>
    python3 tools/world_score.py --compare <folder A> <folder B> --from DATE --out <folder>     # two arms of one night

Each future is a folder `futures/<seed>/` whose `days/` holds the rehearsal's day files; days before --from only give the
day to count from. The complete days are cut into weeks of seven from --from (a last week of fewer than four days is
reported and marked short). For each week, six measures:

1. Brought: the mean number of moments a day that the world brought. "ok" at 6 or more.
2. Alike: the longest run of consecutive days whose variation from the day before is under 0.2, counting the days
   of the run that came in the weeks before. "ok" when no run of 3 or more ends in or passes through the week.
3. Threads: how many threads moved, each once a week: a change of the file's line, a newly fired beat that is not a
   repeat session (id with "@" or starting "session:"), and any opened kind in THREAD_KINDS. "ok" at 1 or more.
4. Fed: how many of the week's meals (breakfast, lunch, dinner a day) he had, and the share of 3 a day.
5. Came back: moments that opened with a kind in RETURN_KINDS; and the readings of the week that were used later: a
   `read` entry with a title whose content words (five letters or more) appear, at least two together, in one later
   thought or one later piece of writing within 14 days. Reported with the share (None without readings).
6. Chose: the offers shown, taken and declined in the week's funnel (`session:` ids ignored); and, across the future up
   to the week, how many offers were shown at least twice and answered the same way every time.

And one count beside them, for the task the world serves (WORLD-3.md, "The task"): Wrote, the sittings of the week, their
words, and how many manuscripts they belong to. It counts what he wrote and says nothing of its worth: that is read.

The score describes the world and names no target for him. The futures are evaluation material, never training data.
Standard library only; deterministic."""
import argparse
import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path
from statistics import mean

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools import night2_read  # noqa: E402

WEEK = 7
SHORT_BELOW = 4
BROUGHT_OK = 6
SAME = 0.2
SAME_RUN = 3
USE_DAYS = 14
THREAD_KINDS = {"undertaking", "story", "standing"}
RETURN_KINDS = {"trace", "undertaking", "standing", "story"}
MEALS = ("breakfast", "lunch", "dinner")
STOP = {"about", "after", "again", "against", "being", "could", "every", "first", "from", "have", "into", "other", "should",
        "since", "still", "their", "there", "these", "they", "this", "those", "through", "under", "until", "were", "what",
        "when", "where", "which", "while", "with", "within", "would", "your", "upon", "between", "because"}


def _kind(e):
    return e.get("k") or e.get("kind")


def _words(title):
    return {w for w in re.findall(r"[a-z]+", (title or "").lower()) if len(w) >= 5 and w not in STOP}


def _repeat(beat):
    return "@" in beat or beat.startswith("session:")


def load(folder, start):
    """(rows, raw days, the file line before the first day) of one future; complete days only, in date order."""
    folder = Path(folder)
    days_dir = folder / "days" if (folder / "days").is_dir() else folder
    rows = {r["date"]: r for r in night2_read.day_rows(folder, start)}
    paths = sorted(days_dir.glob("????-??-??.json"))
    prior = [p for p in paths if p.stem < start]
    before = json.loads(prior[-1].read_text(encoding="utf-8")) if prior else None
    raw = [json.loads(p.read_text(encoding="utf-8")) for p in paths if p.stem >= start]
    raw = [d for d in raw if d.get("complete") and d["date"] in rows]
    return [rows[d["date"]] for d in raw], raw, ((before or {}).get("state") or {}).get("file")


def _day_text(d, after=None):
    """The thoughts and the writings of a day; with `after` (a clock time) only those after it."""
    out = []
    for s in d.get("steps") or []:
        th = (s.get("decision") or {}).get("thought")
        if th and (after is None or (s.get("t") or "") > after):
            out.append(th)
    for e in d.get("entries") or []:
        if _kind(e) == "writing" and e.get("text") and (after is None or (e.get("t") or "") > after):
            out.append(e["text"])
    return out


def _used(raw, i, entry):
    """Whether the reading in day i's entry came back: two of its title words together in a later thought or writing."""
    words = _words(entry.get("title"))
    if len(words) < 2:
        return False
    day = date.fromisoformat(raw[i]["date"])
    t = entry.get("t")
    for j in range(i, len(raw)):
        if date.fromisoformat(raw[j]["date"]) > day + timedelta(days=USE_DAYS):
            break
        if j == i and not t:
            continue
        for text in _day_text(raw[j], t if j == i else None):
            if len(words & set(re.findall(r"[a-z]+", text.lower()))) >= 2:
                return True
    return False


def score_future(rows, raw, file_before):
    """The weeks of one future: a list of dicts, one per week."""
    n = len(rows)
    run, runs = 0, []
    for r in rows:
        run = run + 1 if r["variation"] is not None and r["variation"] < SAME else 0
        runs.append(run)
    files = [file_before] + [r["file"] for r in rows]
    funnel_total = {}
    weeks = []
    for w0 in range(0, n, WEEK):
        idx = range(w0, min(w0 + WEEK, n))
        days = len(idx)
        wk = {"week": w0 // WEEK + 1, "from": rows[w0]["date"], "to": rows[idx[-1]]["date"], "days": days, "short": days < SHORT_BELOW}
        b = mean(rows[i]["brought"] for i in idx)
        wk["brought"] = {"mean": round(b, 2), "ok": b >= BROUGHT_OK}
        longest = max(runs[i] for i in idx)
        wk["alike"] = {"longest_run": longest, "ok": longest < SAME_RUN}
        moved = []
        for i in idx:
            if files[i + 1] is not None and files[i + 1] != files[i]:
                moved.append(f"file: {files[i + 1]}")
            moved += [f"beat: {x}" for x in rows[i]["beats"] if not _repeat(x)]
            for s in raw[i].get("steps") or []:
                moved += [k for k in s.get("opened") or [] if k in THREAD_KINDS]
        wk["threads"] = {"count": len(moved), "moved": moved, "ok": len(moved) >= 1}
        meals = sum(1 for i in idx for m in MEALS if ((raw[i].get("state") or {}).get("today") or {}).get(m))
        wk["fed"] = {"meals": meals, "of": 3 * days, "share": round(meals / (3 * days), 3)}
        returns = sum(1 for i in idx for s in raw[i].get("steps") or [] if RETURN_KINDS & set(s.get("opened") or []))
        readings = used = 0
        for i in idx:
            for e in raw[i].get("entries") or []:
                if _kind(e) == "read" and e.get("title"):
                    readings += 1
                    used += _used(raw, i, e)
        wk["came_back"] = {"returns": returns, "readings": readings, "used": used,
                           "used_share": round(used / readings, 3) if readings else None}
        shown = yes = no = 0
        for i in idx:
            for oid, f in (raw[i].get("funnel") or {}).items():
                if oid.startswith("session:"):
                    continue
                s_, y_, n_ = f.get("shown") or 0, f.get("yes") or 0, f.get("no") or 0
                shown, yes, no = shown + s_, yes + y_, no + n_
                t = funnel_total.setdefault(oid, [0, 0, 0])
                t[0], t[1], t[2] = t[0] + s_, t[1] + y_, t[2] + n_
        same = sorted(o for o, (s_, y_, n_) in funnel_total.items() if s_ >= 2 and (y_ == s_ or n_ == s_))
        wk["chose"] = {"shown": shown, "taken": yes, "declined": no, "same_answer_every_time": len(same), "same_answer_ids": same}
        wrote = [e for i in idx for e in raw[i].get("entries") or [] if _kind(e) == "writing" and e.get("text")]
        wk["wrote"] = {"sittings": len(wrote), "words": sum(e.get("words") or len(e["text"].split()) for e in wrote),
                       "manuscripts": len({e.get("work") or e.get("title") for e in wrote})}
        weeks.append(wk)
    return weeks


def score_folder(futures_dir, start):
    out = {}
    for p in sorted(Path(futures_dir).iterdir()):
        if p.is_dir():
            rows, raw, fb = load(p, start)
            out[p.name] = score_future(rows, raw, fb) if rows else []
    return out


def _futures_dir(folder):
    folder = Path(folder)
    return folder / "futures" if (folder / "futures").is_dir() else folder


def _ok(x):
    return "ok" if x else "no"


def _share(x):
    return "–" if x is None else f"{100 * x:.0f}%"


def render(scores, title="The world's score"):
    lines = [f"# {title}", "", "The world is scored, not him. Evaluation only; never training data.", ""]
    for seed, weeks in sorted(scores.items()):
        lines += [f"## Future {seed}", ""]
        if not weeks:
            lines += ["No complete days.", ""]
            continue
        lines += ["| Week | Brought | Alike | Threads | Fed | Came back | Chose |", "|---|---:|---:|---:|---:|---:|---:|"]
        for w in weeks:
            c, ch = w["came_back"], w["chose"]
            tag = f" (short, {w['days']}d)" if w["short"] else ""
            lines.append(f"| {w['week']}{tag} | {w['brought']['mean']:.1f} {_ok(w['brought']['ok'])} | "
                         f"{w['alike']['longest_run']}d {_ok(w['alike']['ok'])} | {w['threads']['count']} {_ok(w['threads']['ok'])} | "
                         f"{w['fed']['meals']}/{w['fed']['of']} {_share(w['fed']['share'])} | "
                         f"{c['returns']} back, {c['used']}/{c['readings']} used | "
                         f"{ch['taken']}/{ch['shown']} taken, {ch['same_answer_every_time']} same |")
        lines.append("")
        for w in weeks:
            if w["threads"]["moved"]:
                lines.append(f"- Week {w['week']} threads: " + "; ".join(w["threads"]["moved"]))
        lines.append("- Wrote, by week: " + "; ".join(f"{w['wrote']['sittings']} sitting{'' if w['wrote']['sittings'] == 1 else 's'}, "
                                                    f"{w['wrote']['words']:,} words" for w in weeks) + ".")
        full = [w for w in weeks if not w["short"]] or weeks
        w5 = next((w for w in full if w["week"] == 5), full[-1])
        lines += ["", f"Week {w5['week']}: brought {_ok(w5['brought']['ok'])}, alike {_ok(w5['alike']['ok'])}, "
                      f"threads {_ok(w5['threads']['ok'])}.", ""]
    return "\n".join(lines)


SCALARS = (("brought", lambda w: w["brought"]["mean"]), ("alike (longest run)", lambda w: w["alike"]["longest_run"]),
           ("threads", lambda w: w["threads"]["count"]), ("fed (meals)", lambda w: w["fed"]["meals"]),
           ("came back (moments)", lambda w: w["came_back"]["returns"]), ("readings used (share)", lambda w: w["came_back"]["used_share"]),
           ("offers shown", lambda w: w["chose"]["shown"]), ("offers taken", lambda w: w["chose"]["taken"]),
           ("same answer every time", lambda w: w["chose"]["same_answer_every_time"]),
           ("wrote (sittings)", lambda w: w["wrote"]["sittings"]), ("wrote (words)", lambda w: w["wrote"]["words"]))


def compare(a, b):
    """Per measure and week: mean over the matched futures of arm A, of arm B, and B minus A."""
    seeds = sorted(set(a) & set(b))
    res = {"matched": seeds, "measures": {}}
    most = max([len(a[s]) for s in seeds] + [len(b[s]) for s in seeds] + [0])
    for name, get in SCALARS:
        rows = []
        for wk in range(1, most + 1):
            va = [get(a[s][wk - 1]) for s in seeds if len(a[s]) >= wk and get(a[s][wk - 1]) is not None]
            vb = [get(b[s][wk - 1]) for s in seeds if len(b[s]) >= wk and get(b[s][wk - 1]) is not None]
            ma, mb = (mean(va) if va else None), (mean(vb) if vb else None)
            rows.append({"week": wk, "A": ma, "B": mb, "B_minus_A": None if ma is None or mb is None else mb - ma})
        res["measures"][name] = rows
    return res


def render_compare(res, na, nb):
    f = lambda x: "–" if x is None else f"{x:.2f}"
    lines = ["# Two arms compared", "",
             f"{len(res['matched'])} futures matched by seed ({', '.join(res['matched']) or 'none'}; {na} in A, {nb} in B). "
             "Two or three futures a side are a read, not a test, and no significance is claimed.", ""]
    for name, rows in res["measures"].items():
        lines += [f"## {name}", "", "| Week | A | B | B minus A |", "|---:|---:|---:|---:|"]
        lines += [f"| {r['week']} | {f(r['A'])} | {f(r['B'])} | {f(r['B_minus_A'])} |" for r in rows]
        lines.append("")
    return "\n".join(lines)


def _write(out, scores, title):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "SCORE.md").write_text(render(scores, title), encoding="utf-8")
    (out / "score.json").write_text(json.dumps(scores, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--futures")
    ap.add_argument("--compare", nargs=2, metavar=("A", "B"))
    ap.add_argument("--from", dest="start", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    out = Path(a.out)
    if a.compare:
        arms = [score_folder(_futures_dir(f), a.start) for f in a.compare]
        for name, sc in zip("AB", arms):
            _write(out / name, sc, f"The world's score, arm {name}")
        res = compare(*arms)
        (out / "COMPARE.md").write_text(render_compare(res, len(arms[0]), len(arms[1])), encoding="utf-8")
        (out / "score.json").write_text(json.dumps({"A": arms[0], "B": arms[1], "compare": res}, ensure_ascii=False, indent=1,
                                                   sort_keys=True) + "\n", encoding="utf-8")
        print(f"matched futures: {', '.join(res['matched']) or 'none'}")
        return 0
    if not a.futures:
        ap.error("--futures or --compare is required")
    scores = score_folder(a.futures, a.start)
    _write(out, scores, "The world's score")
    print(json.dumps({s: len(w) for s, w in scores.items()}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
