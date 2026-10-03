"""Talking to the mind on the PC (llama-server, OpenAI-compatible), and a stand-in for rehearsals."""
import json
import logging
import random
import re
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


THOUGHTS = [
    "{time}: the {a} and the {b} set me thinking about the {c}. I {doing}, {minutes} minutes.",
    "{time}. The {a} first, then the {b}; the {c} can wait. I {doing} for {minutes} minutes.",
    "{time}, then: a {a} here, a {b} there, the {c} between them. I {doing}, {minutes} minutes.",
    "{time}: nothing settles until the {a} has met the {b}. I {doing} while the {c} turns over.",
]
NOUNS = ("lamp tea stone fan gate bell paper ledger shutter verandah coin step chair kettle notebook shadow curtain "
         "spoon bicycle ticket cloth drawer window pigeon rickshaw umbrella wall clock bench branch stall bridge").split()
PLAN = [("07:30", "Walk to Lodhi Gardens with the papers"), ("10:30", "Khan Market: ink, and a look at the bookshop"),
        ("13:00", "Lunch, then an hour with the Hindi primer"), ("15:00", "Write up the morning's notes at the desk"),
        ("17:00", "See whether the Gymkhana plays bridge tonight"), ("20:00", "Dinner, and the day's reckoning")]
REPLIES = ["Namaste, sir. The weather is not what it was.", "Ji, sir? Tell me, what do you need?", "Arre, sir, the same as yesterday, only warmer.",
           "One minute, sir, I am just finishing this."]
DOINGS = ["Nods, and goes back to what was in hand.", None, "Looks at him a moment longer than needed.", None]
TITLES = ["Notes from the verandah", "On the morning's papers", "A page on the system of needs", "Letter about the bungalow"]
LINES = ["The morning came in with the papers and the heat.", "Nothing here is quite where I left it, and I am no longer sure I did the leaving.",
         "The tea arrived before the argument did.", "I set down what I saw and let the rest wait for the afternoon.",
         "A city is a thought that has learned to walk about.", "The lamp does what lamps do, and so, I suppose, do I."]
SINCE_MEAL = re.compile(r"last meal[^;]* (five|six|seven|eight|nine|ten|eleven|twelve|\d+) hours ago")


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
        ans = {"says": None, "buys": [], "revision": None}
        refused = sum("refuses" in x.get("content", "") for x in messages if x["role"] == "user")
        if refused:
            ans.update(action="walk" if here != "home" else "rest", place="home", minutes=30)
            return json.dumps(self.thought(ans, sit, refused))
        out = [p for p in open_now if p not in ("home", "estates", here)]
        ev = sit["event"]
        hungry = now >= 11 * 60 and ("hungry" in ev or any(SINCE_MEAL.search(x) for x in sit.get("on_mind", [])))
        if now >= 22 * 60 or now < 5 * 60:
            ans.update(action="sleep" if here == "home" else "walk", place="home", minutes=240)
        elif now >= 21 * 60 + 15 and here != "home":
            ans.update(action="walk", place="home", minutes=30)
        elif here not in open_now:
            ans.update(action="walk", place="home", minutes=30)
        elif here == "home" and ("laid out" in ev or "serves dinner" in ev):
            ans.update(action="eat", place="home", minutes=r.choice([30, 45]))
        elif hungry and here == "khan" and sit["imprest_left"] >= 220:
            ans.update(action="eat", place="khan", minutes=45, buys=[{"item": "Lunch at a dhaba: dal, rice, roti", "price_inr": 220}])
        elif "arrive" in ev:
            ans.update(action=r.choice(["stay", "read", "stay"]), place=here, minutes=r.choice([45, 60, 75]))
        elif here == "home" and out and r.random() < 0.55 and now < 20 * 60:
            ans.update(action="walk", place=r.choice(out), minutes=30)
        elif here != "home" and r.random() < 0.5:
            ans.update(action="walk", place="home", minutes=30)
        else:
            ans.update(action=r.choice(["read", "write", "rest", "stay"]), place=here, minutes=r.choice([30, 45, 60, 90]))
        if sit["present"] and ans["action"] not in ("walk", "eat") and r.random() < 0.5:
            ans.update(action="talk", says="Namaste.")
        if here == "khan" and ans["action"] != "walk" and not ans["buys"] and sit["imprest_left"] >= 20 and r.random() < 0.6:
            ans["buys"] = [{"item": "Chai, a cup", "price_inr": 20}]
        if here == "safdarjung" and ans["action"] != "walk" and "arrive" in sit["event"]:
            ans["buys"].append({"item": "Entry ticket, foreign visitors", "price_inr": 300})
        return json.dumps(self.thought(ans, sit))

    @staticmethod
    def thought(ans, sit, attempt=0):
        """A different thought for each situation (and each new attempt), from a small bank of templates."""
        r = random.Random(f"{sit['id']}|{attempt}")
        a, b, c = r.sample(NOUNS, 3)
        doing = f"{ans['action']} {'to' if ans['action'] == 'walk' else 'at'} {ans['place']}"
        text = r.choice(THOUGHTS).format(time=sit["time"], doing=doing, a=a, b=b, c=c, minutes=ans["minutes"])
        ans["thought"] = f"(rehearsal) {text}"
        return ans

    def chat(self, messages, schema=None, max_tokens=700, temperature=None):
        props = (schema or {}).get("properties", {})
        if "answer" in props:
            return json.dumps({"answer": "yes"})
        if "plan" in props:
            r = random.Random(messages[-1]["content"])
            items = [{"time": t, "intention": w} for t, w in PLAN[:r.randint(3, 6)]]
            items[0]["intention"] = "(rehearsal) " + items[0]["intention"]
            return json.dumps({"plan": items})
        if "does" in props:         # one of the people he meets, answering
            r = random.Random(messages[-1]["content"])
            return json.dumps({"says": "(rehearsal) " + r.choice(REPLIES), "does": r.choice(DOINGS)})
        if "continues" in props:    # what he wrote
            ask = messages[-1]["content"]
            shelf = re.findall(r"“([^”]+)” \(", ask.split("Your manuscripts so far:")[1]) if "Your manuscripts so far:" in ask else []
            r = random.Random(ask)
            title = shelf[-1] if shelf and r.random() < 0.7 else "(rehearsal) " + r.choice(TITLES)
            kind = r.choice(["essay", "notes", "letter"])
            return json.dumps({"title": title, "kind": kind, "to": "a friend in Berlin" if kind == "letter" else None,
                               "continues": title in shelf, "text": "(rehearsal) " + " ".join(r.sample(LINES, 3))})
        if "diary" in props:
            ask = messages[-1]["content"]
            times = re.findall(r"^(\d\d:\d\d) ", ask, re.M)
            theses = [{"id": i, "status": s, "evidence": times[:1]} for i, s in re.findall(r"(\w+): [^;]*? \((\w+)\)[;.]", ask.split("Your theses:")[-1])]
            return json.dumps({"diary": "(rehearsal) The owl's diary would go here: a page in Hegel's hand about the day's one real movement, written from the record.",
                               "revision_log": "(rehearsal) No thesis moved today.",
                               "depesche": "(rehearsal) A Depesche would go here." if "depesche" in props else None,
                               "theses": theses})
        return "{}"
