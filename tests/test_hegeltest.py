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
import train_data  # noqa: E402

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
        for name in ("hegeltest-stub.json", "hegeltest-stub.html", "hegeltest-stub-key.json", "hegeltest-stub-shelf.json", "hegeltest-stub-shelf.html",
                     "hegeltest-stub-cont.html", "hegeltest-stub-cont-key.json", "hegeltest-stub-shelf-cont.html", "hegeltest-stub-shelf-cont-key.json"):
            self.assertTrue((self.tmp / name).exists(), name)
        self.assertEqual({k for k in self.out}, {"label", "url", "started", "shelf", "holdout", "answers_per_question", "blind", "biography", "behaviour", "continuation", "continuation_style"})
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
        users = lambda calls: [c["messages"][-1]["content"] for c in calls if "messages" in c]      # (the continuations are asked without a chat)
        self.assertFalse(any("From your shelf" in u for u in users(self.plain_calls)))
        self.assertGreater(sum("From your shelf" in u for u in users(self.shelf_calls)), 40)

    def test_with_the_shelf_the_book_of_the_real_passage_and_its_twin_are_held_out(self):
        users = [c["messages"][-1]["content"] for c in self.shelf_calls if "messages" in c and "in 80 to 140 words" in c["messages"][-1]["content"]]
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
        with mock.patch.object(ht, "RESULTS", self.tmp), self.assertRaises(SystemExit), mock.patch("sys.stderr"):
            cli("--url", "http://127.0.0.1:9", "--label", "x", "--only", "continuation")

    def test_the_continuations_are_asked_in_plain_completion_mode_under_the_header_of_the_corpus(self):
        asks = [c for c in self.plain_calls if "prompt" in c]
        self.assertEqual(len(asks), 80)                                      # the stub gives clean text: no try is repeated
        self.assertFalse(any("messages" in c or "system" in c for c in asks))
        self.assertEqual({(c["temperature"], "stop" in c, c["cache_prompt"]) for c in asks}, {(ht.TEMPERATURE, False, False)})
        for q, row in zip(QUESTIONS, self.out["continuation"]):
            opening, rest = ht.split_passage(q["passage"])
            mine = [c for c in asks if c["prompt"] == ht.header_for(q) + "\n\n" + opening]
            self.assertEqual(len(mine), 4, q["id"])
            self.assertEqual(sorted(c["seed"] for c in mine), [1831 + 17 * i for i in range(4)])
            self.assertTrue(all(c["n_predict"] == int(2.5 * len(rest.split())) for c in mine))
        self.assertFalse(any("shelf" in c["prompt"].lower() for c in asks))
        self.assertFalse([c for c in self.shelf_calls if "prompt" in c and "From your shelf" in c["prompt"]])        # the shelf does not apply to it

    def test_a_continuation_part_has_four_answers_of_about_the_length_of_the_real_half(self):
        rows = self.out["continuation"]
        self.assertEqual([r["id"] for r in rows], [q["id"] for q in QUESTIONS])
        for q, r in zip(QUESTIONS, rows):
            opening, rest = ht.split_passage(q["passage"])
            self.assertEqual((r["opening"], r["rest"]), (ht.typography(opening), ht.typography(rest)))
            self.assertEqual(len(r["answers"]), 4)
            self.assertEqual((len(r["recited"]), len(r["cut"])), (4, 4))
            self.assertEqual(len(set(r["answers"])), 4, q["id"])             # four seeds, four texts
            for a in r["answers"]:
                n = len(rest.split())
                self.assertTrue(0.7 * n <= len(a.split()) <= 1.3 * n, (q["id"], n, len(a.split())))
                self.assertRegex(a, r"[.?!]$")
            self.assertFalse(any(r["recited"]) or any(r["cut"]))
            self.assertIn("latency_s", r)
        self.assertEqual(self.out["continuation_style"]["answers"], 80)

    def test_all_five_options_of_a_continuation_sheet_are_in_one_typography(self):
        qs = json.loads((self.tmp / "hegeltest-stub-cont-key.json").read_text(encoding="utf-8"))["questions"]
        page = (self.tmp / "hegeltest-stub-cont.html").read_text(encoding="utf-8")
        data = json.loads(re.search(r"DATA = (\[.*\]);\n", page).group(1).replace("<\\/", "</"))
        self.assertEqual(len(data), 20)
        for item, k, row in zip(data, qs, self.out["continuation"]):
            self.assertEqual(sorted(item["options"]), list("ABCDE"))
            self.assertEqual(item["options"][item["real"]], row["rest"])
            self.assertEqual(k["real"], item["real"])
            self.assertEqual(k["order"][ord(k["real"]) - 65], "real")
            self.assertEqual(item["opening"], row["opening"])
            self.assertNotIn("question", item)
            self.assertEqual(sorted(item["options"].values()), sorted(row["answers"] + [row["rest"]]))
            for text in list(item["options"].values()) + [item["opening"]]:
                self.assertNotRegex(text, "[“”‘’–…\u00a0]|  |--")
        self.assertIn("The passage begins", page)
        self.assertIn('const LABEL = "stub-cont"', page)
        self.assertIn("Which ending is Hegel's?", page)
        self.assertGreater(len({k["real"] for k in qs}), 2)

    def test_the_continuation_style_compares_the_model_with_the_floor_and_with_the_chat_answers(self):
        st = self.out["continuation_style"]
        self.assertEqual((st["answers"], st["recited"], st["cut"]), (80, 0, 0))
        d = st["delta"]
        self.assertEqual(len(d["model_groups"]), 4)
        self.assertEqual(len(d["chat_groups"]), 4)
        self.assertAlmostEqual(d["model"], sum(d["model_groups"]) / 4, delta=0.002)
        self.assertLess(d["real"], d["model"])                               # the real second halves are the floor; the stub's sentences are not his
        self.assertLess(d["real"], d["chat"])
        self.assertEqual(st["reference"]["features"], 150)
        self.assertGreater(st["reference"]["segments"], 500)

    def test_compare_has_a_continuation_table_beside_the_first(self):
        with mock.patch.object(ht, "RESULTS", self.tmp), contextlib.redirect_stdout(io.StringIO()):
            (self.tmp / "hegeltest-bare.json").write_text(json.dumps({"label": "bare", "shelf": False}), encoding="utf-8")
            ht.compare(["stub", "bare"])
            md = (self.tmp / "hegeltest.md").read_text(encoding="utf-8")
            self.assertIn("| stub | no | 30/30 | 100% | 20/20 | 0 | 0 |", md)                 # the first table is as it was
            self.assertIn("## Continuation", md)
            self.assertIn("| mind | continuation: real picked | judges | recited | cut | Delta (model) | Delta (real halves) | Delta (chat answers) |", md)
            d = self.out["continuation_style"]["delta"]
            self.assertIn(f"| stub | not yet judged | – | 0/80 | 0/80 | {d['model']:.2f} | {d['real']:.2f} | {d['chat']:.2f} |", md)
            self.assertIn("| bare | – | – | – | – | – | – | – |", md)
            key = json.loads((self.tmp / "hegeltest-stub-cont-key.json").read_text(encoding="utf-8"))["questions"]
            wrong = lambda q: next(c for c in "ABCDE" if c != q["real"])
            (self.tmp / "hegeltest-stub-cont-judged.json").write_text(json.dumps(
                {"label": "stub-cont", "judge": "welt", "choices": {q["id"]: (q["real"] if i < 12 else wrong(q)) for i, q in enumerate(key)}}), encoding="utf-8")
            self.assertEqual([(j["judge"], j["hits"], j["answered"]) for j in ht.judged("stub-cont")], [("welt", 12, 20)])
            ht.compare(["stub", "bare"])
            md = (self.tmp / "hegeltest.md").read_text(encoding="utf-8")
            self.assertIn("| stub | 12/20 = 60% | welt | 0/80 | 0/80 |", md)
            self.assertIn("**stub**, welt: 12 real second halves picked of 20 answered (60%)", md)
            self.assertIn("not yet judged", md.split("## Continuation")[0])                    # the blind column of the first table is its own
            for name in ("hegeltest-stub-cont-judged.json", "hegeltest-bare.json"):
                (self.tmp / name).unlink()


