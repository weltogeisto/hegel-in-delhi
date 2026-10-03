"""The owl: at night the larger model writes up the day as Hegel's diary, revision log and, once a week, the Depesche."""
import logging
import re

from .contract import extract_json

log = logging.getLogger("world")
STATUSES = ["unshaken", "shaken", "revised", "abandoned"]
KINDS = ["diary", "said", "work", "world", "file", "people", "bag", "wear", "plan"]      # which entry speaks for a minute


class OwlError(Exception):
    pass


def schema(with_depesche):
    props = {
        "diary": {"type": "string"},
        "revision_log": {"type": "string"},
        "theses": {"type": "array", "items": {"type": "object", "properties": {
            "id": {"type": "string"}, "status": {"type": "string", "enum": STATUSES},
            "evidence": {"type": "array", "items": {"type": "string"}}}, "required": ["id", "status", "evidence"]}},
    }
    if with_depesche:
        props["depesche"] = {"type": "string"}
    return {"type": "object", "properties": props, "required": list(props)}


def record(day, limit=9000):
    """The day as the owl reads it: plain lines, oldest first."""
    lines = [f"Day {day['n']}, {day['title']}" + (f", {day['holiday']}" if day.get("holiday") else "") + "."]
    for e in day["entries"]:
        k = e["k"]
        if k == "diary":
            lines.append(f"{e['t']} thought: {e['text']}")
        elif k == "said":
            lines.append(f"{e['t']} said{' to ' + e['to'] if e.get('to') else ''}: “{e['text']}”")
        elif k in ("world", "file"):
            lines.append(f"{e['t']} happened: {e['text']}")
        elif k == "bag":
            lines.append(f"{e['t']} bought: {e['item']}, ₹{e['price']}")
        elif k == "people":
            lines.append(f"{e['t']} met for the first time: {e['name']}, {e['role']}")
        elif k == "work":
            lines.append(f"{e['t']} {e['title'].lower()}: {e['text']}")
        elif k == "wear":
            lines.append(f"{e['t']} wardrobe: {e['item']}. {e['status']}")
        elif k == "plan":
            lines.append(f"{e['t']} planned: " + "; ".join(f"{i['time']} {i['intention']}" for i in e["items"]))
    places = [s for s in day["segments"] if s["mode"] == "walk"]
    if places:
        lines.append("Walks: " + "; ".join(f"{s['from']} {s['a']} to {s['b']}" for s in places) + ".")
    text = "\n".join(lines)
    return text if len(text) <= limit else text[:limit] + "\n[record cut short]"


def gist(diary, n=320):
    """A short memory of yesterday for the day mind."""
    if not diary:
        return None
    text = re.sub(r"\s+", " ", diary).strip()
    if len(text) <= n:
        return text
    cut = text[:n]
    return cut[:cut.rfind(" ")] + " …"


def entry_text(e, n=160):
    """What an entry says, plain and cut short."""
    k = e["k"]
    if k == "bag":
        text = f"{e['item']}, ₹{e['price']}"
    elif k == "wear":
        text = f"{e['item']}. {e['status']}"
    elif k == "plan":
        text = " · ".join(f"{i['time']} {i['intention']}" for i in e["items"])
    else:
        text = e.get("text") or ""
    text = re.sub(r"\s+", " ", text).strip()
    return text if len(text) <= n else text[:n - 1].rsplit(" ", 1)[0] + "…"


def evidence(day, times):
    """What the times the owl cites point to in the day's entries: [{t, text}], at most three.
    Where several entries share a minute, the one that speaks first in KINDS."""
    out = []
    for x in times if isinstance(times, list) else []:
        m = re.match(r"\s*(\d{1,2}):(\d{2})\s*$", x) if isinstance(x, str) else None
        t = f"{int(m.group(1)):02d}:{m.group(2)}" if m else None
        here = sorted((e for e in day["entries"] if e["t"] == t), key=lambda e: KINDS.index(e["k"]) if e["k"] in KINDS else 99)
        if here and t not in [v["t"] for v in out]:
            out.append({"t": t, "text": entry_text(here[0])})
    return out[:3]


def revise(day, theses, answer):
    """Apply the owl's statuses. A thesis changes only if the owl names a time that matches an entry of the day.
    Returns the changes that were applied."""
    by_id, changes = {t["id"]: t for t in theses}, []
    for a in answer or []:
        t = by_id.get(a.get("id")) if isinstance(a, dict) else None
        if not t or a.get("status") not in STATUSES or a["status"] == t["status"]:
            continue
        proof = evidence(day, a.get("evidence"))
        if not proof:
            log.warning("owl: '%s' %s → %s has no evidence in the day's record; the status stays", t["id"], t["status"], a["status"])
            continue
        changes.append({"id": t["id"], "from": t["status"], "to": a["status"], "evidence": proof})
        t["status"] = a["status"]
    return changes


def write(cfg, day, state, mind, depesche_n=None, problems=None):
    system = (cfg.repo / "mind/owl.md").read_text(encoding="utf-8")
    theses = state.get("theses", [])
    ask = (f"{record(day)}\n\nYour theses: " + "; ".join(f"{t['id']}: {t['text']} ({t['status']})" for t in theses) + ".\n\n")
    if depesche_n is not None:
        ask += f"Tonight is also the night of the weekly Depesche, number {depesche_n}.\n\n"
    ask += "Write the diary, the revision log and the theses (each with its evidence times)" + (", and the Depesche" if depesche_n is not None else "") + ". Answer with the JSON object only."
    messages = [{"role": "system", "content": system}, {"role": "user", "content": ask}]
    for attempt in range(2):
        raw = mind.chat(messages, schema(depesche_n is not None), max_tokens=2200 if depesche_n is not None else 1200, temperature=0.8)
        out = extract_json(raw)
        if not isinstance(out, dict) or not isinstance(out.get("diary"), str) or len(out["diary"].strip()) < 80:
            raise OwlError("the owl's answer was unusable: " + (raw or "")[:200])
        texts = [out.get(k) for k in ("diary", "revision_log", "depesche") if isinstance(out.get(k), str)]
        wrong = sorted(set(problems("\n".join(texts)))) if problems else []
        if not wrong:
            break
        if attempt:
            raise OwlError("the owl wrote what the page will not publish: " + "; ".join(wrong))
        messages += [{"role": "assistant", "content": raw},
                     {"role": "user", "content": "Write it again without " + "; ".join(wrong) + ". Answer with the JSON object only."}]
    written = {"diary": out["diary"].strip(), "revision_log": (out.get("revision_log") or "").strip() or None,
               "theses": revise(day, theses, out.get("theses"))}
    if depesche_n is not None and isinstance(out.get("depesche"), str) and out["depesche"].strip():
        written["depesche"] = {"n": depesche_n, "title": f"Depesche aus Delhi, Nr. {depesche_n}", "text": out["depesche"].strip()}
    return written
