"""His correspondent (HEGEL_CORRESPONDENT, data/correspondent.json, pc/CORRESPONDENT.md): a descendant of Niethammer's
family writes from Munich. Niethammer himself died in 1848 and stays dead.

The state carries `post` only while the switch is on, so without it nothing here runs and nothing changes:
  - outbox: letters to her he wrote and that go to the post the next morning;
  - sent: letters on their way, each with the day its answer is due;
  - letters: the correspondence so far, both ways, newest last, a few kept in full;
  - deliver: a letter from her that has come and is shown in the next situation.
Her first letter comes with money: what he owes and `gift` rupees besides, paid into his purse; the world's
own settling then pays his creditors where they can be reached. Her letters are one model call each, from his card and the correspondence. They are world content, never
training data."""
import json
from datetime import date, timedelta
from pathlib import Path

DATA = Path(__file__).resolve().parent / "data"
KEEP, PROMPT_CHARS = 8, 2400
LETTER_SCHEMA = {"type": "object", "properties": {"letter": {"type": "string"}}, "required": ["letter"]}


def card():
    return json.loads((DATA / "correspondent.json").read_text(encoding="utf-8"))


def is_to(w, c):
    """Whether a writing is a letter to the correspondent."""
    return w.get("kind") == "letter" and any(x in (w.get("to") or "").lower() for x in c["match"])


def start(state, d):
    """The post's state, on the first day the switch is on: her first letter is due that day."""
    if "post" not in state:
        state["post"] = {"outbox": [], "sent": [], "letters": [], "deliver": None, "first_due": d.isoformat()}
    return state["post"]


def written(state, w, d, c):
    """He wrote to her: the sitting goes into the outbox, for the post the next morning."""
    post = state.get("post")
    if post is None or not is_to(w, c):
        return False
    post["outbox"].append({"written": d.isoformat(), "title": w.get("title"), "text": w.get("text") or ""})
    return True


def to_post(state, d, c):
    """In the morning the outbox goes to the post as one letter; its answer is due days_each_way × 2 later.
    Returns the posted letter or None."""
    post = state["post"]
    ready = [x for x in post["outbox"] if x["written"] < d.isoformat()]
    if not ready:
        return None
    post["outbox"] = [x for x in post["outbox"] if x not in ready]
    text = "\n\n".join(x["text"] for x in ready if x["text"]).strip()
    letter = {"posted": d.isoformat(), "written": ready[-1]["written"], "text": text,
              "due": (d + timedelta(days=2 * c["days_each_way"])).isoformat()}
    post["sent"].append(letter)
    post["letters"] = (post["letters"] + [{"by": "Hegel", "date": letter["written"], "text": text}])[-KEEP:]
    return letter


def due(state, d, c):
    """What she writes now: 'first', 'reply' (with the letters she answers), 'nudge', or None."""
    post = state["post"]
    if post.get("first_due") and post["first_due"] <= d.isoformat():
        return ("first", [])
    answered = [x for x in post["sent"] if x["due"] <= d.isoformat()]
    if answered:
        return ("reply", answered)
    last_in = next((x for x in reversed(post["letters"]) if x["by"] != "Hegel"), None)
    last_out = next((x for x in reversed(post["letters"]) if x["by"] == "Hegel"), None)
    if last_in and not post["sent"] and not post["outbox"] and (last_out is None or last_out["date"] < last_in["date"]):
        if (d - date.fromisoformat(last_in["date"])).days >= c["nudge_days"] and not last_in.get("nudge"):
            return ("nudge", [])
    return None


def messages(state, kind, answered, d, c):
    """The one call for her letter: her card, the correspondence so far, and what this letter is."""
    post = state["post"]
    lines = [f"Today is {d.strftime('%A')} {d.day} {d.strftime('%B %Y')}, in {c['city']}."]
    earlier = [x for x in post["letters"] if not any(x["text"] == a["text"] for a in answered)][-4:]
    if earlier:
        lines.append("Your correspondence so far, oldest first:")
        for x in earlier:
            who = "You wrote" if x["by"] != "Hegel" else "Hegel wrote"
            lines.append(f"{who}, {x['date']}: “{x['text'][:PROMPT_CHARS]}”")
    if kind == "reply":
        lines.append("Hegel's letter you are answering:" if len(answered) == 1 else "Hegel's letters you are answering:")
        lines += [f"Written {a['written']}: “{a['text'][:3 * PROMPT_CHARS]}”" for a in answered]
    lines.append(c[kind])
    lines.append('Answer with the JSON object only: {"letter": "..."}')
    return [{"role": "system", "content": c["card"]}, {"role": "user", "content": "\n\n".join(lines)}]


