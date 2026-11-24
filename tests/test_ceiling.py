"""tools/ceiling.py: a morning rebuilt by the engine, five arms of one writing call, three files for the night's slots."""
import json
import shutil
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_world import Sandbox  # noqa: E402

from tools import ceiling  # noqa: E402
from world.__main__ import make_world  # noqa: E402
from world.engine import Engine  # noqa: E402
from world.mind import StubMind  # noqa: E402

D2, D3 = date(2026, 10, 3), date(2026, 10, 4)
HEADS = {D2: ["A bridge over the Yamuna opens to traffic at last", "The monsoon session ends with nine bills passed", "A comet is seen over Ladakh"],
         D3: ["The census begins in the hill districts today", "A court orders the lake to be cleaned in a year", "A new line of the Metro opens"]}


class CeilingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Two stand-in days after day 1, each waking to its own headlines: the record the briefs are cut from."""
        cls.box = Sandbox()
        feeds = cls.box.cfg.state / "feeds"
        feeds.mkdir(parents=True, exist_ok=True)
        for d, heads in HEADS.items():
            (feeds / f"news-{d}.json").write_text(json.dumps(heads))
        engine = Engine(cls.box.cfg, make_world(cls.box.cfg), StubMind())
        for d in HEADS:
            cls.box.run_day(d, engine)
        cls.days = cls.box.cfg.docs / "days"
        cls.td = tempfile.TemporaryDirectory()
        cls.f = Path(cls.td.name)
        cls.briefs = [{"id": "b01", "date": str(D2), "headline": HEADS[D2][2], "object": "a comet", "wiki": "Comet", "alt": "Great comet", "stance": "flatters", "why": ""},
                      {"id": "b02", "date": str(D3), "headline": HEADS[D3][0], "object": "a census", "wiki": "Census of India", "alt": "Census", "stance": "flatters", "why": ""},
                      {"id": "b03", "date": str(D3), "headline": HEADS[D3][1], "object": "a lake", "wiki": "Water pollution in India", "alt": "Lake", "stance": "indicts", "why": ""},
                      {"id": "b04", "date": str(D3), "headline": HEADS[D3][2], "object": "a metro", "wiki": "No such page", "alt": "Nor this", "stance": "flatters", "why": ""}]
        (cls.f / "BRIEFS.json").write_text(json.dumps(cls.briefs))

    @classmethod
    def tearDownClass(cls):
        cls.td.cleanup()
        cls.box.close()

    def fetch(self, url):
        """A stand-in for Wikipedia: every title but the two missing ones has an introduction, a short one for 'Comet'."""
        self.asked.append(url)
        if "No+such+page" in url or "Nor+this" in url:
            return {"query": {"pages": {"-1": {"title": "x", "missing": ""}}}}
        long = "The census counts every person in the land. " * 60
        text = "A comet is a small body." if "titles=Comet" in url else long
        return {"query": {"pages": {"7": {"title": "The Page", "extract": text}}}}

    def texts(self):
        self.asked = []
        return ceiling.cmd_texts(self.f, fetch=self.fetch, pause=0)

    def test_candidates_are_the_mornings_that_woke_to_headlines_after_a_saved_day(self):
        with tempfile.TemporaryDirectory() as td:
            res = ceiling.cmd_candidates(self.days, td)
            found = json.loads((Path(td) / "CANDIDATES.json").read_text())
        self.assertEqual(res, {"mornings": 2, "headlines": 6})
        self.assertEqual([(x["date"], x["headlines"]) for x in found], [(str(d), h) for d, h in HEADS.items()])
        self.assertIsNone(ceiling.usable(self.days, "2026-10-02"))                    # day 1 has no day before it

    def test_a_text_is_the_first_choice_or_the_second_and_a_brief_without_one_is_named(self):
        (self.f / "TEXTS.json").unlink(missing_ok=True)                               # another test may have fetched already
        res = self.texts()
        self.assertEqual((res["with_text"], res["missing"]), (3, ["b04"]))
        got = json.loads((self.f / "TEXTS.json").read_text())
        self.assertEqual(got["b01"]["used"], "alt")                                   # the first choice's introduction was too short
        self.assertEqual((got["b02"]["used"], got["b02"]["source"], got["b02"]["licence"]), ("wiki", "Wikipedia", "CC BY-SA 4.0"))
        self.assertLessEqual(len(got["b02"]["text"]), ceiling.TEXT)
        self.assertTrue(got["b02"]["text"].endswith("."))
        self.assertTrue(got["b02"]["url"].startswith("https://en.wikipedia.org/wiki/"))
        asked = len(self.asked)
        self.assertEqual(self.texts()["with_text"], 3)                                # what is there is kept
        self.assertEqual(len(self.asked), 2)                                          # only the brief still missing is tried again
        self.assertGreater(asked, 2)

    def requests(self):
        self.texts()
        man = ceiling.cmd_requests(self.f, self.days)
        rows = {r["id"]: r for n in (1, 2, 3) for r in ceiling.rows(self.f / f"REQUESTS-ceiling-{n}.jsonl")}
        return man, rows

    def test_five_arms_a_brief_and_a_brief_without_a_text_is_left_out(self):
        man, rows = self.requests()
        self.assertEqual((man["briefs"], man["requests"], man["left_out_for_no_text"]), (3, 15, ["b04"]))
        self.assertEqual(set(rows), {f"{a}|{b}" for a in ceiling.ARMS for b in ("b01", "b02", "b03")})
        self.assertEqual([f["requests"] for f in man["files"].values()], [5, 5, 5])   # whole briefs in each file
        self.assertIs(man["training_eligible"], False)
        for n in (1, 2, 3):
            self.assertEqual(man["files"][f"REQUESTS-ceiling-{n}.jsonl"]["sha256"], ceiling.sha(self.f / f"REQUESTS-ceiling-{n}.jsonl"))

    def test_the_arms_differ_in_one_thing_each(self):
        _, rows = self.requests()
        a, a2, b, c, d = (rows[f"{x}|b02"] for x in ceiling.ARMS)
        self.assertEqual(a["messages"], a2["messages"])
        self.assertEqual(a2["params"]["seed"], a["params"]["seed"] + 1)               # the band: the same call, another seed
        self.assertEqual({k: v for k, v in a["params"].items() if k != "seed"}, {"temperature": 0.7, "max_tokens": 1100, "cache_prompt": False})
        self.assertEqual(a["messages"][:3], b["messages"][:3])                        # B adds the text and nothing else
        self.assertIn("On your phone you read: The Page. The census counts every person", b["messages"][3]["content"])
        self.assertNotIn("On your phone you read", a["messages"][3]["content"])
        self.assertEqual(b["params"], a["params"])
        self.assertEqual(c["messages"][1:], a["messages"][1:])                        # C: other instructions and time to think
        self.assertNotEqual(c["messages"][0], a["messages"][0])
        self.assertEqual((c["params"]["reasoning_budget_tokens"], c["params"]["max_tokens"], c["params"]["seed"]), (2048, 3148, a["params"]["seed"]))
        self.assertEqual((d["messages"][0], d["messages"][3], d["params"]), (c["messages"][0], b["messages"][3], c["params"]))
        self.assertTrue(all(r["schema"]["properties"].keys() >= {"title", "kind", "continues", "text"} for r in rows.values()))

    def test_the_call_is_his_own_writing_call_on_the_morning_as_his_record_has_it(self):
        _, rows = self.requests()
        m = rows["A|b02"]["messages"]
        live = json.loads((self.days / f"{D3}.json").read_text())
        self.assertEqual([x["role"] for x in m], ["system", "user", "assistant", "user"])
        self.assertIn("This call writes the work itself", m[0]["content"])            # the writing task's own instructions
        self.assertIn(f"What happens: {live['steps'][0]['event']}", m[1]["content"])  # the waking as his record has it
        self.assertIn(HEADS[D3][0], m[1]["content"])
        self.assertEqual(m[1]["content"].count("Your plan for today"), 1 if live.get("plan") else 0)
        self.assertEqual(json.loads(m[2]["content"]), live["steps"][0]["decision"])   # his own first decision of that morning
        self.assertTrue(m[3]["content"].startswith(f"This morning you sat down to write about one of the headlines in the papers: “{HEADS[D3][0]}”. You sat down to write."))
        self.assertIn("Date of this sitting: 4 October 2026.", m[3]["content"])
        two = rows["A|b03"]["messages"]
        self.assertEqual(two[:3], m[:3])                                              # two briefs of one morning share the morning
        self.assertIn(HEADS[D3][1], two[3]["content"])

    def test_a_brief_whose_headline_is_not_that_mornings_is_refused(self):
        self.texts()
        bad = [dict(self.briefs[0], headline="Not a headline of that day")]
        with tempfile.TemporaryDirectory() as td:
            (Path(td) / "BRIEFS.json").write_text(json.dumps(bad))
            shutil.copy(self.f / "TEXTS.json", Path(td) / "TEXTS.json")
            with self.assertRaises(ValueError):
                ceiling.cmd_requests(td, self.days)


if __name__ == "__main__":
    unittest.main()
