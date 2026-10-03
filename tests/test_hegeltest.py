"""Tests for the Hegel test (tools/hegel_test.py): its data, its scoring, its sheet, and a whole run against a fake llama-server."""
import contextlib
import io
import json
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import HTTPServer
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from test_world import REPO  # noqa: E402  (this also keeps the tests off the Pi's env file)

import corpus  # noqa: E402
import hegel_test as ht  # noqa: E402

QUESTIONS = json.loads((REPO / "mind/hegeltest/questions.json").read_text(encoding="utf-8"))["questions"]
BIOGRAPHY = json.loads((REPO / "mind/hegeltest/biography.json").read_text(encoding="utf-8"))["questions"]
WORKS = {w["id"]: w for w in corpus.WORKS}


class DataTest(unittest.TestCase):
    def test_twenty_questions_each_with_a_real_passage_of_80_to_140_words(self):
        self.assertEqual(len(QUESTIONS), 20)
        self.assertEqual(len({q["id"] for q in QUESTIONS}), 20)
        self.assertGreaterEqual(len({q["source"] for q in QUESTIONS}), 5)
        for q in QUESTIONS:
            n = len(q["passage"].split())
            self.assertTrue(80 <= n <= 140, (q["id"], n))
            self.assertEqual(q["words"], n)
            self.assertTrue(q["question"].endswith("?") and q["topic"] and q["translation"] and q["ref"], q["id"])
            self.assertIn(q["source"], WORKS)
            self.assertEqual(WORKS[q["source"]]["lang"], "en", q["id"])                  # a passage from a translation, in English
            self.assertEqual(q["work"], WORKS[q["source"]]["work"], q["id"])

    def test_every_passage_is_in_the_cleaned_corpus_and_the_fixes_are_the_only_difference(self):
        text = {}
        for q in QUESTIONS:
            body = text.setdefault(q["source"], " ".join(corpus.read_work(WORKS[q["source"]]).split()))
            self.assertIn(" ".join(q["original"].split()), body, q["id"])
            fixed = q["original"]
            for bad, good in q["fixes"]:
                self.assertIn(bad, fixed, (q["id"], bad))
                fixed = fixed.replace(bad, good)
            self.assertEqual(fixed, q["passage"], q["id"])
            self.assertNotRegex(q["passage"], r"[a-zäöüß][A-ZÄÖÜ]|\\", q["id"])            # no misprint a judge could spot

    def test_no_passage_names_what_is_after_1831(self):
        from world.world import wordlist
        later = wordlist("after_1831.txt", "s?")
        for q in QUESTIONS:
            self.assertIsNone(later.search(q["passage"] + " " + q["question"]), q["id"])

    def test_thirty_questions_about_his_life_each_answered_by_its_own_fact(self):
        self.assertEqual(len(BIOGRAPHY), 30)
        self.assertEqual(len({q["id"] for q in BIOGRAPHY}), 30)
        for q in BIOGRAPHY:
            self.assertTrue(q["question"].endswith("?") and q["fact"], q["id"])
            self.assertTrue(q["answers"] and all(g and all(isinstance(v, str) and v for v in g) for g in q["answers"]), q["id"])
            self.assertEqual(ht.matches("I would say: " + q["fact"] + ".", q["answers"]), len(q["answers"]), q["id"])
            self.assertLess(ht.matches("I could not say.", q["answers"]), len(q["answers"]), q["id"])


