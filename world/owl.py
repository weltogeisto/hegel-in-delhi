"""The owl: at night the larger model writes up the day as Hegel's diary, revision log and, once a week, the Depesche."""
import logging
import re

from .contract import extract_json

log = logging.getLogger("world")
STATUSES = ["unshaken", "shaken", "revised", "abandoned"]
KINDS = ["diary", "said", "writing", "work", "read", "world", "file", "people", "income", "expense", "bag", "wear", "plan"]      # which entry speaks for a minute
WRITING = 400                          # characters of each sitting that the owl reads


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


def record(day, limit=24000):
    """The day as the owl reads it: plain lines, oldest first."""
    lines = [f"Day {day['n']}, {day['title']}" + (f", {day['holiday']}" if day.get("holiday") else "") + "."]
    for e in day["entries"]:
        k = e["k"]
        if k == "diary":
            lines.append(f"{e['t']} thought: {e['text']}")
        elif k == "said" and e.get("by"):
            lines.append(f"{e['t']} {e['by']} said to you: “{e['text']}”")
        elif k == "said":
            lines.append(f"{e['t']} said{' to ' + e['to'] if e.get('to') else ''}: “{e['text']}”")
        elif k == "writing":
            text = re.sub(r"\s+", " ", e["text"]).strip()
            lines.append(f"{e['t']} wrote “{e['title']}” ({e['kind']}{' to ' + e['to'] if e.get('to') else ''}, sitting {e['sitting']}): "
                         + (text if len(text) <= WRITING else text[:WRITING].rsplit(' ', 1)[0] + "…"))
        elif k in ("world", "file"):
            lines.append(f"{e['t']} happened: {e['text']}")
        elif k == "bag":
            lines.append(f"{e['t']} bought: {e['item']}, ₹{e['price']}")
        elif k in ("income", "expense"):
            lines.append(f"{e['t']} {'earned' if k == 'income' else 'paid'}: {e['item']}, ₹{e['amount']:,}" + (" (a cheque, not cashed)" if e.get("cheque") else ""))
        elif k == "read":
            medium = "read" if e.get("source_sha256") else "read on his phone"
            lines.append(f"{e['t']} {medium}, from {e['source']}, “{e['title']}”: {e['text']}")
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
    lines.extend(closing_record(day))
    text = "\n".join(lines)
    return text if len(text) <= limit else fit_record(lines, limit)


def closing_record(day):
    """Canonical outcomes from this day, separately from anyone's claims."""
    state = day.get("state") or {}
    if not state:
        return []
    lines = ["Recorded state at this day's close (authoritative for possessions and transactions; dialogue, plans and manuscripts do not by themselves change these outcomes):"]
    if "imprest" in state:
        lines.append(f"Recorded cash: ₹{state['imprest']:,}.")
    for item in state.get("wardrobe") or []:
        lines.append(f"Recorded wardrobe: {item['item']}: {item['status']}.")
    if state.get("wearing"):
        lines.append(f"Recorded clothing worn: {state['wearing']}.")
    if state.get("file"):
        lines.append("Recorded Directorate file status: " + state['file'])
    if "steps" in day:
        meals = [s['t'] + (f"–{s['end']}" if s.get('end') else "") + f" at {s['decision']['place']}"
                 for s in day["steps"] if (s.get("decision") or {}).get("action") == "eat"]
        if meals or day.get("complete"):
            lines.append("Recorded eating actions: " + ("; ".join(meals) if meals else
                         "none in this completed day's step log") + ".")
            lines.append("Offers, plans and purchases alone do not establish an eating action.")
    readings = [e for e in day.get("entries", []) if e.get("k") == "read"]
    for e in readings:
        lines.append(f"Reading actually delivered at {e['t']}: {e['source']}, {e['title']}" + (f"; {e['work']}, {e.get('ref', '')}" if e.get('work') else "") + ".")
    return lines


def fit_record(lines, limit):
    """Shorten long entries across the entire chronology, never just drop its end.

    A timestamp and attribution still precede each excerpt. If the budget cannot
    even represent every entry, fail explicitly instead of writing a diary from
    an undisclosed partial day. Full source entries remain in the day file.
    """
    notice = "[Long entries shortened; every recorded event is represented below.]"
    flat = [re.sub(r"\s+", " ", line).strip() for line in lines]

    def fitted(cap):
        return "\n".join([notice] + [line if len(line) <= cap else line[:cap - 1].rstrip() + "…" for line in flat])

    low, high = 48, max(map(len, flat), default=48)
    if len(fitted(low)) > limit:
        raise OwlError(f"The day's {len(lines)} record lines cannot fit in the {limit}-character owl budget; no diary generated.")
    while low < high:
        mid = (low + high + 1) // 2
        if len(fitted(mid)) <= limit:
            low = mid
        else:
            high = mid - 1
    return fitted(low)


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
    elif k in ("income", "expense"):
        text = f"{e['item']}, ₹{e['amount']:,}"
    elif k == "read":
        text = f"{e['title']}: {e['text']}"
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


def write(cfg, day, state, mind, depesche_n=None, problems=None, flag=None, topic=None):
    system = (cfg.repo / "mind/owl.md").read_text(encoding="utf-8")
    theses = state.get("theses", [])
    ask = (f"{record(day)}\n\nYour theses: " + "; ".join(f"{t['id']}: {t['text']} ({t['status']})" for t in theses) + ".\n\n")
    if depesche_n is not None:
        ask += f"Tonight is also the night of the weekly Depesche, number {depesche_n}.\n\n"
    ask += "Write the diary, the revision log and the theses (each with its evidence times)" + (", and the Depesche" if depesche_n is not None else "") + ". Answer with the JSON object only."
    messages = [{"role": "system", "content": system}, {"role": "user", "content": ask}]
    for attempt in range(2):
        budget = getattr(cfg, "owl_reasoning_tokens", 0)
        kwargs = {"max_tokens": (2200 if depesche_n is not None else 1200) + budget, "temperature": 0.8}
        if budget:
            kwargs["reasoning_budget"] = budget
        raw = mind.chat(messages, schema(depesche_n is not None), **kwargs)
        out = extract_json(raw)
        if not isinstance(out, dict) or not isinstance(out.get("diary"), str) or len(out["diary"].strip()) < 80:
            raise OwlError("the owl's answer was unusable: " + (raw or "")[:200])
        texts = [out.get(k) for k in ("diary", "revision_log", "depesche") if isinstance(out.get(k), str)]
        wrong = sorted(set(problems("\n".join(texts)))) if problems else []
        if not wrong:
            break
        if attempt:
            raise OwlError("the owl wrote what he could not know in 1831: " + "; ".join(wrong))
        messages += [{"role": "assistant", "content": raw},
                     {"role": "user", "content": "Write it again without " + "; ".join(wrong) + ". Answer with the JSON object only."}]
    written = {"diary": out["diary"].strip(), "revision_log": (out.get("revision_log") or "").strip() or None,
               "theses": revise(day, theses, out.get("theses"))}
    if depesche_n is not None and isinstance(out.get("depesche"), str) and out["depesche"].strip():
        written["depesche"] = {"n": depesche_n, "title": f"Depesche aus Delhi, Nr. {depesche_n}", "text": out["depesche"].strip()}
    texts = {"diary": written["diary"], "revision_log": written["revision_log"], "depesche": (written.get("depesche") or {}).get("text")}
    why = {k: flag(text) for k, text in texts.items() if flag and text and flag(text)}
    if why:
        written["sensitive"], written["why"] = list(why), why           # the page veils these sections
        if topic:
            written["topic"] = {k: topic(v) for k, v in why.items()}
    return written
