"""Three weeks with the stand-in, from Saturday 3 October, the owl writing up each night: the economy as a whole, and the Purse tab
reading the same days. (Ramesh's wage falls due on 1 November, which is outside these three weeks.)"""
import json
import random
import shutil
import statistics
import subprocess
import sys
import unittest
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_deal  # noqa: E402
from test_world import DAY1, REPO, Sandbox  # noqa: E402  (this also keeps the tests off the Pi's env file)

from world.mind import NOUNS, StubMind  # noqa: E402
from world.world import at_dt  # noqa: E402

START, DAYS = date(2026, 10, 3), 21
OFFERS = ("tutoring_german", "iic_talk", "sell_frock", "loan_malhotra", "essay_fee")


_RUN = []


def run():
    """The three weeks, once: (the days as files, the length of each prompt, the extra calls by kind, the length of each Money line)."""
    if not _RUN:
        box, prompts, calls, money = Sandbox(), [], {}, []

        class Watcher(StubMind):
            def decide(self, messages, sit):
                if not any("refuses" in x["content"] for x in messages):
                    prompts.append(len(messages[1]["content"]))
                    money.append(next(len(x) for x in sit["on_mind"] if x.startswith("Money:")))
                return super().decide(messages, sit)

            def chat(self, messages, schema=None, max_tokens=700, temperature=None):
                props = (schema or {}).get("properties", {})
                kind = "plan" if "plan" in props else "voice" if "does" in props else "write" if "continues" in props else \
                    "owl" if "diary" in props else "choice" if "answer" in props else "other"
                calls.setdefault(kind, []).append(1)
                return super().chat(messages, schema, max_tokens, temperature)

        try:
            e, days = box.engine(Watcher()), []
            for i in range(DAYS):
                d = START + timedelta(days=i)
                box.run_day(d, e)
                e.run_owl(box.days.load(d), at_dt(d + timedelta(days=1), 90))
                days.append(box.days.load(d))
        finally:
            box.close()
        _RUN.append((days, prompts, calls, money))
    return _RUN[0]


