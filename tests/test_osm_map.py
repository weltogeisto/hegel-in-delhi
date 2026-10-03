"""Tests for tools/osm_map.py on a small OSM fixture. Standard library only:  python3 -m unittest discover -s tests"""
import json
import math
import os
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))

import osm_map as om  # noqa: E402

BBOX = (28.5900, 77.2000, 28.5920, 77.2030)        # about 295 x 220 m: 25 x 19 tiles of 12 m
P = om.Proj(BBOX, 12)


def ll(x, y):
    """Tile coordinates to (lat, lon)."""
    return P.ll(x, y)


def fixture_xml():
    """A road with a name, a lane, a house, a park with a hole, a footway, a wall with a gate, a pond."""
    nodes, ways, rels = [], [], []
    ids = iter(range(1, 1000))

    def node(x, y, tags=None):
        i = next(ids)
        lat, lon = ll(x, y)
        t = "".join('<tag k="%s" v="%s"/>' % kv for kv in (tags or {}).items())
        nodes.append('<node id="%d" lat="%.7f" lon="%.7f">%s</node>' % (i, lat, lon, t))
        return i

    def way(pts, tags, closed=False, wid=None):
        refs = [node(*p) for p in pts]
        if closed:
            refs.append(refs[0])
        wid = wid or next(ids) + 1000
        t = "".join('<tag k="%s" v="%s"/>' % kv for kv in tags.items())
        ways.append('<way id="%d">%s%s</way>' % (wid, "".join('<nd ref="%d"/>' % r for r in refs), t))
        return wid

    way([(0.5, 9.5), (12.5, 9.5), (23.5, 9.5)], {"highway": "secondary", "name": "Tughlaq Road", "oneway": "yes"}, wid=2001)
    way([(12.5, 9.5), (12.5, 18.5)], {"highway": "residential"}, wid=2002)
    way([(3.1, 2.1), (5.0, 2.1), (5.0, 4.0), (3.1, 4.0)], {"building": "house", "name": "A Real Family's Residence"}, closed=True, wid=2003)
    outer = way([(14, 1), (22, 1), (22, 7), (14, 7)], {}, closed=True, wid=2004)
    inner = way([(17, 3), (19, 3), (19, 5), (17, 5)], {}, closed=True, wid=2005)
    way([(15.5, 2.5), (15.5, 6.5)], {"highway": "footway"}, wid=2006)
    way([(0.5, 12.5), (8.5, 12.5)], {"barrier": "wall"}, wid=2007)
    node(4.5, 12.5, {"barrier": "gate"})
    way([(1, 14), (3, 14), (3, 16), (1, 16)], {"natural": "water"}, closed=True, wid=2008)
    rels.append('<relation id="3001"><member type="way" ref="%d" role="outer"/><member type="way" ref="%d" role="inner"/>'
                '<tag k="type" v="multipolygon"/><tag k="leisure" v="park"/></relation>' % (outer, inner))
    return '<osm version="0.6">%s%s%s</osm>' % ("".join(nodes), "".join(ways), "".join(rels))


class ProjectionTest(unittest.TestCase):
    def test_grid_size_and_corners(self):
        self.assertEqual((P.w, P.h), (25, 19))
        self.assertEqual(P.xy(BBOX[2], BBOX[1]), (0.0, 0.0))          # the north-west corner is the origin, y points south
        x, y = P.xy(BBOX[0], BBOX[3])
        self.assertAlmostEqual(x, (BBOX[3] - BBOX[1]) * P.kx / 12)
        self.assertAlmostEqual(y, (BBOX[2] - BBOX[0]) * P.ky / 12)

    def test_x_is_scaled_by_cos_of_the_latitude(self):
        a, b = P.xy(28.591, 77.2010), P.xy(28.591, 77.2020)
        d_east = (b[0] - a[0]) * 12                                    # metres
        self.assertAlmostEqual(d_east, 0.001 * 111194.93 * math.cos(math.radians(28.591)), delta=0.5)
        c = P.xy(28.5920, 77.2010)
        self.assertAlmostEqual((a[1] - c[1]) * 12, 0.001 * 111194.93, delta=0.5)   # a thousandth of a degree north is 111 m

    def test_round_trip(self):
        for x, y in ((0, 0), (5.25, 7.5), (23.9, 18.1)):
            self.assertAlmostEqual(P.xy(*P.ll(x, y))[0], x, places=6)
            self.assertAlmostEqual(P.xy(*P.ll(x, y))[1], y, places=6)

    def test_the_real_extract_fits_the_canvas(self):
        full = om.Proj()
        self.assertTrue(10 <= full.res <= 16)
        self.assertLessEqual(full.w * 16, 4096)
        self.assertLessEqual(full.w * 16 * full.h * 16, 12_000_000)


