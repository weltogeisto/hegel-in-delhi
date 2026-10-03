"""Real-world feeds: weather, air quality and headlines. Cached per day; when a feed is down the world
falls back to the seasonal normal (weather) or to nothing (news, air) rather than inventing."""
import html
import json
import logging
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import timedelta

from .clock import LAT, LON

log = logging.getLogger("world")
UA = {"User-Agent": "hegel-in-delhi/1.0 (+https://weltogeisto.github.io/hegel-in-delhi/)"}

# Delhi monthly normals, mean daily max and min in °C.
NORMALS = {1: (21, 8), 2: (24, 11), 3: (30, 16), 4: (36, 22), 5: (40, 26), 6: (39, 28),
           7: (35, 27), 8: (34, 27), 9: (34, 25), 10: (33, 20), 11: (28, 13), 12: (23, 9)}
# CPCB National AQI breakpoints for 24-hour means: (conc lo, conc hi, index lo, index hi).
PM25 = [(0, 30, 0, 50), (30, 60, 50, 100), (60, 90, 100, 200), (90, 120, 200, 300), (120, 250, 300, 400), (250, 500, 400, 500)]
# The morning papers carry the state, the economy, the courts and the weather. Crime and violence stay out, which the
# page has no business setting beside a pixel-art walk; wars and civil strife stay in, so a headline on the crime list
# is dropped unless it is also about one of them.
CRIME = re.compile(r"\b(kill\w*|dead|death\w*|die[sd]?|dying|murder\w*|rape\w*|sexual\w*|assault\w*|harass\w*|molest\w*|abus\w*|"
                   r"suicide|accident\w*|crash\w*|blast\w*|explosion|shot|shoot\w*|stabb\w*|injur\w*|"
                   r"bod(y|ies)|lynch\w*|gang|arrest\w*|custody|missing|drown\w*|fire\b|burn\w*)", re.I)
STRIFE = re.compile(r"\b(wars?|warfare|armies|army|military|troops|soldiers?|ceasefire|missiles?|drones?|shelling|border|insurgen\w*|"
                    r"militant\w*|clash\w*|conflict\w*|unrest|curfew|protest\w*|riot\w*|communal|coup|rebels?|invasion|invad\w*|battle\w*|"
                    r"air ?strikes?|(?:military|missile|drone|rocket|artillery) strikes?)", re.I)
PM10 = [(0, 50, 0, 50), (50, 100, 50, 100), (100, 250, 100, 200), (250, 350, 200, 300), (350, 430, 300, 400), (430, 600, 400, 500)]


def fit_for_papers(title):
    """A headline the morning papers may carry: not about crime or violence, unless it is about war or civil strife."""
    return not CRIME.search(title) or bool(STRIFE.search(title))


def get(url, timeout=15):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def sub_index(c, table):
    if c is None:
        return None
    for lo, hi, ilo, ihi in table:
        if c <= hi:
            return round(ilo + (ihi - ilo) * (max(c, lo) - lo) / (hi - lo))
    return 500


def naqi(pm25, pm10):
    """India's National AQI from 24-hour PM2.5 and PM10 means (the larger sub-index)."""
    vals = [v for v in (sub_index(pm25, PM25), sub_index(pm10, PM10)) if v is not None]
    return max(vals) if vals else None


def sky(code, aqi, rain):
    if code is None:
        base = "clear"
    elif code == 0:
        base = "clear"
    elif code == 1:
        base = "mostly clear"
    elif code == 2:
        base = "partly cloudy"
    elif code == 3:
        base = "overcast"
    elif code in (45, 48):
        base = "fog"
    elif 51 <= code <= 57:
        base = "drizzle"
    elif 61 <= code <= 67:
        base = "heavy rain" if rain and rain >= 4 else "rain"
    elif 80 <= code <= 82:
        base = "a sudden heavy shower" if rain and rain >= 4 else "showers"
    elif code >= 95:
        base = "thunderstorm"
    else:
        base = "clear"
    if aqi and base in ("clear", "mostly clear", "partly cloudy"):
        if aqi >= 200:
            return "a brown haze"
        if aqi >= 150:
            return base + ", hazy"
    return base


def normal_hours(d):
    """A plausible day from the monthly normals: coolest at six, warmest at three."""
    hi, lo = NORMALS[d.month]
    hours = []
    for h in range(24):
        # piecewise-linear curve between 06:00 (min) and 15:00 (max)
        if 6 <= h <= 15:
            t = lo + (hi - lo) * (h - 6) / 9
        else:
            k = (h - 15) % 24
            t = hi - (hi - lo) * k / 15
        hours.append({"temp": round(t), "rain": 0.0, "code": None, "aqi": None, "sky": "clear"})
    return hours


