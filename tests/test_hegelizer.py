"""Tests for tools/hegelizer.py: the units built from the real shelf (window, no overlap with the Hegel test's passages, the scan check, the split), and the
paraphrase against a fake llama-server (the prompt as sent, validation, the retry, the failed file, resuming, workers, an interrupted run, a server that stops).

The synthetic texts are fixtures for these tests, written into temporary folders only."""
import argparse
import contextlib
import io
import json
import math
import random
import re
import shutil
import sys
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from test_world import REPO  # noqa: E402  (this also keeps the tests off the Pi's env file)

import hegelizer as hz  # noqa: E402
import train_data  # noqa: E402
from world import shelf  # noqa: E402

QUESTIONS = json.loads((REPO / "mind/hegeltest/questions.json").read_text(encoding="utf-8"))["questions"]
ENGLISH = {"wallace-logic", "wallace-mind", "dyde-right", "sibree-history", "haldane-1", "haldane-2", "haldane-3", "baillie-1", "baillie-2", "bosanquet-art"}


def cli(*argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = hz.main(list(argv))
    return code, out.getvalue(), err.getvalue()


def S(n, tag):
    """A sentence of n words that starts with a capital and ends with a full stop (so that shelf.sentences cuts after it)."""
    return " ".join([f"A{tag}"] + [f"b{tag}x{i}" for i in range(n - 2)] + [f"z{tag}."])


def passage(sentences, size, tag):
    return " ".join(S(size, f"{tag}s{i}") for i in range(sentences))


class RealShelfTest(unittest.TestCase):
    """--build on the shelf of the repository, once for all the tests of this class."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="hegelizer-build-"))
        cls.code, cls.said, _ = cli("--build", "--out", str(cls.tmp))
        cls.units = hz.read_rows(cls.tmp / hz.UNITS)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_every_english_work_has_units_and_the_report_counts_them(self):
        self.assertEqual(self.code, 0)
        self.assertEqual({u["work"] for u in self.units}, ENGLISH)
        for work in ENGLISH:
            self.assertRegex(self.said, rf"\n  {work} +\d+ +\d+ +\d+ +\d+ ")
        total = re.search(r"\n  all +(\d+) +(\d+) +(\d+) +(\d+) +(\d+) +(\d+) +(\d+)", self.said)
        self.assertEqual(int(total[1]), len(self.units))
        self.assertEqual((int(total[2]), int(total[3])), (sum(u["split"] == "train" for u in self.units), sum(u["split"] == "held" for u in self.units)))
        self.assertEqual(int(total[4]), sum(hz.words_of(u["original"]) for u in self.units))
        self.assertGreater(len(self.units), 3000)
        self.assertGreater(int(total[4]), 700000)

    def test_a_unit_has_150_to_250_words_and_the_fields_the_trainer_reads(self):
        for u in self.units:
            self.assertEqual(set(u), {"id", "work", "ref", "original", "split"})
            self.assertTrue(hz.UNIT_WORDS[0] <= hz.words_of(u["original"]) <= hz.UNIT_WORDS[1], u["id"])
            self.assertIn(u["split"], ("train", "held"))
            self.assertRegex(u["id"], rf"^{re.escape(u['work'])}:\d+$")
        self.assertEqual(len({u["id"] for u in self.units}), len(self.units))

    def test_a_unit_is_contiguous_text_of_its_work(self):
        books = shelf.load()                    # (its passages without the editor's apparatus, as build_units reads them)
        body = {w["id"]: " ".join(hz.apparatus(t) for t in books.data["texts"][w["start"]:w["start"] + w["n"]]) for w in books.works if w["lang"] == "en"}
        for u in self.units:
            self.assertIn(u["original"], body[u["work"]], u["id"])

    def test_no_unit_shares_eight_words_with_the_twenty_passages_of_the_hegel_test(self):
        runs = set()
        for q in QUESTIONS:
            runs |= train_data.shingles(q["passage"], train_data.HELD_OUT_RUN) | train_data.shingles(q["original"], train_data.HELD_OUT_RUN)
        self.assertEqual(hz.RUN, train_data.HELD_OUT_RUN)
        for u in self.units:
            self.assertFalse(runs & train_data.shingles(u["original"], train_data.HELD_OUT_RUN), u["id"])
        self.assertGreaterEqual(len(runs), 2000)
        dropped = int(re.search(r"\n  all +\d+ +\d+ +\d+ +\d+ +(\d+) ", self.said)[1])
        self.assertGreaterEqual(dropped, 15)                          # the passages themselves, in the units that held them
        self.assertEqual(hz.blind_runs()[0], runs)

    def test_a_unit_that_overlaps_a_test_passage_is_dropped_whatever_the_typography(self):
        q = QUESTIONS[0]
        books = {"works": [{"id": "x", "work": "X", "lang": "en", "start": 0, "n": 2}], "data": {"refs": ["a", "b"], "texts": [q["passage"] + " " + passage(14, 10, "p"), passage(30, 10, "q") + " " + passage(10, 10, "r")]}}
        fake = type("Books", (), books)()
        units, report = hz.build_units(fake)
        self.assertEqual(report["x"]["overlap"], 1)
        self.assertTrue(all(q["passage"][:40] not in u["original"] for u in units))

    def test_no_unit_still_shows_its_scan_and_a_thousand_were_dropped_for_it(self):
        counts = hz.english_counts(shelf.load())
        self.assertFalse([u["id"] for u in self.units if hz.damaged(u["original"], counts)])
        dropped = int(re.search(r"\n  all +\d+ +\d+ +\d+ +\d+ +\d+ +(\d+) ", self.said)[1])
        self.assertGreater(dropped, 500)

    def test_five_percent_of_each_work_is_held_out_and_the_split_is_the_same_every_time(self):
        for work in ENGLISH:
            mine = [u for u in self.units if u["work"] == work]
            held = sum(u["split"] == "held" for u in mine)
            self.assertEqual(held, max(1, round(hz.HELD_SHARE * len(mine))), work)
        share = sum(u["split"] == "held" for u in self.units) / len(self.units)
        self.assertTrue(0.045 <= share <= 0.055, share)
        again = tempfile.mkdtemp(prefix="hegelizer-again-")
        self.addCleanup(shutil.rmtree, again, True)
        cli("--build", "--out", again)
        self.assertEqual((Path(again) / hz.UNITS).read_bytes(), (self.tmp / hz.UNITS).read_bytes())
        plain = [{k: v for k, v in u.items() if k != "split"} for u in self.units]
        self.assertEqual(hz.assign_split(plain), self.units)
        other = hz.assign_split(plain, seed=7)
        self.assertNotEqual([u["split"] for u in other], [u["split"] for u in self.units])
        self.assertEqual(sum(u["split"] == "held" for u in other), sum(u["split"] == "held" for u in self.units))

    def test_the_build_warns_of_finished_rows_that_no_longer_match(self):
        folder = Path(tempfile.mkdtemp(prefix="hegelizer-stale-"))
        self.addCleanup(shutil.rmtree, folder, True)
        hz.write_rows(folder / hz.DONE, [{"id": "dyde-right:0", "work": "dyde-right", "ref": "x", "split": "train", "plain": "p", "original": "not the unit"}])
        _, said, _ = cli("--build", "--out", str(folder))
        self.assertIn("WARNING: 1 rows of", said)
        self.assertEqual(hz.mismatched(self.units, hz.read_rows(folder / hz.DONE)), 1)

    def test_without_a_shelf_it_says_so(self):
        with mock.patch.object(hz.shelf, "load", return_value=None):
            code, _, err = cli("--build", "--out", str(self.tmp / "none"))
        self.assertEqual(code, 1)
        self.assertIn("no shelf", err)


class WindowTest(unittest.TestCase):
    def test_consecutive_passages_are_merged_until_the_unit_is_in_the_window(self):
        ps = [(f"r{i}", passage(10, 12, i)) for i in range(4)]            # 120 words each
        units, lost = hz.work_units(ps)
        self.assertEqual(units, [("r0", ps[0][1] + " " + ps[1][1]), ("r2", ps[2][1] + " " + ps[3][1])])
        self.assertEqual(lost, 0)

    def test_a_passage_that_would_overflow_is_filled_from_the_front_and_the_rest_begins_the_next_unit(self):
        a, b, c = passage(14, 10, "a"), passage(14, 10, "b"), passage(14, 10, "c")      # 140 words each
        units, lost = hz.work_units([("ra", a), ("rb", b), ("rc", c)])
        front, rest = hz.fill(b, 110)
        self.assertEqual(hz.words_of(front), 110)
        self.assertEqual(units[0], ("ra", a + " " + front))
        self.assertEqual(hz.words_of(units[0][1]), 250)
        self.assertEqual(units[1], ("rb", rest + " " + c))                   # the ref is that of the passage the unit begins in
        self.assertEqual((len(units), lost), (2, 0))

    def test_a_passage_longer_than_the_window_is_cut_at_sentence_ends(self):
        p = passage(60, 10, "long")                                          # 600 words
        pieces = hz.split_long(p, 250)
        self.assertEqual([hz.words_of(x) for x in pieces], [250, 250, 100])
        self.assertEqual(" ".join(pieces), p)
        units, lost = hz.work_units([("r", p)])
        self.assertEqual([hz.words_of(t) for _, t in units], [250, 250])
        self.assertEqual(lost, 1)                                            # the 100 words left at the end make no unit
        self.assertEqual(" ".join(t for _, t in units), " ".join(pieces[:2]))

    def test_fragments_that_make_no_unit_are_counted(self):
        self.assertEqual(hz.work_units([("r", passage(10, 10, "s"))]), ([], 1))             # a tail of 100 words
        one = " ".join(["Word"] + ["more"] * 298 + ["end."])                                  # a single sentence of 300 words
        self.assertEqual(hz.work_units([("r", one)]), ([], 1))
        units, lost = hz.work_units([("r", passage(10, 10, "t")), ("r2", one), ("r3", passage(16, 10, "u"))])
        self.assertEqual((len(units), lost), (1, 2))                         # 100 words, then a sentence that does not fit them: the 100 are lost, the sentence too
        self.assertEqual(hz.words_of(units[0][1]), 160)

    def test_whatever_the_passages_every_unit_is_in_the_window_and_in_order(self):
        rng = random.Random(5)
        ps = [(f"r{i}", passage(rng.randint(5, 17), rng.randint(6, 14), i)) for i in range(300)]
        units, lost = hz.work_units(ps)
        self.assertGreater(len(units), 100)
        self.assertTrue(all(150 <= hz.words_of(t) <= 250 for _, t in units))
        body = " ".join(p for _, p in ps)
        positions = [body.find(t) for _, t in units]
        self.assertTrue(all(x >= 0 for x in positions) and positions == sorted(positions))
        self.assertLessEqual(lost, 3)

    def test_fill_takes_whole_sentences(self):
        text = " ".join([S(10, "a"), S(10, "b"), S(10, "c")])
        self.assertEqual(hz.fill(text, 25), (S(10, "a") + " " + S(10, "b"), S(10, "c")))
        self.assertEqual(hz.fill(text, 5), ("", text))
        self.assertEqual(hz.fill(text, 100), (text, ""))


class ApparatusTest(unittest.TestCase):
    """The editor's apparatus goes before units are made: a restyled page of his must not copy section numbers or note labels."""

    def test_section_numbers_labels_references_and_footnote_marks_go(self):
        cases = {"§ 168. Since marriage proceeds out of freedom": "Since marriage proceeds out of freedom",
                 "it is so. Note. — Marriage, or monogamy, rather": "it is so. Marriage, or monogamy, rather",
                 "it is so. Addition. — The state is": "it is so. The state is",
                 "as was shown (§ 258) the state": "as was shown the state",
                 "the ethical (cf. § 142 and § 150) life[3] goes on*)": "the ethical life goes on",
                 "§ 1. PHILOSOPHY misses an advantage": "Philosophy misses an advantage",
                 "(1) the first, (2) the second": "(1) the first, (2) the second"}                    # his own enumerations stay
        for raw, clean in cases.items():
            self.assertEqual(hz.apparatus(raw), clean, raw)
        self.assertEqual(hz.apparatus("in § 41 we saw"), "in § 41 we saw")                       # in the run of a sentence: build_units drops the unit

    def test_no_unit_of_the_real_shelf_keeps_a_section_mark(self):
        units, report = hz.build_units(shelf.load())
        self.assertFalse([u["id"] for u in units if "§" in u["original"]])
        self.assertTrue(all("apparatus" in r for r in report.values()))


class DamageTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.counts = hz.english_counts(shelf.load())

    def test_the_scan_marks_of_the_writings_primer_are_recognised(self):
        for text in ("the tho abstract sphere", "Wo rid' s", "tlie state", "hke a", "rnay be"):
            self.assertTrue(hz.damaged(text, self.counts), text)

    def test_ordinary_text_is_not(self):
        for text in ("the like of it", "a lie", "the size of the state"):
            self.assertFalse(hz.damaged(text, self.counts), text)

    def test_the_other_litter_and_the_counts_are_kept_as_they_were(self):
        for text in ("the simpHcity of it", "a stray ■ sign", "x ^ y", "a { brace"):
            self.assertTrue(hz.damaged(text, None), text)
        self.assertFalse(hz.damaged("tlie state", None))                        # without counts only the litter counts
        self.assertIs(hz.english_counts(shelf.load()), self.counts)             # counted once per shelf
        self.assertGreater(self.counts["the"], 10000)
        self.assertEqual((hz.RARE, hz.COMMON, hz.MISREAD_RARE, hz.MISREAD_COMMON), (10, 2000, 50, 300))
        self.assertEqual(hz.near("ab") & {"b", "a", "cb", "abc"}, {"b", "a", "cb", "abc"})


class JudgeTest(unittest.TestCase):
    ORIGINAL = " ".join(f"w{i}" for i in range(100))

    def reply(self, words, **kw):
        return hz.judge(self.ORIGINAL, " ".join(words) if not isinstance(words, str) else words, **kw)

    def test_a_reply_in_the_right_length_without_a_copy_stands_as_one_paragraph(self):
        plain, why = self.reply([f"x{i}" for i in range(100)])
        self.assertEqual((why, hz.words_of(plain)), (None, 100))
        plain, _ = self.reply("First part of it.\n\nSecond part, " + " ".join(f"x{i}" for i in range(98)))
        self.assertNotIn("\n", plain)

    def test_the_word_ratio_is_between_06_and_14(self):
        for n, ok in ((59, False), (60, True), (140, True), (141, False)):
            self.assertEqual(self.reply([f"x{i}" for i in range(n)])[1] is None, ok, n)

    def test_empty_and_cut_off_replies_fail(self):
        self.assertEqual(self.reply("   ")[1], "empty")
        self.assertEqual(self.reply("")[1], "empty")
        self.assertEqual(self.reply("<think>hm</think>")[1], "empty")
        self.assertEqual(self.reply([f"x{i}" for i in range(100)], finish="length")[1], "cut off at max_tokens")
        self.assertIsNone(self.reply([f"x{i}" for i in range(100)], finish="stop")[1])

    def test_a_run_of_eight_words_shared_with_the_original_fails_whatever_the_case_and_punctuation(self):
        words = [f"x{i}" for i in range(100)]
        words[10:18] = [f"w{i}" for i in range(30, 38)]
        plain, why = self.reply(words)
        self.assertIn("shares 8 words", why)
        words[10:18] = [f"W{i}," if i % 2 else f"w{i}." for i in range(30, 38)]
        self.assertIn("shares 8 words", self.reply(words)[1])
        words[10:18] = [f"w{i}" for i in range(30, 37)] + ["other"]
        self.assertIsNone(self.reply(words)[1])                                    # seven are fine
        self.assertEqual(hz.runs_of("The Tübingen—Schönheit, 'and' (so)", 2), hz.runs_of("the tubingen schonheit and so", 2))

    def test_list_markers_headings_and_announcements_fail(self):
        body = " ".join(f"x{i}" for i in range(100))
        for text in ("- one\n- two\n" + body, "1. one\n2. two\n" + body, "* one\n" + body, "# Rewritten\n" + body, "**Rewritten**\n" + body, "> quoted\n" + body,
                     "1) one\n" + body, "Here is the rewritten text:\n" + body):
            self.assertIsNotNone(self.reply(text)[1], text)
        self.assertIsNone(self.reply("1831. " + body)[1])                              # a year is no list marker
        self.assertIsNone(self.reply("Reason, he said - and rightly - rules.\n" + body)[1])

    def test_quotes_round_the_whole_reply_and_think_tags_are_removed(self):
        body = " ".join(f"x{i}" for i in range(100))
        self.assertEqual(self.reply(f"“{body}”")[0], body)
        self.assertEqual(self.reply(f"<think>hm</think>\n{body}")[0], body)
        self.assertEqual(self.reply(f'"Yes," he said, {body}')[0], f'"Yes," he said, {body}')       # a quotation inside stays

    def test_the_prompt_is_the_agreed_one(self):
        self.assertEqual(hz.PARAPHRASE_SYSTEM, "You rewrite passages of old philosophy in plain present-day English.")
        self.assertEqual(hz.PARAPHRASE_ASK, "Rewrite the passage below in plain, modern English, as a careful writer would today. Keep every claim, example and step of the "
                         "argument, in the same order. Add nothing, explain nothing, leave nothing out. Do not quote it. Use clear sentences and everyday words, about the "
                         "same length. Answer with the rewritten text only.\n\n{original}")
        self.assertEqual((hz.TEMPERATURE, hz.RETRY_TEMPERATURE, hz.RATIO, hz.RUN, hz.UNIT_WORDS, hz.HELD_SHARE), (0.3, 0.7, (0.6, 1.4), 8, (150, 250), 0.05))


class Llama:
    """A fake llama-server on a free port: GET /health, and POST /v1/chat/completions answered by reply(original, temperature, n) where n counts the earlier
    calls for that text. A reply is a text, a (text, finish_reason) or an int, the HTTP status to answer with."""

    def __init__(self, reply, delay=0.0):
        self.reply, self.delay, self.calls, self.lock, self.active, self.peak = reply, delay, [], threading.Lock(), 0, 0
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_GET(self):
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'{"status":"ok"}')

            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])).decode("utf-8"))
                original = body["messages"][-1]["content"].split("\n\n", 1)[1]
                with outer.lock:
                    n = sum(c["original"] == original for c in outer.calls)
                    outer.calls.append({"original": original, "temperature": body["temperature"], "body": body, "path": self.path})
                    outer.active += 1
                    outer.peak = max(outer.peak, outer.active)
                try:
                    time.sleep(outer.delay)
                    got = outer.reply(original, body["temperature"], n)
                finally:
                    with outer.lock:
                        outer.active -= 1
                if isinstance(got, int):
                    self.send_response(got)
                    self.end_headers()
                    return
                text, finish = got if isinstance(got, tuple) else (got, "stop")
                data = json.dumps({"choices": [{"message": {"content": text}, "finish_reason": finish}]}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.httpd.server_address[1]}"

    def __enter__(self):
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()
        return self

    def __exit__(self, *a):
        self.httpd.shutdown()
        self.httpd.server_close()


