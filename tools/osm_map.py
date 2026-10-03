#!/usr/bin/env python3
"""Hegel in Delhi: the map, from OpenStreetMap.

Fetches (once, cached) a ~3 x 2 km extract of Lutyens' Delhi from the OSM API, rasterises it onto the page's
tile grid and writes docs/map/lutyens.json, the walking times in world/data/places.json, and (on request) a
debug picture. Standard library only. Map data (c) OpenStreetMap contributors, ODbL 1.0.

    python3 tools/osm_map.py              # build from tools/.cache (fetches missing tiles, politely)
    python3 tools/osm_map.py --offline    # never touch the network
    python3 tools/osm_map.py --png out.png --no-write

The OSM API is the only source: the Overpass API is not used. The cache holds the raw XML and is not committed.
"""
import argparse
import collections
import heapq
import json
import math
import os
import random
import re
import struct
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CACHE = os.path.join(HERE, ".cache")
OUT = os.path.join(ROOT, "docs", "map", "lutyens.json")
PLACES_JSON = os.path.join(ROOT, "world", "data", "places.json")

API = "https://api.openstreetmap.org/api/0.6/"
UA = "hegel-in-delhi/1.0 (+https://git" + "hub.com/weltogeisto/hegel-in-delhi)"
BBOX = (28.5855, 77.1995, 28.6045, 77.2300)      # south, west, north, east
TILE_DEG = 0.004
RES = 12.0                                        # metres per tile
EARTH_R = 6371000.0
PACE = 75.0                                       # metres a minute, day 1's walking pace
NIRMAN_BHAWAN = (28.6111, 77.2156)                # off the map, to the north
QUANT = 16                                        # building outlines are stored in 1/16 tile

# ground classes, shared with docs/index.html
CLASSES = ["grass", "road", "foot", "path", "water", "lawn", "wall", "gate", "tree", "flower", "rgrass", "pgrass",
           "hedge", "sand", "bld", "court", "redwall", "parking", "plaza"]
(GRASS, ROAD, FOOT, PATH, WATER, LAWN, WALL, GATE, TREE, FLOWER, RGRASS, PGRASS, HEDGE, SAND, BLD, COURT, REDWALL,
 PARKING, PLAZA) = range(len(CLASSES))
INF = float("inf")
# what a step onto a class costs when walking; the page uses the same table
WALK_COST = {ROAD: 1.0, FOOT: 1.0, PATH: 1.0, PLAZA: 1.0, GATE: 1.0, PARKING: 1.2, SAND: 2.5,
             GRASS: 1.6, PGRASS: 1.6, RGRASS: 1.6, LAWN: 3.0}
PLOT_R = 4                                        # how far a bungalow's inferred compound reaches, in tiles
GOOD_SPOT = {ROAD, FOOT, PATH, SAND, GATE, PLAZA, PARKING}
BUILDABLE = {GRASS, LAWN, PGRASS, RGRASS, PLAZA, PARKING, COURT, SAND}

ROAD_RANK = {"service": 1, "track": 1, "living_street": 2, "residential": 2, "unclassified": 2, "tertiary": 3,
             "tertiary_link": 3, "secondary_link": 4, "secondary": 5, "primary_link": 5, "primary": 6, "trunk": 7,
             "motorway": 8}
FOOTWAYS = {"footway", "path", "steps", "pedestrian", "cycleway", "bridleway"}
PRIVATE = {"private", "no", "military", "customers", "permit"}
# a few spellings the page and the day files already use, or the official ones
NAME_ALIAS = {"Tughlaq Road": "Tughlak Road", "Tees January Road": "Tees January Marg",
              "Subramaniyam Bharti Marg": "Subramania Bharti Marg", "IV Avenue Road": "Fourth Avenue Road",
              "Agrangzeb road": "Aurangzeb Road",
              "Doctor Avul Pakir Jainulabdeen Abdul Kalam Marg": "Doctor A.P.J. Abdul Kalam Marg"}

PRIVATE_LANDUSE = {"residential", "institutional", "military", "education", "religious", "cultural_centre",
                   "commercial", "plant_nursery", "industrial", "garages"}
GREEN_LANDUSE = {"grass", "recreation_ground", "village_green", "meadow", "cemetery", "orchard"}
GREEN_LEISURE = {"park", "garden", "golf_course", "nature_reserve", "common"}
COURT_SPORTS = {"tennis", "basketball", "volleyball", "badminton", "squash", "netball", "handball", "futsal", "padel",
                "table_tennis", "skateboard", "basketball;volleyball", "tennis;basketball"}

# Public landmarks, by OSM way id: (kind, the name the page uses, style). Only these carry names in the JSON.
LANDMARKS = {
    243175581: ("tomb", "Mohammed Shah's tomb", "oct"),
    220693076: ("tomb", "Bara Gumbad", ""),
    163779658: ("tomb", "Sheesh Gumbad", "blue"),
    359512682: ("tomb", "Sikandar Lodi's tomb", "oct"),
    103602249: ("safdarjung", "Safdarjung's Tomb", ""),
    168873339: ("memorial", "Gandhi Smriti", ""),
}
# mapped as a theatre, not as a building, though it is the IIC's auditorium
UNTAGGED_BUILDINGS = {1355894098}
# areas whose buildings are the landmark: way id -> (kind, name)
LANDMARK_AREAS = {
    80954566: ("club", "Delhi Gymkhana Club"),            # leisure=sports_centre; the club house is its largest building
    80442501: ("shops", "Khan Market"),                   # landuse=retail
    1355894099: ("iic", "India International Centre"),    # amenity=arts_centre
}
# the place ids of the page, how to find each in OSM, and where the loops go (all by OSM node/way id)
PLACE_SPECS = {
    "lodhi": {"area": 80442502, "gate": 10242883134,
              "loop": [243175581, 220693076, 163779658, 359512682, 275460693]},      # the four tombs, then the Rose Garden
    "safdarjung": {"area": 103603614, "gate": 1869899374},
    "khan": {"area": 80442501, "spot": (28.59950, 77.22600),
             "loop": [(28.59950, 77.22600), (28.59990, 77.22575), (28.60030, 77.22600), (28.60030, 77.22655),
                      (28.60000, 77.22690), (28.59955, 77.22655), (28.59950, 77.22600)]},
    "gandhi": {"area": 168873339, "gate": 14051886918},
    "gym": {"area": 80954566, "gate": 11648546454},
    "iic": {"area": 1355894099, "gate": 10995243797},
}

requests_made = 0
_last_request = 0.0


# ───────────────────────── projection ─────────────────────────

class Proj:
    """Equirectangular: x east, y south, in tiles, from the north-west corner of the bbox."""

    def __init__(self, bbox=BBOX, res=RES):
        self.south, self.west, self.north, self.east = bbox
        self.res = res
        self.ky = EARTH_R * math.pi / 180
        self.kx = self.ky * math.cos(math.radians((self.south + self.north) / 2))
        self.w = math.ceil((self.east - self.west) * self.kx / res - 1e-9)
        self.h = math.ceil((self.north - self.south) * self.ky / res - 1e-9)

    def xy(self, lat, lon):
        return (lon - self.west) * self.kx / self.res, (self.north - lat) * self.ky / self.res

    def ll(self, x, y):
        return self.north - y * self.res / self.ky, self.west + x * self.res / self.kx


# ───────────────────────── fetching (cached, polite) ─────────────────────────

def http_get(url):
    global requests_made, _last_request
    wait = 1.1 - (time.time() - _last_request)
    if wait > 0:
        time.sleep(wait)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    _last_request = time.time()
    requests_made += 1
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def tile_boxes(bbox=BBOX, step=TILE_DEG):
    s, w, n, e = bbox
    out, la = [], s
    while la < n - 1e-9:
        lo = w
        while lo < e - 1e-9:
            out.append((round(la, 5), round(lo, 5), round(min(la + step, n), 5), round(min(lo + step, e), 5)))
            lo += step
        la += step
    return out