class Rehearsal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.days, cls.prompts, cls.calls, cls.money = run()

    def entries(self, kind=None):
        return [(d["date"], e) for d in self.days for e in d["entries"] if kind is None or e["k"] == kind]

    def test_every_day_is_whole_with_few_refusals(self):
        refused = 0
        for day in self.days:
            segs = day["segments"]
            self.assertEqual((segs[0]["from"], segs[-1]["to"]), ("00:00", "24:00"), day["date"])
            self.assertTrue(all(a["to"] == b["from"] for a, b in zip(segs, segs[1:])), day["date"])
            steps = [s for s in day["steps"] if "decision" in s]
            self.assertTrue(15 <= len(steps) <= 35, (day["date"], len(steps)))     # real-map walks are shorter: more steps fit
            refused += sum(len(s["mind"].get("refused", [])) for s in steps)
            self.assertTrue(day["complete"] and day["owl"], day["date"])
        self.assertLessEqual(refused / DAYS, 2)

    def test_cash_is_never_negative_and_the_entries_add_up_to_the_state(self):
        for day in self.days:
            cash = day["opening"]["cash"]
            self.assertEqual(day["opening"]["imprest"], cash)
            for e in day["entries"]:
                cash += {"bag": -e.get("price", 0), "expense": -e.get("amount", 0)}.get(e["k"], 0)
                cash += e["amount"] if e["k"] == "income" and not e.get("cheque") else 0
                self.assertGreaterEqual(cash, 0, (day["date"], e))
            self.assertEqual(cash, day["state"]["imprest"], day["date"])
            self.assertEqual(set(day["opening"]), {"imprest", "wearing", "wardrobe", "cash", "account", "owed", "cheques"})

    def test_groceries_every_sunday_and_the_dhobi_every_saturday_are_paid_or_owed(self):
        for i in range(DAYS):
            d = START + timedelta(days=i)
            day = self.days[i]
            paid = [e["item"] for e in day["entries"] if e["k"] == "expense"]
            owed = [e["owe"]["why"] for e in day["entries"] if e.get("owe")] + [o["why"] for o in day["state"]["owed"] if o["since"] == d.isoformat()]
            if d.weekday() == 6:
                self.assertTrue("Groceries for Ramesh's kitchen" in paid or "groceries" in owed, d)
            if d.weekday() == 5:
                self.assertTrue("The dhobi" in paid or "the washing" in owed, d)
        day10 = self.days[7]
        self.assertEqual(day10["date"], "2026-10-10")
        self.assertTrue("Electricity" in [e["item"] for e in day10["entries"] if e["k"] == "expense"]
                        or any(e.get("owe", {}).get("why") == "electricity" for e in day10["entries"]))

    def test_ramesh_is_not_due_his_wage_inside_these_weeks(self):
        self.assertFalse(any("wage" in json.dumps(e) for _, e in self.entries()))
        self.assertFalse(any(o.get("cost") == "wage" for d in self.days for o in d["state"]["owed"]))

    def test_the_directorate_goes_through_the_vouchers(self):
        visits = [e for _, e in self.entries() if e.get("recoup")]
        self.assertTrue(visits)
        first = visits[0]["recoup"]
        self.assertTrue(first["admitted"] > 0 and first["queried"] > 0, first)         # day 1's notebook admitted, the rest queried
        self.assertEqual(first, {"admitted": 640, "queried": first["queried"]})
        self.assertTrue(any(e["k"] == "file" and "queries" in e["text"] for _, e in self.entries()))
        acc = self.days[-1]["state"]["account"]
        self.assertEqual(acc["admitted"], sum(e["recoup"]["admitted"] for e in visits))
        self.assertEqual(acc["queried"], sum(e["recoup"]["queried"] for e in visits))

    def test_offers_are_made_and_accepted_and_the_lessons_pay_on_lesson_days(self):
        made = [b for b in self.days[-1]["state"]["beats"] if b in OFFERS]
        self.assertGreaterEqual(len(made), 2)
        accepted = [e["text"] for _, e in self.entries("world") if e["text"].startswith(("He agrees.", "He accepts"))]
        self.assertGreaterEqual(len(accepted), 2, accepted)
        answers = [e for _, e in self.entries() if e["k"] in ("world", "file") and e["text"].startswith(("He agrees", "He accepts", "He declines", "He keeps", "Shri Hegde carries", "Shri Hegde picks"))]
        self.assertEqual(len(self.calls["choice"]), len(answers))                       # one yes-or-no call for every offer and for the Hegde gate, none more
        lessons = [(d["date"], e) for d in self.days for e in d["entries"] if e["k"] == "income" and e["item"] == "German lesson"]
        self.assertGreaterEqual(len(lessons), 3)
        attended = [(d["date"], b) for d in self.days for b in d["state"]["beats"] if b.startswith("tutoring_german@")]
        for day, b in {(d, b) for d, b in attended if d == b.split("@")[1]}:
            self.assertIn(day, [x for x, _ in lessons], b)                              # on the day of every lesson he attended
            self.assertEqual(date.fromisoformat(day).weekday() in (1, 4), True)
        self.assertTrue(all(e["amount"] == 1000 and e["from"] == "Ananya" for _, e in lessons))

    def test_a_phone_and_sim_are_bought_and_one_look_up_is_recorded(self):
        st = self.days[-1]["state"]
        self.assertTrue(st["tech"]["phone"] and st["tech"]["sim"])
        self.assertEqual(len([1 for _, e in self.entries("bag") if e["item"] == "Mobile phone, basic Android"]), 1)
        sim = [e for _, e in self.entries("bag") if e["item"] == "Prepaid SIM card"]
        self.assertTrue(len(sim) == 1 and sim[0]["note"].startswith("Bought in "), sim)
        reads = self.entries("read")
        self.assertEqual(len(reads), 1)
        self.assertEqual(reads[0][1]["title"], "Karl Marx")
        self.assertEqual(reads[0][1]["source"], "Wikipedia")

    def test_the_prompts_stay_compact_and_the_extra_calls_are_few(self):
        self.assertLess(statistics.mean(self.prompts), 2800)
        self.assertLess(max(self.prompts), 4300)
        self.assertLessEqual(max(self.money), 200)
        per_day = {k: len(v) / DAYS for k, v in self.calls.items()}
        self.assertEqual(per_day["plan"], 1)
        self.assertEqual(per_day["owl"], 1)
        self.assertLess(per_day["choice"], 1)                                            # offers are rare

    def test_every_day_shows_the_money_line_to_the_mind(self):
        for day in self.days:
            steps = [s for s in day["steps"] if "decision" in s]
            self.assertTrue(steps)
        self.assertTrue(all("cheques" in d["state"] and "owed" in d["state"] and "account" in d["state"] for d in self.days))


