"""What he looks up on his phone: Wikipedia's search, then the summary of the first page, kept in the state folder.
He has read it once it is in the record, so it counts as met for the 1831 gate."""
import http.client
import json
import logging
import re
import time
import urllib.error
import urllib.parse
import urllib.request

from .feeds import UA
from .works import cut

log = logging.getLogger("world")
API = "https://en.wikipedia.org"
EXTRACT = 700                                   # characters of the page that he reads
NOLOAD, NOTHING = "The page will not load.", "Nothing comes up for that."


def fetch(url, timeout=10):
    """The JSON at url. One more try after a short wait if Wikipedia says slow down (429), as it asks. Raises OSError on failure."""
    for attempt in (0, 1):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code != 429 or attempt:
                raise OSError(f"HTTP {e.code} from {url}")
            after = (e.headers or {}).get("Retry-After", "")
            time.sleep(min(10, int(after)) if after.isdigit() else 3)
        except (ValueError, http.client.HTTPException) as e:
            raise OSError(f"unusable answer from {url}: {e}")


def key(query):
    return re.sub(r"[^a-z0-9]+", "-", query.lower()).strip("-")[:60] or "page"


def find(query, cache):
    """{title, text, source, url} for the first page that Wikipedia finds for query, or {note} when it cannot be read.
    `cache` is a folder: a page once read is not fetched again."""
    p = cache / f"{key(query)}.json"
    try:
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass
    try:
        found = fetch(f"{API}/w/api.php?action=opensearch&search={urllib.parse.quote(query)}&limit=1&format=json")
        titles = found[1] if isinstance(found, list) and len(found) > 1 else []
        if not titles:
            return {"note": NOTHING}
        page = fetch(f"{API}/api/rest_v1/page/summary/{urllib.parse.quote(titles[0].replace(' ', '_'), safe='')}")
        text = " ".join(str(page.get("extract") or "").split())
        if not text:
            return {"note": NOTHING}
        url = ((page.get("content_urls") or {}).get("desktop") or {}).get("page") or f"{API}/wiki/{urllib.parse.quote(titles[0].replace(' ', '_'))}"
        got = {"title": str(page.get("title") or titles[0]), "text": cut(text, EXTRACT), "source": "Wikipedia", "url": url}
    except (OSError, ValueError, AttributeError, TypeError, IndexError) as e:
        log.warning("look-up of %r failed: %s", query, e)
        return {"note": NOLOAD}
    try:
        cache.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(got, ensure_ascii=False) + "\n", encoding="utf-8")
    except OSError:
        pass
    return got