def fetch_tiles(bbox=BBOX, offline=False, log=print):
    """Cache the raw OSM XML of every tile; returns the list of cache files."""
    os.makedirs(CACHE, exist_ok=True)
    files = []

    def one(t, depth=0):
        name = "tile_%d_%d%s.xml" % (round(t[0] * 1e4), round(t[1] * 1e4), "" if depth == 0 else "_%d" % depth)
        path = os.path.join(CACHE, name)
        if os.path.exists(path):
            files.append(path)
            return
        if offline:
            raise SystemExit("missing %s and --offline was given" % name)
        try:
            data = http_get(API + "map?bbox=%.5f,%.5f,%.5f,%.5f" % (t[1], t[0], t[3], t[2]))
        except urllib.error.HTTPError as e:
            if e.code == 400 and depth < 2:          # too many nodes: split in four
                mla, mlo = (t[0] + t[2]) / 2, (t[1] + t[3]) / 2
                for sub in ((t[0], t[1], mla, mlo), (t[0], mlo, mla, t[3]), (mla, t[1], t[2], mlo), (mla, mlo, t[2], t[3])):
                    one(tuple(round(v, 5) for v in sub), depth + 1)
                return
            raise
        with open(path, "wb") as f:
            f.write(data)
        files.append(path)
        log("fetched %s (%d bytes), %d requests so far" % (name, len(data), requests_made))

    for t in tile_boxes(bbox):
        one(t)
    return files


# ───────────────────────── parsing ─────────────────────────

class OSM:
    def __init__(self):
        self.nodes = {}      # id -> (lat, lon)
        self.ntags = {}      # id -> tags, only for tagged nodes
        self.ways = {}       # id -> (node ids, tags)
        self.rels = {}       # id -> (members [(type, ref, role)], tags)

    def add_xml(self, root):
        for e in root:
            if e.tag == "node":
                i = int(e.get("id"))
                self.nodes[i] = (float(e.get("lat")), float(e.get("lon")))
                tags = {t.get("k"): t.get("v") for t in e.findall("tag")}
                if tags:
                    self.ntags[i] = tags
            elif e.tag == "way":
                self.ways[int(e.get("id"))] = ([int(n.get("ref")) for n in e.findall("nd")],
                                               {t.get("k"): t.get("v") for t in e.findall("tag")})
            elif e.tag == "relation":
                self.rels[int(e.get("id"))] = ([(m.get("type"), int(m.get("ref")), m.get("role") or "") for m in e.findall("member")],
                                               {t.get("k"): t.get("v") for t in e.findall("tag")})

    def way_ll(self, wid):
        nds, _ = self.ways[wid]
        return [self.nodes[n] for n in nds if n in self.nodes]


def parse_osm(paths=(), xml_strings=()):
    osm = OSM()
    for p in paths:
        osm.add_xml(ET.parse(p).getroot())
    for s in xml_strings:
        osm.add_xml(ET.fromstring(s))
    return osm


AREA_KEYS = ("building", "landuse", "leisure", "natural", "water", "amenity", "tourism", "historic", "man_made", "sport")


def is_area(tags, closed):
    if tags.get("area") == "no":
        return False
    if tags.get("area") == "yes":
        return True
    if not closed:
        return False
    if "highway" in tags or "barrier" in tags or "railway" in tags or "waterway" in tags:
        return False
    if tags.get("natural") in ("tree_row", "coastline", "cliff", "ridge"):
        return False
    return any(k in tags for k in AREA_KEYS)


def assemble_rings(osm, way_ids):
    """Join the member ways of a multipolygon into closed rings of (lat, lon)."""
    segs = [list(osm.ways[w][0]) for w in way_ids if w in osm.ways and len(osm.ways[w][0]) > 1]
    rings = []
    while segs:
        ring = segs.pop()
        while ring[0] != ring[-1]:
            for i, s in enumerate(segs):
                if s[0] == ring[-1]:
                    ring += s[1:]
                elif s[-1] == ring[-1]:
                    ring += s[::-1][1:]
                elif s[-1] == ring[0]:
                    ring = s[:-1] + ring
                elif s[0] == ring[0]:
                    ring = s[::-1][:-1] + ring
                else:
                    continue
                segs.pop(i)
                break
            else:
                break
        if ring[0] == ring[-1] and len(ring) >= 4:
            rings.append([osm.nodes[n] for n in ring if n in osm.nodes])
    return rings


def iter_areas(osm):
    """Yield (id, tags, rings) for every closed area way and multipolygon; rings in (lat, lon), even-odd."""
    for wid, (nds, tags) in osm.ways.items():
        if len(nds) >= 4 and nds[0] == nds[-1] and is_area(tags, True):
            ring = osm.way_ll(wid)
            if len(ring) >= 4:
                yield wid, tags, [ring]
    for rid, (members, tags) in osm.rels.items():
        if tags.get("type") == "multipolygon" and is_area(tags, True):
            rings = assemble_rings(osm, [ref for t, ref, role in members if t == "way" and role in ("outer", "inner", "")])
            if rings:
                yield rid, tags, rings


# ───────────────────────── geometry on the grid ─────────────────────────

def clip_segment(x0, y0, x1, y1, w, h, m=1):
    """Liang-Barsky against [-m, w+m] x [-m, h+m]; None when the segment is outside."""
    dx, dy, t0, t1 = x1 - x0, y1 - y0, 0.0, 1.0
    for p, q in ((-dx, x0 + m), (dx, w + m - x0), (-dy, y0 + m), (dy, h + m - y0)):
        if p == 0:
            if q < 0:
                return None
        else:
            r = q / p
            if p < 0:
                if r > t1:
                    return None
                t0 = max(t0, r)
            else:
                if r < t0:
                    return None
                t1 = min(t1, r)
    return x0 + t0 * dx, y0 + t0 * dy, x0 + t1 * dx, y0 + t1 * dy


def segment_cells(x0, y0, x1, y1):
    """Every cell the segment touches, 4-connected, in order (Amanatides and Woo)."""
    cx, cy, ex, ey = math.floor(x0), math.floor(y0), math.floor(x1), math.floor(y1)
    cells = [(cx, cy)]
    dx, dy = x1 - x0, y1 - y0
    sx, sy = (1 if dx > 0 else -1), (1 if dy > 0 else -1)
    tx = ((cx + (1 if sx > 0 else 0)) - x0) / dx if dx else INF
    ty = ((cy + (1 if sy > 0 else 0)) - y0) / dy if dy else INF
    ddx, ddy = (abs(1 / dx) if dx else INF), (abs(1 / dy) if dy else INF)
    for _ in range(abs(ex - cx) + abs(ey - cy)):
        if tx < ty:
            cx += sx
            tx += ddx
        else:
            cy += sy
            ty += ddy
        cells.append((cx, cy))
    return cells


def polyline_cells(pts, w, h):
    out, seen = [], set()
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        c = clip_segment(x0, y0, x1, y1, w, h)
        if not c:
            continue
        for cell in segment_cells(*c):
            if 0 <= cell[0] < w and 0 <= cell[1] < h and cell not in seen:
                seen.add(cell)
                out.append(cell)
    return out