class SplitTest(unittest.TestCase):
    def test_every_real_passage_splits_at_a_sentence_end_into_two_halves_of_at_least_35_words(self):
        for q in QUESTIONS:
            opening, rest = ht.split_passage(q["passage"])
            self.assertEqual(opening + " " + rest, q["passage"], q["id"])
            self.assertGreaterEqual(len(opening.split()), 35, q["id"])
            self.assertGreaterEqual(len(rest.split()), 35, q["id"])
            self.assertRegex(opening, r"[.?!;:]$", q["id"])                     # a sentence split, not the word-nearest-the-middle fallback
            self.assertEqual(ht.split_passage(q["passage"]), (opening, rest))      # and the same one every time
            n = len(q["passage"].split())
            self.assertLessEqual(abs(len(opening.split()) - n / 2), n / 2 - 35 + 1)

    def test_the_split_is_at_the_sentence_end_nearest_the_middle(self):
        sent = lambda n, end: " ".join(["w"] * (n - 1) + ["end" + end])
        for sizes, first in (((40, 25, 35), 1), ((45, 20, 35), 1), ((30, 35, 35), 2), ((36, 12, 12, 40), 2), ((30, 10, 14, 6, 40), 3), ((20, 20, 20, 20, 20), 2)):
            parts = [sent(n, ".") for n in sizes]
            opening, rest = ht.split_passage(" ".join(parts))
            self.assertEqual((opening, rest), (" ".join(parts[:first]), " ".join(parts[first:])), sizes)
        marks = [sent(40, ";"), sent(30, "?"), sent(30, "!")]
        self.assertEqual(ht.split_passage(" ".join(marks)), (marks[0], " ".join(marks[1:])))        # ; ? ! : close a sentence like a full stop

    def test_abbreviations_and_initials_do_not_end_a_sentence(self):
        text = ("Hegel, i.e. the philosopher, e.g. in lectures, viz. on the state, etc. and cf. the rest, met Mr. Smith at St. Helena with S. W. Dyde, "
                "who took it down. Then more words follow here. Done!")
        self.assertEqual([text[:e].split()[-1] for _, e in ht.sentence_ends(text)], ["down.", "here.", "Done!"])
        self.assertEqual([k for k, _ in ht.sentence_ends("No. Yes; and no: well? Yes! Done")], [1, 2, 4, 5, 6])
        self.assertEqual([k for k, _ in ht.sentence_ends("No. Yes; and no: well? Yes! Done", ".?!")], [1, 5, 6])
        quoted = 'He said "no." Then left (at last.) Gone.'
        self.assertEqual([quoted[:e].split()[-1] for _, e in ht.sentence_ends(quoted)], ['"no."', "last.)", "Gone."])      # a closing quote or bracket stays with its sentence
        self.assertEqual(ht.sentence_ends("a.b c.d 3.5 end"), [])

    def test_without_a_usable_sentence_end_it_splits_at_the_middle_word(self):
        text = " ".join(f"w{i}" for i in range(90)) + "."
        opening, rest = ht.split_passage(text)
        self.assertEqual((len(opening.split()), len(rest.split())), (45, 45))
        self.assertEqual(opening + " " + rest, text)
        short = "Short one. " + " ".join(["x"] * 60) + " end."                      # a sentence end at 2 words leaves an opening too short
        o, r = ht.split_passage(short)
        self.assertEqual(len(o.split()) + len(r.split()), len(short.split()))
        self.assertGreaterEqual(len(o.split()), 30)