ITEMS = ["chai", "samosa", "a notebook", "ink", "newspapers", "wine", "a kurta", "Mobile phone, basic Android", "a SIM card", "mobile data", "a phone",
         "Bakshish for Ramesh", "A gift for the dhobi", "A tip for Nidhi", "a horse", "Lunch at a dhaba", "a Hindi dictionary", "Entry ticket, foreign visitors"]


class Chaos(StubMind):
    """A mind that decides anything, buys anything, says yes or no to every offer and looks things up at random: the economy must keep its books."""

    def __init__(self, seed):
        self.r = random.Random(seed)

    def decide(self, messages, sit):
        r = self.r
        if any("refuses" in x["content"] for x in messages):
            return super().decide(messages, sit)
        h = int(sit["time"][:2])
        act, place = ("sleep", "home") if h >= 22 or h < 5 else (r.choice(["stay", "walk", "read", "write", "talk", "buy", "eat", "rest"]), r.choice(sit["open_now"]))
        ans = {"thought": "(rehearsal) " + " ".join(r.sample(NOUNS, 9)) + ".", "action": act, "place": place, "minutes": r.choice([5, 30, 60, 120]),
               "says": "Namaste, Nidhi." if sit["present"] and r.random() < .5 else None, "revision": None,
               "buys": [{"item": r.choice(ITEMS), "price_inr": r.choice([20, 50, 300, 500, 9000])} for _ in range(r.choice([0, 0, 1, 2, 3]))]}
        if r.random() < .15:
            ans["looks_up"] = r.choice(["Karl Marx", "Delhi", "   ", "qzxq nothing"])
        return json.dumps(ans)

    def chat(self, messages, schema=None, max_tokens=700, temperature=None):
        if "answer" in (schema or {}).get("properties", {}):
            return json.dumps({"answer": self.r.choice(["yes", "no"])})
        return super().chat(messages, schema, max_tokens, temperature)


class ChaosTest(unittest.TestCase):
    def test_whatever_he_decides_the_books_balance_and_the_days_are_whole(self):
        for seed, start in ((1, START), (2, START), (3, date(2026, 10, 30))):          # the last one runs over Ramesh's wage and Diwali
            box = Sandbox()
            try:
                e = box.engine(Chaos(seed))
                e.lookup = lambda q, cache: random.Random(q).choice([{"note": "The page will not load."}, {"title": q, "text": f"About {q}.", "source": "Wikipedia", "url": "https://en.wikipedia.org/wiki/x"}])
                for i in range(6):
                    d = start + timedelta(days=i)
                    box.run_day(d, e)
                    day = box.days.load(d)
                    cash = day["opening"]["cash"]
                    for x in day["entries"]:
                        cash += -x.get("price", 0) if x["k"] == "bag" else -x.get("amount", 0) if x["k"] == "expense" else x["amount"] if x["k"] == "income" and not x.get("cheque") else 0
                        self.assertGreaterEqual(cash, 0, (seed, d, x))
                    self.assertEqual(cash, day["state"]["imprest"], (seed, d))
                    segs = day["segments"]
                    self.assertTrue(segs[0]["from"] == "00:00" and segs[-1]["to"] == "24:00" and all(a["to"] == b["from"] for a, b in zip(segs, segs[1:])), (seed, d))
            finally:
                box.close()