def fill_cells(rings, w, h):
    """Cells whose centre lies inside the rings (even-odd)."""
    edges = []
    for r in rings:
        for (x0, y0), (x1, y1) in zip(r, r[1:] + r[:1]):
            if y0 != y1:
                edges.append((x0, y0, x1, y1) if y0 < y1 else (x1, y1, x0, y0))
    if not edges:
        return
    ymin = max(0, math.floor(min(e[1] for e in edges)))
    ymax = min(h - 1, math.floor(max(e[3] for e in edges)))
    for y in range(ymin, ymax + 1):
        yc = y + 0.5
        xs = sorted(x0 + (yc - y0) * (x1 - x0) / (y1 - y0) for x0, y0, x1, y1 in edges if y0 <= yc < y1)
        for a, b in zip(xs[0::2], xs[1::2]):
            for x in range(max(0, math.ceil(a - 0.5)), min(w - 1, math.ceil(b - 0.5) - 1) + 1):
                yield x, y


def in_ring(px, py, ring):
    c = False
    for (x0, y0), (x1, y1) in zip(ring, ring[1:] + ring[:1]):
        if (y0 > py) != (y1 > py) and px < x0 + (py - y0) * (x1 - x0) / (y1 - y0):
            c = not c
    return c


def coverage_cells(ring, w, h, n=4, thresh=0.35):
    """Cells at least `thresh` covered by the polygon, sampled n x n."""
    xs, ys = [p[0] for p in ring], [p[1] for p in ring]
    out = []
    for y in range(max(0, math.floor(min(ys))), min(h - 1, math.floor(max(ys))) + 1):
        for x in range(max(0, math.floor(min(xs))), min(w - 1, math.floor(max(xs))) + 1):
            hit = sum(in_ring(x + (i + 0.5) / n, y + (j + 0.5) / n, ring) for i in range(n) for j in range(n))
            if hit / (n * n) >= thresh:
                out.append((x, y))
    return out


def ring_area(ring):
    return 0.5 * abs(sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(ring, ring[1:] + ring[:1])))


def ring_centroid(ring):
    return sum(p[0] for p in ring) / len(ring), sum(p[1] for p in ring) / len(ring)


def bbox_of(cells):
    xs, ys = [c[0] for c in cells], [c[1] for c in cells]
    return [min(xs), min(ys), max(xs), max(ys)]


NB4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
NB8 = NB4 + ((1, 1), (1, -1), (-1, 1), (-1, -1))
SQ2 = math.sqrt(2)


# ───────────────────────── the map ─────────────────────────

class Road:
    def __init__(self, name, cls):
        self.name, self.cls, self.cells = name, cls, set()


class Building:
    def __init__(self, bid, kind, ring, cells, tags):
        self.id, self.kind, self.ring, self.cells, self.tags = bid, kind, ring, cells, tags
        self.name, self.style, self.lev = None, "", 0
        self.area = ring_area(ring)


class Map:
    def __init__(self, proj):
        self.proj, self.w, self.h = proj, proj.w, proj.h
        n = self.w * self.h
        self.ground = bytearray(n)           # terrain class per cell
        self.rid = [-1] * n                  # index into self.roads
        self.bid = [-1] * n                  # index into self.buildings
        self.inferred = bytearray(n)         # 1 where a wall or gate was inferred, not mapped
        self.roads, self.road_ix = [], {}
        self.buildings = []
        self.trees, self.bushes = set(), set()
        self.roundabouts, self.signs, self.pois = [], [], {}
        self.plots = []
        self.touched = set()                 # cells any building outline reaches into
        self.courts = []                     # (0 tennis, 1 other, outline) of every court
        self.notes = {}

    def inb(self, x, y):
        return 0 <= x < self.w and 0 <= y < self.h

    def get(self, x, y):
        return self.ground[y * self.w + x] if self.inb(x, y) else 255

    def set(self, x, y, c):
        if self.inb(x, y):
            self.ground[y * self.w + x] = c

    def cost(self, x, y):
        """Step cost onto a cell; INF when it cannot be walked."""
        if not self.inb(x, y):
            return INF
        k = y * self.w + x
        if self.bid[k] >= 0 or (k in self.tree_cells) or (k in self.bush_cells):
            return INF
        return WALK_COST.get(self.ground[k], INF)

    tree_cells = frozenset()
    bush_cells = frozenset()

    def freeze_plants(self):
        self.tree_cells = frozenset(y * self.w + x for x, y in self.trees)
        self.bush_cells = frozenset(y * self.w + x for x, y in self.bushes)

    def road(self, name, cls):
        key = (name, cls)
        if key not in self.road_ix:
            self.road_ix[key] = len(self.roads)
            self.roads.append(Road(name, cls))
        return self.road_ix[key]

    def road_name_at(self, x, y):
        if not self.inb(x, y):
            return ""
        r = self.rid[y * self.w + x]
        return self.roads[r].name if r >= 0 else ""


def clean_name(tags):
    n = (tags.get("name:en") or tags.get("name") or "").strip()
    return NAME_ALIAS.get(n, n.replace("Tughlaq", "Tughlak"))


def classify_ground(m, osm, areas):
    """Open ground, parks, water, courts, parking, plazas, from the area polygons."""
    w, h, P = m.w, m.h, m.proj
    ground = m.ground
    lists = collections.defaultdict(list)
    for aid, tags, rings in areas:
        xy = [[P.xy(*p) for p in r] for r in rings]
        lu, le, na = tags.get("landuse"), tags.get("leisure"), tags.get("natural")
        if lu in PRIVATE_LANDUSE:
            lists["private"].append(xy)
        if lu == "retail" or tags.get("amenity") == "marketplace":
            lists["plaza"].append(xy)
        if lu in GREEN_LANDUSE or le in GREEN_LEISURE or na in ("wood", "scrub", "grassland", "heath"):
            lists["green"].append(xy)
        if na == "water" or "water" in tags or lu in ("basin", "reservoir") or le == "swimming_pool":
            lists["water"].append((xy, le == "swimming_pool"))
        if le == "pitch":
            sport = tags.get("sport", "")
            small = sum(ring_area(r) for r in xy[:1]) * m.proj.res ** 2 < 1500
            if sport in COURT_SPORTS or (not sport and small):
                lists["court"].append((xy, sport))
            else:
                lists["field"].append(xy)
        if tags.get("amenity") == "parking" or tags.get("parking") in ("surface", "lane", "street_side"):
            lists["parking"].append(xy)
        if tags.get("highway") == "pedestrian":
            lists["plaza"].append(xy)
    for kind, cls in (("private", LAWN), ("plaza", PLAZA), ("green", PGRASS)):
        for xy in lists[kind]:
            for x, y in fill_cells(xy, w, h):
                ground[y * w + x] = cls
    for xy, small in lists["water"]:
        cells = set(fill_cells(xy, w, h))
        if small or not cells:       # pools and ponds under a tile: whichever cells they mostly cover
            cells |= set(coverage_cells(xy[0], w, h, 4, 0.4))
        for x, y in cells:
            ground[y * w + x] = WATER
    for xy in lists["field"]:        # football, cricket, polo, athletics: a field of grass, not a clay court
        for x, y in fill_cells(xy, w, h):
            if ground[y * w + x] in (GRASS, LAWN):
                ground[y * w + x] = PGRASS
    for xy, sport in lists["court"]:
        cells = set(fill_cells(xy, w, h)) | set(coverage_cells(xy[0], w, h, 4, 0.5))
        for x, y in cells:
            ground[y * w + x] = COURT
        m.courts.append((0 if sport == "tennis" else 1, xy[0][:-1]))     # the page draws the courts themselves, pixel by pixel
    for xy in lists["parking"]:
        for x, y in fill_cells(xy, w, h):
            if ground[y * w + x] in (GRASS, LAWN, PLAZA, PGRASS):
                ground[y * w + x] = PARKING