class CutTest(unittest.TestCase):
    def test_cut_takes_the_sentence_end_nearest_the_length_asked(self):
        text = " ".join(["a"] * 19 + ["b."]) + " " + " ".join(["c"] * 19 + ["d."]) + " " + " ".join(["e"] * 19 + ["f."]) + " " + " ".join(["g"] * 19 + ["h."])
        self.assertEqual(len(ht.cut(text, 55).split()), 60)                      # ends at 20, 40, 60, 80: 60 is nearest 55
        self.assertEqual(len(ht.cut(text, 44).split()), 40)
        self.assertEqual(len(ht.cut(text, 80).split()), 80)
        self.assertTrue(ht.cut(text, 55).endswith("f."))

    def test_cut_returns_none_when_no_sentence_ends_between_07_and_13_times_the_length(self):
        text = " ".join(["a"] * 19 + ["b."]) + " " + " ".join(["c"] * 79 + ["d."])
        self.assertIsNone(ht.cut(text, 50))                                        # ends at 20 (too short) and at 100 (too long): window 35 to 65
        self.assertIsNone(ht.cut("no end here " * 30, 40))
        self.assertIsNone(ht.cut("", 40))
        self.assertIsNotNone(ht.cut(text, 100))
        self.assertIsNone(ht.cut(" ".join(["a"] * 59 + ["b;"]) + " " + " ".join(["c"] * 9), 60))      # a semicolon is no end for a continuation

    def test_cut_does_not_stop_at_an_abbreviation(self):
        text = " ".join(["a"] * 38) + " viz. the end of it and so on and on and on and on and on and on. " + "x " * 30
        self.assertEqual(ht.cut(text, 52).split()[-1], "on.")