class PurseTest(unittest.TestCase):
    """The Purse tab, in node, against the same days."""

    def page(self, calls, D, entries=None):
        io = {"calls": calls, "D": D, "ENTRIES": entries or [], "storage": None}
        got = subprocess.run(["node", "-e", test_deal.PageNodeTest.HARNESS, str(REPO / "docs/index.html"), json.dumps(io)], capture_output=True, text=True)
        self.assertEqual(got.returncode, 0, got.stderr)
        return json.loads(got.stdout)

    def setUp(self):
        if not shutil.which("node"):
            self.skipTest("node is not installed")

    def test_the_tab_is_called_purse_and_the_money_kinds_are_labelled(self):
        page = (REPO / "docs/index.html").read_text(encoding="utf-8")
        self.assertIn('data-tab="purse" aria-selected="false">Purse</button>', page)
        self.assertNotIn('data-tab="bag"', page)
        self.assertNotIn(">Bag<", page)
        k = self.page([["KLABEL"]], {"date": "x"})[0]
        self.assertEqual((k["income"], k["expense"], k["bag"]), ("Earned", "Paid", "Bought"))

    def test_day_one_is_read_as_it_was_ten_thousand_five_hundred_and_one_left(self):
        entries = [dict(e, m=i, i=i) for i, e in enumerate(DAY1["entries"])]
        (p,) = self.page([["purse", entries]], DAY1)
        self.assertEqual((p["cash"], p["advance"], sum(p["vouchers"]), len(p["vouchers"]), p["paid"], p["earned"]), (10501, 15000, 4499, 7, 4499, 0))
        (html,) = self.page([["purseHtml", entries]], DAY1)
        self.assertIn('<p class="cash">Cash <b>₹10,501</b></p>', html)
        self.assertIn("Vouchered, not yet gone through: ₹4,499 (7)", html)
        self.assertIn("Today: ₹0 in cash earned, ₹4,499 spent.", html)
        self.assertIn("<h3>Owed</h3><p class=\"empty\">Nothing.</p>", html)
        self.assertIn("None. He has no bank account.", html)
        (early,) = self.page([["purse", [e for e in entries if e["t"] < "06:30"]]], DAY1)
        self.assertEqual(early["cash"], 0)                                                 # before the advance is handed over

    def test_the_fold_of_a_day_by_hand(self):
        D = {"date": "2026-10-20", "opening": {"imprest": 5000, "cash": 5000, "wearing": "kurta", "wardrobe": [],
             "account": {"advance": 15000, "vouchers": [{"price": 120, "office": True}], "admitted": 640, "queried": 3859},
             "owed": [{"to": "Ramesh", "amount": 1500, "why": "groceries", "since": "x"}], "cheques": [{"from": "the IIC", "amount": 10000, "since": "x"}]}}
        es = [{"k": "expense", "t": "06:00", "item": "Groceries", "amount": 1500, "to": "Ramesh", "why": "groceries", "settles": True},
              {"k": "bag", "t": "07:00", "item": "Chai", "price": 20},
              {"k": "income", "t": "08:00", "item": "German lesson", "amount": 1000, "from": "Ananya"},
              {"k": "income", "t": "09:00", "item": "Honorarium", "amount": 10000, "from": "the IIC", "cheque": True},
              {"k": "world", "t": "10:00", "text": "x", "owe": {"to": "the dhobi", "amount": 300, "why": "the washing"}},
              {"k": "income", "t": "11:00", "item": "Imprest refilled", "amount": 140, "recoup": {"admitted": 140, "queried": 0}}]
        entries = [dict(e, m=i, i=i) for i, e in enumerate(es)]
        (p,) = self.page([["purse", entries]], D)
        self.assertEqual((p["cash"], p["earned"], p["paid"]), (5000 - 1500 - 20 + 1000 + 140, 1140, 1520))
        self.assertEqual(p["owed"], [{"to": "the dhobi", "amount": 300, "why": "the washing"}])
        self.assertEqual(p["cheques"], [{"from": "the IIC", "amount": 10000}, {"from": "the IIC", "amount": 10000}])
        self.assertEqual((p["vouchers"], p["admitted"], p["queried"], p["advance"]), ([], 780, 3859, 15000))
        (html,) = self.page([["purseHtml", entries]], D)
        self.assertIn("Cash <b>₹4,620</b>", html)
        self.assertIn("<li>the dhobi: ₹300 (the washing)</li>", html)
        self.assertIn("<li>₹10,000 from the IIC</li>", html)
        self.assertIn("Admitted so far ₹780; queried ₹3,859.", html)
        self.assertIn("<h3>Money in today</h3>", html)
        self.assertLess(html.index("Money in today"), html.index("German lesson"))
        self.assertLess(html.index("German lesson"), html.index("Money out today"))
        self.assertLess(html.index("Money out today"), html.index("Groceries"))
        self.assertIn("<b>German lesson</b>, ₹1,000. From Ananya.", html)
        self.assertIn("<b>Honorarium</b>, ₹10,000 by cheque, not yet cashed. From the IIC.", html)
        self.assertIn("<b>Groceries</b>, ₹1,500. To Ramesh.", html)

    def test_the_new_kinds_in_the_feed_and_what_he_read_with_its_licence(self):
        read = {"k": "read", "title": "Karl <Marx>", "text": "A German philosopher & theorist.", "source": "Wikipedia", "url": "https://en.wikipedia.org/wiki/Karl_Marx"}
        elsewhere = dict(read, url="javascript:alert(1)")
        got = self.page([["line", read], ["line", elsewhere], ["line", {"k": "income", "item": "Fee <x>", "amount": 6000, "from": "the Review"}],
                         ["line", {"k": "expense", "item": "Groceries", "amount": 1500, "to": "Ramesh"}]], {"date": "x"})
        self.assertEqual(got[0], '<b>Karl &lt;Marx&gt;</b>, read on his phone.<br>A German philosopher &amp; theorist.<br>'
                                 '<small class="src"><a href="https://en.wikipedia.org/wiki/Karl_Marx" target="_blank" rel="noopener">From Wikipedia (CC BY-SA)</a></small>')
        self.assertNotIn("<a ", got[1])
        self.assertNotIn("javascript", got[1])
        self.assertIn("From Wikipedia (CC BY-SA)", got[1])
        self.assertEqual(got[2], "<b>Fee &lt;x&gt;</b>, ₹6,000. From the Review.")
        self.assertEqual(got[3], "<b>Groceries</b>, ₹1,500. To Ramesh.")
        veil = self.page([["vz", "k", "caste", "<p>x</p>", "p"]], {"date": "x"})[0]
        self.assertIn("veil", veil)                                                          # the sensitive veil is the page's, whatever the kind

    def test_a_garment_he_sold_leaves_the_wardrobe_tab(self):
        page = (REPO / "docs/index.html").read_text(encoding="utf-8")
        self.assertIn("e.gone ? items.delete(e.item) : items.set(e.item, e)", page)

    def test_the_purse_agrees_with_the_state_at_the_end_of_every_rehearsed_day(self):
        for day in run()[0]:
            entries = [dict(e, m=i, i=i) for i, e in enumerate(day["entries"])]
            (p,) = self.page([["purse", entries]], day)
            st = day["state"]
            self.assertEqual(p["cash"], st["imprest"], day["date"])
            self.assertEqual(sorted((o["to"], o["amount"], o["why"]) for o in p["owed"]), sorted((o["to"], o["amount"], o["why"]) for o in st["owed"]), day["date"])
            self.assertEqual(sorted(c["amount"] for c in p["cheques"]), sorted(c["amount"] for c in st["cheques"]), day["date"])
            self.assertEqual(sum(p["vouchers"]), sum(v["price"] for v in st["account"]["vouchers"]), day["date"])
            self.assertEqual((p["admitted"], p["queried"], p["advance"]), (st["account"]["admitted"], st["account"]["queried"], 15000), day["date"])