def lay_roads(m, osm):
    """Vehicle roads from highway ways, lowest class first so the main roads win the road index."""
    P = m.proj
    ways = []
    places = [[P.xy(*p) for p in osm.way_ll(aid)] for aid in sorted({s["area"] for s in PLACE_SPECS.values()}) if aid in osm.ways]
    for wid, (nds, tags) in osm.ways.items():
        hw = tags.get("highway")
        if hw not in ROAD_RANK:
            continue
        if tags.get("area") == "yes" or tags.get("tunnel") in ("culvert", "building_passage") or tags.get("layer", "0").lstrip("-").isdigit() and int(tags.get("layer", "0")) < 0:
            continue
        pts = [P.xy(*osm.nodes[n]) for n in nds if n in osm.nodes]
        if len(pts) < 2:
            continue
        private = hw == "service" and tags.get("access") in PRIVATE
        if private and not any(in_ring(x, y, r) for r in places for x, y in pts):
            continue        # drives inside bungalow compounds would only clutter the blocks
        ring = tags.get("junction") == "roundabout" or bool(re.match(r"(?i)rotary", tags.get("name", "")))
        rank = 0 if private else ROAD_RANK[hw]
        ways.append((rank, wid, tags, pts, private, ring))
    ways.sort(key=lambda t: (t[0], t[1]))
    for rank, wid, tags, pts, private, ring in ways:
        hw = tags["highway"]
        name = clean_name(tags)
        if ring:
            ri = m.road("", "roundabout")
        else:
            ri = m.road(name if not private else "", "drive" if private else hw)
        cls = SAND if private else ROAD
        for x, y in polyline_cells(pts, m.w, m.h):
            k = y * m.w + x
            m.ground[k] = cls
            m.rid[k] = ri
            m.roads[ri].cells.add(k)
    # the island of a roundabout: its ring is often several ways
    rings = assemble_rings(osm, [t[1] for t in ways if t[5]])
    for ring in rings:
        pts = [P.xy(*p) for p in ring]
        cells = [(x, y) for x, y in fill_cells([pts], m.w, m.h) if m.ground[y * m.w + x] != ROAD]
        if not cells:
            continue
        for x, y in cells:
            m.ground[y * m.w + x] = RGRASS
        cx, cy = ring_centroid(pts[:-1])
        m.roundabouts.append({"x": round(cx, 2), "y": round(cy, 2), "r": round(math.sqrt(len(cells) / math.pi), 2)})
    # fill the one-cell median between the carriageways of the main roads
    main = {i for i, r in enumerate(m.roads) if r.cls in ("secondary", "secondary_link", "tertiary", "primary", "trunk")}
    fills = []
    for y in range(m.h):
        for x in range(m.w):
            k = y * m.w + x
            if m.ground[k] in (ROAD,) or m.rid[k] >= 0:
                continue
            for dx, dy in ((1, 0), (0, 1)):
                if m.inb(x - dx, y - dy) and m.inb(x + dx, y + dy):
                    a, b = (y - dy) * m.w + x - dx, (y + dy) * m.w + x + dx
                    if m.ground[a] == ROAD and m.ground[b] == ROAD and m.rid[a] in main and m.rid[b] in main:
                        fills.append((k, m.rid[a]))
                        break
    for k, r in fills:
        m.ground[k] = ROAD
        m.rid[k] = r
        m.roads[r].cells.add(k)


def lay_paths(m, osm):
    P = m.proj
    for wid, (nds, tags) in osm.ways.items():
        hw = tags.get("highway")
        if hw not in FOOTWAYS or tags.get("area") == "yes":
            continue
        if tags.get("footway") in ("crossing", "sidewalk", "traffic_island") or tags.get("tunnel") in ("building_passage", "culvert"):
            continue
        if tags.get("access") == "no" and tags.get("foot") != "yes":
            continue
        pts = [P.xy(*osm.nodes[n]) for n in nds if n in osm.nodes]
        if len(pts) < 2:
            continue
        for x, y in polyline_cells(pts, m.w, m.h):
            k = y * m.w + x
            g = m.ground[k]
            if g in (ROAD, SAND, GATE, WALL, REDWALL) or (g == WATER and tags.get("bridge") != "yes"):
                continue
            m.ground[k] = PATH if g in (PGRASS, RGRASS, LAWN, WATER, GRASS) else FOOT


def lay_walls(m, osm):
    P = m.proj
    for wid, (nds, tags) in osm.ways.items():
        b = tags.get("barrier")
        if b not in ("wall", "hedge", "city_wall"):
            continue
        pts = [P.xy(*osm.nodes[n]) for n in nds if n in osm.nodes]
        if len(pts) < 2:
            continue
        brick = tags.get("wall") in ("brick", "stone") or tags.get("material") in ("brick", "stone", "sandstone") or "historic" in tags
        cls = HEDGE if b == "hedge" else REDWALL if brick else WALL
        for x, y in polyline_cells(pts, m.w, m.h):
            k = y * m.w + x
            if m.ground[k] in (ROAD, SAND, PATH, FOOT, GATE, WATER):
                continue
            m.ground[k] = cls
    # mapped gates stand in a mapped wall
    for nid, tags in osm.ntags.items():
        if tags.get("barrier") not in ("gate", "wicket_gate", "lift_gate") and not tags.get("entrance"):
            continue
        x, y = P.xy(*osm.nodes[nid])
        best = None
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                cx, cy = int(math.floor(x)) + dx, int(math.floor(y)) + dy
                if m.get(cx, cy) in (WALL, REDWALL, HEDGE):
                    d = math.hypot(cx + 0.5 - x, cy + 0.5 - y)
                    if best is None or d < best[0]:
                        best = (d, cx, cy)
        if best and best[0] < 1.6:
            m.set(best[1], best[2], GATE)


def lay_buildings(m, osm, areas):
    """Footprints: polygons in tile coordinates, plus the cells they block."""
    P = m.proj
    lm_areas = {}
    for aid, tags, rings in areas:
        if aid in LANDMARK_AREAS:
            lm_areas[aid] = [P.xy(*p) for p in rings[0]]
    for aid, tags, rings in areas:
        is_b = "building" in tags or aid in UNTAGGED_BUILDINGS
        if not is_b:
            continue
        ring = [P.xy(*p) for p in rings[0]][:-1]
        if len(ring) < 3:
            continue
        xs, ys = [p[0] for p in ring], [p[1] for p in ring]
        if max(xs) < 0 or max(ys) < 0 or min(xs) > m.w or min(ys) > m.h:
            continue
        cells = [(x, y) for x, y in coverage_cells(ring, m.w, m.h) if m.ground[y * m.w + x] in BUILDABLE]
        b = Building(aid, None, ring, cells, tags)
        m.buildings.append(b)
        m.touched.update(y * m.w + x for x, y in coverage_cells(ring, m.w, m.h, 4, 0.07))   # no tree grows through a roof
    m.buildings.sort(key=lambda b: b.id)
    metres2 = (m.proj.res) ** 2
    # landmark areas: the club house is the largest building inside the club; Khan Market and the IIC take theirs all
    inside = collections.defaultdict(list)
    for b in m.buildings:
        c = ring_centroid(b.ring)
        for aid, ring in lm_areas.items():
            if in_ring(c[0], c[1], ring):
                inside[aid].append(b)
    for b in m.buildings:
        t = b.tags
        a_m2 = b.area * metres2
        gx, gy = ring_centroid(b.ring)
        under = m.get(int(gx), int(gy))
        lev = int(re.match(r"\d+", t.get("building:levels", "0")).group(0)) if re.match(r"\d+", t.get("building:levels", "0")) else 0
        kind = building_kind(t, a_m2, lev, under)
        if b.id in LANDMARKS:
            kind, b.name, b.style = LANDMARKS[b.id]
        b.kind = kind
        b.lev = lev
    for aid, bs in inside.items():
        kind, name = LANDMARK_AREAS[aid]
        if kind == "club":
            big = max(bs, key=lambda b: b.area)
            big.kind, big.name = "club", name
        else:
            for b in bs:
                if b.kind not in ("shed",):
                    b.kind = kind
            max(bs, key=lambda b: b.area).name = name
    for i, b in enumerate(m.buildings):
        for x, y in b.cells:
            m.bid[y * m.w + x] = i