class TypographyTest(unittest.TestCase):
    def test_one_typography_for_curly_quotes_dashes_dots_and_spaces(self):
        self.assertEqual(ht.typography("“The state” — it is ‘free’ – and\u00a0that’s it…  \n Yes -- no - maybe."), "\"The state\"—it is 'free'—and that's it... Yes—no—maybe.")
        self.assertEqual(ht.typography("r:—the process"), "r:—the process")                 # the translations' own dash stays what it is
        self.assertEqual(ht.typography("a well-known self-identity"), "a well-known self-identity")
        self.assertEqual(ht.typography(None), "")

    def test_real_and_model_text_leave_it_alike(self):
        real = " ".join(next(q["passage"] for q in QUESTIONS if mark in q["passage"]) for mark in ("—", "“"))
        model = real.replace("“", "\"").replace("”", "\"").replace("—", " – ").replace("’", "'")
        self.assertEqual(ht.typography(real), ht.typography(model))
        self.assertNotRegex(ht.typography(real), "[“”]")


class RecitationTest(unittest.TestCase):
    def test_a_run_of_eight_words_shared_with_the_real_half_is_a_recitation_whatever_the_typography(self):
        real = ht.split_passage(QUESTIONS[0]["passage"])[1]
        runs = ht.shingles(real)
        copy = "A mind may say: ALTHOUGH a state may be declared to violate right principles, and to be defective in various ways -- so he went on."
        self.assertTrue(ht.shares_run(copy, runs))
        self.assertTrue(ht.shares_run(real, runs))
        seven = "a state may be declared to violate. Then something else entirely follows here, and more."
        self.assertFalse(ht.shares_run(seven, runs))
        self.assertFalse(ht.shares_run("The state is the actuality of the ethical idea, and nothing else is.", runs))
        self.assertFalse(ht.shares_run("", runs))
        self.assertEqual(ht.shingles("a b c d e f g h i", 8), {tuple("abcdefgh"), tuple("bcdefghi")})
        self.assertEqual(ht.shingles("Schönheit-und Tübingen", 2), ht.shingles("schonheit und tubingen", 2))


class HeaderTest(unittest.TestCase):
    def test_the_prompt_header_is_the_one_of_the_training_text(self):
        for q in QUESTIONS:
            self.assertEqual(ht.header_for(q), train_data.header(WORKS[q["source"]], q["ref"], q["ref"]), q["id"])
        self.assertEqual(ht.header_for(QUESTIONS[0]), "Hegel's Philosophy of Right, tr. S. W. Dyde (1896), §258, Addition")
        self.assertEqual(ht.header_for(QUESTIONS[1]), "Hegel, Lectures on the Philosophy of History, tr. J. Sibree (1857), Introduction")
        self.assertEqual(ht.header_for(QUESTIONS[0], "§272"), "Hegel's Philosophy of Right, tr. S. W. Dyde (1896), §272")

    def test_the_header_without_a_ref_is_the_start_of_the_header_lines_of_the_training_text(self):
        corpus_file = REPO / "mind/train/corpus.jsonl"
        if not corpus_file.exists():
            self.skipTest("mind/train/corpus.jsonl is not built here")
        with corpus_file.open(encoding="utf-8") as f:
            heads = {json.loads(line)["text"].split("\n\n")[0] for line in f}
        for q in QUESTIONS:
            self.assertTrue(any(h.startswith(ht.header_for(q, "") + ", ") for h in heads), q["id"])

    def test_without_the_corpus_tools_it_is_built_from_the_question(self):
        with mock.patch.object(ht, "corpus_tools", return_value=None):
            self.assertEqual(ht.header_for(QUESTIONS[0]), "Hegel, Philosophy of Right, tr. S. W. Dyde (1896), §258, Addition")
            self.assertEqual(ht.header_for(QUESTIONS[0], "§272"), "Hegel, Philosophy of Right, tr. S. W. Dyde (1896), §272")
            self.assertTrue(all(ht.header_for(q).startswith("Hegel, ") and q["ref"] in ht.header_for(q) for q in QUESTIONS))

    def test_a_failed_import_falls_back_and_says_so(self):
        ht.corpus_tools.cache_clear()
        self.addCleanup(ht.corpus_tools.cache_clear)
        with mock.patch.dict(sys.modules, {"train_data": None}), mock.patch("sys.stderr", new_callable=io.StringIO) as err:
            self.assertIsNone(ht.corpus_tools())
            self.assertEqual(ht.header_for(QUESTIONS[0]), "Hegel, Philosophy of Right, tr. S. W. Dyde (1896), §258, Addition")
        self.assertIn("corpus headers unavailable", err.getvalue())


