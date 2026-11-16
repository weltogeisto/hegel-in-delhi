"""The street (HEGEL_STREET, pc/WORLD-2-WEEK1.md P4): a deck of small things seen and heard, drawn at a moment that would
otherwise open on nothing. Standard library only; the linter's rules live here so that `python3 -m world check` and
tools/street_lint.py run the same ones.

A card: id, text (at most 240 characters), places, months, hours [from, to], and optionally days, weather, cooldown_days.
The state keeps `state["street"]`: card id -> the date it was last seen."""
import json
import random
import re
from datetime import date, timedelta
from pathlib import Path

from .clock import days_match, fmt, hm

DATA = Path(__file__).resolve().parent / "data"
DECK = DATA / "street.json"
WEATHER = ("rain", "dry", "fog", "poor_air")
CHANCE = 2 / 3                 # about two empty moments in three get a card
COOLDOWN = 21                  # days before a card may come again, unless it says otherwise
POOR_AIR = 300                 # the index at which the engine itself says "The air is very poor today"
RAIN_CODES = set(range(51, 68)) | set(range(80, 83)) | set(range(95, 100))
FOG_CODES = (45, 48)
LIMIT = 240
KEYS = {"id", "text", "places", "months", "hours", "days", "weather", "cooldown_days"}
IMPERATIVES = {"go", "ask", "look", "try", "consider", "remember", "take", "buy", "visit", "come", "see", "listen", "watch",
               "notice", "walk", "stop", "wait", "think", "taste", "smell", "feel", "imagine", "stay", "enjoy", "follow", "read", "stand"}
DOCTRINE = ["spirit", "dialectic", "dialectical", "the concept", "the absolute", "sublation", "the idea", "world-history"]


def load_deck(path=None):
    """The cards of the deck at path (the real deck by default); [] when the file is not there."""
    p = Path(path) if path else DECK
    if not p.exists():
        return []
    return json.loads(p.read_text(encoding="utf-8")).get("cards", [])


def weather_words(wx, d, m):
    """What the hour's weather (an entry of Feeds.weather()['hours']) counts as for a card: a set of rain, dry, fog, poor_air.
    rain: some rain in the hour (0.1 mm or more) or a drizzle, rain, shower or thunderstorm code (51-67, 80-82, 95-99).
    fog: the feed's own fog codes (45, 48); with no code at all (the feed is down and the seasonal normal stands in), a morning
         before 10:00 in December or January.
    poor_air: the air index at 300 or more, where the engine itself says the air is very poor.
    dry: neither rain nor fog."""
    code = wx.get("code")
    rain = (wx.get("rain") or 0) >= 0.1 or code in RAIN_CODES
    fog = code in FOG_CODES or (code is None and d.month in (12, 1) and m < 600)
    out = set()
    if rain:
        out.add("rain")
    if fog:
        out.add("fog")
    if not rain and not fog:
        out.add("dry")
    if (wx.get("aqi") or 0) >= POOR_AIR:
        out.add("poor_air")
    return out


def fits(card, pid, d, m, words, seen):
    """Does the card fit this place, month, minute, day and weather, with its cooldown passed and not seen today?"""
    if pid not in card["places"] or d.month not in card["months"]:
        return False
    a, b = hm(card["hours"][0]), hm(card["hours"][1])
    if not a <= m < b:
        return False
    if card.get("days") and not days_match(card["days"], d):
        return False
    if card.get("weather") and card["weather"] not in words:
        return False
    last = seen.get(card["id"])
    if last:
        gap = (d - date.fromisoformat(last)).days
        if gap < 1 or gap < card.get("cooldown_days", COOLDOWN):
            return False
    return True


def draw(deck, seen, pid, d, m, wx):
    """The card for this place and minute, or None. The same for the same morning: the draw is seeded by date, time and place."""
    rng = random.Random(f"street|{d.isoformat()}|{fmt(m)}|{pid}")
    if rng.random() >= CHANCE:
        return None
    words = weather_words(wx, d, m)
    fit = sorted((c for c in deck if fits(c, pid, d, m, words, seen)), key=lambda c: c["id"])
    return rng.choice(fit) if fit else None


# ── the linter ──────────────────────────────────────────────────────
def _sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def _window(spec, d):
    """A place's opening window in minutes on d (the sun's hours as a fixed 05:00 to 19:30), 'always', or None."""
    if spec == "always":
        return [(0, 1440)]
    out = []
    for days, (a, b) in spec.items():
        out.append((300 if a == "sun" else hm(a), 1170 if b == "sun" else hm(b)))
    return out


