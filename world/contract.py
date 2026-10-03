"""The contract between the world and the mind: what the mind is told and what it must answer.

The bake-off and the live world both use this module, so the bake-off tests exactly the
interface the world will use.
"""
import json
import re

PLACES = ["home", "lodhi", "safdarjung", "khan", "gandhi", "gym", "iic", "estates"]
ACTIONS = ["stay", "walk", "read", "write", "talk", "buy", "eat", "rest", "sleep"]
NULLABLE_STR = {"anyOf": [{"type": "string"}, {"type": "null"}]}
SCHEMA = {
    "type": "object",
    "properties": {
        "thought": {"type": "string"},
        "action": {"type": "string", "enum": ACTIONS},
        "place": {"type": "string", "enum": PLACES},
        "minutes": {"type": "integer", "minimum": 5, "maximum": 240},
        "says": NULLABLE_STR,
        "buys": {"type": "array", "items": {
            "type": "object",
            "properties": {"item": {"type": "string"}, "price_inr": {"type": "integer", "minimum": 0}},
            "required": ["item", "price_inr"]}},
        "revision": NULLABLE_STR,
        "looks_up": NULLABLE_STR,           # optional, and not required: something to look up on his phone
    },
    "required": ["thought", "action", "place", "minutes", "says", "buys", "revision"],
}
ASK = "Decide your next step. Answer with the JSON object only."
PLAN_ASK = ("Before you decide, plan today: three to six intentions, each with a time (HH:MM) and one short sentence "
            "(under 120 characters) on what you mean to do. "
            'Answer with the JSON object only: {"plan": [{"time": "09:00", "intention": "..."}]}')
PLAN_SCHEMA = {
    "type": "object",
    "properties": {"plan": {"type": "array", "minItems": 3, "maxItems": 6, "items": {
        "type": "object",
        "properties": {"time": {"type": "string"}, "intention": {"type": "string", "maxLength": 120}},
        "required": ["time", "intention"]}}},
    "required": ["plan"],
}
VOICE_ASK = 'Answer with the JSON object only: {"says": "...", "does": null}'
VOICE_SCHEMA = {
    "type": "object",
    "properties": {"says": {"type": "string", "maxLength": 420}, "does": {"anyOf": [{"type": "string", "maxLength": 200}, {"type": "null"}]}},
    "required": ["says", "does"],
}
WRITING_KINDS = ["essay", "letter", "notes", "chapter", "poem", "other"]
WRITE_ASK = ("You sat down to write. What did you write? Up to about 450 words, in English: a title, the kind "
             f"({', '.join(WRITING_KINDS[:-1])} or other), whom it is to if it is a letter, and the text. If it carries on one of your "
             "manuscripts, say so and give that title.")
WRITE_FORMAT = 'Answer with the JSON object only: {"title": "...", "kind": "essay", "to": null, "continues": false, "text": "..."}'
WRITE_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string", "maxLength": 100},
        "kind": {"type": "string", "enum": WRITING_KINDS},
        "to": NULLABLE_STR,
        "continues": {"type": "boolean"},
        "text": {"type": "string", "maxLength": 3000},
    },
    "required": ["title", "kind", "to", "continues", "text"],
}


def render(s, ask=ASK):
    """The user message for one situation. Optional sections appear only when the world supplies them,
    so bake-off situations render exactly as they always have."""
    present = ", ".join(s["present"]) if s["present"] else "nobody"
    closes = s.get("closes") or {}
    open_now = ", ".join(f"{p} (until {closes[p]})" if p in closes else p for p in s["open_now"])
    text = (
        f"{s['day']}, {s['time']} Delhi time. You are at: {s['place']}.\n"
        f"Weather: {s['weather']}. Air quality index: {s['aqi']}.\n"
        f"Wearing: {s['outfit']}. {s.get('cash_label', 'Imprest left')}: ₹{s['imprest_left']:,}.\n"
        f"Present: {present}.\n"
        f"Open now: {open_now}.\n"
    )
    if s.get("for_sale"):
        text += f"For sale here: {'; '.join(s['for_sale'])}.\n"
    if s.get("on_mind"):
        text += "\nOn your mind:\n" + "".join(f"- {x}\n" for x in s["on_mind"])
    if s.get("remember"):
        text += "\nYou remember:\n" + "".join(f"- {x}\n" for x in s["remember"])
    if s.get("earlier"):
        text += "\nEarlier today:\n" + "".join(f"- {x}\n" for x in s["earlier"])
    if s.get("shelf"):
        text += "\nFrom your shelf:\n" + "".join(f"- {x['label']}: “{x['text']}”\n" for x in s["shelf"])
    text += f"\nWhat happens: {s['event']}\n\n{ask}"
    return text


def extract_json(text):
    text = re.sub(r"<think>.*?</think>", "", text or "", flags=re.S).strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, flags=re.S)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                return None
    return None


def check_shape(ans):
    """Errors in the answer itself, before the world looks at it."""
    errors, warnings = [], []
    if not isinstance(ans, dict):
        return ["answer is not a JSON object"], warnings
    for k in SCHEMA["required"]:
        if k not in ans:
            errors.append(f"missing '{k}'")
    if errors:
        return errors, warnings
    if ans["action"] not in ACTIONS:
        errors.append(f"unknown action '{ans['action']}'")
    if ans["place"] not in PLACES:
        errors.append(f"unknown place '{ans['place']}'")
    if not isinstance(ans["minutes"], int) or isinstance(ans["minutes"], bool) or not 5 <= ans["minutes"] <= 240:
        errors.append(f"minutes out of range: {ans['minutes']}")
    if not isinstance(ans["buys"], list) or not all(
            isinstance(b, dict) and isinstance(b.get("item"), str) and isinstance(b.get("price_inr"), int)
            and not isinstance(b.get("price_inr"), bool) and b["price_inr"] >= 0 for b in ans["buys"]):
        errors.append("buys is malformed")
    for k in ("says", "revision", "looks_up"):
        if ans.get(k) is not None and not isinstance(ans[k], str):
            errors.append(f"'{k}' must be text or null")
    if isinstance(ans.get("looks_up"), str) and len(ans["looks_up"]) > 100:
        errors.append("looks_up is too long: a few words to look up")
    thought = ans["thought"] if isinstance(ans["thought"], str) else ""
    if len(thought.strip()) < 20:
        errors.append("thought is empty or too short")
    elif len(thought) > 700:
        warnings.append("thought is very long")
    return errors, warnings


def check(ans, s):
    """The bake-off check: shape, plus the situation's open places and imprest."""
    errors, warnings = check_shape(ans)
    if errors:
        return errors, warnings
    if ans["place"] not in s["open_now"]:
        errors.append(f"'{ans['place']}' is closed now")
    spent = sum(b["price_inr"] for b in ans["buys"])
    if spent > s["imprest_left"]:
        errors.append(f"spends ₹{spent} with ₹{s['imprest_left']} left")
    if ans["says"] and not s["present"]:
        warnings.append("talks although nobody is present")
    if ans["action"] == "walk" and ans["place"] == s["place"]:
        warnings.append("walks to where he already is")
    return errors, warnings