class CompleteTest(unittest.TestCase):
    def test_complete_posts_a_raw_prompt_and_returns_the_content(self):
        with FakeServer() as srv:
            text = ht.complete(srv.url, "Hegel, Philosophy of Right\n\nThe state is free.", 60, 0.9, 20, seed=7)
            body = ht.StubLlama.calls[-1]
        self.assertTrue(text.strip() and not text.startswith(" "))
        self.assertEqual(body, {"prompt": "Hegel, Philosophy of Right\n\nThe state is free.", "n_predict": 60, "temperature": 0.9, "seed": 7, "cache_prompt": False})

    def test_the_continuation_is_its_first_paragraph_even_after_opening_blank_lines(self):
        for content, want in (("\n\nIt goes on. Still.\n\nA new start.", "It goes on. Still."), (" It goes on.\n \nNot this.", "It goes on.")):
            reply = mock.MagicMock()
            reply.__enter__.return_value.read.return_value = json.dumps({"content": content}).encode()
            with mock.patch.object(ht.urllib.request, "urlopen", return_value=reply):
                self.assertEqual(ht.complete("http://x", "p", 20, 0.5, 20), want)

    def test_without_a_seed_none_is_sent(self):
        with FakeServer() as srv:
            ht.complete(srv.url, "p", 20, 0.5, 20)
            self.assertNotIn("seed", ht.StubLlama.calls[-1])

    def test_a_server_that_does_not_answer_is_an_empty_continuation(self):
        with mock.patch("sys.stderr"):
            self.assertEqual(ht.complete("http://127.0.0.1:9", "p", 10, 0.1, 1), "")


class RetryTest(unittest.TestCase):
    """continuation(): one slot of a sheet, with the seeds it tries and what it keeps, against a scripted server."""

    REST = ht.split_passage(QUESTIONS[0]["passage"])[1]
    WORDS = len(REST.split())
    CLEAN = " ".join(["Reason"] + ["and"] * 7 + ["freedom"] * 5) + ". " + " ".join(f"item{i}" for i in range(int(WORDS * 0.9))) + "."
    ARGS = type("A", (), {"timeout": 5})()

    def run_slot(self, replies):
        seeds = []

        def fake(url, prompt, tokens, temperature, timeout, seed=None):
            seeds.append(seed)
            return replies[min(len(seeds), len(replies)) - 1]

        with mock.patch.object(ht, "complete", fake):
            return ht.continuation("u", "p", self.WORDS, ht.shingles(self.REST), self.ARGS, 100), seeds

    def test_a_clean_first_try_is_kept(self):
        (text, recited, hard), seeds = self.run_slot([self.CLEAN])
        self.assertEqual((text, recited, hard, seeds), (self.CLEAN, False, False, [100]))

    def test_a_recitation_is_asked_again_with_the_next_seed(self):
        (text, recited, hard), seeds = self.run_slot([self.REST, self.CLEAN])
        self.assertEqual((text, recited, hard, seeds), (self.CLEAN, False, False, [100, 101]))

    def test_a_text_that_stays_a_recitation_is_kept_and_marked(self):
        (text, recited, hard), seeds = self.run_slot([self.REST])
        self.assertEqual((recited, hard, seeds), (True, False, [100, 101, 102]))
        self.assertEqual(text, ht.cut(self.REST, self.WORDS))

    def test_a_text_without_a_sentence_end_near_the_length_is_asked_again_and_then_cut_at_the_word(self):
        endless = " ".join(f"w{i}" for i in range(self.WORDS * 2))
        (text, recited, hard), seeds = self.run_slot([endless, self.CLEAN])
        self.assertEqual((text, hard, seeds), (self.CLEAN, False, [100, 101]))
        (text, recited, hard), seeds = self.run_slot([endless])
        self.assertEqual((len(text.split()), recited, hard, seeds), (self.WORDS, False, True, [100, 101, 102]))

    def test_the_best_try_stays_not_recited_before_not_cut(self):
        endless = " ".join(f"w{i}" for i in range(self.WORDS * 2))
        (text, recited, hard), seeds = self.run_slot([self.REST, endless, self.REST])
        self.assertEqual((recited, hard, len(text.split())), (False, True, self.WORDS))      # the hard-cut one: a copy would flatter the model
        (text, recited, hard), seeds = self.run_slot([""])                              # a server that says nothing: three tries, an empty text, cut
        self.assertEqual((text, recited, hard, seeds), ("", False, True, [100, 101, 102]))

    def test_the_typography_of_the_model_is_normalised_before_anything_is_compared(self):
        curly = self.CLEAN.replace("Reason", "“Reason”").replace("freedom", "freedom —")
        (text, recited, hard), _ = self.run_slot([curly])
        self.assertNotRegex(text, "[“”]")
        self.assertTrue(text.startswith('"Reason"'))


