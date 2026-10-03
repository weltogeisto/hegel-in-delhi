"""The people he meets answer him: who answers, what the voice is told, and what comes back."""
import re

from .contract import VOICE_ASK
from .memory import names_of
from .works import cut

SAY_CAP, DOES_CAP, EVENT_CAP = 420, 200, 600


def addressed(cast, says, present):
    """The person present whom `says` names first, or None."""
    hits = []
    for cid in present:
        c = cast[cid]
        terms = names_of(c) | ({re.sub(r"^the ", "", c["name"], flags=re.I)} if c.get("background") else set())
        m = re.search(r"\b(" + "|".join(re.escape(x) for x in terms) + r")\b", says or "", re.I)
        if m:
            hits.append((m.start(), cid))
    return min(hits)[1] if hits else None


def pick(cast, says, present):
    """Who answers: the one he names, else the first person present who is not background, else a background person."""
    return addressed(cast, says, present) or next((c for c in present if not cast[c].get("background")), None) \
        or (present[0] if present else None)


def render(c, sit, where, says, remember):
    """The user message for one voice. `where` is the place's name; `says` is what he said to them, or None when they speak first."""
    text = f"You are {c['name']}, {c['role']}." + (f" {c['card']}" if c.get("card") else "") + "\n\n"
    text += f"{sit['day']}, {sit['time']}, {where}. His outfit: {sit['outfit']}.\n"
    text += f"What is happening (told from his side, so 'you' there means him): {sit['event'][:EVENT_CAP]}\n"
    if remember:
        text += "\nWhat has passed between you and him:\n" + "".join(f"- {x}\n" for x in remember)
    text += f"\nHe says: “{says}”\n" if says else "\nYou have just caught sight of him. You speak first.\n"
    return text + "\n" + VOICE_ASK


def clean(c, out):
    """{by, says, does} from the voice's answer, or None if it is unusable."""
    says = " ".join(out["says"].split()).strip("\"“” ") if isinstance(out, dict) and isinstance(out.get("says"), str) else ""
    if len(says) < 2:
        return None
    does = " ".join(out["does"].split()) if isinstance(out.get("does"), str) else ""
    by = c["name"][0].upper() + c["name"][1:]
    return {"by": by, "says": cut(says, SAY_CAP), "does": cut(does, DOES_CAP).rstrip(".") + "." if does else None}


def heard(v):
    """The event line for what a person said, and what they did: 'Nidhi Rao says: “…” She pushes the book across.'"""
    return f"{v['by']} says: “{v['says']}”" + (f" {v['does']}" if v.get("does") else "")
