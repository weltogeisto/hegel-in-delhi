"""The owl: at night the larger model writes up the day as Hegel's diary, revision log and, once a week, the Depesche."""
import re

from .contract import extract_json

STATUSES = ["unshaken", "shaken", "revised", "abandoned"]


class OwlError(Exception):
    pass


def schema(with_depesche):
    props = {
        "diary": {"type": "string"},
        "revision_log": {"type": "string"},
        "theses": {"type": "array", "items": {"type": "object", "properties": {
            "id": {"type": "string"}, "status": {"type": "string", "enum": STATUSES}}, "required": ["id", "status"]}},
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


def write(cfg, day, state, mind, depesche_n=None):
    system = (cfg.repo / "mind/owl.md").read_text(encoding="utf-8")
    theses = state.get("theses", [])
    ask = (f"{record(day)}\n\nYour theses: " + "; ".join(f"{t['id']}: {t['text']} ({t['status']})" for t in theses) + ".\n\n")
    if depesche_n is not None:
        ask += f"Tonight is also the night of the weekly Depesche, number {depesche_n}.\n\n"
    ask += "Write the diary, the revision log and the theses" + (", and the Depesche" if depesche_n is not None else "") + ". Answer with the JSON object only."
    messages = [{"role": "system", "content": system}, {"role": "user", "content": ask}]
    raw = mind.chat(messages, schema(depesche_n is not None), max_tokens=2200 if depesche_n is not None else 1200, temperature=0.8)
    out = extract_json(raw)
    if not isinstance(out, dict) or not isinstance(out.get("diary"), str) or len(out["diary"].strip()) < 80:
        raise OwlError("the owl's answer was unusable: " + (raw or "")[:200])
    by_id = {t["id"]: t for t in theses}
    for t in out.get("theses") or []:
        if isinstance(t, dict) and t.get("id") in by_id and t.get("status") in STATUSES:
            by_id[t["id"]]["status"] = t["status"]
    written = {"diary": out["diary"].strip(), "revision_log": (out.get("revision_log") or "").strip() or None}
    if depesche_n is not None and isinstance(out.get("depesche"), str) and out["depesche"].strip():
        written["depesche"] = {"n": depesche_n, "title": f"Depesche aus Delhi, Nr. {depesche_n}", "text": out["depesche"].strip()}
    return written
