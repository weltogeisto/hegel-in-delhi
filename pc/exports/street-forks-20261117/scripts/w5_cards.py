"""Street cards in fork days: python3 w5_cards.py DAYFILE...  (the `street:` kinds in each step's `opened`, and state.street)."""
import json, sys
for f in sys.argv[1:]:
    d = json.load(open(f))
    kinds = [(s["t"], k) for s in d["steps"] for k in s.get("opened", []) if k.startswith("street:")]
    empty = sum("Nothing in particular happens" in s.get("event", "") for s in d["steps"])
    print(f, "| steps", len(d["steps"]), "| cards", len(kinds), kinds[:6], "| empty moments", empty, "| spent", d["state"].get("street"))