class ScoringTest(unittest.TestCase):
    def test_matches_ignores_case_diacritics_and_sharp_s_and_a_number_stands_alone(self):
        groups = [["Stuttgart"], ["1770", "seventeen seventy"]]
        self.assertEqual(ht.matches("born in STUTTGART in 1770.", groups), 2)
        self.assertEqual(ht.matches("Stuttgart, in the year seventeen seventy", groups), 2)
        self.assertEqual(ht.matches("Stuttgart, 17701 or 11770", groups), 1)
        self.assertEqual(ht.matches("Bei Straßburg", [["Strassburg"]]), 1)
        self.assertEqual(ht.matches("Tübingen", [["Tubingen"]]), 1)
        self.assertEqual(ht.matches("", groups), 0)

    def test_clean_answer_takes_the_prose_out_of_what_a_model_wraps_it_in(self):
        self.assertEqual(ht.clean_answer("<think>hm</think>\n“The state is free.”"), "The state is free.")
        self.assertEqual(ht.clean_answer("```\nThe  state\nis free.\n```"), "The state is free.")
        self.assertEqual(ht.clean_answer('{"answer": "The state is free."}'), "The state is free.")
        self.assertEqual(ht.clean_answer("Hegel: The state is free."), "The state is free.")
        self.assertEqual(ht.clean_answer(None), "")

    def test_the_order_of_a_sheet_is_a_shuffle_that_the_label_and_the_question_decide(self):
        a = ht.order_for("bonsai", "state", 4)
        self.assertEqual(sorted(a), [0, 1, 2, 3, 4])
        self.assertEqual(a, ht.order_for("bonsai", "state", 4))
        self.assertTrue(any(ht.order_for("bonsai", q["id"], 4) != ht.order_for("qwen", q["id"], 4) for q in QUESTIONS))
        self.assertGreater(len({ht.order_for("x", q["id"], 4).index(4) for q in QUESTIONS}), 2)      # the real one does not always sit in the same place

    def test_the_voice_is_the_soul_without_the_world_and_the_json(self):
        v = ht.voice()
        self.assertIn("From your shelf", v)
        self.assertNotIn("## The world's rules", v)
        self.assertNotIn("## Your answer", v)


def blind_for(answers=4):
    return [{"id": q["id"], "shelf": False, "answers": [f"Model answer {i} to {q['id']}." for i in range(answers)], "latency_s": 0.0} for q in QUESTIONS]


class SheetTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="hegel-sheet-"))
        patch = mock.patch.object(ht, "RESULTS", self.tmp)
        patch.start()
        self.addCleanup(patch.stop)
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_every_question_has_five_options_and_the_key_names_the_real_one(self):
        qs, key = ht.write_sheet("t1", blind_for(), False)
        self.assertEqual(len(qs), 20)
        by_id = {q["id"]: q for q in QUESTIONS}
        for q, k in zip(qs, key):
            self.assertEqual(sorted(q["options"]), list("ABCDE"))
            self.assertEqual(q["options"][q["real"]], by_id[q["id"]]["passage"])
            self.assertEqual(k["real"], q["real"])
            self.assertEqual(sorted(k["order"]), ["model 1", "model 2", "model 3", "model 4", "real"])
            self.assertEqual(k["order"][ord(q["real"]) - 65], "real")
        self.assertGreater(len({q["real"] for q in qs}), 2)

    def test_the_sheet_and_its_key_are_written_and_the_same_run_makes_the_same_sheet(self):
        ht.write_sheet("t2", blind_for(), True)
        page = (self.tmp / "hegeltest-t2.html").read_text(encoding="utf-8")
        self.assertIn("Candidate: <b>t2</b> (with his shelf)", page)
        self.assertIn('const LABEL = "t2"', page)
        key = json.loads((self.tmp / "hegeltest-t2-key.json").read_text(encoding="utf-8"))
        self.assertEqual(key["label"], "t2")
        self.assertEqual(len(key["questions"]), 20)
        first = page
        ht.write_sheet("t2", blind_for(), True)
        self.assertEqual(first, (self.tmp / "hegeltest-t2.html").read_text(encoding="utf-8"))
        ht.write_sheet("t3", blind_for(), False)
        self.assertNotIn("(with his shelf)", (self.tmp / "hegeltest-t3.html").read_text(encoding="utf-8"))

    def test_text_that_looks_like_markup_cannot_break_the_page(self):
        blind = blind_for()
        blind[0]["answers"][0] = '</script><!--<script>alert(1)</script> & "quotes" <b>'
        ht.write_sheet("t4", blind, False)
        page = (self.tmp / "hegeltest-t4.html").read_text(encoding="utf-8")
        self.assertEqual(page.count("</script>"), 1)                       # the one that ends the script
        self.assertNotIn("<!--", page)                                     # nor can a comment start inside it
        if shutil.which("node"):                                           # and the data still say what was said
            js = re.search(r"<script>(.*)</script>", page, re.S).group(1).split("const key =")[0].replace("const LABEL", "var LABEL")
            got = subprocess.run(["node", "-e", js + "; console.log(JSON.stringify(Object.values(DATA[0].options).filter(x => x.includes('alert'))))"], capture_output=True, text=True)
            self.assertEqual(json.loads(got.stdout), ['</script><!--<script>alert(1)</script> & "quotes" <b>'], got.stderr)

    def test_the_script_of_the_sheet_parses(self):
        if not shutil.which("node"):
            self.skipTest("node is not installed")
        ht.write_sheet("t5", blind_for(), False)
        page = (self.tmp / "hegeltest-t5.html").read_text(encoding="utf-8")
        js = re.search(r"<script>(.*)</script>", page, re.S).group(1)
        (self.tmp / "sheet.js").write_text(js, encoding="utf-8")
        got = subprocess.run(["node", "--check", str(self.tmp / "sheet.js")], capture_output=True, text=True)
        self.assertEqual(got.returncode, 0, got.stderr)


