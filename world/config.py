"""Configuration from ~/.config/hegel/env (the same file the bash scripts source) and the environment."""
import os
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def read_env_file(path):
    values = {}
    try:
        lines = Path(path).read_text(encoding="utf-8").splitlines()
    except OSError:
        return values
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key.startswith("export "):
            key = key[len("export "):].strip()
        value = re.sub(r"\s+#.*$", "", value).strip().strip('"').strip("'")
        values[key] = value
    return values


class Config:
    def __init__(self, overrides=None):
        env_path = os.environ.get("HEGEL_ENV", str(Path.home() / ".config/hegel/env"))
        v = read_env_file(env_path)
        v.update({k: val for k, val in os.environ.items() if k.isupper()})
        v.update(overrides or {})
        self.values = v
        self.repo = Path(v.get("HEGEL_REPO", REPO)).expanduser()
        self.docs = self.repo / "docs"
        self.branch = v.get("HEGEL_BRANCH", "main")
        self.push = v.get("HEGEL_PUSH", "1") not in ("0", "no", "false", "")
        self.state = Path(v.get("HEGEL_STATE", Path.home() / ".local/state/hegel")).expanduser()
        self.lead = int(v.get("LEAD_MIN", "15"))
        self.feeds = v.get("HEGEL_FEEDS", "1") not in ("0", "no", "false", "")
        self.shelf = v.get("HEGEL_SHELF", "1") not in ("0", "no", "false", "")          # his books in front of him (mind/shelf)
        self.news_feeds = [u.strip() for u in v.get("NEWS_FEEDS", (
            "https://www.thehindu.com/news/national/feeder/default.rss,"
            "https://indianexpress.com/section/india/feed/")).split(",") if u.strip()]
        host, port = v.get("PC_HOST"), v.get("MIND_PORT", "8081")
        self.mind_url = v.get("MIND_URL") or (f"http://{host}:{port}" if host else None)
        self.owl_url = v.get("OWL_URL") or (f"http://{host}:{v.get('OWL_PORT', port)}" if host else self.mind_url)
        self.wake = str(self.repo / "scripts/wake_pc.sh") if v.get("PC_MAC") else None
        self.owl_at = v.get("OWL_AT", "01:30")
        self.depesche_day = v.get("DEPESCHE_DAY", "Saturday")
        self.timeout = int(v.get("MIND_TIMEOUT", "300"))

    def get(self, key, default=None):
        return self.values.get(key, default)
