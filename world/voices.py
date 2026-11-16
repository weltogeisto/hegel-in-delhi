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


def _words(says, terms):
    """True if one of the plain lowercase `terms` stands in `says` as a word (a plural s or es allowed)."""
    return any(re.search(r"\b" + re.escape(t) + r"(?:s|es)?\b", says or "", re.I) for t in terms)


def seller_of(cast, text, present):
    """The first person present whose `sells` words (cast.json) occur in `text`, or None."""
    return next((c for c in present if _words(text, cast[c].get("sells", []))), None)


def last_spoken(cast, entries, segments, place, present):
    """The person present he last spoke with at `place` today: the last of the day's words either way, from the records.

    Entries carry no place of their own, so the place is the segment that holds the minute; a minute no segment holds yet
    is the step under way, which is here.
    """
    names = {cast[c]["name"][0].upper() + cast[c]["name"][1:]: c for c in present}
    def here(t):
        seg = next((s for s in segments or [] if s.get("from", "") <= t < s.get("to", "")), None)
        return seg is None or seg.get("at") == place
    for e in reversed(entries or []):
        if e.get("k") != "said":
            continue
        cid = e.get("to_id") if e.get("to_id") in present else names.get(e.get("by"))
        if cid and here(e.get("t", "")):
            return cid
    return None


def pick(cast, says, present, recipient=None, facts=False, purchases=None, entries=None, segments=None, place=None):
    """An explicit present recipient takes precedence; legacy speech keeps its fallback.

    With `facts` on, when his words name no one the answer comes from the person whose trade the words concern, or whom
    he bought from in this step, then the one he last spoke with here today, then the legacy fallback.
    """
    if recipient is not None:
        if recipient not in cast or recipient not in present:
            raise ValueError("explicit speech recipient is not present")
        return recipient
    named = addressed(cast, says, present)
    if named:
        return named
    if facts:
        trade = seller_of(cast, says, present) or next(
            (c for x in purchases or [] if (c := seller_of(cast, str(x.get("item", "")), present))), None)
        if trade:
            return trade
        last = last_spoken(cast, entries, segments, place, present)
        if last:
            return last
    return next((c for c in present if not cast[c].get("background")), None) or (present[0] if present else None)


def recorded_facts(world, cid, state, voice_facts=False):
    """Only world facts this speaker handles; never Hegel's private thoughts.

    These are the state before this exchange. Checked current payments are
    passed separately, so a ready garment may be collected in the same step.
    A recurring bill's due day is not evidence of a visit or delivery date.
    """
    facts = []
    if cid == "masterji":
        flag = state.get("flags", {}).get("bandhgala")
        status = {"ordered": "ordered; not yet ready for collection",
                  "ready": "ready for collection; not yet collected",
                  "collected": "already collected; do not charge for the same order again"}.get(flag)
        if status:
            garment = next((g for g in state.get("wardrobe", []) if g.get("id") == "bandhgala"), {})
            facts.append("Your bandhgala order for him: " + status + ". " + garment.get("status", ""))
    if cid in {"ramesh", "dhobi"}:
        cost = next((c for c in world.costs if c.get("id") == "dhobi"), None)
        if cost:
            due = cost.get("when", {}).get("weekday")
            facts.append(f"The recorded household washing charge is ₹{cost['amount']:,}" +
                         (f", due each {due}" if due else "") +
                         ". This is a billing schedule, not a confirmed collection or delivery visit.")
            if "owed" in state:
                balance = sum(o["amount"] for o in state["owed"] if o.get("cost") == "dhobi")
                facts.append(f"The current recorded unpaid washing balance is ₹{balance:,}. " +
                             ("Do not request payment for a settled or not-yet-due charge." if balance == 0 else
                              "Only this recorded balance remains due; do not add a second charge."))
    if voice_facts and cid == "hegde":
        facts += hegde_facts(state)
    if voice_facts and cid == "saxena":
        facts += saxena_facts(world, state)
    return facts


def hegde_facts(state):
    """Shri Hegde's side of the record: where he lives, the file, whether he called. No date: the state keeps none for the gate."""
    beats = state.get("beats", [])
    facts = ["You live in the second bedroom of the bungalow, because the Professor agreed at the gate."
             if state.get("flags", {}).get("hegde_lodger") else
             "You are staying at the guest house in Chanakyapuri. You do not live at the bungalow."]
    if state.get("file"):
        facts.append("The Directorate's word on the file today: " + state["file"])
    if "hegde_call" in beats:
        facts.append("You called at the bungalow at ten, in person, and the Professor received you.")
    elif "hegde_card" in beats:
        facts.append("You called at ten and found no one at home; you waited twenty minutes on the verandah and left your card.")
    return facts


