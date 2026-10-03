"""Delhi time, minutes of the day, and the sun over Lutyens' Delhi."""
import math
from datetime import date, datetime, timedelta, timezone

IST = timezone(timedelta(hours=5, minutes=30), "IST")
LAT, LON = 28.600, 77.210           # Tughlak Road, roughly
DAY_ONE = date(2026, 10, 2)
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
DAYNAMES = [w[:3] for w in WEEKDAYS]
MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]


def now_ist():
    return datetime.now(IST)


def parse_now(text):
    """'2026-10-03T14:05' (Delhi time) -> aware datetime."""
    return datetime.fromisoformat(text).replace(tzinfo=IST)


def hm(text):
    """'06:05' -> 365. '24:00' is allowed and means the end of the day."""
    h, m = text.split(":")
    return int(h) * 60 + int(m)


def fmt(minutes):
    """365 -> '06:05'. 1440 -> '24:00'."""
    minutes = int(round(minutes))
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def minute_of(dt):
    return dt.hour * 60 + dt.minute


def at_dt(d, minutes):
    """Minute `minutes` of date d, in Delhi time."""
    return datetime(d.year, d.month, d.day, tzinfo=IST) + timedelta(minutes=minutes)


def days_match(spec, d):
    """'daily', 'Mon-Fri', 'Tue-Sun', 'Mon,Wed,Sat'."""
    if spec == "daily":
        return True
    wd = d.weekday()
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            a, b = (DAYNAMES.index(x) for x in part.split("-"))
            if (a <= wd <= b) if a <= b else (wd >= a or wd <= b):
                return True
        elif DAYNAMES.index(part) == wd:
            return True
    return False


def day_number(d):
    return (d - DAY_ONE).days + 1


def long_date(d):
    """'Saturday, 3 October 2026'."""
    return f"{WEEKDAYS[d.weekday()]}, {d.day} {MONTHS[d.month - 1]} {d.year}"


def sun(d, lat=LAT, lon=LON):
    """Sunrise and sunset in Delhi minutes for a date (NOAA approximation, about a minute)."""
    n = d.timetuple().tm_yday
    g = 2 * math.pi / 365 * (n - 1)
    eqt = 229.18 * (0.000075 + 0.001868 * math.cos(g) - 0.032077 * math.sin(g)
                    - 0.014615 * math.cos(2 * g) - 0.040849 * math.sin(2 * g))
    decl = (0.006918 - 0.399912 * math.cos(g) + 0.070257 * math.sin(g) - 0.006758 * math.cos(2 * g)
            + 0.000907 * math.sin(2 * g) - 0.002697 * math.cos(3 * g) + 0.00148 * math.sin(3 * g))
    phi = math.radians(lat)
    cos_ha = math.cos(math.radians(90.833)) / (math.cos(phi) * math.cos(decl)) - math.tan(phi) * math.tan(decl)
    ha = math.degrees(math.acos(max(-1.0, min(1.0, cos_ha))))
    rise = 720 - 4 * (lon + ha) - eqt + 330
    set_ = 720 - 4 * (lon - ha) - eqt + 330
    return round(rise), round(set_)