class GeometryTest(unittest.TestCase):
    def test_segment_cells_are_4_connected_and_reach_the_end(self):
        cells = om.segment_cells(0.5, 0.5, 5.5, 3.5)
        self.assertEqual(cells[0], (0, 0))
        self.assertEqual(cells[-1], (5, 3))
        for a, b in zip(cells, cells[1:]):
            self.assertEqual(abs(a[0] - b[0]) + abs(a[1] - b[1]), 1)

    def test_fill_cells_is_even_odd(self):
        outer = [(0, 0), (6, 0), (6, 6), (0, 6)]
        hole = [(2, 2), (4, 2), (4, 4), (2, 4)]
        got = set(om.fill_cells([outer, hole], 10, 10))
        self.assertEqual(len(got), 36 - 4)
        self.assertNotIn((2, 2), got)
        self.assertIn((1, 1), got)

    def test_rle_and_delta_round_trip(self):
        vals = [0, 0, 0, 5, 5, 1, 0, 0]
        self.assertEqual(om.rle(vals), [0, 3, 5, 2, 1, 1, 0, 2])
        self.assertEqual(om.unrle(om.rle(vals)), vals)
        self.assertEqual(om.delta([3, 4, 9]), [3, 1, 5])


class RasterTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.osm = om.parse_osm(xml_strings=[fixture_xml()])
        cls.m = om.build_map(cls.osm, BBOX, 12, full=False)

    def at(self, x, y):
        return self.m.ground[y * self.m.w + x]

    def test_parsing(self):
        self.assertEqual(len(self.osm.ways), 8)
        self.assertEqual(len(self.osm.rels), 1)
        rings = om.assemble_rings(self.osm, [2004, 2005])
        self.assertEqual(len(rings), 2)
        self.assertTrue(all(r[0] == r[-1] for r in rings))

    def test_a_road_is_laid_and_named(self):
        for x in range(24):
            self.assertEqual(self.at(x, 9), om.ROAD)
        r = self.m.roads[self.m.rid[9 * self.m.w + 5]]
        self.assertEqual((r.name, r.cls), ("Tughlak Road", "secondary"))   # the page's spelling of the OSM name
        self.assertEqual(self.m.road_name_at(20, 9), "Tughlak Road")
        lane = self.m.roads[self.m.rid[14 * self.m.w + 12]]
        self.assertEqual((lane.name, lane.cls), ("", "residential"))       # unnamed lanes stay unnamed
        self.assertEqual(self.m.road_name_at(12, 15), "")

    def test_the_junction_belongs_to_the_main_road(self):
        self.assertEqual(self.m.road_name_at(12, 9), "Tughlak Road")

    def test_building_footprint_blocks_cells_and_keeps_no_residence_name(self):
        self.assertEqual(len(self.m.buildings), 1)
        b = self.m.buildings[0]
        self.assertEqual(b.kind, "bungalow")
        self.assertIsNone(b.name)                                          # no real residence is named on the map
        self.assertEqual(sorted(b.cells), [(3, 2), (3, 3), (4, 2), (4, 3)])
        self.assertGreaterEqual(self.m.bid[2 * self.m.w + 3], 0)
        self.assertEqual(self.m.cost(3, 2), om.INF)
        self.assertEqual(len(b.ring), 4)

    def test_park_multipolygon_with_a_hole(self):
        self.assertEqual(self.at(15, 1), om.PGRASS)
        self.assertEqual(self.at(20, 6), om.PGRASS)
        self.assertNotEqual(self.at(18, 4), om.PGRASS)                     # the inner ring is not park
        self.assertEqual(self.at(15, 4), om.PATH)                          # the footway through it

    def test_wall_gate_and_water(self):
        self.assertEqual(self.at(2, 12), om.WALL)
        self.assertEqual(self.at(7, 12), om.WALL)
        self.assertEqual(self.at(4, 12), om.GATE)
        self.assertEqual(self.cost(4, 12), 1.0)
        self.assertEqual(self.cost(2, 12), om.INF)
        self.assertEqual(self.at(2, 15), om.WATER)

    def cost(self, x, y):
        return self.m.cost(x, y)


