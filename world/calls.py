"""Every call to the mind written down in order, and played back (HEGEL_RECORD_CALLS; the check of a live morning against its replay,
asked on PR #1 on 21 November and answered there).

The recorder writes one JSON line per event to state/calls/calls-<UTC date>.jsonl:

  header   once a file: the hash of the code (world/ and mind/), the HEGEL_ switches, the mind's settings;
  tick     each tick that does something: the time the engine was given and the hash of the feed cache;
  call     each request in order: its moment (`at`, the step's time or "owl|<date>"), its kind (decision, voice, writing, complete,
           chat, tokens), the path, the full request, and the reply or the error it raised.

The player serves a recording back to an HTTPMind in place of the server: each request must equal the recorded one, field by field,
or it stops with the first difference. Nothing here calls a model. Evaluation only: no record is ever training data."""
import hashlib
import json
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

CODE = ("world", "mind")


def code_hash(repo):
    """sha256 over the paths and bytes of the code and the data it reads (world/, mind/), caches left out."""
    h = hashlib.sha256()
    for top in CODE:
        for p in sorted((Path(repo) / top).rglob("*")):
            if p.is_file() and "__pycache__" not in p.parts and p.suffix in (".py", ".json", ".md", ".txt"):
                h.update(str(p.relative_to(repo)).encode())
                h.update(p.read_bytes())
    return h.hexdigest()


def folder_hash(folder):
    """sha256 over the names and bytes of the files in a folder (the feed cache); None when it does not exist."""
    folder = Path(folder)
    if not folder.is_dir():
        return None
    h = hashlib.sha256()
    for p in sorted(folder.iterdir()):
        if p.is_file():
            h.update(p.name.encode())
            h.update(p.read_bytes())
    return h.hexdigest()


PLACES = ("HEGEL_STATE", "HEGEL_PUSH", "HEGEL_REPO", "HEGEL_ENV", "HEGEL_RECORD_CALLS")
SECRET = ("TOKEN", "KEY", "SECRET", "PASSWORD")


def switches(cfg):
    """The HEGEL_ switches and LEAD_MIN a Config was made from: not the ones that name places or the recording itself, and nothing
    whose name says it is a secret."""
    env = getattr(cfg, "values", None) or {}
    return {k: v for k, v in sorted(env.items()) if (k.startswith("HEGEL_") or k == "LEAD_MIN") and k not in PLACES
            and not any(s in k for s in SECRET)}


def utc():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Recorder:
    def __init__(self, folder, header=None):
        self.folder, self.header, self.path, self.n = Path(folder), dict(header or {}), None, 0

    def _write(self, row):
        path = self.folder / f"calls-{datetime.now(timezone.utc).date().isoformat()}.jsonl"
        if path != self.path:
            self.path = path
            self.folder.mkdir(parents=True, exist_ok=True)
            if not path.exists():
                self._line({"type": "header", "utc": utc(), **self.header})
        self._line(row)

    def _line(self, row):
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

    def call(self, at, kind, path, payload, reply=None, error=None):
        self.n += 1
        self._write({"type": "call", "i": self.n, "at": at, "kind": kind, "path": path, "payload": payload,
                     "reply": reply, "error": error, "utc": utc()})

    def tick(self, now, feeds):
        self._write({"type": "tick", "now": now.isoformat(timespec="seconds"), "feeds": feeds, "calls_before": self.n, "utc": utc()})


def read(paths):
    """The rows of one or more recording files, in order."""
    rows = []
    for p in paths:
        rows += [json.loads(line) for line in Path(p).read_text(encoding="utf-8").splitlines() if line.strip()]
    return rows


class Mismatch(Exception):
    pass


def first_difference(want, got, where=""):
    """The path of the first field where two JSON values differ, with both sides; None when they are equal."""
    if type(want) is not type(got) and not (isinstance(want, (int, float)) and isinstance(got, (int, float))):
        return f"{where or '(top)'}: recorded {short(want)}, replay {short(got)}"
    if isinstance(want, dict):
        for k in sorted(set(want) | set(got)):
            if k not in want or k not in got:
                return f"{where}.{k}: recorded {short(want.get(k, '(absent)'))}, replay {short(got.get(k, '(absent)'))}"
            d = first_difference(want[k], got[k], f"{where}.{k}")
            if d:
                return d
        return None
    if isinstance(want, list):
        for i, (a, b) in enumerate(zip(want, got)):
            d = first_difference(a, b, f"{where}[{i}]")
            if d:
                return d
        if len(want) != len(got):
            return f"{where}: recorded {len(want)} items, replay {len(got)}"
        return None
    if want != got:
        if isinstance(want, str) and isinstance(got, str):
            i = next((n for n, (a, b) in enumerate(zip(want, got)) if a != b), min(len(want), len(got)))
            return f"{where} at character {i}: recorded {short(want[max(0, i - 40):i + 80])}, replay {short(got[max(0, i - 40):i + 80])}"
        return f"{where}: recorded {short(want)}, replay {short(got)}"
    return None


def short(x, n=160):
    s = json.dumps(x, ensure_ascii=False)
    return s if len(s) <= n else s[:n] + "…"


class Player:
    """Serves the recorded calls in order. `send(path, payload)` stands in for HTTPMind._send."""

    def __init__(self, rows):
        self.calls = [r for r in rows if r.get("type") == "call"]
        self.pos = 0

    def send(self, path, payload):
        if self.pos >= len(self.calls):
            raise Mismatch(f"call {self.pos + 1}: the recording has no more calls ({path})")
        r = self.calls[self.pos]
        self.pos += 1
        where = f"call {r['i']} ({r['kind']} at {r['at']})"
        if r["path"] != path:
            raise Mismatch(f"{where}: recorded {r['path']}, replay {path}")
        d = first_difference(r["payload"], json.loads(json.dumps(payload)))
        if d:
            raise Mismatch(f"{where}: request{d if d.startswith(('.', '[')) else ' ' + d}")
        e = r.get("error")
        if e:
            if "http" in e:
                raise urllib.error.HTTPError(path, e["http"], "recorded", None, None)
            raise urllib.error.URLError(e.get("words", "recorded error"))
        return r["reply"]


def play(mind, player):
    """Make an HTTPMind ask the player instead of the server, already awake."""
    mind._send = player.send
    mind.ready = True
    return mind