def problems(cards, places, names=None):
    """(problems, warnings) for a list of cards. `places` maps place id to its record (with `hours`, `name`); names are the
    place names the capital-letters warning forgives. Each problem is 'id: what is wrong'."""
    bad, warn, ids = [], [], set()
    names = list(names if names is not None else (p.get("name", "") for p in places.values()))
    names += [p.get("short", "") for p in places.values()]
    names = sorted({n for n in names if n}, key=len, reverse=True)
    for i, c in enumerate(cards):
        if not isinstance(c, dict):
            bad.append(f"card {i}: not an object")
            continue
        cid = c.get("id")
        tag = cid if isinstance(cid, str) and cid else f"card {i}"

        def no(msg):
            bad.append(f"{tag}: {msg}")
        if not isinstance(cid, str) or not re.fullmatch(r"[a-z][a-z0-9_]*", cid):
            no("id must be lowercase letters, digits and underscores")
        elif cid in ids:
            no("duplicate id")
        else:
            ids.add(cid)
        for k in sorted(set(c) - KEYS):
            no(f"unknown field {k}")
        text = c.get("text")
        if not isinstance(text, str) or not 1 <= len(text) <= LIMIT:
            no(f"text must be 1 to {LIMIT} characters" + (f" (it is {len(text)})" if isinstance(text, str) else ""))
            text = text if isinstance(text, str) else ""
        pl = c.get("places")
        if not isinstance(pl, list) or not pl:
            no("places must be a list of place ids")
            pl = []
        for p in pl:
            if p not in places:
                no(f"unknown place {p!r}")
        months = c.get("months")
        if not isinstance(months, list) or not months or not all(type(x) is int and 1 <= x <= 12 for x in months):
            no("months must be a list of 1 to 12")
        hours, a, b = c.get("hours"), None, None
        if not (isinstance(hours, list) and len(hours) == 2 and all(isinstance(x, str) and re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d|24:00", x) for x in hours)):
            no("hours must be [\"HH:MM\", \"HH:MM\"]")
        else:
            a, b = hm(hours[0]), hm(hours[1])
            if a >= b:
                no("hours: from must be before to")
            else:
                for p in pl:
                    if p in places and not any(a < y and x < b for x, y in _window(places[p]["hours"], None)):
                        no(f"hours {hours[0]}-{hours[1]} fall outside the opening hours of {p}")
        if "days" in c:
            try:
                if not isinstance(c["days"], str):
                    raise ValueError
                for k in range(7):
                    days_match(c["days"], date(2026, 11, 16) + timedelta(days=k))
            except (ValueError, IndexError):
                no(f"days {c['days']!r} is not a day spec (daily, Mon-Sat, Mon,Wed)")
        if "weather" in c and c["weather"] not in WEATHER:
            no(f"weather must be one of {', '.join(WEATHER)}")
        if "cooldown_days" in c and not (type(c["cooldown_days"]) is int and c["cooldown_days"] >= 0):
            no("cooldown_days must be a whole number of days")
        if re.search(r"\byou(r|rs|rself)?\b", text, re.I):
            no("addresses him (you/your)")
        if "?" in text:
            no("has a question mark")
        for s in _sentences(text):
            w = re.match(r"[A-Za-z]+", s)
            if w and w.group(0).lower() in IMPERATIVES:
                no(f"a sentence opens like an instruction: {s[:30]!r}")
        if "₹" in text or re.search(r"\bRs\b", text, re.I):
            no("names a price (₹ or Rs)")
        for term in DOCTRINE:
            if re.search(r"\b" + re.escape(term) + r"\b", text, re.I):
                no(f"uses a term of his system: {term}")
        if "(rehearsal)" in text.lower():
            no("contains (rehearsal)")
        plain = text
        for n in names:
            plain = plain.replace(n, " ")
        caps = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+", plain)
        if caps:
            warn.append(f"{tag}: two capitalised words in a row ({'; '.join(caps)}): is it a living person?")
    if cards and sum(1 for c in cards if isinstance(c, dict) and "home" in (c.get("places") or [])) * 4 < len(cards):
        bad.append("deck: fewer than a quarter of the cards happen at home")
    return bad, warn


def check_file(path, places):
    """(problems, warnings) for the deck file at path. The deck's own `names` list holds the capitalised names a reader has
    looked at and passed, so that the warning speaks only of names nobody has yet read."""
    try:
        deck = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        return [f"deck: cannot be read: {e}"], []
    cards = deck.get("cards") if isinstance(deck, dict) else None
    if not isinstance(cards, list):
        return ['deck: must be {"note": ..., "cards": [...]}'], []
    seen = [n for n in deck.get("names", []) if isinstance(n, str)]          # names a reader has looked at and passed: monuments, the dead
    return problems(cards, places, names=[p.get("name", "") for p in places.values()] + seen)