class WalkTest(unittest.TestCase):
    def grid(self, w=24, h=12, fill=om.ROAD):
        pr = om.Proj(BBOX, 12)
        pr.w, pr.h = w, h
        m = om.Map(pr)
        for k in range(w * h):
            m.ground[k] = fill
        m.freeze_plants()
        return m

    def test_a_straight_road_is_cells_times_twelve_metres(self):
        m = self.grid()
        table, metres = om.walk_table(m, {"a": (0, 5), "b": (23, 5)})
        self.assertAlmostEqual(metres["a-b"], 23 * 12)
        self.assertEqual(table["a-b"], round(23 * 12 / om.PACE))

    def test_a_diagonal_costs_root_two(self):
        m = self.grid()
        _, metres = om.walk_table(m, {"a": (0, 0), "b": (6, 6)})
        self.assertAlmostEqual(metres["a-b"], 6 * 12 * math.sqrt(2))

    def test_walls_and_buildings_are_walked_round(self):
        m = self.grid()
        for y in range(0, 10):
            m.ground[y * m.w + 12] = om.WALL
        _, around = om.walk_table(m, {"a": (0, 5), "b": (23, 5)})
        # through the gap at y 10 and 11: down 5-ish, along, up again
        self.assertGreater(around["a-b"], 23 * 12 + 20)
        m.ground[10 * m.w + 12] = om.WALL
        m.ground[11 * m.w + 12] = om.WALL
        table, none = om.walk_table(m, {"a": (0, 5), "b": (23, 5)})
        self.assertIsNone(table["a-b"])                                    # sealed off
        self.assertEqual(none["a-b"], om.INF)

    def test_no_cutting_a_corner_between_two_diagonal_walls(self):
        m = self.grid(6, 6)
        m.ground[2 * m.w + 3] = om.WALL
        m.ground[3 * m.w + 2] = om.WALL
        cost = om.cost_grid(m)
        dist, met = om.dijkstra(m.w, m.h, cost, 2 * m.w + 2, 12)   # (2,2) to (3,3) is a diagonal through the gap of the two walls
        self.assertGreater(met[3 * m.w + 3], 12 * math.sqrt(2) + 1)

    def test_ground_is_priced(self):
        m = self.grid(12, 3, om.PGRASS)
        for x in range(12):
            m.ground[1 * m.w + x] = om.ROAD
        cost = om.cost_grid(m)
        self.assertEqual(cost[1 * m.w + 3], 1.0)
        self.assertEqual(cost[0], om.WALK_COST[om.PGRASS])
        self.assertGreater(om.WALK_COST[om.PGRASS], om.WALK_COST[om.ROAD])

    def test_estates_is_the_walk_to_the_north_edge_plus_the_rest_times_1_3(self):
        m = self.grid()
        table, metres = om.walk_table(m, {"a": (3, 8), "b": (20, 8)}, estates=(10, 0))
        nbx, nby = m.proj.xy(*om.NIRMAN_BHAWAN)
        rest = 1.3 * math.hypot(10.5 - nbx, 0.5 - nby) * 12
        got = metres["a-estates"]
        # 7 columns over and 8 rows up, as the octile walk: 7 diagonal + 1 straight steps
        self.assertAlmostEqual(got, (7 * math.sqrt(2) + 1) * 12 + rest, places=3)
        self.assertEqual(table["a-estates"], round(got / om.PACE))