def building_kind(tags, a_m2, lev, under):
    b = tags.get("building", "yes")
    if b in ("house", "detached", "bungalow", "villa", "semidetached_house"):
        return "bungalow"
    if b in ("apartments", "residential", "dormitory", "terrace", "flats"):
        return "residential"
    if b in ("roof", "shed", "garage", "garages", "carport", "service", "hut", "greenhouse", "kiosk", "cabin", "container", "toilets"):
        return "shed"
    if b in ("retail", "supermarket"):
        return "shop"
    if b in ("school", "kindergarten", "university", "college"):
        return "school"
    if b in ("commercial", "office", "public", "government", "civic", "hospital", "hotel", "fire_station", "industrial", "train_station"):
        return "office"
    if tags.get("amenity") == "place_of_worship" or b in ("temple", "mosque", "church", "religious", "shrine"):
        return "temple"
    if tags.get("amenity") in ("school", "college", "kindergarten"):
        return "school"
    if tags.get("shop"):
        return "shop"
    if tags.get("office") or tags.get("amenity") or tags.get("tourism"):
        return "office"
    if a_m2 < 45:
        return "shed"
    if lev >= 4 or a_m2 > 2500:
        return "office" if under != LAWN or a_m2 > 2500 else "residential"
    if lev == 3:
        return "residential"
    if under == LAWN and 90 <= a_m2 <= 2500:
        return "bungalow"
    return "residential" if a_m2 < 900 else "office"


# ───────────────────────── verges, compounds, trees ─────────────────────────

def distance_map(m, sources):
    """Chebyshev distance in cells from the nearest source cell (breadth first, 8 neighbours)."""
    d = [-1] * (m.w * m.h)
    q = collections.deque()
    for k in sources:
        d[k] = 0
        q.append(k)
    while q:
        k = q.popleft()
        x, y = k % m.w, k // m.w
        for dx, dy in NB8:
            nx, ny = x + dx, y + dy
            if m.inb(nx, ny) and d[ny * m.w + nx] < 0:
                d[ny * m.w + nx] = d[k] + 1
                q.append(ny * m.w + nx)
    return d


def make_verges(m):
    """The strip of private ground that touches a road is public verge: walkable, planted with the avenue."""
    road = [k for k in range(m.w * m.h) if m.ground[k] == ROAD]
    d = distance_map(m, road)
    for k in range(m.w * m.h):
        if m.ground[k] == LAWN and d[k] == 1 and m.bid[k] < 0:
            m.ground[k] = GRASS
    return d


def infer_compounds(m, rd):
    """Bungalow plots are not mapped in OSM. Each cluster of bungalow buildings in private ground gets the plot
    nearest to it (a breadth-first Voronoi, at most R cells out), a wall round it, a gate towards the road and a
    gravel drive. Walls and gates made here are flagged `inferred`."""
    w, h, R = m.w, m.h, PLOT_R
    seeds = [i for i, b in enumerate(m.buildings) if b.kind in ("bungalow", "shed") and b.cells]
    parent = {i: i for i in seeds}

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    owner = {}
    for i in seeds:
        for x, y in m.buildings[i].cells:
            owner[(x, y)] = i
    for (x, y), i in owner.items():
        for dx in (-2, -1, 0, 1, 2):
            for dy in (-2, -1, 0, 1, 2):
                j = owner.get((x + dx, y + dy))
                if j is not None and j != i:
                    parent[find(i)] = find(j)
    clusters = collections.defaultdict(list)
    for i in seeds:
        clusters[find(i)].append(i)
    keep = []
    for root, ids in sorted(clusters.items()):
        bs = [m.buildings[i] for i in ids]
        main = max(bs, key=lambda b: b.area)
        gx, gy = ring_centroid(main.ring)
        under = m.get(int(gx), int(gy))
        if main.kind == "bungalow" and under in (LAWN, GRASS) and main.area * m.proj.res ** 2 >= 120:
            keep.append(ids)
    label = {}
    q = collections.deque()
    for n, ids in enumerate(keep, 1):
        for i in ids:
            for c in m.buildings[i].cells:
                if c not in label:
                    label[c] = n
                    q.append((c, 0))
    while q:
        (x, y), dist = q.popleft()
        if dist >= R:
            continue
        for dx, dy in NB8:
            c = (x + dx, y + dy)
            if c in label or not m.inb(*c):
                continue
            k = c[1] * w + c[0]
            if m.ground[k] != LAWN or m.bid[k] >= 0 or rd[k] < 2:
                continue
            label[c] = label[(x, y)]
            q.append((c, dist + 1))
    walls = {}
    for (x, y), L in label.items():
        k = y * w + x
        if m.bid[k] >= 0:
            continue
        for dx, dy in NB4:
            n = label.get((x + dx, y + dy), 0)
            if n != L and (n == 0 or L < n):
                walls[(x, y)] = L
                break
    for (x, y), L in list(walls.items()):        # a wall that only touches diagonally gets a cell to join it
        for dx, dy in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
            if walls.get((x + dx, y + dy)) == L and (x + dx, y) not in walls and (x, y + dy) not in walls:
                for c in ((x + dx, y), (x, y + dy)):
                    if label.get(c) == L and m.bid[c[1] * w + c[0]] < 0:
                        walls[c] = L
                        break
    for (x, y), L in walls.items():
        m.set(x, y, WALL)
        m.inferred[y * w + x] = 1
    plots = []
    for n, ids in enumerate(keep, 1):
        cells = [c for c, L in label.items() if L == n]
        wall = [c for c, L in walls.items() if L == n]
        main = max((m.buildings[i] for i in ids), key=lambda b: b.area)
        cx, cy = ring_centroid(main.ring)
        gate = None
        best = None
        for (x, y) in wall:
            for dx, dy in NB4:
                ox, oy = x + dx, y + dy
                if not m.inb(ox, oy) or label.get((ox, oy), 0) != 0 or m.cost(ox, oy) == INF:
                    continue
                k = oy * w + ox
                score = (rd[k], abs(x + .5 - cx) + abs(y + .5 - cy))
                if best is None or score < best[0]:
                    best = (score, (x, y), (ox, oy))
        drive = []
        if best:
            gate, out = best[1], best[2]
            m.set(gate[0], gate[1], GATE)
            tx, ty = min(((x, y) for i in ids for x, y in m.buildings[i].cells), key=lambda c: abs(c[0] - gate[0]) + abs(c[1] - gate[1]))
            inner = (2 * gate[0] - out[0], 2 * gate[1] - out[1])     # the cell straight in from the gate
            line = [inner] if label.get(inner) == n and m.bid[inner[1] * w + inner[0]] < 0 else []
            for x, y in line + segment_cells(gate[0] + .5, gate[1] + .5, tx + .5, ty + .5)[1:]:
                k = y * w + x
                if m.bid[k] >= 0:
                    break
                if m.ground[k] == LAWN:
                    m.ground[k] = SAND
                    drive.append((x, y))
                elif m.ground[k] == SAND and (x, y) not in drive and label.get((x, y)) == n:
                    drive.append((x, y))
        plots.append({"n": n, "buildings": ids, "cells": cells, "walls": wall, "gate": gate, "out": best[2] if best else None,
                      "drive": drive, "main": main})
    m.plots = plots
    return plots