def modern(original):
    """A valid plain version: the words of the original with a marker word after every sixth (1.16 times as long; no run of eight words is the original's)."""
    out = []
    for i, w in enumerate(original.split(), 1):
        out.append(w)
        if i % 6 == 0:
            out.append("zq")
    return " ".join(out)


def scripted(original, temperature, n):
    """Plain versions by what the unit's text begins with: COPY is answered with the text itself, SHORT with too few words at the first temperature, LIST with a list,
    DEAD with HTTP 500, anything else with a good version."""
    kind = original.split()[0]
    if kind == "COPY":
        return original
    if kind == "SHORT":
        return modern(original) if temperature > 0.5 else "too short"
    if kind == "LIST":
        return "- " + modern(original)
    if kind == "DEAD":
        return 500
    return modern(original)


def unit_rows(kinds, work="t", words=160):
    """Units for a fake run: unit k begins with kinds[k] (a marker word) and has `words` words in all."""
    rows = []
    for k, kind in enumerate(kinds):
        original = " ".join([kind] + [f"u{k}w{j}" for j in range(words - 1)])
        rows.append({"id": f"{work}:{k}", "work": work, "ref": f"§{k}", "original": original, "split": "held" if k % 10 == 9 else "train"})
    return rows


class RunTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="hegelizer-run-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        for patch in (mock.patch.object(hz, "PATIENCE", 0),):
            patch.start()
            self.addCleanup(patch.stop)

    def units(self, kinds):
        rows = unit_rows(kinds)
        hz.write_rows(self.tmp / hz.UNITS, rows)
        return rows

    def run_it(self, srv, *extra):
        return cli("--paraphrase", "--url", srv.url, "--out", str(self.tmp), "--timeout", "20", *extra)

    def done(self):
        return hz.read_rows(self.tmp / hz.DONE)

    def test_a_unit_is_asked_with_the_prompt_the_temperature_and_the_tokens_of_the_spec(self):
        rows = self.units(["GOOD"] * 3)
        with Llama(scripted) as srv:
            code, said, _ = self.run_it(srv)
        self.assertEqual(code, 0, said)
        self.assertEqual(len(srv.calls), 3)
        for c in srv.calls:
            unit = next(u for u in rows if u["original"] == c["original"])
            body = c["body"]
            self.assertEqual(c["path"], "/v1/chat/completions")
            self.assertEqual([m["role"] for m in body["messages"]], ["system", "user"])
            self.assertEqual(body["messages"][0]["content"], hz.PARAPHRASE_SYSTEM)
            self.assertEqual(body["messages"][1]["content"], hz.PARAPHRASE_ASK.format(original=unit["original"]))
            self.assertEqual((body["temperature"], body["chat_template_kwargs"]), (0.3, {"enable_thinking": False}))
            self.assertEqual(body["max_tokens"], math.ceil(1.6 * 1.4 * 160))
        self.assertIn("3 units, 0 done, 0 failed, 3 to do with 1 worker(s)", said)

    def test_the_rows_hold_the_plain_version_beside_the_real_text(self):
        rows = self.units(["GOOD"] * 12)
        with Llama(scripted) as srv:
            self.run_it(srv)
        got = {r["id"]: r for r in self.done()}
        self.assertEqual(set(got), {u["id"] for u in rows})
        for u in rows:
            r = got[u["id"]]
            self.assertEqual(list(r), ["id", "work", "ref", "split", "plain", "original"])
            self.assertEqual((r["work"], r["ref"], r["split"], r["original"]), (u["work"], u["ref"], u["split"], u["original"]))
            self.assertEqual(r["plain"], modern(u["original"]))
        self.assertEqual({r["split"] for r in got.values()}, {"train", "held"})
        self.assertFalse((self.tmp / hz.FAILED).read_text() if (self.tmp / hz.FAILED).exists() else "")

    def test_the_units_come_in_a_fixed_shuffled_order(self):
        self.units(["GOOD"] * 20)
        with Llama(scripted) as srv:
            self.run_it(srv)
        order = [c["original"].split()[1] for c in srv.calls]
        self.assertNotEqual(order, sorted(order, key=lambda x: int(x[1:].split("w")[0])))
        shutil.rmtree(self.tmp)
        self.tmp.mkdir()
        self.units(["GOOD"] * 20)
        with Llama(scripted) as again:
            self.run_it(again)
        self.assertEqual(order, [c["original"].split()[1] for c in again.calls])

    def test_a_reply_that_cannot_stand_is_asked_again_at_a_higher_temperature(self):
        self.units(["SHORT", "LIST"])
        with Llama(scripted) as srv:
            self.run_it(srv)
        short = [c["temperature"] for c in srv.calls if c["original"].startswith("SHORT")]
        self.assertEqual(short, [0.3, 0.7])
        self.assertEqual([r["id"] for r in self.done()], ["t:0"])                  # SHORT came right the second time; LIST never does
        self.assertEqual([c["temperature"] for c in srv.calls if c["original"].startswith("LIST")], [0.3, 0.7])

    def test_a_unit_that_fails_twice_is_recorded_as_failed_with_the_reasons_and_not_asked_again_unless_told_to(self):
        rows = self.units(["GOOD", "COPY", "LIST"])
        with Llama(scripted) as srv:
            self.run_it(srv)
        failed = hz.read_rows(self.tmp / hz.FAILED)
        self.assertEqual(sorted(f["id"] for f in failed), ["t:1", "t:2"])
        by = {f["id"]: f for f in failed}
        self.assertIn("shares 8 words in a row with the original", by["t:1"]["reason"])
        self.assertIn("at 0.3", by["t:1"]["reason"])
        self.assertIn("at 0.7", by["t:1"]["reason"])
        self.assertIn("list marker", by["t:2"]["reason"])
        self.assertEqual(set(failed[0]), {"id", "work", "reason"})
        self.assertEqual([r["id"] for r in self.done()], ["t:0"])
        with Llama(scripted) as again:
            code, said, _ = self.run_it(again)
            self.assertEqual((code, again.calls), (0, []))                          # nothing to do: the failed ones are skipped
            self.assertIn("2 failed (skipped; --retry-failed tries them again)", said)
            self.run_it(again, "--retry-failed")
        self.assertEqual(len(again.calls), 4)                                       # the two failed ones, twice each
        self.assertEqual({c["original"].split()[0] for c in again.calls}, {"COPY", "LIST"})
        self.assertEqual(len(hz.read_rows(self.tmp / hz.FAILED)), 4)               # they failed again: recorded again, still failed
        self.assertEqual(len(rows), 3)

    def test_a_failed_unit_that_comes_right_on_a_retry_is_done_and_no_longer_failed(self):
        self.units(["GOOD", "FLAKY"])
        flaky = {"on": False}
        with Llama(lambda o, t, n: "tiny" if o.startswith("FLAKY") and not flaky["on"] else modern(o)) as srv:
            self.run_it(srv)
            self.assertEqual([r["id"] for r in self.done()], ["t:0"])
            flaky["on"] = True
            self.run_it(srv, "--retry-failed")
        self.assertEqual(sorted(r["id"] for r in self.done()), ["t:0", "t:1"])
        self.assertEqual(hz.failed_ids(hz.read_rows(self.tmp / hz.FAILED), {r["id"] for r in self.done()}), set())
        code, said, _ = cli("--stats", "--out", str(self.tmp))
        self.assertIn("failed 0", said)

    def test_a_run_carries_on_where_the_last_one_stopped(self):
        rows = self.units(["GOOD"] * 12)
        with Llama(scripted) as srv:
            self.run_it(srv, "--limit", "5")
            first = {r["id"] for r in self.done()}
            self.assertEqual(len(first), 5)
            self.assertEqual(len(srv.calls), 5)
            _, said, _ = self.run_it(srv)
        self.assertIn("12 units, 5 done, 0 failed, 7 to do", said)
        self.assertEqual(len(srv.calls), 12)                                        # not one unit twice
        self.assertEqual(len({c["original"] for c in srv.calls}), 12)
        self.assertEqual(sorted(r["id"] for r in self.done()), sorted(u["id"] for u in rows))

    def test_a_half_line_left_by_a_crash_is_cut_off_and_its_unit_done_again(self):
        rows = self.units(["GOOD"] * 4)
        good = [{"id": u["id"], "work": u["work"], "ref": u["ref"], "split": u["split"], "plain": modern(u["original"]), "original": u["original"]} for u in rows[:2]]
        half = json.dumps({**good[0], "id": rows[2]["id"], "original": rows[2]["original"]}, ensure_ascii=False)[:60]
        (self.tmp / hz.DONE).write_text("".join(json.dumps(r) + "\n" for r in good) + half, encoding="utf-8")
        with Llama(scripted) as srv:
            self.run_it(srv)
        raw = (self.tmp / hz.DONE).read_text(encoding="utf-8")
        self.assertTrue(raw.endswith("\n"))
        lines = [json.loads(x) for x in raw.splitlines()]                           # every line is whole
        self.assertEqual(sorted(r["id"] for r in lines), sorted(u["id"] for u in rows))
        self.assertEqual(len(srv.calls), 2)                                         # the half line's unit and the one that was never started

    def test_rows_that_are_not_the_units_are_refused_before_anything_is_asked(self):
        rows = self.units(["GOOD"] * 3)
        (self.tmp / hz.DONE).write_text(json.dumps({"id": "t:0", "work": "t", "ref": "x", "split": "train", "plain": "p", "original": "another text"}) + "\n", encoding="utf-8")
        with Llama(scripted) as srv:
            code, _, err = self.run_it(srv)
        self.assertEqual((code, srv.calls), (1, []))
        self.assertIn("do not match the units", err)
        self.assertEqual(len(rows), 3)

    def test_workers_ask_in_parallel_and_never_more_than_asked_for(self):
        self.units(["GOOD"] * 8)
        with Llama(scripted, delay=0.2) as srv:
            code, said, _ = self.run_it(srv, "--workers", "4")
        self.assertEqual(code, 0)
        self.assertIn("with 4 worker(s)", said)
        self.assertTrue(2 <= srv.peak <= 4, srv.peak)
        self.assertEqual(len(self.done()), 8)
        with Llama(scripted, delay=0.01) as one:
            shutil.rmtree(self.tmp)
            self.tmp.mkdir()
            self.units(["GOOD"] * 4)
            self.run_it(one)
        self.assertEqual(one.peak, 1)

    def test_a_progress_line_comes_every_25_units_with_the_time_to_go(self):
        self.units(["GOOD"] * 52)
        with Llama(scripted) as srv:
            _, said, _ = self.run_it(srv, "--workers", "2")
        lines = [x for x in said.splitlines() if re.match(r"^\d+/52 done, \d+ failed in this run; [\d.]+ s per unit; .+ to go$", x)]
        self.assertEqual(len(lines), 2, said)
        self.assertTrue(lines[0].startswith("25/52 done"))
        self.assertTrue(lines[1].startswith("50/52 done"))
        self.assertIn("52/52 done; this run: 52 written, 0 failed", said)

    def test_ctrl_c_stops_starting_units_finishes_those_in_flight_and_leaves_whole_lines(self):
        self.units(["GOOD"] * 8)
        real, seen = hz.wait, {"n": 0}

        def interrupted(pending, return_when):
            seen["n"] += 1
            if seen["n"] == 2:
                raise KeyboardInterrupt
            return real(pending, return_when=return_when)

        with Llama(scripted, delay=0.05) as srv, mock.patch.object(hz, "wait", interrupted):
            code, said, _ = self.run_it(srv, "--workers", "2")
        self.assertEqual(code, 130)
        self.assertIn("interrupted: not starting more", said)
        rows = self.done()
        self.assertTrue(1 <= len(rows) < 8, len(rows))
        self.assertEqual(len(srv.calls), len(rows))                                 # everything that was started was finished and written
        self.assertTrue((self.tmp / hz.DONE).read_text(encoding="utf-8").endswith("\n"))
        with Llama(scripted) as again:
            self.run_it(again)
        self.assertEqual(sorted(r["id"] for r in self.done()), sorted(f"t:{k}" for k in range(8)))
        self.assertEqual(len(again.calls), 8 - len(rows))

    def test_a_second_ctrl_c_drops_the_calls_in_flight_and_the_files_still_hold_whole_lines(self):
        self.units(["GOOD"] * 6)
        real, seen = hz.wait, {"n": 0}

        def interrupted(pending, return_when):
            seen["n"] += 1
            if seen["n"] in (2, 3):
                raise KeyboardInterrupt
            return real(pending, return_when=return_when)

        with Llama(scripted, delay=0.05) as srv, mock.patch.object(hz, "wait", interrupted):
            args = argparse.Namespace(url=srv.url, workers=2, limit=None, retry_failed=False, timeout=20)
            with self.assertRaises(KeyboardInterrupt), contextlib.redirect_stdout(io.StringIO()):
                hz.cmd_paraphrase(args, self.tmp)                                  # (main() answers this with a hard exit)
        text = (self.tmp / hz.DONE).read_text(encoding="utf-8") if (self.tmp / hz.DONE).exists() else ""
        self.assertTrue(text == "" or text.endswith("\n"))
        for line in text.splitlines():
            json.loads(line)

    def test_a_server_that_stops_answering_is_no_fault_of_the_unit(self):
        self.units(["GOOD", "DEAD", "GOOD", "GOOD"])
        with Llama(scripted) as srv:
            code, said, _ = self.run_it(srv)
        self.assertEqual(code, 1)
        self.assertIn("the server stopped answering", said)
        self.assertIn("Run the same command to carry on", said)
        self.assertNotIn("t:1", {r["id"] for r in self.done()})
        self.assertFalse((self.tmp / hz.FAILED).exists() and (self.tmp / hz.FAILED).read_text(encoding="utf-8").strip())
        self.assertEqual(sum(c["original"].startswith("DEAD") for c in srv.calls), hz.TRIES)        # tried, then given up
        with Llama(lambda o, t, n: modern(o)) as again:                              # the server is back
            code, _, _ = self.run_it(again)
        self.assertEqual((code, sorted(r["id"] for r in self.done())), (0, ["t:0", "t:1", "t:2", "t:3"]))

    def test_no_server_at_the_address_is_said_before_anything_is_written(self):
        self.units(["GOOD"] * 2)
        code, _, err = cli("--paraphrase", "--url", "http://127.0.0.1:9", "--out", str(self.tmp))
        self.assertEqual(code, 1)
        self.assertIn("no llama-server at http://127.0.0.1:9", err)
        self.assertEqual(self.done(), [])

    def test_without_units_it_says_to_build_them(self):
        with Llama(scripted) as srv:
            code, _, err = self.run_it(srv)
        self.assertEqual(code, 1)
        self.assertIn("run --build first", err)

    def test_a_reply_cut_off_at_the_token_limit_does_not_stand(self):
        self.units(["GOOD"])
        with Llama(lambda o, t, n: (modern(o), "length")) as srv:
            self.run_it(srv)
        self.assertEqual(self.done(), [])
        self.assertIn("cut off at max_tokens", hz.read_rows(self.tmp / hz.FAILED)[0]["reason"])


class StatsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="hegelizer-stats-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        patch = mock.patch.object(hz, "PATIENCE", 0)
        patch.start()
        self.addCleanup(patch.stop)

    def test_the_stats_count_units_by_split_and_work_and_show_the_gate_and_three_samples(self):
        rows = unit_rows(["GOOD"] * 18 + ["COPY", "LIST"], work="alpha") + [{**u, "work": "beta", "id": u["id"].replace("t:", "beta:")} for u in unit_rows(["GOOD"] * 10)]
        hz.write_rows(self.tmp / hz.UNITS, rows)
        with Llama(scripted) as srv:
            cli("--paraphrase", "--url", srv.url, "--out", str(self.tmp))
        code, said, _ = cli("--stats", "--out", str(self.tmp), "--seed", "3")
        self.assertEqual(code, 0)
        self.assertIn("units 30 (train 27, held 3); done 28 (train 26, held 2); failed 2 (train 1, held 1); to do 0", said)
        self.assertRegex(said, r"\n  alpha +20 +18 +2 +18 +2\n")
        self.assertRegex(said, r"\n  beta +10 +9 +1 +10 +0\n")
        self.assertIn("words of the plain version / the original: mean 1.16 (min 1.16, max 1.16) over 28 units", said)
        self.assertIn("gate (failed under 10% of the units, mean ratio 0.8 to 1.2): failed 6.7%, ratio 1.16: passes", said)
        self.assertEqual(said.count("\n  plain:"), 3)
        self.assertIn("failures:", said)
        self.assertRegex(said, r"alpha:18: at 0\.3: shares 8 words")
        for block in said.split("\n[")[1:]:
            self.assertRegex(block, r"^(alpha|beta):\d+\]")
            unit = next(u for u in rows if u["id"] == block.split("]")[0])
            self.assertEqual(unit["split"], "train")                                 # samples are of the training data
        self.assertEqual(said, cli("--stats", "--out", str(self.tmp), "--seed", "3")[1])
        self.assertNotEqual(said, cli("--stats", "--out", str(self.tmp), "--seed", "4")[1])

    def test_the_gate_stops_when_too_many_failed_or_the_ratio_is_off(self):
        hz.write_rows(self.tmp / hz.UNITS, unit_rows(["GOOD"] * 6 + ["COPY"] * 2))
        with Llama(scripted) as srv:
            cli("--paraphrase", "--url", srv.url, "--out", str(self.tmp))
        self.assertIn("failed 25.0%, ratio 1.16: STOP, report", cli("--stats", "--out", str(self.tmp))[1])
        shutil.rmtree(self.tmp)
        self.tmp.mkdir()
        hz.write_rows(self.tmp / hz.UNITS, unit_rows(["GOOD"] * 6))
        with Llama(lambda o, t, n: " ".join(modern(o).split()[:100])) as srv:                 # 0.62 times: valid, but short of the gate's 0.8
            cli("--paraphrase", "--url", srv.url, "--out", str(self.tmp))
        self.assertIn("ratio 0.62: STOP, report", cli("--stats", "--out", str(self.tmp))[1])

    def test_stats_without_units_say_to_build_them(self):
        code, _, err = cli("--stats", "--out", str(self.tmp))
        self.assertEqual(code, 1)
        self.assertIn("run --build first", err)