class OutputTest(unittest.TestCase):
    def test_json_shape(self):
        osm = om.parse_osm(xml_strings=[fixture_xml()])
        m = om.build_map(osm, BBOX, 12, full=False)
        d = json.loads(om.dumps(om.to_json(m)))
        for key in ("version", "bbox", "origin", "metres_per_tile", "w", "h", "ground", "buildings", "roads", "trees", "pois", "attribution"):
            self.assertIn(key, d)
        self.assertIn("OpenStreetMap", d["attribution"])
        self.assertEqual(len(om.unrle(d["ground"])), d["w"] * d["h"])
        self.assertNotIn("name", d["buildings"][0])                         # the house's real name did not travel
        self.assertEqual([r["name"] for r in d["roads"] if r["name"]], ["Tughlak Road"])
        cells = []
        s = 0
        for v in d["roads"][0]["cells"]:
            s += v
            cells.append(s)
        self.assertEqual(cells, sorted(cells))

    def test_places_json_only_the_walk_block_changes(self):
        text = ('{\n  "note": "kept as it is",\n  "places": {"a": {}, "b": {}, "c": {}},\n  "walk": {\n'
                '    "a-b": 1, "a-c": 2,\n    "b-c": 3\n  }\n}\n')
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "places.json")
            with open(path, "w") as f:
                f.write(text)
            old, new = om.update_places({"a-b": 7, "a-c": 8, "b-c": 9}, path, ids=["a", "b", "c"])
            with open(path) as f:
                out = f.read()
        self.assertEqual(old, {"a-b": 1, "a-c": 2, "b-c": 3})
        self.assertEqual(dict(new), {"a-b": 7, "a-c": 8, "b-c": 9})
        self.assertEqual(out.split('"walk"')[0], text.split('"walk"')[0])
        self.assertEqual(json.loads(out)["walk"], {"a-b": 7, "a-c": 8, "b-c": 9})
        self.assertEqual(out.count("\n"), text.count("\n"))


class CommittedMapTest(unittest.TestCase):
    """The map the page loads and the walking times the world uses come from the same extract."""

    @classmethod
    def setUpClass(cls):
        cls.map = json.loads((REPO / "docs/map/lutyens.json").read_text(encoding="utf-8"))
        cls.walk = json.loads((REPO / "world/data/places.json").read_text(encoding="utf-8"))["walk"]

    def test_places_sit_where_they_are_in_reality(self):
        d = self.map
        proj = om.Proj((d["bbox"]["south"], d["bbox"]["west"], d["bbox"]["north"], d["bbox"]["east"]), d["metres_per_tile"])
        real = {"khan": ((28.6001, 77.2265), 150), "gandhi": ((28.6019, 77.2144), 100), "gym": ((28.5978, 77.2045), 300),
                "lodhi": ((28.5936, 77.2201), 500), "safdarjung": ((28.5894, 77.2106), 250), "iic": ((28.5934, 77.2228), 200)}
        for pid, ((lat, lon), tol) in real.items():
            x, y = d["pois"][pid]["spot"]
            slat, slon = proj.ll(x + .5, y + .5)
            metres = math.hypot((slat - lat) * proj.ky, (slon - lon) * proj.kx)
            self.assertLess(metres, tol, "%s is %.0f m from where it is in reality" % (pid, metres))
            x0, y0, x1, y1 = d["pois"][pid]["rect"]
            self.assertTrue(x0 <= x <= x1 and y0 <= y <= y1, pid)

    def test_home_is_on_tughlak_road(self):
        d = self.map
        x, y = d["pois"]["home"]["entrance"]
        names = {}
        for r in d["roads"]:
            s = 0
            for v in r["cells"]:
                s += v
                names[s] = r["name"]
        near = {names.get((y + dy) * d["w"] + x + dx) for dx in (-1, 0, 1) for dy in (-1, 0, 1)}
        self.assertIn("Tughlak Road", near)
        self.assertEqual([b["kind"] for b in d["buildings"]].count("home"), 1)
        self.assertEqual([b for b in d["buildings"] if b["kind"] == "home"][0]["id"], "home")

    def test_walk_table_is_the_extracts_distances_at_75_metres_a_minute(self):
        ids = ["home", "lodhi", "safdarjung", "khan", "gandhi", "gym", "iic", "estates"]
        pairs = {a + "-" + b for i, a in enumerate(ids) for b in ids[i + 1:]}
        self.assertEqual(set(self.walk), pairs)
        for k, minutes in self.walk.items():
            self.assertEqual(minutes, round(self.map["walk_metres"][k] / 75), k)
            self.assertGreaterEqual(minutes, 3, k)
            self.assertLess(minutes, 60, k)

    def test_the_file_stays_small(self):
        self.assertLess((REPO / "docs/map/lutyens.json").stat().st_size, 1_500_000)


if __name__ == "__main__":
    unittest.main()
