"""The museums, concerts and plays on the page's map (pc/CULTURE.md, "the map on the page"): every venue of
world/data/culture.json has a place on docs/map/lutyens.json, on a walkable cell, and a name on the page, so that the
page draws him where he is rather than at home."""
import json
import math
import re
import unittest
from pathlib import Path

R = Path(__file__).resolve().parents[1]
MAP = json.loads((R / "docs/map/lutyens.json").read_text(encoding="utf-8"))
VENUES = json.loads((R / "world/data/culture.json").read_text(encoding="utf-8"))["places"]
PAGE = (R / "docs/index.html").read_text(encoding="utf-8")


def ground():
    g, r = [], MAP["ground"]
    for i in range(0, len(r), 2):
        g += [r[i]] * r[i + 1]
    return g


class VenueMapTest(unittest.TestCase):
    def test_every_venue_has_a_place_on_a_walkable_cell(self):
        g, w = ground(), MAP["w"]
        walk = {MAP["classes"].index(c) for c in ("road", "foot", "path", "plaza", "parking")}
        for pid in VENUES:
            with self.subTest(pid=pid):
                p = MAP["pois"][pid]
                x, y = p["spot"]
                self.assertTrue(0 <= x < w and 0 <= y < MAP["h"])
                self.assertIn(g[y * w + x], walk)
                x0, y0, x1, y1 = p["rect"]
                self.assertTrue(x0 <= x <= x1 and y0 <= y <= y1)

    def test_the_habitat_centre_sits_where_openstreetmap_has_it(self):
        b = MAP["bbox"]
        ky = 6371000.0 * math.pi / 180
        kx = ky * math.cos(math.radians((b["south"] + b["north"]) / 2))
        x, y = (77.22499 - b["west"]) * kx / 12, (b["north"] - 28.58958) * ky / 12      # way 287659125, its centroid
        x0, y0, x1, y1 = MAP["pois"]["habitat"]["rect"]
        self.assertTrue(x0 <= x <= x1 and y0 <= y <= y1)

    def test_the_venues_beyond_the_map_are_signposted_at_its_north_edge(self):
        for pid in ("national_museum", "ngma", "kamani"):
            with self.subTest(pid=pid):
                self.assertEqual(MAP["pois"][pid]["spot"][1], 0)
                self.assertRegex(PAGE, re.escape(pid) + r":\s*\{name:'[^']+', label:'To [^']+', edge:true,")

    def test_the_page_names_every_venue(self):
        for pid in VENUES:
            with self.subTest(pid=pid):
                self.assertRegex(PAGE, r"\n  " + re.escape(pid) + r":\s*\{name:'")


if __name__ == "__main__":
    unittest.main()
