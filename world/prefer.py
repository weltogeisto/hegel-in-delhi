"""T49: a preference among his own answers (HEGEL_DECISION_DRAWS, off at 1).

The mind is asked the same question up to N times, one reply at a time. His decision is the first reply that the
world accepts and that is fresh: it shares no four-word phrase (report.grams, T9's rule) with a thought the prompt
shows under "Earlier today". If no reply is fresh, the first accepted one stands, so a phrase he needs comes back
whenever every answer uses it. If none is accepted, the first reply goes to the world's refusal loop as before.
Nothing is refused for its wording, and no model judges anything."""
import re

from .report import grams

SHOWN_THOUGHT = re.compile(r"; you thought: “(.*)”$")


def shown_thoughts(earlier):
    """The thoughts the prompt shows: the first sentence of each recent step, as World.situation writes its lines."""
    out = []
    for line in earlier or []:
        m = SHOWN_THOUGHT.search(line.split(" Engine note: ", 1)[0])
        if m:
            out.append(m.group(1))
    return out


def fresh(thought, shown):
    said = grams(thought or "")
    return not any(said & grams(t) for t in shown)


def choose(draw, check, shown, draws, away=Exception):
    """draw() -> a raw reply; check(raw) -> (errors, thought). Returns (the chosen reply, a note for the record).

    The note counts the replies drawn, those the world refused, those that echoed, and which one was picked. A mind
    that goes away after its first reply ends the drawing; what it has said so far is used."""
    first = held = None
    note = {"n": 0, "refused": 0, "echo": 0}
    for i in range(draws):
        try:
            raw = draw()
        except away:
            if first is None:
                raise
            note["cut_short"] = True
            break
        note["n"] += 1
        if first is None:
            first = raw
        errors, thought = check(raw)
        if errors:
            note["refused"] += 1
            continue
        if fresh(thought, shown):
            return raw, dict(note, picked=i)
        note["echo"] += 1
        if held is None:
            held = (raw, i)
    raw, i = held if held else (first, 0)
    return raw, dict(note, picked=i)
