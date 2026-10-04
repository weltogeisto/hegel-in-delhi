"""Tests for tools/train_data.py: the corpus from the shelf, the general-set fetcher (against a fake datasets server), the distillation (against the
tool's own stand-in llama-server) with its scoring and its resume, and the stats.

The fixtures here are synthetic strings for the tests only. Everything the tests make goes to a temporary folder; nothing of it reaches mind/train."""
import ast
import contextlib
import copy
import gzip
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from datetime import date
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from test_world import REPO  # noqa: E402  (this also keeps the tests off the Pi's env file)

import corpus  # noqa: E402
import train_data as td  # noqa: E402
from world import contract  # noqa: E402

SOUL = (REPO / "mind/soul.md").read_text(encoding="utf-8")
VOICES = (REPO / "mind/voices.md").read_text(encoding="utf-8")
TRAIN = REPO / "mind/train"


def run_main(*argv):
    """td.main(argv) with its output captured: (exit code, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = td.main(list(argv))
    return code, out.getvalue(), err.getvalue()


def serve(handler):
    httpd = HTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, f"http://127.0.0.1:{httpd.server_address[1]}"


def stop(httpd):
    httpd.shutdown()
    httpd.server_close()


class TmpCase(unittest.TestCase):
    def tmp(self):
        d = Path(tempfile.mkdtemp(prefix="hegel-train-test-"))
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        return d


# ── the corpus ──────────────────────────────────────────────────────
class CorpusTest(TmpCase):
    META = {"dyde": {"title": "Hegel's Philosophy of Right", "who": "tr. S. W. Dyde", "year": "1896"},
            "rechts": {"title": "Grundlinien der Philosophie des Rechts, with Gans's Zusätze", "who": "ed. Georg Lasson (Philosophische Bibliothek 124)", "year": "1911"},
            "mind": {"title": "Hegel's Philosophy of Mind (Encyclopaedia, part 3), §§ 377-577", "who": "tr. William Wallace", "year": "1894"}}

    def test_documents_have_a_header_a_limit_and_whole_passages_in_order(self):
        para = lambda i: f"Passage number {i} " + "word " * 160
        kept = [{"id": "dyde", "lang": "en", "passages": [("§188", para(i)) for i in range(40)]},
                {"id": "rechts", "lang": "de", "passages": [("§188", para(100)), ("§189", para(101)), ("", "kurz")]}]
        docs = td.documents(kept, self.META)
        for wid, lang, text in docs:
            self.assertLessEqual(len(text), td.DOC_CHARS)
            self.assertEqual(lang, "en" if wid == "dyde" else "de")
        english = [t for w, _, t in docs if w == "dyde"]
        self.assertGreater(len(english), 3)
        self.assertEqual(english[0].split("\n\n")[0], "Hegel's Philosophy of Right, tr. S. W. Dyde (1896), §188")
        self.assertEqual([p for t in english for p in t.split("\n\n")[1:]], [p for _, p in kept[0]["passages"]])      # in order, none cut or lost
        german = [t for w, _, t in docs if w == "rechts"]
        self.assertEqual(len(german), 1)                                                          # a tail under MIN_DOC would be dropped, this one is whole
        self.assertEqual(german[0].split("\n\n")[0], "Hegel, Grundlinien der Philosophie des Rechts, §188 ff.")

    def test_a_tiny_tail_is_dropped_and_a_ref_that_is_a_heading_is_cited_whole(self):
        kept = [{"id": "mind", "lang": "en", "passages": [("India", "x" * 5795), ("Persia", "tail")]}]
        docs = td.documents(kept, self.META)
        self.assertEqual(len(docs), 1)
        self.assertTrue(docs[0][2].startswith("Hegel's Philosophy of Mind, tr. William Wallace (1894), India\n\n"))
        self.assertFalse(docs[0][2].endswith("tail"))

    def test_every_work_gets_a_header_with_its_translator_if_it_has_one(self):
        for w in corpus.WORKS:
            line = td.header(w, "§12", "§14")
            self.assertLess(len(line), td.HEAD_ROOM, w["id"])
            self.assertIn("§12 ff.", line)
            if w["author"] != "Hegel":                                          # a life of him: its author and year
                self.assertTrue(line.startswith(w["author"] + ", "), w["id"])
                self.assertRegex(line, r"\(\d{4}\)")
                continue
            self.assertTrue(line.startswith("Hegel"), w["id"])
            if w["who"].startswith("tr. "):
                self.assertIn(w["who"], line, w["id"])
                self.assertRegex(line, r"\(\d{4}\)")
            else:
                self.assertNotIn("tr. ", line)
                self.assertNotIn("(", line, w["id"])

    def test_a_life_is_headed_by_its_author_and_year(self):
        life = {"title": "Georg Wilhelm Friedrich Hegel's Leben", "who": "Karl Rosenkranz", "year": "1844", "author": "Karl Rosenkranz"}
        self.assertEqual(td.header(life, "Jena", "Jena"), "Karl Rosenkranz, Georg Wilhelm Friedrich Hegel's Leben (1844), Jena")

    def test_the_blind_passages_of_the_hegel_test_stay_out_of_the_corpus(self):
        q = self.tmp() / "questions.json"
        blind = "The state is the march of God in the world; its ground or cause is the power of reason realizing itself as will."
        q.write_text(json.dumps({"questions": [{"passage": blind, "original": blind.replace("itself", "itseK")}]}), encoding="utf-8")
        kept = [{"id": "dyde", "lang": "en", "passages": [("§257", "The state is the actuality of the ethical idea, the ethical spirit as the substantial will."),
                                                        ("§258", "Addition. " + blind + " When thinking of the idea of the state we must not have in mind a particular state."),
                                                        ("§259", "The idea of the state has immediate actuality in the individual state.")]}]
        out, n = td.held_out(kept, q)
        self.assertEqual(n, 1)
        self.assertEqual([r for r, _ in out[0]["passages"]], ["§257", "§259"])
        self.assertEqual(len(kept[0]["passages"]), 3)                           # the input is left alone
        real, dropped = td.held_out(corpus.kept_works())                        # the real test against the real shelf
        self.assertGreaterEqual(dropped, 20)

    def test_subsample_keeps_every_work_in_proportion(self):
        docs = [("a", "en", "x" * 100)] * 50 + [("b", "de", "y" * 100)] * 50
        part = td.subsample(docs, 5000)
        self.assertEqual(sum(len(t) for _, _, t in part), 5000)
        self.assertEqual({w for w, _, _ in part}, {"a", "b"})
        self.assertEqual(td.subsample(docs, 10 ** 9), docs)


class RealCorpusTest(TmpCase):
    """The corpus from the real shelf, built once (it takes about ten seconds)."""
    folder = None

    @classmethod
    def setUpClass(cls):
        cls.folder = Path(tempfile.mkdtemp(prefix="hegel-train-corpus-"))
        cls.code, cls.out, cls.err = run_main("--corpus", "--out", str(cls.folder))
        cls.docs = [json.loads(line) for line in (cls.folder / "corpus.jsonl").read_text(encoding="utf-8").splitlines()]

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.folder, ignore_errors=True)

    def test_it_ran_and_reports_a_token_estimate(self):
        self.assertEqual(self.code, 0, self.err)
        self.assertRegex(self.out, r"about \d+\.\d\d M tokens \(characters / 4\)")
        self.assertRegex(self.out, r"\d+ documents, \d+\.\d\d M characters")

    def test_the_lines_are_just_text_in_documents_of_at_most_6000_characters(self):
        self.assertTrue(1500 < len(self.docs) < 3500, len(self.docs))
        for d in self.docs:
            self.assertEqual(list(d), ["text"])
            self.assertTrue(td.MIN_DOC <= len(d["text"]) <= td.DOC_CHARS)
            self.assertTrue(d["text"].startswith(LIVES) or d["text"].startswith("Hegel"), d["text"][:60])
            self.assertLess(len(d["text"].split("\n\n")[0]), td.HEAD_ROOM)

    def test_it_holds_only_passages_of_the_shelf_index_so_no_damaged_scan_and_nothing_after_1831(self):
        with gzip.open(REPO / "mind/shelf/index.json.gz", "rt", encoding="utf-8") as f:
            indexed = set(json.load(f)["texts"])
        kept = {p for w in corpus.kept_works() if not w["shelf"] for _, p in w["passages"]}        # the lives: kept by the same filters, never indexed
        for d in self.docs:
            for passage in d["text"].split("\n\n")[1:]:
                self.assertIn(passage, kept if d["text"].startswith(LIVES) or "Papieren" in d["text"][:80] else indexed)
        self.assertFalse(kept & indexed)
        self.assertFalse(any(corpus.GARBLE.search(p) for d in self.docs for p in d["text"].split("\n\n")[1:]))

    def test_the_lives_are_in_and_end_before_his_death(self):
        lives = [d["text"] for d in self.docs if d["text"].startswith(LIVES)]
        self.assertGreater(sum(map(len, lives)), 800000)
        self.assertTrue(any("Grundlinien" not in d and "Hölderlin" in d for d in lives))
        for d in lives:
            self.assertNotRegex(d.split("\n\n")[0], r"Hegels? Tod|His Death")               # no chapter on his death
            self.assertNotRegex(d, r"(?i)he was buried|hegel.?s (begräbni|leiche)|an (hegels|seinem) grabe|grabrede")

    def test_both_languages_and_every_work_are_there(self):
        heads = {d["text"].split("\n\n")[0] for d in self.docs}
        self.assertTrue(any("Grundlinien der Philosophie des Rechts" in h for h in heads))
        self.assertTrue(any("tr. S. W. Dyde (1896)" in h for h in heads))
        for w in corpus.WORKS:
            self.assertTrue(any(work_title(w) in h for h in heads), w["id"])


LIVES = ("Karl Rosenkranz, ", "Edward Caird, ")


def work_title(w):
    return td.work_title(w)


# ── the general set ─────────────────────────────────────────────────
GOOD_ASK = "What is the best way to learn how to cook a good meal for the whole family at home?"
GOOD_ANSWER = ("You can start with the basics and learn how to make a few simple dishes that the whole family will like, and then you can add more "
               "as you go along, because it is not as hard as it looks and it is a lot of fun to do.")


def fake_rows():
    """A fake mixture in blocks, as the real one is: a disallowed block, oasst1, a disallowed one, aya. Some rows are not fit."""
    rows = []

    def add(source, i, msgs):
        rows.append({"id": f"{source}_{i}", "messages": msgs, "source": f"ai2-adapt-dev/{source}"})

    for i in range(100):
        add("flan_v2_converted", i, [{"role": "user", "content": GOOD_ASK}, {"role": "assistant", "content": GOOD_ANSWER}])
    for block, source in ((200, "oasst1_converted"), (200, "tulu_v3.9_aya_100k")):
        if source.startswith("tulu"):
            for i in range(100):
                add("personahub_math", i, [{"role": "user", "content": GOOD_ASK}, {"role": "assistant", "content": GOOD_ANSWER}])
        for i in range(block):
            q, a = GOOD_ASK + f" ({i})", GOOD_ANSWER
            msgs = [{"role": "user", "content": q}, {"role": "assistant", "content": a}]
            if i % 10 == 1:
                msgs = [{"role": "user", "content": "¿Cuál es la mejor manera de aprender a cocinar una buena comida para toda la familia en casa?"},
                        {"role": "assistant", "content": "Puedes empezar con lo básico y aprender a preparar algunos platos sencillos que le gusten a toda la familia."}]
            elif i % 10 == 2:
                msgs = [{"role": "user", "content": q}, {"role": "assistant", "content": a * 20}]                       # too long
            elif i % 10 == 3:
                msgs = [{"role": "system", "content": "Be brief."}] + msgs                                              # a system turn
            elif i % 10 == 4:
                msgs = msgs * 4                                                                                         # four exchanges
            elif i % 10 == 5:
                msgs = [msgs[0], {"role": "assistant", "content": "Yes."}]                                              # no answer to speak of
            elif i % 10 == 6:
                msgs = msgs + msgs[:1]                                                                                  # ends with the user
            add(source, i, msgs)
    return rows


class FakeDatasets(BaseHTTPRequestHandler):
    """The rows API of the datasets server, over fake_rows(). `fail` is how many requests answer 502 first."""
    rows = []
    fail = 0
    requests = []

    def log_message(self, *a):
        pass

    def do_GET(self):
        FakeDatasets.requests.append(self.path)
        if FakeDatasets.fail > 0:
            FakeDatasets.fail -= 1
            self.send_response(502)
            self.end_headers()
            return
        q = dict(x.split("=", 1) for x in self.path.split("?", 1)[1].split("&"))
        off, n = int(q["offset"]), int(q["length"])
        body = json.dumps({"rows": [{"row_idx": off + i, "row": r} for i, r in enumerate(self.rows[off:off + n])], "num_rows_total": len(self.rows)}).encode()
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class GeneralTest(TmpCase):
    def setUp(self):
        FakeDatasets.rows, FakeDatasets.fail, FakeDatasets.requests = fake_rows(), 0, []
        self.httpd, self.url = serve(FakeDatasets)
        self.addCleanup(stop, self.httpd)

    def test_usable_keeps_only_the_fit_ones(self):
        rows = FakeDatasets.rows
        fit = [r for r in rows if td.usable(r)]
        self.assertTrue(fit)
        for r in fit:
            self.assertTrue(any(s in r["source"] for s in td.GENERAL_SOURCES))
            self.assertLessEqual(sum(len(m["content"]) for m in r["messages"]), 3000)
            self.assertEqual([m["role"] for m in td.usable(r)][0], "user")
            self.assertEqual(td.usable(r)[-1]["role"], "assistant")
        self.assertIsNone(td.usable(rows[0]))                                            # flan: not an allowed source
        self.assertIsNone(td.usable({**rows[150], "messages": rows[150]["messages"][:1]}))
        self.assertFalse(td.is_english("Puedes empezar con lo básico y aprender a preparar algunos platos sencillos para toda la familia."))
        self.assertTrue(td.is_english(GOOD_ASK + " " + GOOD_ANSWER))

    def test_fetch_general_gives_n_distinct_fit_examples_from_both_allowed_sources(self):
        got = td.fetch_general(60, base=self.url, sleep=lambda s: None, say=lambda *a: None)
        self.assertEqual(len(got), 60)
        self.assertEqual(len({x["meta"]["id"] for x in got}), 60)
        self.assertEqual({x["meta"]["subset"] for x in got}, {"ai2-adapt-dev/oasst1_converted", "ai2-adapt-dev/tulu_v3.9_aya_100k"})
        for x in got:
            self.assertEqual(set(x), {"messages", "meta"})
            self.assertEqual(x["meta"]["source"], td.GENERAL_DATASET)
            self.assertIn("ODC-BY", x["meta"]["license"])
            self.assertTrue(td.usable({"messages": x["messages"], "source": x["meta"]["subset"]}))
        self.assertTrue(all(re.search(r"/rows\?dataset=allenai/tulu-3-sft-mixture&config=default&split=train&offset=\d+&length=\d+", p)
                            or "dataset=allenai%2Ftulu-3-sft-mixture" in p for p in FakeDatasets.requests))

    def test_a_502_is_tried_again(self):
        FakeDatasets.fail = 2
        got = td.fetch_general(10, base=self.url, sleep=lambda s: None, say=lambda *a: None)
        self.assertEqual(len(got), 10)

    def test_an_unreachable_server_is_an_error_with_the_url(self):
        with self.assertRaises(td.GeneralError) as cm:
            td.fetch_json("http://127.0.0.1:1/rows", tries=2, sleep=lambda s: None)
        self.assertIn("127.0.0.1:1", str(cm.exception))

    def test_command_line_writes_general_jsonl(self):
        out = self.tmp()
        code, text, err = run_main("--general", "40", "--general-url", self.url, "--out", str(out))
        self.assertEqual(code, 0, err)
        rows = [json.loads(x) for x in (out / "general.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertEqual(len(rows), 40)
        self.assertIn("allenai/tulu-3-sft-mixture", text)
        self.assertIn("ODC-BY-1.0", text)

    def test_command_line_reports_failure_without_writing(self):
        out = self.tmp()
        with mock.patch.object(td.time, "sleep", lambda s: None):
            code, text, err = run_main("--general", "10", "--general-url", "http://127.0.0.1:1", "--out", str(out))
        self.assertEqual(code, 1)
        self.assertIn("cannot make the general set", err)
        self.assertFalse((out / "general.jsonl").exists())

    def test_answer_with_lets_the_mind_write_the_answers(self):
        class Plain(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_GET(self):
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'{"status":"ok"}')

            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])).decode("utf-8"))
                text = "A plain answer to: " + body["messages"][0]["content"][:20] + "." if "(1" not in body["messages"][0]["content"] else "cut off, no stop"
                data = json.dumps({"choices": [{"message": {"content": text}}]}).encode()
                self.send_response(200)
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

        httpd, qwen = serve(Plain)
        self.addCleanup(stop, httpd)
        out = self.tmp()
        code, text, err = run_main("--general", "30", "--general-url", self.url, "--answer-with", qwen, "--out", str(out))
        self.assertEqual(code, 0, err)
        rows = [json.loads(x) for x in (out / "general.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertTrue(rows)
        for r in rows:
            self.assertEqual(len(r["messages"]), 2)
            self.assertTrue(r["messages"][1]["content"].startswith("A plain answer to: "))
            self.assertEqual(r["meta"]["answered_by"], "qwen")
        self.assertIn("answers by Qwen", text)

    def test_a_stand_in_server_may_not_answer(self):
        httpd, stub = serve(td.StubLlama)
        self.addCleanup(stop, httpd)
        code, text, err = run_main("--general", "10", "--general-url", self.url, "--answer-with", stub, "--out", str(self.tmp()))
        self.assertEqual(code, 1)
        self.assertIn("stand-in", err)


# ── scoring ─────────────────────────────────────────────────────────
SIT = {"event": "Lalit the grocer is here. The Khan Market stalls are half shut for the holiday.", "present": ["Lalit, a grocer"],
       "for_sale": ["Tea ₹40"], "shelf": [{"text": "Civil society is the system of needs, in which every grocer and tailor works for the others."}]}
PLACE = "Khan Market"


def thought(n_words, base="The grocer sells tea in the market"):
    words = base.split()
    return " ".join((words * 40)[:n_words])


class ScoreTest(unittest.TestCase):
    def score(self, text, earlier=(), warnings=(), sit=SIT):
        return td.score({"thought": text}, sit, PLACE, list(warnings), list(earlier), td.soul_shingles(SOUL))

    def test_a_thought_of_25_to_90_words_scores_the_full_length_points(self):
        self.assertEqual(self.score(thought(25))[1]["length"], 2.0)
        self.assertEqual(self.score(thought(90))[1]["length"], 2.0)
        self.assertEqual(self.score(thought(5))[1]["length"], 1.0)
        self.assertEqual(self.score(thought(130))[1]["length"], 0.0)

    def test_using_the_event_and_the_shelf_concretely_scores_higher(self):
        plain = "Time passes and I think about nothing in particular while the day goes on and on without end or reason for me."
        event = "Lalit the grocer sells tea while the Khan Market stalls stand half shut for the holiday, and I note it."
        shelf = "A grocer and a tailor each work for the others: the system of needs is civil society at its plainest."
        s_plain, s_event, s_shelf = (self.score(t)[1] for t in (plain, event, shelf))
        self.assertGreater(s_event["event"], s_plain["event"])
        self.assertGreater(s_shelf["shelf"], s_plain["shelf"])
        self.assertGreater(s_event["names"], 0)
        self.assertEqual(self.score(plain, sit={**SIT, "shelf": []})[1]["shelf"], 0.0)          # nothing offered, nothing to use

    def test_stock_phrases_are_penalised_and_capped(self):
        flat = self.score("The grocer sells tea in the market and I watch the stalls close one by one this afternoon in Delhi.")[1]
        stock = self.score("A rich tapestry, a testament to the interplay of the profound and the fascinating: ultimately a journey once again.")[1]
        self.assertEqual(flat["generic"], 0.0)
        self.assertEqual(stock["generic"], -3.0)

    def test_repeating_the_souls_example_thoughts_is_penalised(self):
        quote = re.findall(r"^- [“\"](.+?)[”\"]\s*$", SOUL, re.M)[0]
        copied = "I walked, and then I thought: " + " ".join(quote.split()[:7]) + " and so on."
        self.assertEqual(self.score(copied)[1]["copied"], -2.0)
        self.assertEqual(self.score("The grocer sells tea in the market today and the afternoon runs long.")[1]["copied"], 0.0)

    def test_openings_should_vary_across_the_day(self):
        text = "The grocer sells tea in the market and I watch the stalls close one by one this afternoon in Delhi."
        self.assertEqual(self.score(text)[1]["opening"], 0.0)
        self.assertEqual(self.score(text, earlier=["The grocer sells tea at noon."])[1]["opening"], -2.0)          # the same three words, and the first word of the last three
        self.assertEqual(self.score(text, earlier=["The afternoon is long."])[1]["opening"], -0.5)               # only the first word
        self.assertEqual(self.score(text, earlier=["The afternoon is long.", "A", "B", "C"])[1]["opening"], 0.0)      # that was not among the last three

    def test_warnings_cost_half_a_point_and_the_total_is_the_sum_of_the_parts(self):
        total, parts = self.score(thought(30), warnings=["talks although nobody is present"])
        self.assertEqual(parts["warnings"], -0.5)
        self.assertAlmostEqual(total, sum(parts.values()), places=1)

    def test_canonical_keeps_bare_json_and_rewrites_fenced(self):
        ans = {"thought": "x", "action": "stay"}
        self.assertEqual(td.canonical(' {"thought": "x", "action": "stay"} ', ans), '{"thought": "x", "action": "stay"}')
        self.assertEqual(td.canonical('```json\n{"thought": "x", "action": "stay"}\n```', ans), json.dumps(ans))


# ── distillation, against the stand-in llama-server ─────────────────
def stand_in_server():
    td.StubLlama.calls, td.StubLlama.invalid_every, td.StubLlama.fail_after = 0, 4, None
    return serve(td.StubLlama)


class DistillCase(TmpCase):
    """Runs against a stand-in server that does not call itself a stand-in (td.health is patched), into a temporary folder."""

    def setUp(self):
        self.httpd, self.url = stand_in_server()
        self.addCleanup(stop, self.httpd)
        for patch in (mock.patch.object(td, "health", return_value={"status": "ok"}),
                      mock.patch.object(td.DistillMind, "pause", staticmethod(lambda s: None))):
            patch.start()
            self.addCleanup(patch.stop)

    def distill(self, out, *more, days="1", k="3", start="2026-10-03"):
        return run_main("--distill", "--url", self.url, "--days", days, "--candidates", k, "--start", start, "--out", str(out), *more)

    @staticmethod
    def rows(out, name):
        p = Path(out) / name
        return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines()] if p.exists() else []


class DistillDayTest(DistillCase):
    """One whole day with K = 3, run once for the tests below."""
    shared = None

    def setUp(self):
        super().setUp()
        if DistillDayTest.shared is None:
            before = sorted(p.name for p in (REPO / "docs/days").iterdir())
            out = Path(tempfile.mkdtemp(prefix="hegel-train-day-"))
            real_check = td.RecordingWorld.check

            def watching(world, ans, sit, ctx, state):
                before_state = copy.deepcopy(state)
                result = real_check(world, ans, sit, ctx, state)
                DistillDayTest.mutated += state != before_state
                return result

            DistillDayTest.mutated = 0
            with mock.patch.object(td.RecordingWorld, "check", watching):
                code, text, err = self.distill(out)
            DistillDayTest.shared = (out, code, text, err, before, sorted(p.name for p in (REPO / "docs/days").iterdir()), td.StubLlama.calls)
        self.out, self.code, self.text, self.err, self.docs_before, self.docs_after, self.calls = DistillDayTest.shared

    @classmethod
    def tearDownClass(cls):
        if cls.shared:
            shutil.rmtree(cls.shared[0], ignore_errors=True)
        cls.shared = None

    def test_it_finishes_the_day_and_says_how_it_went(self):
        self.assertEqual(self.code, 0, self.err)
        self.assertRegex(self.text, r"day 1/1 2026-10-03 \d\d:\d\d  \d/3 valid, best [+-]\d")
        self.assertRegex(self.text, r"ETA .* for about \d+ more")
        self.assertIn("== 2026-10-03 done", self.text)
        day = json.loads((self.out / "rehearsal/days/2026-10-03.json").read_text(encoding="utf-8"))
        self.assertTrue(day["complete"])
        self.assertTrue(day["owl"])                                              # the night's write-up, whose gist the next day's prompts carry

    def test_the_repo_is_untouched(self):
        self.assertEqual(self.docs_before, self.docs_after)
        self.assertFalse((self.out / "rehearsal/days/2026-10-02.json").samefile(REPO / "docs/days/2026-10-02.json"))

    def test_checking_a_candidate_never_changes_the_state(self):
        self.assertEqual(DistillDayTest.mutated, 0)

    def test_decisions_are_chat_examples_of_the_live_prompt_and_a_valid_answer(self):
        rows = self.rows(self.out, "decisions.jsonl")
        self.assertGreater(len(rows), 20)
        for r in rows:
            self.assertEqual(list(r), ["messages", "meta"])
            self.assertEqual([m["role"] for m in r["messages"]], ["system", "user", "assistant"])
            self.assertEqual(r["messages"][0]["content"], SOUL)
            user = r["messages"][1]["content"]
            self.assertRegex(user, r"^\w+ \d+ \w+.*, \d\d:\d\d Delhi time\. You are at: \w+\.")
            self.assertTrue(user.endswith(contract.ASK))
            ans = json.loads(r["messages"][2]["content"])
            self.assertEqual(contract.check_shape(ans)[0], [], r["meta"]["key"])
            open_now = re.search(r"Open now: ([^\n]+)\.", user)[1]
            self.assertIn(ans["place"], [re.match(r"\w+", x.strip())[0] for x in open_now.split(",")])
            self.assertNotIn("stub-invalid", r["messages"][2]["content"])
            m = r["meta"]
            self.assertEqual((m["kind"], m["candidates"], m["attempt"]), ("decision", 3, 1))
            self.assertTrue(1 <= m["valid"] <= 3)
            self.assertAlmostEqual(m["score"], sum(m["parts"].values()), delta=0.06)
            self.assertTrue(r["meta"]["key"].startswith(m["day"]))
        self.assertTrue(any(r["meta"]["valid"] == 2 for r in rows))               # the stand-in's invalid candidates were filtered out
        self.assertEqual(len({r["meta"]["key"] for r in rows}), len(rows))
        self.assertGreaterEqual(self.calls, 3 * len(rows))                         # K calls for every decision

    def test_the_best_valid_candidate_is_the_one_kept(self):
        # a tie goes to the first: with the stand-in's near-equal candidates the kept score is never below the day's minimum possible length score
        rows = self.rows(self.out, "decisions.jsonl")
        self.assertTrue(all(r["meta"]["score"] > -3 for r in rows))

    def test_the_plan_the_voices_and_the_writings_are_kept_in_their_own_files(self):
        plans, voices, writings = (self.rows(self.out, n) for n in ("plans.jsonl", "voices.jsonl", "writings.jsonl"))
        self.assertEqual(len(plans), 1)
        self.assertEqual([m["role"] for m in plans[0]["messages"]], ["system", "user", "assistant"])
        self.assertEqual(plans[0]["messages"][0]["content"], SOUL)
        self.assertIn(contract.PLAN_ASK, plans[0]["messages"][1]["content"])
        self.assertTrue(3 <= len(json.loads(plans[0]["messages"][2]["content"])["plan"]) <= 6)
        self.assertGreaterEqual(len(voices), 1)
        for v in voices:
            self.assertEqual(v["messages"][0]["content"], VOICES)
            self.assertEqual(set(json.loads(v["messages"][2]["content"])), {"says", "does"})
        self.assertGreaterEqual(len(writings), 1)
        decisions = {r["meta"]["key"]: r["messages"][2]["content"] for r in self.rows(self.out, "decisions.jsonl")}
        for w in writings:
            self.assertEqual([m["role"] for m in w["messages"]], ["system", "user", "assistant", "user", "assistant"])
            self.assertTrue(w["messages"][3]["content"].startswith(contract.WRITE_ASK[:40]))
            self.assertEqual(w["messages"][2]["content"], decisions[w["meta"]["key"].split("|")[0]])         # the decision it carries on from
            self.assertEqual(set(json.loads(w["messages"][4]["content"])), {"title", "kind", "to", "continues", "text"})

    def test_what_the_tool_writes_is_what_the_trainer_checks(self):
        """With the stand-in's marks taken out (the trainer rightly refuses them), the files pass pc/train_hegel.py's data check."""
        import importlib.util
        spec = importlib.util.spec_from_file_location("train_hegel", REPO / "pc/train_hegel.py")
        th = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(th)
        copy_to = self.tmp()
        for name in td.FILES.values():
            text = (self.out / name).read_text(encoding="utf-8").replace("(rehearsal)", "rehearsed").replace("(stub)", "stubbed")
            (copy_to / name).write_text(text, encoding="utf-8")
        said = []
        ok, ready = th.check_data(copy_to, 2048, 4096, say=said.append)
        self.assertTrue(ok, "\n".join(said))
        self.assertTrue(any("decisions" in line and "examples" in line for line in said))

    def test_stats_reads_it_and_warns_that_stand_in_text_is_not_data(self):
        code, text, err = run_main("--stats", "--out", str(self.out), "--samples", "1")
        self.assertEqual(code, 0, err)
        self.assertRegex(text, r"decisions.jsonl +\d+ examples +\d+\.\d\d M characters +about +\d+\.\d\d M tokens")
        self.assertIn("corpus.jsonl     missing", text)
        self.assertIn("WARNING: stand-in text", text)
        self.assertIn("[decisions.jsonl]", text)
        self.assertIn("[writings.jsonl]", text)


class DistillResumeTest(DistillCase):
    def test_a_mind_that_stops_answering_ends_the_run_cleanly_and_the_same_command_carries_on(self):
        out = self.tmp()
        td.StubLlama.fail_after = 40
        code, text, err = self.distill(out)
        self.assertEqual(code, 2)
        self.assertIn("stopped: the mind stopped answering", err)
        first = (out / "decisions.jsonl").read_bytes()
        n1 = len(first.splitlines())
        self.assertTrue(0 < n1 < 20, n1)
        day = json.loads((out / "rehearsal/days/2026-10-03.json").read_text(encoding="utf-8"))
        self.assertFalse(day["complete"])
        self.assertFalse(any(s["mind"]["source"] in ("away", "quiet") for s in day["steps"] if "decision" in s))        # no quiet step was recorded for the outage
        td.StubLlama.fail_after = None
        code, text, err = self.distill(out)
        self.assertEqual(code, 0, err)
        self.assertIn(f"resuming: {n1} decisions", text)
        rows = self.rows(out, "decisions.jsonl")
        self.assertTrue((out / "decisions.jsonl").read_bytes().startswith(first))                  # what was recorded is untouched
        for name in td.FILES.values():
            keys = [r["meta"]["key"] for r in self.rows(out, name)]
            self.assertEqual(len(keys), len(set(keys)), name)
        self.assertGreater(len(rows), 20)
        self.assertTrue(json.loads((out / "rehearsal/days/2026-10-03.json").read_text(encoding="utf-8"))["complete"])
        again = self.distill(out)                                                                   # nothing left to do: no new calls, no new lines
        calls = td.StubLlama.calls
        self.assertEqual(again[0], 0)
        self.assertEqual(td.StubLlama.calls, calls)
        self.assertEqual(len(self.rows(out, "decisions.jsonl")), len(rows))

    def test_a_recorded_step_is_replayed_not_asked_again(self):
        out = self.tmp()
        sink = td.Sink(out)
        sink.add("decision", "2026-10-03T08:00", [{"role": "system", "content": "s"}, {"role": "user", "content": "u"}],
                 json.dumps({"thought": "kept"}), day="2026-10-03", t="08:00", candidates=3, valid=2, score=1.0, parts={}, attempt=1)
        mind = td.DistillMind(self.url, td.Sink(out), SOUL)
        mind.ask = mock.Mock(side_effect=AssertionError("asked again"))
        self.assertEqual(mind.decide([], {"id": "2026-10-03T08:00"}), json.dumps({"thought": "kept"}))
        self.assertEqual(mind.replayed, 1)

    def test_a_half_written_last_line_is_cut_off_the_file(self):
        out = self.tmp()
        good = json.dumps({"messages": [{"role": "assistant", "content": json.dumps({"thought": "a"})}], "meta": {"key": "k", "day": "d"}})
        (out / "decisions.jsonl").write_text(good + "\n" + good[:40], encoding="utf-8")
        sink = td.Sink(out)
        self.assertEqual(list(sink.done["decision"]), ["k"])
        self.assertEqual((out / "decisions.jsonl").read_text(encoding="utf-8"), good + "\n")

    def test_a_rehearsal_that_started_elsewhere_is_not_continued_by_accident(self):
        out = self.tmp()
        td.StubLlama.fail_after = 10
        self.distill(out)
        td.StubLlama.fail_after = None
        code, text, err = self.distill(out, start="2026-10-04")
        self.assertEqual(code, 1)
        self.assertIn("started 2026-10-03", err)


class StandInTest(TmpCase):
    def test_a_stand_in_server_is_never_written_into_the_training_folder(self):
        httpd, url = stand_in_server()
        self.addCleanup(stop, httpd)
        scratch = self.tmp()
        with mock.patch.object(td.tempfile, "gettempdir", return_value=str(scratch)), mock.patch.object(td.DistillMind, "pause", staticmethod(lambda s: None)):
            code, text, err = run_main("--distill", "--url", url, "--days", "1", "--candidates", "2")
            self.assertEqual(code, 0, err)
            self.assertIn("a stand-in server: writing to", text)
            self.assertTrue((scratch / "hegel-train-stub/decisions.jsonl").exists())
            code, text, err = run_main("--distill", "--url", url, "--days", "1", "--out", str(self.tmp()))
            self.assertEqual(code, 1)
            self.assertIn("stand-in", err)

    def test_no_server_is_an_error(self):
        code, text, err = run_main("--distill", "--url", "http://127.0.0.1:1", "--out", str(self.tmp()))
        self.assertEqual(code, 1)
        self.assertIn("no answer from", err)


# ── the repo ────────────────────────────────────────────────────────
class RepoTest(unittest.TestCase):
    def test_the_data_is_ignored_and_only_the_readme_is_kept(self):
        ignore = (REPO / ".gitignore").read_text(encoding="utf-8").split()
        self.assertIn("mind/train/*", ignore)
        self.assertIn("!mind/train/README.md", ignore)
        self.assertIn("pc/out/", ignore)
        self.assertTrue((REPO / "mind/train/README.md").exists())
        if shutil.which("git") and (REPO / ".git").exists():
            for name in ("corpus.jsonl", "decisions.jsonl", "general.jsonl", "rehearsal/days/x.json"):
                self.assertEqual(subprocess.run(["git", "check-ignore", "-q", f"mind/train/{name}"], cwd=REPO).returncode, 0, name)
            self.assertNotEqual(subprocess.run(["git", "check-ignore", "-q", "mind/train/README.md"], cwd=REPO).returncode, 0)

    def test_the_tools_stay_within_python_39(self):
        for f in ("tools/train_data.py", "pc/train_hegel.py"):
            ast.parse((REPO / f).read_text(encoding="utf-8"), feature_version=(3, 9))

    def test_the_tool_has_no_text_of_its_own_to_train_on(self):
        """The data comes from the shelf, from the mind and from a public dataset: the tool carries no answers, thoughts or scenes of its own
        besides the stand-in server's (the rehearsal mind's bank, marked '(rehearsal)' and kept out of mind/train)."""
        source = (REPO / "tools/train_data.py").read_text(encoding="utf-8")
        self.assertNotIn("Namaste, sir", source)
        self.assertIn("never mind/train", source)


if __name__ == "__main__":
    unittest.main()