def plant(m, osm, rd, reserved):
    w, h, P = m.w, m.h, m.proj
    rng = random.Random(1820)
    TREEABLE = (GRASS, LAWN, PGRASS, PLAZA)
    ok = lambda x, y, kinds=TREEABLE: (m.inb(x, y) and m.ground[y * w + x] in kinds and m.bid[y * w + x] < 0 and (y * w + x) not in reserved
                                      and (y * w + x) not in m.touched and (x, y) not in m.trees)
    for nid, tags in osm.ntags.items():
        if tags.get("natural") == "tree":
            x, y = P.xy(*osm.nodes[nid])
            if ok(int(x), int(y)):
                m.trees.add((int(x), int(y)))
    for wid, (nds, tags) in osm.ways.items():
        if tags.get("natural") == "tree_row":
            pts = [P.xy(*osm.nodes[n]) for n in nds if n in osm.nodes]
            for x, y in polyline_cells(pts, w, h):
                if ok(x, y, TREEABLE + (PATH,)) and m.ground[y * w + x] != PATH:
                    m.trees.add((x, y))
    inhabited = {}
    for y in range(h):
        for x in range(w):
            k = y * w + x
            g = m.ground[k]
            if m.bid[k] >= 0 or k in reserved or k in m.touched or (x, y) in m.trees:
                continue
            r = rng.random()
            if g in (GRASS, LAWN) and rd[k] == 1 and (x + y) % 2 == 0:
                m.trees.add((x, y))                        # the avenue
            elif g == GRASS:
                if r < 0.04:
                    m.trees.add((x, y))
                elif r < 0.05:
                    m.bushes.add((x, y))
            elif g == LAWN:
                if r < 0.07:
                    m.trees.add((x, y))
                elif r < 0.10:
                    m.bushes.add((x, y))
            elif g == PGRASS:
                if r < 0.16:
                    m.trees.add((x, y))
                elif r < 0.185:
                    m.bushes.add((x, y))
            elif g == PLAZA and r < 0.01:
                m.trees.add((x, y))
    m.freeze_plants()


# ───────────────────────── places ─────────────────────────

def osm_xy(m, osm, ref):
    P = m.proj
    if isinstance(ref, tuple):
        return P.xy(*ref)
    if ref in osm.nodes:
        return P.xy(*osm.nodes[ref])
    if ref in osm.ways:
        ring = [P.xy(*p) for p in osm.way_ll(ref)]
        return ring_centroid(ring)
    raise KeyError(ref)


def snap(m, x, y, kinds=GOOD_SPOT, maxr=5):
    """The nearest cell of a walkable kind to (x, y), by growing squares."""
    cx, cy = int(math.floor(x)), int(math.floor(y))
    best = None
    for r in range(0, maxr + 1):
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                if max(abs(dx), abs(dy)) != r:
                    continue
                nx, ny = cx + dx, cy + dy
                if m.inb(nx, ny) and m.ground[ny * m.w + nx] in kinds and m.cost(nx, ny) < INF:
                    d = math.hypot(nx + .5 - x, ny + .5 - y)
                    if best is None or d < best[0]:
                        best = (d, nx, ny)
        if best and best[0] <= r + 0.5:
            break
    return (best[1], best[2]) if best else None


def pick_home(m):
    """A real bungalow plot on Tughlak Road: its gate on the road, a nameless building of a bungalow's size, room for
    a garden, as near 28.595 N, 77.212 E as the data allows."""
    tx, ty = m.proj.xy(28.595, 77.212)
    best = None
    for p in m.plots:
        if not p["gate"] or not p["out"] or m.cost(*p["out"]) == INF:
            continue
        if not any(m.road_name_at(p["out"][0] + dx, p["out"][1] + dy) == "Tughlak Road" for dx, dy in NB8 + ((0, 0),)):
            continue
        b = p["main"]
        a = b.area * m.proj.res ** 2
        if b.name or "name" in b.tags or not (250 <= a <= 1200):
            continue
        free = sum(1 for x, y in p["cells"] if m.ground[y * m.w + x] in (LAWN, SAND) and m.bid[y * m.w + x] < 0)
        cx, cy = ring_centroid(b.ring)
        score = math.hypot(cx - tx, cy - ty) + (0 if free >= 14 else 2 * (14 - free)) + (0 if p["drive"] else 4)
        if best is None or score < best[0]:
            best = (score, p)
    return best[1] if best else None


def footsteps(m, osm, centre, radius):
    """The footway beside the memorial (Gandhi's last steps), as cells, in walking order."""
    P = m.proj
    best = []
    for wid, (nds, tags) in osm.ways.items():
        if tags.get("highway") != "footway" or tags.get("footway") in ("crossing", "sidewalk"):
            continue
        pts = [P.xy(*osm.nodes[n]) for n in nds if n in osm.nodes]
        if pts and min(math.hypot(x - centre[0], y - centre[1]) for x, y in pts) <= radius and len(pts) >= 2:
            cells = [list(c) for c in polyline_cells(pts, m.w, m.h)]
            if len(cells) > len(best):
                best = cells
    return best


def place_pois(m, osm):
    """rect, spot, entrance (and loops) for the page's place ids; marks Hegel's own bungalow."""
    pois, P = {}, m.proj
    home = pick_home(m)
    if home:
        b = home["main"]
        b.kind, b.name, b.id = "home", None, "home"
        cells = home["cells"] + home["walls"]
        gate, out = home["gate"], home["out"]
        drive = home["drive"]
        spot = drive[-1] if drive else out      # the verandah; the entrance (for the walking times) is the road outside the gate
        pois["home"] = {"rect": bbox_of(cells), "spot": list(spot), "entrance": list(out), "gate": list(gate)}
        names = [m.road_name_at(out[0] + dx, out[1] + dy) for dx, dy in NB8 + ((0, 0),)]
        m.notes["home"] = {"road": "Tughlak Road" if "Tughlak Road" in names else next((n for n in names if n), "")}
    for pid, spec in PLACE_SPECS.items():
        poly = [P.xy(*p) for p in osm.way_ll(spec["area"])] if spec["area"] in osm.ways else None
        if poly is None:
            continue
        rect = bbox_of([(int(math.floor(x)), int(math.floor(y))) for x, y in poly])
        rect = [max(0, rect[0]), max(0, rect[1]), min(m.w - 1, rect[2]), min(m.h - 1, rect[3])]
        if "gate" in spec:
            gx, gy = osm_xy(m, osm, spec["gate"])
        else:
            gx, gy = P.xy(*spec["spot"])
        ent = snap(m, gx, gy)
        if not ent:
            continue
        if pid == "gandhi":      # the memorial plus its garden
            rect = [rect[0] - 3, rect[1] - 3, rect[2] + 3, rect[3] + 3]
        rect = [max(0, min(rect[0], ent[0])), max(0, min(rect[1], ent[1])), min(m.w - 1, max(rect[2], ent[0])), min(m.h - 1, max(rect[3], ent[1]))]
        poi = {"rect": rect, "spot": list(ent), "entrance": list(ent)}
        if pid == "gandhi":
            poi["steps"] = footsteps(m, osm, ring_centroid(poly), 8)
        if "loop" in spec:
            loop = []
            for ref in spec["loop"]:
                x, y = osm_xy(m, osm, ref)
                c = snap(m, x, y, {PATH, FOOT, SAND, ROAD, PLAZA, PARKING}, 7)
                if c and list(c) != (loop[-1] if loop else None):
                    loop.append(list(c))
            if not loop or loop[0] != list(ent):              # a stroll starts and ends where the walk to it does
                loop.insert(0, list(ent))
            if loop[-1] != list(ent):
                loop.append(list(ent))
            poi["loop"] = loop
        pois[pid] = poi
    m.pois = pois
    return pois


# ───────────────────────── walking ─────────────────────────