def saxena_facts(world, state):
    """Mr. Saxena's side: the file's status line, what is queried and owed at his desk, what falls due there."""
    facts = []
    if state.get("file"):
        facts.append("The file's status line today: " + state["file"])
    if "owed" in state:
        owed = [o for o in state["owed"] if o.get("with") == "saxena"]
        facts += [f"Owed and queried at your desk: ₹{o['amount']:,}, {o.get('why', 'unspecified')}" +
                  (f", since {o['since']}" if o.get("since") else "") + "." for o in owed]
        if not owed:
            facts.append("Nothing is recorded as queried or owed at your desk.")
    for a in state.get("appointments", []):
        beat = next((b for b in world.beats if b["id"] == a.get("beat")), {})
        if "saxena" in beat.get("needs", []) or beat.get("where") == "estates":
            facts.append(f"Due at your desk: {a['what']}, on {a['date']}" + (f" at {a['t']}" if a.get("t") else "") + ".")
    return facts


def paid_here(place, entries, limit=6):
    """His settled purchases earlier today at this place, from the day's records, so a seller does not ask twice.

    A voice remembers only what was said; without this, a seller who named a
    price asks for it again in the next exchange, and he pays twice.
    """
    goods = {s["item"] for s in place.get("sells", [])}
    paid = [f"{e['t']} {e['item']} ₹{e['price']:,}" for e in entries
            if e.get("k") == "bag" and e.get("item") in goods and type(e.get("price")) in (int, float)]
    if not paid:
        return []
    return ["He has already paid at this place today, and these are settled: " + "; ".join(paid[-limit:]) +
            ". Do not ask for them again; ask only for anything new he takes now."]


def render(c, sit, where, says, remember, first_meeting=None, purchases=None, meal_status=None, world_facts=None, voice_facts=False):
    """The user message for one voice. `where` is the place's name; `says` is what he said to them, or None when they speak first."""
    text = f"You are {c['name']}, {c['role']}." + (f" {c['card']}" if c.get("card") else "")
    if voice_facts and c.get("pronoun"):
        who = c["name"][0].upper() + c["name"][1:]
        text += f" {who} is a {'woman' if c['pronoun'] == 'she' else 'man'}: {'she, her' if c['pronoun'] == 'she' else 'he, him'}."
    text += "\n\n"
    text += f"{sit['day']}, {sit['time']}, {where}. His outfit: {sit['outfit']}.\n"
    text += "You are speaking here, at this current place. The event may also quote words spoken earlier somewhere else; those words do not move you or this place.\n"
    if sit.get("weather"):
        text += f"Current observed weather: {sit['weather']}. Earlier weather is unknown unless supplied in the history; do not invent a weather history.\n"
    if meal_status is not None:
        text += (f"Household meal currently served by the world: {meal_status}. "
                 "This is the authoritative current service status. Do not invent a completed meal service; you may offer future preparation.\n")
    if world_facts:
        text += "Recorded facts within your role, before this exchange (authoritative over conflicting dialogue; checked current payments below still apply):\n" + "".join(f"- {fact}\n" for fact in world_facts)
    if first_meeting is True:
        text += "Relationship: this is your first encounter with him. Do not invent a previous order, visit, payment or promise between you.\n"
    elif first_meeting is False:
        text += "Relationship: you have met him. Only the history supplied below establishes what passed between you; do not invent additional encounters or agreements.\n"
    if "for_sale" in sit:
        text += "Listed goods and prices here: " + ("; ".join(sit["for_sale"]) or "none listed") + ". Do not replace these prices with invented ones.\n"
    if purchases is not None:
        if purchases:
            text += "This exchange includes these purchases/payments at the recorded prices: " + "; ".join(
                f"{x['item']} ₹{x['price']:,}" for x in purchases) + ". Do not charge or request payment for these items a second time, or invent another transaction.\n"
        else:
            text += "No payment or purchase is recorded for this exchange. His words may request or promise it; do not narrate taking money or a completed paid handover. You may discuss terms, ask for payment or make an ordinary gesture.\n"
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