class DeltaTest(unittest.TestCase):
    def test_the_reference_is_150_features_over_segments_of_the_english_books_without_the_overlapping_passages(self):
        ref = ht.reference()
        self.assertIs(ref, ht.reference())                                          # built once per process
        self.assertEqual(len(ref["features"]), 150)
        self.assertEqual(len(ref["mean"]), 150)
        self.assertTrue(all(sd > 0 for sd in ref["sd"]))
        self.assertTrue({"the", "of", "and", "is"} <= set(ref["features"][:6]))
        self.assertGreater(ref["segments"], 800)
        self.assertTrue(900 < ref["words"] / ref["segments"] < 1100)                   # segments of about a thousand words
        self.assertGreaterEqual(ref["left_out"], 20)                                   # at least the twenty passages themselves
        self.assertTrue(0.5 < sum(ref["mean"]) < 0.75)                                 # the 150 commonest words are about two thirds of his English

    def test_delta_ranks_the_real_halves_closer_to_his_translators_than_the_chat_answers_of_a_model(self):
        rests = " ".join(ht.split_passage(q["passage"])[1] for q in QUESTIONS)
        size = len(rests.split())
        chat = json.loads((REPO / "mind/results/hegeltest-qwen.json").read_text(encoding="utf-8"))["blind"]
        modern = " ".join(" ".join(b["answers"][0].split()[:55]) for b in chat)           # modern chat prose of the same length
        real, other = ht.delta(rests), ht.delta(modern)
        self.assertLess(real, other - 0.1, (real, other, size))
        self.assertLess(real, 1.0)

    def test_delta_of_a_text_is_the_mean_of_its_distances_in_standard_deviations(self):
        ref = ht.reference()
        text = " ".join(["the", "of", "and"] * 10 + ["zzz"] * 10)
        words = text.split()
        want = sum(abs((words.count(f) / len(words) - m) / s) for f, m, s in zip(ref["features"], ref["mean"], ref["sd"])) / 150
        self.assertAlmostEqual(ht.delta(text), want)
        self.assertIsNone(ht.delta(""))
        self.assertIsNone(ht.delta("1234 !!!"))
        with mock.patch.object(ht, "reference", return_value=None):
            self.assertIsNone(ht.delta("the state"))

    def test_the_continuation_style_groups_by_seed_and_cuts_the_chat_answers_to_the_length_of_the_real_halves(self):
        rows = [{"id": q["id"], "rest": ht.split_passage(q["passage"])[1], "answers": [f"the thing of {i} and {q['id']}." for i in range(4)],
                 "recited": [False, True, False, False], "cut": [False, False, False, True]} for q in QUESTIONS]
        blind = [{"id": q["id"], "answers": [" ".join(["freedom"] * 300) for _ in range(4)]} for q in QUESTIONS]
        st = ht.continuation_style({"continuation": rows, "blind": blind})
        self.assertEqual((st["answers"], st["recited"], st["cut"]), (80, 20, 20))
        self.assertEqual(len(st["delta"]["model_groups"]), 4)
        self.assertEqual(len(st["delta"]["chat_groups"]), 4)
        self.assertEqual(ht.groups_of(rows)[0].count("thing of 0"), 20)
        self.assertIsNone(ht.continuation_style({"continuation": rows})["delta"]["chat"])
        with mock.patch.object(ht, "reference", return_value=None):
            self.assertEqual(ht.continuation_style({"continuation": rows})["delta"], None)


class MergeTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="hegel-merge-"))
        patch = mock.patch.object(ht, "RESULTS", self.tmp)
        patch.start()
        self.addCleanup(patch.stop)
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_a_run_of_one_part_keeps_the_other_parts_of_the_file_that_is_there(self):
        earlier = {"label": "keep", "url": "http://pc:8082", "started": "2026-10-05T10:00:00", "shelf": True, "holdout": "family", "answers_per_question": 4,
                   "blind": blind_for(), "biography": {"right": 17, "n": 30, "partial": 0.8, "items": []},
                   "behaviour": {"n": 20, "valid": 20, "refused": 0, "leaking": 0, "leaks": [], "thought_words": 40.0, "thought_chars": 250.0, "rows": []}}
        path = self.tmp / "hegeltest-keep.json"
        path.write_text(json.dumps(earlier, indent=1) + "\n", encoding="utf-8")
        with FakeServer() as srv:
            self.assertEqual(cli("--url", srv.url, "--label", "keep", "--only", "cont", "--timeout", "20"), 0)
            calls = list(ht.StubLlama.calls)
        out = json.loads(path.read_text(encoding="utf-8"))
        for k in ("label", "url", "shelf", "holdout", "answers_per_question", "blind", "biography", "behaviour"):
            self.assertEqual(out[k], earlier[k], k)
        self.assertNotEqual(out["started"], earlier["started"])
        self.assertEqual(len(out["continuation"]), 20)
        self.assertEqual(len(calls), 80)                                              # only the continuations were asked
        self.assertTrue(all("prompt" in c for c in calls))
        self.assertIsNotNone(out["continuation_style"]["delta"]["chat"])               # the chat answers of the blind part already there serve as the contrast
        self.assertEqual(list(out)[:9], list(earlier))                                 # the same order as before; the new parts come last
        self.assertTrue((self.tmp / "hegeltest-keep-cont.html").exists())
        self.assertFalse((self.tmp / "hegeltest-keep.html").exists())                  # the blind sheet is not touched

    def test_a_run_of_the_blind_part_keeps_the_continuations_and_renews_the_contrast(self):
        with FakeServer() as srv:
            cli("--url", srv.url, "--label", "mix", "--only", "cont", "--timeout", "20")
            first = json.loads((self.tmp / "hegeltest-mix.json").read_text(encoding="utf-8"))
            self.assertIsNone(first["continuation_style"]["delta"]["chat"])
            cli("--url", srv.url, "--label", "mix", "--only", "blind", "--timeout", "20", "--answers", "2")
        out = json.loads((self.tmp / "hegeltest-mix.json").read_text(encoding="utf-8"))
        self.assertEqual(out["continuation"], first["continuation"])
        self.assertEqual(len(out["blind"]), 20)
        self.assertEqual(out["answers_per_question"], 2)
        self.assertIsNotNone(out["continuation_style"]["delta"]["chat"])
        self.assertEqual(len(out["continuation_style"]["delta"]["chat_groups"]), 2)

    def test_a_new_label_gets_a_file_with_only_the_part_that_ran(self):
        with FakeServer() as srv:
            cli("--url", srv.url, "--label", "fresh", "--only", "cont", "--timeout", "20")
        out = json.loads((self.tmp / "hegeltest-fresh.json").read_text(encoding="utf-8"))
        self.assertEqual(set(out), {"label", "url", "started", "shelf", "holdout", "answers_per_question", "continuation", "continuation_style"})
        self.assertEqual((out["label"], out["shelf"], out["holdout"]), ("fresh", False, None))

    def test_the_shelf_flag_does_not_reach_the_continuations_or_the_record_of_the_file(self):
        earlier = {"label": "sh", "url": "u", "started": "x", "shelf": True, "holdout": "family", "answers_per_question": 4}
        (self.tmp / "hegeltest-sh.json").write_text(json.dumps(earlier), encoding="utf-8")
        with FakeServer() as srv:
            cli("--url", srv.url, "--label", "sh", "--only", "cont", "--timeout", "20")
            self.assertTrue(all("From your shelf" not in c.get("prompt", "") for c in ht.StubLlama.calls))
        out = json.loads((self.tmp / "hegeltest-sh.json").read_text(encoding="utf-8"))
        self.assertEqual((out["shelf"], out["holdout"], out["url"]), (True, "family", "u"))


class ExportTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="hegel-ppl-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def export(self, *extra):
        out = io.StringIO()
        with mock.patch.object(sys, "argv", ["hegel_test.py", "--export-ppl", str(self.tmp / "ppl"), *extra]), contextlib.redirect_stdout(out):
            rc = ht.main()
        return rc, out.getvalue()

    def blocks(self, name):
        return (self.tmp / "ppl" / name).read_text(encoding="utf-8").strip().split("\n\n")

    def test_it_writes_the_twenty_real_passages_and_twenty_seen_ones_under_their_headers(self):
        rc, said = self.export()
        self.assertEqual(rc, 0)
        held, seen = self.blocks("heldout.txt"), self.blocks("seen.txt")
        self.assertEqual((len(held), len(seen)), (40, 40))                         # a header and a passage, twenty times
        for q, head, body in zip(QUESTIONS, held[0::2], held[1::2]):
            self.assertEqual((head, body), (ht.header_for(q), q["passage"]))
        for q, head, body in zip(QUESTIONS, seen[0::2], seen[1::2]):
            self.assertTrue(head.startswith(ht.header_for(q, "") + ", ") and head != ht.header_for(q, ""), head)      # the same work as the question's, under a ref of its own
            self.assertTrue(80 <= len(body.split()) <= 140, len(body.split()))
        self.assertEqual(len(set(seen[1::2])), 20)

    def test_the_seen_passages_are_in_the_shelf_and_share_no_run_of_eight_words_with_the_held_out_ones(self):
        self.export()
        held, seen = self.blocks("heldout.txt")[1::2], self.blocks("seen.txt")[1::2]
        index = ht.shelf.load()
        texts = set(index.data["texts"])
        self.assertTrue(all(b in texts for b in seen))
        runs = set()
        for q in QUESTIONS:
            runs |= train_data.shingles(q["passage"], 8) | train_data.shingles(q["original"], 8)
        for b in seen:
            self.assertFalse(train_data.shingles(b, 8) & runs)
            self.assertFalse(ht.shares_run(b, ht.shingles(" ".join(held))))
        self.assertFalse(train_data.shingles(" ".join(seen), 8) & train_data.shingles("\n\n".join(held), 8))

    def test_the_seen_passages_are_the_same_every_time_and_another_seed_picks_others(self):
        self.export()
        first = (self.tmp / "ppl" / "seen.txt").read_text(encoding="utf-8")
        shutil.rmtree(self.tmp / "ppl")
        self.export()
        self.assertEqual(first, (self.tmp / "ppl" / "seen.txt").read_text(encoding="utf-8"))
        self.export("--seed", "7")
        self.assertNotEqual(first, (self.tmp / "ppl" / "seen.txt").read_text(encoding="utf-8"))

    def test_it_prints_both_paths_and_the_four_commands_with_and_without_the_adapter(self):
        _, said = self.export()
        for name in ("heldout.txt", "seen.txt"):
            self.assertIn(str(self.tmp / "ppl" / name), said)
            self.assertIn(f"llama-perplexity -m QWEN.gguf -f {self.tmp / 'ppl' / name} -c 512 -ngl 99", said)
            self.assertIn(f"llama-perplexity -m QWEN.gguf --lora pc/out/hegel-lora.gguf -f {self.tmp / 'ppl' / name} -c 512 -ngl 99", said)
        self.assertEqual(said.count("llama-perplexity -m"), 4)

    def test_the_seen_passages_carry_no_mark_of_the_scan(self):
        vocab = ht.english_vocabulary()
        self.assertTrue(ht.misprinted("But it must be sought out and won; and Eather purpoee imder", vocab))
        self.assertTrue(ht.misprinted("the simpHcity of itseK", vocab))
        self.assertFalse(ht.misprinted("Rather must it be first sought out and won, for the purpose is freedom.", vocab))
        self.export()
        for body in self.blocks("seen.txt")[1::2]:
            self.assertFalse(ht.misprinted(body, vocab))

    def test_without_a_shelf_it_says_so(self):
        with mock.patch.object(ht.shelf, "load", return_value=None), mock.patch("sys.stderr"):
            self.assertEqual(self.export()[0], 1)


class StubTest(unittest.TestCase):
    def test_the_stub_answers_a_completion_with_sentences_of_about_the_length_asked(self):
        with FakeServer() as srv:
            texts = [ht.complete(srv.url, "p", n, 0.9, 20, seed=s) for n in (90, 150, 250) for s in (1, 2)]
        self.assertEqual(len(set(texts)), 6)
        for t, n in zip(texts, (90, 90, 150, 150, 250, 250)):
            self.assertRegex(t, r"[.]$")
            self.assertAlmostEqual(len(t.split()), n / 2.5, delta=12)
            self.assertNotIn("\n\n", t)


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
