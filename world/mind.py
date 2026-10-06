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

    def complete(self, prompt, max_tokens=700, temperature=None, seed=None):
        """The text that continues prompt, from llama-server's /completion: the raw prompt, no chat template, no system prompt and no stop
        string (a model that opens with a blank line would stop before its first word), so the caller cleans up. MindAway as for chat()."""
        self.ensure_awake()
        payload = {"prompt": prompt, "n_predict": max_tokens, "temperature": self.temperature if temperature is None else temperature,
                   "cache_prompt": False}
        if seed is not None:
            payload["seed"] = seed
        req = urllib.request.Request(self.url + "/completion", data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                content = json.loads(r.read().decode("utf-8"))["content"]
            return content if isinstance(content, str) else ""
        except urllib.error.HTTPError as e:
            raise MindAway(f"HTTP {e.code} from the mind")
        except (urllib.error.URLError, OSError, ValueError, KeyError, TypeError) as e:
            raise MindAway(f"mind request failed: {e}")

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
ABOUTS = ["the morning's walk and what it showed him", "the tea, the heat and the order of the day", "what the neighbours' habits say of the city",
          "a thought that would not wait for the afternoon"]
LINES = ["The morning came in with the papers and the heat.", "Nothing here is quite where I left it, and I am no longer sure I did the leaving.",
         "The tea arrived before the argument did.", "I set down what I saw and let the rest wait for the afternoon.",
         "A city is a thought that has learned to walk about.", "The lamp does what lamps do, and so, I suppose, do I."]
SINCE_MEAL = re.compile(r"last meal[^;]* (five|six|seven|eight|nine|ten|eleven|twelve|\d+) hours ago")
VOUCHERS = re.compile(r"(\d+) vouchers? pending ₹([\d,]+)")
DATE_AT = re.compile(r"(\w+ \d+ \w+) (\d\d:\d\d): (German lesson|your talk at the IIC)")      # an appointment line of the prompt


class StubMind:
    """A stand-in for rehearsals and tests: plausible, deterministic, clearly not Hegel.
    Its thoughts start with '(rehearsal)' so a stub day can never pass for a real one.
    It exercises the economy: it says yes to every offer, keeps its lessons and its talk, goes to the Directorate on a weekday
    once its vouchers pass ₹2,000, buys a phone and SIM at Khan Market once it has ₹10,000 and someone there to vouch, and looks up Marx once."""
    source = "stub"
    read = False                    # has the look-up he asked for come back?
    lesson = ("", 0)                # the day and the minute the lesson under way ends

    def ensure_awake(self):
        pass

    @staticmethod
    def booked(sit, now):
        """(place, minute) of a lesson or talk today that he must keep and that is near, else None."""
        for line in sit.get("on_mind", []):
            m = DATE_AT.match(line)
            if m and sit["day"].startswith(m[1]):
                at = int(m[2][:2]) * 60 + int(m[2][3:])
                if at - 90 <= now < at + 60:
                    return ("home" if m[3] == "German lesson" else "iic"), at
        return None

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
        ev, cash = sit["event"], sit["imprest_left"]
        hungry = now >= 11 * 60 and ("hungry" in ev or any(SINCE_MEAL.search(x) for x in sit.get("on_mind", [])))
        owns = any("You have a phone with a SIM" in x for x in sit.get("on_mind", []))
        if "On your phone you read" in ev or "look it up on" in ev or "page will not load" in ev or "Nothing comes up" in ev:
            self.read = True
        vouchers = next((int(v[2].replace(",", "")) for x in sit.get("on_mind", []) if (v := VOUCHERS.search(x))), 0)
        vouch = [p for p in sit["present"] if not p.startswith("the ") and f"{p} is here; you have not met" not in ev]
        booked = self.booked(sit, now)
        if (end := re.search(r"It runs until (\d\d):(\d\d)", ev)):
            self.lesson = (sit["day"], int(end[1]) * 60 + int(end[2]))
        if self.lesson[0] == sit["day"] and now < self.lesson[1]:
            booked = ("home", now)
        if now >= 22 * 60 or now < 5 * 60:
            ans.update(action="sleep" if here == "home" else "walk", place="home", minutes=240)
        elif now >= 21 * 60 + 15 and here != "home":
            ans.update(action="walk", place="home", minutes=30)
        elif here not in open_now:
            ans.update(action="walk", place="home", minutes=30)
        elif booked and booked[0] in open_now and here != booked[0]:
            ans.update(action="walk", place=booked[0], minutes=30)                      # to the lesson or the talk
        elif booked and here == booked[0]:
            ans.update(action="rest" if here == "home" else "read", place=here, minutes=max(5, min(60, booked[1] - now)) if now < booked[1] else 30)
        elif here == "home" and "expect bakshish" in ev:
            ans.update(action="buy", place="home", minutes=15, buys=[{"item": "Bakshish for Ramesh", "price_inr": 500}])
        elif here == "khan" and cash >= 10000 and vouch and any("Mobile phone" in x for x in sit["for_sale"]):
            ans.update(action="buy", place="khan", minutes=30, buys=[{"item": "Mobile phone, basic Android", "price_inr": 9000},
                       {"item": "Prepaid SIM card", "price_inr": 300}, {"item": "Mobile data, 28 days", "price_inr": 350}])
        elif vouchers > 2000 and "estates" in open_now and here != "estates" and 570 <= now <= 16 * 60 and sit["day"][:3] in ("Mon", "Tue", "Wed", "Thu", "Fri"):
            ans.update(action="walk", place="estates", minutes=30)                      # the vouchers want going through
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
        if owns and not self.read:
            ans["looks_up"] = "Karl Marx"
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

    def complete(self, prompt, max_tokens=700, temperature=None, seed=None):
        """Two paragraphs of rehearsal prose, the same for the same prompt and seed."""
        r = random.Random(f"{prompt}|{seed}")
        return "(rehearsal) " + " ".join(r.sample(LINES, 3)) + "\n\n" + " ".join(r.sample(LINES, 3))

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
        if "continues" in props:    # what he wrote, or with "about" what he means to write
            ask = messages[-1]["content"]
            shelf = re.findall(r"“([^”]+)” \(", ask.split("Your manuscripts so far:")[1]) if "Your manuscripts so far:" in ask else []
            r = random.Random(ask)
            title = shelf[-1] if shelf and r.random() < 0.7 else "(rehearsal) " + r.choice(TITLES)
            kind = r.choice(["essay", "notes", "letter"])
            out = {"title": title, "kind": kind, "to": "a friend in Berlin" if kind == "letter" else None, "continues": title in shelf}
            if "about" in props:
                out["about"] = "(rehearsal) " + r.choice(ABOUTS)
            else:
                out["text"] = "(rehearsal) " + " ".join(r.sample(LINES, 3))
            return json.dumps(out)
        if "diary" in props:
            ask = messages[-1]["content"]
            times = re.findall(r"^(\d\d:\d\d) ", ask, re.M)
            theses = [{"id": i, "status": s, "evidence": times[:1]} for i, s in re.findall(r"(\w+): [^;]*? \((\w+)\)[;.]", ask.split("Your theses:")[-1])]
            return json.dumps({"diary": "(rehearsal) The owl's diary would go here: a page in Hegel's hand about the day's one real movement, written from the record.",
                               "revision_log": "(rehearsal) No thesis moved today.",
                               "depesche": "(rehearsal) A Depesche would go here." if "depesche" in props else None,
                               "theses": theses})
        return "{}"