def cost_grid(m):
    return [m.cost(k % m.w, k // m.w) for k in range(m.w * m.h)]


def dijkstra(w, h, cost, src, res=RES):
    """Cheapest path from cell index `src` to every cell, 8 neighbours, no corner cutting. Returns (cost, metres)."""
    dist = [INF] * (w * h)
    met = [0.0] * (w * h)
    dist[src] = 0.0
    heap = [(0.0, src)]
    while heap:
        d, k = heapq.heappop(heap)
        if d > dist[k]:
            continue
        x, y = k % w, k // w
        for dx, dy in NB8:
            nx, ny = x + dx, y + dy
            if not (0 <= nx < w and 0 <= ny < h):
                continue
            nk = ny * w + nx
            c = cost[nk]
            if c == INF:
                continue
            step = 1.0
            if dx and dy:
                if cost[y * w + nx] == INF or cost[ny * w + x] == INF:
                    continue
                step = SQ2
            nd = d + step * c
            if nd < dist[nk]:
                dist[nk] = nd
                met[nk] = met[k] + step * res
                heapq.heappush(heap, (nd, nk))
    return dist, met


def edge_exit(m, cost, home_src):
    """The cell on the north edge that is the cheapest way towards Nirman Bhawan: the walk to it plus the rest of
    the way as the crow flies, times 1.3."""
    dist, met = dijkstra(m.w, m.h, cost, home_src, m.proj.res)
    nbx, nby = m.proj.xy(*NIRMAN_BHAWAN)
    best = None
    for x in range(m.w):
        k = x
        if dist[k] == INF:
            continue
        total = met[k] + 1.3 * math.hypot(x + .5 - nbx, 0.5 - nby) * m.proj.res
        if best is None or total < best[0]:
            best = (total, x)
    return (best[1], 0) if best else None


def walk_table(m, entrances, estates=None):
    """Minutes between every pair of places: the metres of the cheapest grid path between entrances at PACE m/min,
    rounded. `estates` is the north-edge cell of the road to Nirman Bhawan: the path to it, plus the rest as the
    crow flies times 1.3. Returns ({"a-b": minutes}, {"a-b": metres})."""
    cost = cost_grid(m)
    ids = list(entrances)
    nbx, nby = m.proj.xy(*NIRMAN_BHAWAN)
    metres = {}
    runs = {}
    for a in ids:
        x, y = entrances[a]
        runs[a] = dijkstra(m.w, m.h, cost, y * m.w + x, m.proj.res)
    names = list(ids) + (["estates"] if estates else [])
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            if "estates" in (a, b):
                other = b if a == "estates" else a
                ex, ey = estates
                d = runs[other][1][ey * m.w + ex] if runs[other][0][ey * m.w + ex] < INF else INF
                rest = 1.3 * math.hypot(ex + .5 - nbx, ey + .5 - nby) * m.proj.res
                metres[a + "-" + b] = d + rest
            else:
                k = entrances[b][1] * m.w + entrances[b][0]
                metres[a + "-" + b] = runs[a][1][k] if runs[a][0][k] < INF else INF
    return {k: (round(v / PACE) if v < INF else None) for k, v in metres.items()}, metres


def signs_for(m, estates):
    """Exit signs where the main roads leave the map: Nirman Bhawan (north), Chanakyapuri (west), Hauz Khas (south).
    Each stands on the verge beside the road, a tile in from the edge."""
    out = []

    def edge_roads(edge, names):
        cells = []
        for x in range(m.w):
            for y in range(m.h):
                on = (edge == "north" and y == 0) or (edge == "south" and y == m.h - 1) or (edge == "west" and x == 0)
                if on and m.ground[y * m.w + x] == ROAD and (not names or m.road_name_at(x, y) in names):
                    cells.append((x, y))
        return cells

    def verge_beside(x, y, edge):
        """A free open cell next to the road cell, a little in from the edge."""
        dx, dy = (0, 1) if edge == "north" else (0, -1) if edge == "south" else (1, 0)
        for step in (1, 2, 3):
            for side in (1, -1, 2, -2, 3, -3):
                cx, cy = x + dx * step + (side if dy else 0), y + dy * step + (side if dx else 0)
                if m.inb(cx, cy) and m.ground[cy * m.w + cx] in (GRASS, LAWN, PGRASS) and m.bid[cy * m.w + cx] < 0 and m.cost(cx, cy) < INF:
                    return cx, cy
        return x, y
    for label, sub, edge, names, target in (
            ("Nirman Bhawan", "Directorate of Estates", "north", None, estates),
            ("Chanakyapuri", None, "west", {"Mustafa Kemal Ataturk Marg"}, (28.5976, 77.1888)),
            ("Hauz Khas", None, "south", {"Aurobindo Marg"}, (28.5494, 77.2001))):
        cells = edge_roads(edge, names)
        if not cells:
            continue
        tx, ty = target if edge == "north" else m.proj.xy(*target)
        x, y = min(cells, key=lambda c: math.hypot(c[0] - tx, c[1] - ty))
        sx, sy = verge_beside(x, y, edge)
        sign = {"x": sx, "y": sy, "label": label}
        if sub:
            sign["sub"] = sub
        out.append(sign)
    return out


# ───────────────────────── assembling ─────────────────────────

def build_map(osm, bbox=BBOX, res=RES, full=True):
    """Rasterise an OSM extract. `full` adds the inferred compounds, the page's places, the planting."""
    m = Map(Proj(bbox, res))
    areas = list(iter_areas(osm))
    classify_ground(m, osm, areas)
    lay_roads(m, osm)
    lay_paths(m, osm)
    lay_walls(m, osm)
    lay_buildings(m, osm, areas)
    rd = make_verges(m)
    if full:
        infer_compounds(m, rd)
        place_pois(m, osm)
        reserved = set()
        for p in m.pois.values():
            pts = [p["spot"], p["entrance"]] + p.get("loop", []) + ([p["gate"]] if "gate" in p else [])
            for x, y in pts:
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        if m.inb(x + dx, y + dy):
                            reserved.add((y + dy) * m.w + x + dx)
        for p in m.plots:
            for c in [p["gate"], p["out"]] + p["drive"]:
                if c:
                    reserved.add(c[1] * m.w + c[0])
        plant(m, osm, rd, reserved)
    m.freeze_plants()
    return m


def finish_places(m):
    """The off-map Directorate: the north-edge cell on the way to Nirman Bhawan, and the exit signs."""
    cost = cost_grid(m)
    if "home" not in m.pois:
        return None
    hx, hy = m.pois["home"]["entrance"]
    ex = edge_exit(m, cost, hy * m.w + hx)
    if ex:
        m.pois["estates"] = {"rect": [max(0, ex[0] - 1), 0, min(m.w - 1, ex[0] + 1), 2], "spot": list(ex), "entrance": list(ex)}
    m.signs = signs_for(m, ex or (0, 0))
    return ex


# ───────────────────────── output ─────────────────────────

def rle(values):
    out, prev, n = [], None, 0
    for v in values:
        if v == prev:
            n += 1
        else:
            if prev is not None:
                out += [prev, n]
            prev, n = v, 1
    if prev is not None:
        out += [prev, n]
    return out


def unrle(runs):
    out = []
    for i in range(0, len(runs), 2):
        out += [runs[i]] * runs[i + 1]
    return out


def delta(sorted_ints):
    out, prev = [], 0
    for v in sorted_ints:
        out.append(v - prev)
        prev = v
    return out


def to_json(m, metres=None):
    P = m.proj
    roads = []
    for r in m.roads:
        if r.cells:
            roads.append({"name": r.name, "class": r.cls, "cells": delta(sorted(r.cells))})
    # the page indexes roads by position, so keep the order of m.roads and drop none
    roads = [{"name": r.name, "class": r.cls, "cells": delta(sorted(r.cells))} for r in m.roads]
    buildings = []
    for b in m.buildings:
        o = {"id": b.id, "kind": b.kind}
        if b.name:
            o["name"] = b.name
        if b.style:
            o["style"] = b.style
        if b.lev > 1:
            o["lev"] = b.lev
        o["poly"] = [int(round(v * QUANT)) for p in b.ring for v in p]
        o["cells"] = delta(sorted(y * m.w + x for x, y in b.cells))
        buildings.append(o)
    out = {
        "version": 1,
        "attribution": "© OpenStreetMap contributors, ODbL",
        "license": "Open Database License 1.0, https://opendatacommons.org/licenses/odbl/1-0/",
        "bbox": {"south": P.south, "west": P.west, "north": P.north, "east": P.east},
        "origin": {"lat": P.north, "lon": P.west},
        "metres_per_tile": P.res,
        "w": m.w, "h": m.h,
        "poly_quantum": QUANT,
        "classes": CLASSES,
        "ground": rle(m.ground),
        "buildings": buildings,
        "roads": roads,
        "trees": [list(c) for c in sorted(m.trees, key=lambda c: (c[1], c[0]))],
        "bushes": [list(c) for c in sorted(m.bushes, key=lambda c: (c[1], c[0]))],
        "courts": [[kind] + [int(round(v * QUANT)) for p in ring for v in p] for kind, ring in m.courts],
        "roundabouts": m.roundabouts,
        "signs": m.signs,
        "pois": m.pois,
    }
    if metres:
        out["walk_metres"] = {k: (round(v) if v < INF else None) for k, v in sorted(metres.items())}
    return out


def dumps(obj):
    """Compact JSON, one top-level key per line so diffs stay readable."""
    parts = []
    for k, v in obj.items():
        parts.append(json.dumps(k) + ":" + json.dumps(v, separators=(",", ":"), ensure_ascii=False))
    return "{\n" + ",\n".join(parts) + "\n}\n"


# ───────────────────────── debug picture ─────────────────────────

PNG_COL = {GRASS: (140, 207, 99), ROAD: (143, 148, 164), FOOT: (224, 208, 155), PATH: (233, 221, 176), WATER: (75, 147, 218),
           LAWN: (162, 219, 119), WALL: (194, 100, 74), GATE: (240, 60, 60), TREE: (47, 122, 62), FLOWER: (226, 69, 127),
           RGRASS: (153, 216, 111), PGRASS: (130, 197, 92), HEDGE: (60, 127, 62), SAND: (232, 220, 194), BLD: (200, 200, 200),
           COURT: (201, 122, 79), REDWALL: (150, 63, 44), PARKING: (190, 190, 200), PLAZA: (236, 228, 208)}
KIND_COL = {"bungalow": (240, 238, 232), "residential": (222, 212, 190), "office": (190, 196, 210), "shop": (240, 180, 70),
            "shed": (170, 150, 140), "school": (216, 160, 130), "temple": (232, 190, 140), "tomb": (168, 153, 138),
            "safdarjung": (201, 113, 79), "memorial": (255, 255, 255), "club": (196, 101, 74), "shops": (242, 177, 52),
            "iic": (185, 176, 160), "home": (255, 216, 77)}


def write_png(path, width, height, rgb):
    raw = b"".join(b"\x00" + bytes(rgb[y * width * 3:(y + 1) * width * 3]) for y in range(height))

    def chunk(t, d):
        c = struct.pack(">I", len(d)) + t + d
        return c + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
                + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b""))


