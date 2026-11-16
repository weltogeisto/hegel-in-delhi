#!/usr/bin/env python3
"""Lint the street deck: python3 tools/street_lint.py [FILE]   (default world/data/street.json)

Prints each problem as `id: problem` and exits 1 when there is any. A warning (two capitalised words in a row that are not a
place name: a living person?) is printed for a human to look at and does not fail. The rules are world/street.py's."""
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from world import street  # noqa: E402


def main(argv):
    path = Path(argv[1]) if len(argv) > 1 else street.DECK
    if not path.exists():
        print(f"{path}: no such deck")
        return 1
    places = json.loads((street.DATA / "places.json").read_text(encoding="utf-8"))["places"]
    places.update(json.loads((street.DATA / "culture.json").read_text(encoding="utf-8"))["places"])
    bad, warn = street.check_file(path, places)
    for x in warn:
        print(f"warning  {x}")
    for x in bad:
        print(x)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
