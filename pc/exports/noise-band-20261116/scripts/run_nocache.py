"""A seeded one-day rehearsal in which every call to the server also says cache_prompt=false, so that no reply depends on what the server
happened to hold from earlier requests. The only change is that one field in each POST body; the code under ~/w2/main is untouched.
    python3 run_nocache.py OUTDIR SEED"""
import json
import sys
import urllib.request
from pathlib import Path

OUT, SEED = sys.argv[1], sys.argv[2]
sys.path.insert(0, str(Path.home() / "w2/main"))
import world.__main__ as wm          # noqa: E402

real = urllib.request.urlopen


def tap(req, timeout=None):
    if isinstance(req, str) or getattr(req, "data", None) is None:       # health check and other GETs: untouched
        return real(req, timeout=timeout)
    payload = json.loads(req.data.decode("utf-8"))
    payload["cache_prompt"] = False
    new = urllib.request.Request(req.full_url, data=json.dumps(payload).encode("utf-8"), headers=dict(req.header_items()), method="POST")
    return real(new, timeout=timeout)


urllib.request.urlopen = tap
sys.argv = ["world", "simulate", "--docs", str(Path.home() / "w2/shadow-docs"), "--date", "2026-11-16", "--days", "1",
            "--mind", "http://127.0.0.1:8082", "--set", "HEGEL_DECISION_DRAWS=4", "--set", "HEGEL_CORRESPONDENT=1",
            "--seed", SEED, "--out", OUT]
wm.main()