class Feeds:
    def __init__(self, cfg):
        self.cfg = cfg
        self.dir = cfg.state / "feeds"
        self.online = cfg.feeds

    def _cache(self, name, max_age, fetch):
        path = self.dir / name
        if path.exists() and (max_age is None or time.time() - path.stat().st_mtime < max_age):
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except ValueError:
                pass
        if not self.online:
            return None
        try:
            data = fetch()
        except Exception as e:  # a dead feed must never stop the world
            log.warning("feed %s failed: %s", name, e)
            if path.exists():
                return json.loads(path.read_text(encoding="utf-8"))
            return None
        self.dir.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        return data

    def weather(self, d, today=None):
        """24 hourly dicts for date d: temp, rain (mm), code, aqi, sky. Plus 'source'."""
        fresh = 3 * 3600 if today is None or d >= today else None

        def fetch():
            start = (d - timedelta(days=1)).isoformat()
            q = {"latitude": LAT, "longitude": LON, "timezone": "Asia/Kolkata", "start_date": d.isoformat(), "end_date": d.isoformat()}
            fc = json.loads(get("https://api.open-meteo.com/v1/forecast?" + urllib.parse.urlencode(
                dict(q, hourly="temperature_2m,precipitation,weather_code"))))
            try:
                aq = json.loads(get("https://air-quality-api.open-meteo.com/v1/air-quality?" + urllib.parse.urlencode(
                    dict(q, start_date=start, hourly="pm2_5,pm10"))))
            except Exception as e:
                log.warning("air quality feed failed: %s", e)
                aq = None
            return {"forecast": fc, "air": aq}

        raw = self._cache(f"weather-{d.isoformat()}.json", fresh, fetch)
        if not raw:
            return {"source": "normal", "hours": normal_hours(d)}
        fc = raw["forecast"]["hourly"]
        hours = []
        pm25 = pm10 = []
        if raw.get("air"):
            pm25, pm10 = raw["air"]["hourly"].get("pm2_5") or [], raw["air"]["hourly"].get("pm10") or []
        for h in range(24):
            aqi = None
            if pm25 or pm10:
                i = h + 24          # air data starts a day earlier: trailing 24-hour mean
                w25 = [x for x in pm25[max(0, i - 23):i + 1] if x is not None]
                w10 = [x for x in pm10[max(0, i - 23):i + 1] if x is not None]
                aqi = naqi(sum(w25) / len(w25) if w25 else None, sum(w10) / len(w10) if w10 else None)
            temp = fc["temperature_2m"][h] if h < len(fc["temperature_2m"]) else None
            rain = (fc["precipitation"][h] if h < len(fc["precipitation"]) else 0) or 0
            code = fc["weather_code"][h] if h < len(fc["weather_code"]) else None
            hours.append({"temp": round(temp) if temp is not None else None, "rain": round(rain, 1),
                          "code": code, "aqi": aqi, "sky": sky(code, aqi, rain)})
        if any(x["temp"] is None for x in hours):
            normal = normal_hours(d)
            for x, n in zip(hours, normal):
                if x["temp"] is None:
                    x["temp"] = n["temp"]
        return {"source": "open-meteo", "hours": hours}

    def headlines(self, d, n=3):
        """Up to n real headlines for the morning papers, or [] when the feeds are down."""
        def fetch():
            seen, papers = set(), []
            for url in self.cfg.news_feeds:
                try:
                    root = ET.fromstring(get(url))
                except Exception as e:
                    log.warning("news feed %s failed: %s", url, e)
                    continue
                titles = []
                for item in root.iter("item"):
                    title = html.unescape(re.sub(r"<[^>]+>", "", item.findtext("title") or "")).strip()
                    title = re.sub(r"\s+", " ", title)
                    key = title.lower()[:60]
                    if 20 <= len(title) <= 160 and key not in seen and fit_for_papers(title):
                        seen.add(key)
                        titles.append(title)
                    if len(titles) >= 6:
                        break
                papers.append(titles)
            # alternate between papers so no single one owns the verandah
            out = [t for row in zip(*[p + [None] * (6 - len(p)) for p in papers]) for t in row if t]
            if not out:
                raise RuntimeError("no headlines from any feed")
            return out
        items = self._cache(f"news-{d.isoformat()}.json", None, fetch) or []
        return items[:n]
