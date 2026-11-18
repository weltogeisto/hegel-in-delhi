"""The contract between the world and the mind: what the mind is told and what it must answer.

The bake-off and the live world both use this module, so the bake-off tests exactly the
interface the world will use.
"""
import copy
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
        "speaks_to": dict(NULLABLE_STR, description="Optional recipient ID from the current prompt; omit or use null if no ID is listed."),
        "buys": {"type": "array", "items": {
            "type": "object",
            "properties": {"item": {"type": "string"}, "price_inr": {"type": "integer", "minimum": 0}},
            "required": ["item", "price_inr"]}},
        "revision": NULLABLE_STR,
        "looks_up": NULLABLE_STR,           # optional, and not required: something to look up on his phone
    },
    "required": ["thought", "action", "place", "minutes", "says", "buys", "revision"],
}
WANTS_LINE = ("If you wish this city had something it does not offer you, or allowed something it does not, you may say so in `wants`, "
              "in one line. It is written down. Nothing follows from it at once.")      # HEGEL_WANTS: the last sentence of the decision's instructions (pc/WANTS-SCREEN.md)
WANTS_PROPERTY = dict(NULLABLE_STR, description="Optional: something you wish this city had or allowed, in one line; omit or null if nothing.")
WANTS_MAX = 160
ASK = "Decide your next step. Answer with the JSON object only."
PAYMENT_ASK = ("Each buys row must distinguish purpose='purchase' (a new item, source_charge_id=null) "
               "from purpose='settlement' (an existing obligation, source_charge_id=its recorded canonical ID). "
               "A speaker's demand cannot create or reopen a charge. The world settles recorded obligations "
               "when their conditions permit; do not pay a settled receipt again. ")
PLAN_ASK =("Before you decide, plan today: three to six intentions, each with a time (HH:MM) and one short sentence "
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
VOICE_ASK_ACT = 'Answer with the JSON object only: {"says": "...", "does": null, "act": null}'      # HEGEL_PROMISES: for a person with a menu
PROMISE_LINES = ('You may promise him only this: {menu}.\n'
                 'A promise is made in `act`, as {{"kind": "promise", "what": "<one of those words>", "minutes": <minutes until you keep it>}}; otherwise `act` is null.\n'
                 'You promise nothing else.\n')      # HEGEL_PROMISES: what a person with a menu is told, after the facts about them (data/promises.json)


def voice_schema(menu=None):
    """VOICE_SCHEMA itself, unchanged, unless the person has a menu of promises (HEGEL_PROMISES): then it gains the optional `act`, null or
    one promise whose `what` is a key of the menu. The minutes' bounds are the widest of the menu's; the world checks each entry's own."""
    if not menu:
        return VOICE_SCHEMA
    schema = copy.deepcopy(VOICE_SCHEMA)
    lo, hi = min(x["minutes"][0] for x in menu.values()), max(x["minutes"][1] for x in menu.values())
    schema["properties"]["act"] = {"anyOf": [{"type": "null"}, {"type": "object", "properties": {
        "kind": {"type": "string", "enum": ["promise"]}, "what": {"type": "string", "enum": list(menu)},
        "minutes": {"type": "integer", "minimum": lo, "maximum": hi}}, "required": ["kind", "what", "minutes"]}]}      # optional, and not required
    return schema


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
SITTING_ASK = ("You sat down to write. Say what you will write, not the text yet: a title, the kind "
               f"({', '.join(WRITING_KINDS[:-1])} or other), whom it is to if it is a letter, and in one sentence, from your day, what this "
               "sitting is about. If it carries on one of your manuscripts, say so and give that title.")
SITTING_FORMAT = 'Answer with the JSON object only: {"title": "...", "kind": "essay", "to": null, "continues": false, "about": "..."}'
SITTING_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string", "maxLength": 100},
        "kind": {"type": "string", "enum": WRITING_KINDS},
        "to": NULLABLE_STR,
        "continues": {"type": "boolean"},
        "about": {"type": "string", "maxLength": 200},
    },
    "required": ["title", "kind", "to", "continues", "about"],
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
    if s.get("speakers"):
        text += "Recipient IDs here: " + "; ".join(f"{x['id']} = {x['name']}" for x in s["speakers"]) + ".\n"
        text += "'speaks_to'=addressee ID/null; speak here before any move.\n"
    if s.get("for_sale"):
        text += f"For sale here: {'; '.join(s['for_sale'])}.\n"
    if s.get("on_mind"):
        text += "\nOn your mind:\n" + "".join(f"- {x}\n" for x in s["on_mind"])
    if s.get("remember"):
        text += "\nYou remember:\n" + "".join(f"- {x}\n" for x in s["remember"])
    if s.get("notebook"):
        text += "\nYour notebook of this age, as you keep it each night:\n" + s["notebook"] + "\n"
    if s.get("earlier"):
        text += "\nEarlier today:\n" + "".join(f"- {x}\n" for x in s["earlier"])
    if s.get("shelf"):
        text += "\nFrom your shelf:\n" + "".join(f"- {x['label']}: “{x['text']}”\n" for x in s["shelf"])
    if s.get('reconcile_payments') and ask == ASK:
        ask = PAYMENT_ASK + ask
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


