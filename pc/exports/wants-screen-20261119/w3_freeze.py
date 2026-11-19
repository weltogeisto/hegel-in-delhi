"""W3's freeze with the arms as pc/WANTS-SCREEN.md declares them: A = mind/soul-ordinary.md (live on shadow from Day 48), B (unused) the same.
tools/wants_screen.py's own freeze goes through prompt_screen.ARMS, whose A is the old mind/soul.md; this sets the declared path before the freeze."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path.home() / "w3" / "main"))
from tools import prompt_screen as ps
ps.ARMS = {"A": "mind/soul-ordinary.md", "B": "mind/soul-ordinary.md"}
shadow = (Path.home() / "w3" / "SHADOW").read_text().strip()
r = ps.freeze(Path.home() / "w3" / "native", shadow, Path.home() / "w3" / "screen", first_day=48)
print(json.dumps({"shadow": r["shadow"], "days": r["days"], "pool": r["pool"], "contexts": len(r["rows"]), "arms": r["arms"]}))