class FakeServer:
    """A llama-server that is the tool's own stub, on a free port, in a thread."""

    def __enter__(self):
        ht.StubLlama.calls = []
        self.httpd = HTTPServer(("127.0.0.1", 0), ht.StubLlama)
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()
        self.url = f"http://127.0.0.1:{self.httpd.server_address[1]}"
        return self

    def __exit__(self, *a):
        self.httpd.shutdown()
        self.httpd.server_close()


def cli(*argv):
    with mock.patch.object(sys, "argv", ["hegel_test.py", *argv]), contextlib.redirect_stdout(io.StringIO()):
        return ht.main()


class RunTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="hegel-run-"))
        with mock.patch.object(ht, "RESULTS", cls.tmp), FakeServer() as srv:
            cls.rc = cli("--url", srv.url, "--label", "stub", "--timeout", "20")
            cls.plain_calls = list(ht.StubLlama.calls)
            cls.rc_shelf = cli("--url", srv.url, "--label", "stub-shelf", "--shelf", "--timeout", "20")
            cls.shelf_calls = ht.StubLlama.calls[len(cls.plain_calls):]
        cls.out = json.loads((cls.tmp / "hegeltest-stub.json").read_text(encoding="utf-8"))
        cls.out_shelf = json.loads((cls.tmp / "hegeltest-stub-shelf.json").read_text(encoding="utf-8"))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_a_run_makes_json_a_sheet_and_a_key(self):
        self.assertEqual((self.rc, self.rc_shelf), (0, 0))
        for name in ("hegeltest-stub.json", "hegeltest-stub.html", "hegeltest-stub-key.json", "hegeltest-stub-shelf.json", "hegeltest-stub-shelf.html"):
            self.assertTrue((self.tmp / name).exists(), name)
        self.assertEqual({k for k in self.out}, {"label", "url", "started", "shelf", "holdout", "answers_per_question", "blind", "biography", "behaviour"})
        self.assertFalse(self.out["shelf"])
        self.assertTrue(self.out_shelf["shelf"])
        self.assertEqual(self.out_shelf["holdout"], "family")

    def test_blind_part_asks_each_question_four_times(self):
        self.assertEqual(len(self.out["blind"]), 20)
        for b in self.out["blind"]:
            self.assertEqual(len(b["answers"]), 4)
            self.assertTrue(all(len(a.split()) > 40 for a in b["answers"]))
            self.assertEqual(len(set(b["answers"])), 4)                      # four different seeds, four different answers
            self.assertFalse(b["shelf"])

    def test_the_biography_part_is_scored(self):
        b = self.out["biography"]
        self.assertEqual((b["n"], b["right"]), (30, 30))                       # the stub gives the right fact
        self.assertEqual(b["partial"], 1.0)
        self.assertEqual(self.out_shelf["biography"]["right"], 30)

    def test_the_behaviour_part_runs_the_twenty_situations_through_the_live_contract(self):
        h = self.out["behaviour"]
        self.assertEqual((h["n"], h["valid"], h["refused"], h["leaking"]), (20, 20, 0, 0))
        self.assertEqual([r["id"] for r in h["rows"]], [s["id"] for s in json.loads((REPO / "mind/situations.json").read_text(encoding="utf-8"))["situations"]])
        self.assertTrue(all(r["thought_words"] > 3 for r in h["rows"]))
        self.assertTrue(all(r["shelf"] == [] for r in h["rows"]))
        shelved = self.out_shelf["behaviour"]["rows"]
        self.assertGreaterEqual(sum(bool(r["shelf"]) for r in shelved), 10)

    def test_the_plain_run_never_shows_a_shelf_and_the_shelf_run_does(self):
        users = lambda calls: [c["messages"][-1]["content"] for c in calls]
        self.assertFalse(any("From your shelf" in u for u in users(self.plain_calls)))
        self.assertGreater(sum("From your shelf" in u for u in users(self.shelf_calls)), 40)

    def test_with_the_shelf_the_book_of_the_real_passage_and_its_twin_are_held_out(self):
        users = [c["messages"][-1]["content"] for c in self.shelf_calls if "in 80 to 140 words" in c["messages"][-1]["content"]]
        self.assertGreaterEqual(len(users), 80)
        titles = {}
        for u in users:
            q = next(x for x in QUESTIONS if x["question"] in u)
            held = {WORKS[i]["work"] for i in ht.FAMILY.get(q["source"], [q["source"]])}
            lines = re.findall(r"^- (.*?)(?: §\d+[a-z]?|, [^:]*)?: “", u, re.M)
            titles.setdefault(q["id"], set()).update(lines)
            self.assertFalse(held & set(lines), (q["id"], held, lines))
            self.assertNotIn(q["passage"][:80], u)
            self.assertNotIn(q["original"][:80], u)
        self.assertGreaterEqual(sum(bool(t) for t in titles.values()), 12)           # and the shelf did offer something to most of them (floor 14)

    def test_compare_makes_a_table_and_reads_the_judgments_against_the_key(self):
        with mock.patch.object(ht, "RESULTS", self.tmp), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(ht.compare(["stub", "stub-shelf"]), 0)
            md = (self.tmp / "hegeltest.md").read_text(encoding="utf-8")
            self.assertIn("| stub | no | 30/30 | 100% | 20/20 | 0 | 0 |", md)
            self.assertIn("| stub-shelf | yes | 30/30 |", md)
            self.assertIn("not yet judged", md)
            key = json.loads((self.tmp / "hegeltest-stub-key.json").read_text(encoding="utf-8"))["questions"]
            wrong = lambda q: next(c for c in "ABCDE" if c != q["real"])
            # one judge exported by the page, one file holding two judges
            (self.tmp / "hegeltest-stub-judged.json").write_text(json.dumps(
                {"label": "stub", "judge": "welt", "choices": {q["id"]: (q["real"] if i < 5 else wrong(q)) for i, q in enumerate(key)}}), encoding="utf-8")
            (self.tmp / "hegeltest-stub-judged-claude.json").write_text(json.dumps(
                {"judges": [{"judge": "claude", "choices": {q["id"]: wrong(q) for q in key[:10]}}, {"judge": "other", "choices": {"nonsense": "A"}}]}), encoding="utf-8")
            (self.tmp / "hegeltest-stub-judged-broken.json").write_text("{not json", encoding="utf-8")
            got = {j["judge"]: (j["hits"], j["answered"]) for j in ht.judged("stub")}
            self.assertEqual(got, {"welt": (5, 20), "claude": (0, 10), "other": (0, 0)})
            self.assertEqual(ht.judged("nobody"), [])
            ht.compare(["stub"])
            md = (self.tmp / "hegeltest.md").read_text(encoding="utf-8")
            self.assertIn("5/30 = 17%", md)
            self.assertIn("**stub**, welt: 5 real passages picked of 20 answered (25%)", md)

    def test_the_cli_asks_for_what_it_needs(self):
        with mock.patch.object(ht, "RESULTS", self.tmp), self.assertRaises(SystemExit), mock.patch("sys.stderr"):
            cli("--label", "x")


class ServerTest(unittest.TestCase):
    def test_the_stub_server_speaks_the_contracts_json_for_a_decision(self):
        sys.path.insert(0, str(REPO / "mind"))
        import bakeoff
        s = json.loads((REPO / "mind/situations.json").read_text(encoding="utf-8"))["situations"][0]
        from world import contract
        with FakeServer() as srv:
            raw, constrained = bakeoff.ask(srv.url, "soul", contract.render(s), "local", 20)
        self.assertTrue(constrained)
        self.assertFalse(contract.check_shape(contract.extract_json(raw))[0])

    def test_an_unreachable_server_is_an_empty_answer_not_a_crash(self):
        with mock.patch("sys.stderr"):
            self.assertEqual(ht.ask("http://127.0.0.1:9", "s", "u", 0.1, 10, 1), "")


if __name__ == "__main__":
    unittest.main()