def decision_schema(sit=None):
    """The decision schema for a situation: SCHEMA itself, unchanged, unless the situation lists more places than PLACES
    (HEGEL_CULTURE), when its place list widens to them, or carries `wants` (HEGEL_WANTS), when the optional field is added,
    or carries `reconcile_payments`, when every buys row must also say its purpose and its source charge. It takes the situation,
    as the PC's runtime and tools/decision_sampler.py expect."""
    places = (sit or {}).get("places")
    wants = bool((sit or {}).get("wants"))
    reconcile = bool((sit or {}).get("reconcile_payments"))
    if (not places or list(places) == PLACES) and not wants and not reconcile:
        return SCHEMA
    schema = copy.deepcopy(SCHEMA)
    if places and list(places) != PLACES:
        schema["properties"]["place"] = dict(schema["properties"]["place"], enum=list(places))
    if wants:
        schema["properties"]["wants"] = dict(WANTS_PROPERTY)          # optional, and not required (HEGEL_WANTS)
    if reconcile:
        item = schema["properties"]["buys"]["items"]
        item["properties"].update(purpose={"type": "string", "enum": ["purchase", "settlement"]},
                                  source_charge_id=NULLABLE_STR)
        item["required"] += ["purpose", "source_charge_id"]
    return schema


def check_shape(ans, places=None):
    """Errors in the answer itself, before the world looks at it. `places`: the world's places, if more than PLACES."""
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
    if ans["place"] not in (places or PLACES):
        errors.append(f"unknown place '{ans['place']}'")
    if not isinstance(ans["minutes"], int) or isinstance(ans["minutes"], bool) or not 5 <= ans["minutes"] <= 240:
        errors.append(f"minutes out of range: {ans['minutes']}")
    if not isinstance(ans["buys"], list) or not all(
            isinstance(b, dict) and isinstance(b.get("item"), str) and isinstance(b.get("price_inr"), int)
            and not isinstance(b.get("price_inr"), bool) and b["price_inr"] >= 0 for b in ans["buys"]):
        errors.append("buys is malformed")
    for k in ("says", "revision", "looks_up", "speaks_to", "wants"):
        if ans.get(k) is not None and not isinstance(ans[k], str):
            errors.append(f"'{k}' must be text or null")
    if isinstance(ans.get("looks_up"), str) and len(ans["looks_up"]) > 100:
        errors.append("looks_up is too long: a few words to look up")
    if isinstance(ans.get("wants"), str) and len(ans["wants"]) > WANTS_MAX:
        errors.append(f"wants is too long: one line of at most {WANTS_MAX} characters")
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
