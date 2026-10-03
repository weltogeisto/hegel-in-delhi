"""Talking to the mind on the PC (llama-server, OpenAI-compatible), and a stand-in for rehearsals."""
import json
import logging
import random
import subprocess
import time
import urllib.error
import urllib.request

from .contract import SCHEMA

log = logging.getLogger("world")


class MindAway(Exception):
    """The PC did not wake or did not answer."""


class HTTPMind:
    source = "mind"

    def __init__(self, url, wake=None, timeout=300, temperature=0.7):
        self.url, self.wake, self.timeout, self.temperature = url.rstrip("/"), wake, timeout, temperature
        self.ready = False

    def health(self, timeout=3):
        try:
            with urllib.request.urlopen(self.url + "/health", timeout=timeout) as r:
                return r.status == 200
        except Exception:
            return False

    def ensure_awake(self):
        if self.ready:
            return
        t0 = time.time()
        if self.wake:
            try:
                p = subprocess.run(["bash", self.wake], capture_output=True, text=True, timeout=240)
            except subprocess.TimeoutExpired:
                raise MindAway("wake_pc.sh timed out")
            if p.returncode != 0:
                raise MindAway("wake_pc.sh: " + (p.stderr or p.stdout).strip()[-200:])
        elif not self.health():
            raise MindAway(f"no answer from {self.url}/health")
        self.ready = True
        log.info("mind awake after %.0fs", time.time() - t0)

    def chat(self, messages, schema=None, max_tokens=700, temperature=None):
        self.ensure_awake()
        payload = {"model": "local", "messages": messages, "max_tokens": max_tokens,
                   "temperature": self.temperature if temperature is None else temperature,
                   "chat_template_kwargs": {"enable_thinking": False}}
        if schema:
            payload["response_format"] = {"type": "json_schema", "json_schema": {"name": "answer", "schema": schema}}
        for constrained in ((True, False) if schema else (False,)):
            if not constrained:
                payload.pop("response_format", None)
            req = urllib.request.Request(self.url + "/v1/chat/completions", data=json.dumps(payload).encode("utf-8"),
                                         headers={"Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as r:
                    data = json.loads(r.read().decode("utf-8"))
                return (data["choices"][0]["message"].get("content") or "").strip()
            except urllib.error.HTTPError as e:
                if constrained and schema and e.code in (400, 422, 500):
                    continue        # an older server without json_schema support: ask unconstrained
                raise MindAway(f"HTTP {e.code} from the mind")
            except (urllib.error.URLError, OSError, ValueError, KeyError) as e:
                raise MindAway(f"mind request failed: {e}")
        raise MindAway("no answer")

    def decide(self, messages, sit):
        return self.chat(messages, SCHEMA)


class StubMind:
    """A stand-in for rehearsals and tests: plausible, deterministic, clearly not Hegel.
    Its thoughts start with '(rehearsal)' so a stub day can never pass for a real one."""
    source = "stub"

    def ensure_awake(self):
        pass

    def decide(self, messages, sit):
        r = random.Random(sit["id"])
        h, m = map(int, sit["time"].split(":"))
        now, here, open_now = h * 60 + m, sit["place"], sit["open_now"]
        ans = {"thought": f"(rehearsal) {sit['time']}: {sit['event'][:80]}", "says": None, "buys": [], "revision": None}
        if any("refuses" in x.get("content", "") for x in messages if x["role"] == "user"):
            ans.update(action="walk" if here != "home" else "rest", place="home", minutes=30)
            return json.dumps(ans)
        out = [p for p in open_now if p not in ("home", "estates", here)]
        if now >= 22 * 60 or now < 5 * 60:
            ans.update(action="sleep" if here == "home" else "walk", place="home", minutes=240)
        elif now >= 21 * 60 + 15 and here != "home":
            ans.update(action="walk", place="home", minutes=30)
        elif here not in open_now:
            ans.update(action="walk", place="home", minutes=30)
        elif "arrive" in sit["event"]:
            ans.update(action=r.choice(["stay", "read", "stay"]), place=here, minutes=r.choice([45, 60, 75]))
        elif here == "home" and out and r.random() < 0.55 and now < 20 * 60:
            ans.update(action="walk", place=r.choice(out), minutes=30)
        elif here != "home" and r.random() < 0.5:
            ans.update(action="walk", place="home", minutes=30)
        else:
            ans.update(action=r.choice(["read", "write", "rest", "stay"]), place=here, minutes=r.choice([30, 45, 60, 90]))
        if sit["present"] and ans["action"] != "walk" and r.random() < 0.5:
            ans.update(action="talk", says="Namaste.")
        if here == "khan" and ans["action"] != "walk" and sit["imprest_left"] >= 20 and r.random() < 0.6:
            ans["buys"] = [{"item": "Chai, a cup", "price_inr": 20}]
        if here == "safdarjung" and ans["action"] != "walk" and "arrive" in sit["event"]:
            ans["buys"].append({"item": "Entry ticket, foreign visitors", "price_inr": 300})
        return json.dumps(ans)

    def chat(self, messages, schema=None, max_tokens=700, temperature=None):
        props = (schema or {}).get("properties", {})
        if "answer" in props:
            return json.dumps({"answer": "yes"})
        if "diary" in props:
            return json.dumps({"diary": "(rehearsal) The owl's diary would go here: a page in Hegel's hand about the day's one real movement, written from the record.",
                               "revision_log": "(rehearsal) No thesis moved today.",
                               "depesche": "(rehearsal) A Depesche would go here." if "depesche" in props else None,
                               "theses": []})
        return "{}"