def debug_png(m, path, s=5):
    W, H = m.w * s, m.h * s
    img = bytearray(W * H * 3)

    def paint(x0, y0, x1, y1, col):
        for y in range(max(0, y0), min(H, y1)):
            row = y * W * 3
            for x in range(max(0, x0), min(W, x1)):
                img[row + x * 3: row + x * 3 + 3] = bytes(col)
    for y in range(m.h):
        for x in range(m.w):
            paint(x * s, y * s, x * s + s, y * s + s, PNG_COL[m.ground[y * m.w + x]])
    for b in m.buildings:
        ring = [(px * s, py * s) for px, py in b.ring]
        for x, y in fill_cells([ring], W, H):
            img[(y * W + x) * 3:(y * W + x) * 3 + 3] = bytes(KIND_COL.get(b.kind, (150, 150, 150)))
    for x, y in m.trees:
        paint(x * s + 1, y * s + 1, x * s + s - 1, y * s + s - 1, (30, 100, 45))
    for x, y in m.bushes:
        paint(x * s + 2, y * s + 2, x * s + s - 2, y * s + s - 2, (226, 69, 127))
    for pid, p in m.pois.items():
        x, y = p["spot"]
        paint(x * s - 2, y * s - 2, x * s + s + 2, y * s + s + 2, (255, 0, 255))
        for x, y in p.get("loop", []):
            paint(x * s, y * s, x * s + s, y * s + s, (255, 120, 0))
    write_png(path, W, H, img)


# ───────────────────────── places.json ─────────────────────────

def walk_block(table):
    """The "walk" block of places.json, laid out as before: one line per first place."""
    lines, by = [], collections.OrderedDict()
    for k, v in table.items():
        by.setdefault(k.split("-")[0], []).append('"%s": %s' % (k, v))
    for first, items in by.items():
        lines.append("    " + ", ".join(items))
    return '  "walk": {\n' + ",\n".join(lines) + "\n  }"


def update_places(table, path=PLACES_JSON, ids=None):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    old = json.loads(text)["walk"]
    ids = ids or list(json.loads(text)["places"])
    ordered = collections.OrderedDict()
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            key = a + "-" + b if a + "-" + b in table else b + "-" + a
            ordered[a + "-" + b] = table[key]
    new_text = re.sub(r'  "walk": \{.*?\n  \}', lambda _: walk_block(ordered), text, count=1, flags=re.S)
    json.loads(new_text)
    with open(path, "w", encoding="utf-8") as f:
        f.write(new_text)
    return old, ordered


def print_table(old, new, metres):
    print("%-22s %7s %7s %8s" % ("pair", "before", "after", "metres"))
    for k, v in new.items():
        ok = old.get(k, old.get("-".join(reversed(k.split("-")))))
        mm = metres.get(k, metres.get("-".join(reversed(k.split("-"))), 0))
        print("%-22s %7s %7s %8s" % (k, ok, v, round(mm)))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--offline", action="store_true", help="use only tools/.cache")
    ap.add_argument("--png", help="write a debug picture")
    ap.add_argument("--no-write", action="store_true", help="do not write the JSON or places.json")
    ap.add_argument("--out", default=OUT)
    args = ap.parse_args(argv)
    t0 = time.time()
    files = fetch_tiles(offline=args.offline)
    osm = parse_osm(files)
    print("parsed %d nodes, %d ways, %d relations from %d tiles in %.1fs (%d API requests this run)"
          % (len(osm.nodes), len(osm.ways), len(osm.rels), len(files), time.time() - t0, requests_made))
    m = build_map(osm)
    ex = finish_places(m)
    entrances = {pid: tuple(p["entrance"]) for pid, p in m.pois.items() if pid != "estates"}
    table, metres = walk_table(m, entrances, tuple(m.pois["estates"]["entrance"]) if "estates" in m.pois else None)
    missing = [k for k, v in table.items() if v is None]
    if missing:
        print("UNREACHABLE:", missing, file=sys.stderr)
    if args.png:
        debug_png(m, args.png)
    print("grid %dx%d at %g m, %d buildings, %d roads, %d trees, %d plots, home on %s"
          % (m.w, m.h, m.proj.res, len(m.buildings), len(m.roads), len(m.trees), len(m.plots), m.notes.get("home", {}).get("road")))
    if args.no_write:
        return 0
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(dumps(to_json(m, metres)))
    print("wrote %s (%d bytes)" % (os.path.relpath(args.out, ROOT), os.path.getsize(args.out)))
    old, new = update_places(table, ids=["home", "lodhi", "safdarjung", "khan", "gandhi", "gym", "iic", "estates"])
    print_table(old, new, metres)
    return 0


if __name__ == "__main__":
    sys.exit(main())