class CommandLineTest(unittest.TestCase):
    def test_it_wants_to_be_told_what_to_do(self):
        for argv in ([], ["--paraphrase"], ["--paraphrase", "--url", "http://x", "--workers", "0"]):
            with self.assertRaises(SystemExit), contextlib.redirect_stderr(io.StringIO()):
                hz.main(argv)

    def test_the_constants_the_runbook_names_are_module_level(self):
        for name in ("PARAPHRASE_SYSTEM", "PARAPHRASE_ASK", "UNIT_WORDS", "HELD_SHARE", "SPLIT_SEED", "RATIO", "RUN", "TEMPERATURE", "RETRY_TEMPERATURE", "TOKENS_PER_WORD",
                     "PROGRESS_EVERY", "GATE_FAILED", "GATE_RATIO", "MARKUP"):
            self.assertTrue(hasattr(hz, name), name)

    def test_the_file_is_standard_library_only(self):
        source = (REPO / "tools/hegelizer.py").read_text(encoding="utf-8")
        modules = set(re.findall(r"^(?:import|from) (\w+)", source, re.M)) | set(re.findall(r"^\s+import (\w+)", source, re.M))
        self.assertLessEqual(modules, {"argparse", "json", "math", "os", "random", "re", "statistics", "sys", "time", "urllib", "concurrent", "pathlib", "world", "collections",
                                       "train_data"})


if __name__ == "__main__":
    unittest.main()