def clean(raw):
    """The letter's text, or None if it is unusable."""
    try:
        text = json.loads(raw).get("letter") if raw else None
    except (ValueError, AttributeError):
        return None
    if not isinstance(text, str):
        return None
    text = text.strip()
    return text if 40 <= len(text.split()) <= 600 else None


def arrived(state, kind, answered, text, d, c):
    """Her letter has come: it is recorded, the letters it answers are done, and it waits to be shown."""
    post = state["post"]
    if kind == "first":
        post["first_due"] = None
    post["sent"] = [x for x in post["sent"] if x not in answered]
    item = {"by": c["name"], "date": d.isoformat(), "text": text}
    if kind == "nudge":
        item["nudge"] = True
    post["letters"] = (post["letters"] + [item])[-KEEP:]
    post["deliver"] = {"kind": kind, "date": d.isoformat(), "text": text}
    return item


def event(state, present, c):
    """The situation's lines and the record's entries for a letter that has come, once: [(line, entry)], or [].
    With the first letter comes the money: what he owes now, and the gift besides, into his purse."""
    post = state.get("post") or {}
    letter = post.get("deliver")
    if not letter:
        return []
    post["deliver"] = None
    how = "Ramesh brings the post" if "ramesh" in present else "The post has come"
    if letter["kind"] == "first":
        line = f"{how}: a registered letter from {c['city']}, from {c['full_name']}, whom you do not know. It reads: “{letter['text']}”"
    else:
        line = f"{how}: a letter from {c['name']} in {c['city']}. It reads: “{letter['text']}”"
    out = [(line, {"k": "letter", "by": c["full_name"], "from": c["city"], "to": "Hegel", "text": letter["text"]})]
    if letter["kind"] == "first" and c.get("gift"):
        owed = sum(o.get("amount", 0) for o in state.get("owed", []))
        amount = owed + c["gift"]
        state["imprest"] = state.get("imprest", 0) + amount
        post["gift"] = {"date": letter["date"], "owed": owed, "amount": amount}
        what = f"₹{amount:,}: what you owe, ₹{owed:,}, and ₹{c['gift']:,} besides" if owed else f"₹{amount:,}"
        out.append((f"With the letter comes money sent from {c['city']} through a transfer office, paid out to you in cash: {what}.",
                    {"k": "income", "item": f"Money from {c['city']}, with {c['full_name']}'s letter", "amount": amount, "from": c["full_name"],
                     "text": f"{c['full_name']} sends ₹{amount:,} from {c['city']}."}))
    return out


def on_mind(state, c):
    """What he has in mind about the correspondence, a line or none."""
    post = state.get("post") or {}
    out = []
    last_in = next((x for x in reversed(post.get("letters", [])) if x["by"] != "Hegel"), None)
    last_out = next((x for x in reversed(post.get("letters", [])) if x["by"] == "Hegel"), None)
    if post.get("outbox"):
        out.append(f"Your letter to {c['name']} goes to the post tomorrow morning.")
    elif post.get("sent"):
        x = post["sent"][-1]
        out.append(f"Your letter to {c['name']} went to the post on {x['posted']}; an answer may come in about {2 * c['days_each_way']} days.")
    if last_in and (last_out is None or last_out["date"] < last_in["date"]) and not post.get("outbox"):
        out.append(f"{c['name']}'s letter from {c['city']} of {last_in['date']} awaits your answer.")
    return out


def last_letter(state, c):
    """Her last letter, for the writing request when he sits down to write, or None."""
    post = state.get("post") or {}
    last_in = next((x for x in reversed(post.get("letters", [])) if x["by"] != "Hegel"), None)
    if not last_in:
        return None
    return f"{c['name']}'s last letter to you, of {last_in['date']}: “{last_in['text'][:PROMPT_CHARS]}”"
