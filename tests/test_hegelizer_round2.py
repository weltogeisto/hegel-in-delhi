import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import urllib.error

from tools import hegelizer as hg
from tools import hegelizer_round2 as r2
from tools.recorded_llama import RecordedClient, LatencyGuard, TransportError, UnknownRequest, freeze_plan, json_bytes


def original():
    return " ".join("old" + str(i) for i in range(80)) + "."


def version(tag="fresh"):
    return " ".join(["old" + str(i) for i in reversed(range(30))] + [tag + str(i) for i in range(50)]) + "."


def unit(i=0, split="train"):
    return {"id": "work:" + str(i), "parent_id": "work:" + str(i), "work": "work", "ref": str(i),
            "original": original(), "split": split, "kind": "full", "recipe": 4}


def result(i=0, accepted=True):
    return dict(unit(i), recipe=4, accepted=accepted, versions=[
        {"variant": 1, "plain": version("first") if accepted else None},
        {"variant": 2, "plain": version("second") if accepted else None}])


class DiversityTest(unittest.TestCase):
    def test_occurrences_count_and_overlap_is_symmetric_f1(self):
        self.assertEqual(r2.unigram_overlap("a a b b", "a b c c"), 0.5)
        self.assertEqual(r2.unigram_overlap("a b c c", "a a b b"), 0.5)

    def test_shared_order_unchanged_and_reversed(self):
        self.assertEqual(r2.kendall_tau("a b c d", "a b c d"), 1)
        self.assertEqual(r2.kendall_tau("a b c d", "d c b a"), -1)
        self.assertEqual(r2.kendall_tau("a b", "x a"), 0)

    def test_repeated_words_match_once_per_occurrence(self):
        self.assertAlmostEqual(r2.kendall_tau("a a b", "b a a"), -1 / 3)
        self.assertLessEqual(r2.kendall_tau("a b", "a a a b b"), 1)

    def test_filters_are_independent_and_boundaries_inclusive(self):
        self.assertIn("word overlap above 0.60", r2.diversity("a b c d", "d c b a")["problems"])
        kept = r2.diversity("a b c d e f g h i j", "a b c d k l m n o p")                     # order kept, half the words new
        self.assertEqual((kept["kendall_tau"], kept["problems"]), (1.0, []))              # tau is recorded, not a reason to ask again
        self.assertEqual(r2.diversity(original(), version())["problems"], [])

    def test_exact_overlap_and_tau_boundaries_pass(self):
        self.assertEqual(r2.diversity("a b c d e", "c b a x y")["problems"], [])
        source = "a b c d e f g h i j k l m n"
        plain = "d c b a f e g h u v w x y z"
        self.assertEqual(r2.kendall_tau(source, plain), 0.5)
        self.assertEqual(r2.diversity(source, plain)["problems"], [])

    def test_known_scan_misreadings_are_rejected_without_rewriting(self):
        for text in ["A behef is held.", "The imiversal is here.", "The universahty is plain."]:
            self.assertTrue(hg.damaged(text, {}), text)
        self.assertFalse(hg.damaged("A belief in universal universality.", {}))


class CorpusTest(unittest.TestCase):
    def test_short_pieces_are_one_to_three_intact_sentences(self):
        sentences = [(" ".join("word" + str(i) for i in range(20)) + ".").capitalize() for _ in range(7)]
        text = " ".join(sentences)
        pieces = r2.short_pieces(text)
        self.assertTrue(pieces)
        for piece in pieces:
            self.assertIn(piece, text)
            self.assertTrue(40 <= len(piece.split()) <= 120)
            self.assertTrue(1 <= len(hg.shelf.sentences(piece)) <= 3)

    def test_long_sentence_is_not_cut_to_force_a_short_piece(self):
        self.assertEqual(r2.short_pieces(" ".join(["word"] * 121) + "."), [])

    def test_a_third_of_full_units_supply_children_with_same_split(self):
        sentence = " ".join("word" + str(i) for i in range(40)) + "."
        full = [dict(unit(i, "held" if i == 2 else "train"), original=" ".join([sentence] * 3)) for i in range(6)]
        for u in full:
            for key in ["parent_id", "kind", "recipe"]:
                u.pop(key)
        with mock.patch.object(hg, "build_units", return_value=(full, {})):
            made, report = r2.build_units(object())
            made2, _ = r2.build_units(object())
        self.assertEqual(made, made2)
        self.assertEqual(report["selected_short_source_units"], 2)
        parents = {u["id"]: u for u in made if u["kind"] == "full"}
        for u in made:
            self.assertEqual(u["split"], parents[u["parent_id"]]["split"])
            self.assertIn(u["original"], parents[u["parent_id"]]["original"])

    def test_round_two_build_cli_preserves_pilot_files_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as td:
            folder = Path(td)
            for name in [hg.UNITS, hg.DONE, hg.FAILED]:
                (folder / name).write_bytes(b"pilot-original\n")
            with mock.patch.object(hg.shelf, "load", return_value=object()), mock.patch.object(r2, "build_units", return_value=([unit()], {})), mock.patch("sys.stdout", new=io.StringIO()):
                self.assertEqual(hg.main(["--round-two", "--build", "--out", td]), 0)
                frozen = (folder / r2.UNITS).read_bytes()
                with self.assertRaises(FileExistsError):
                    hg.main(["--round-two", "--build", "--out", td])
            self.assertEqual((folder / r2.UNITS).read_bytes(), frozen)
            for name in [hg.UNITS, hg.DONE, hg.FAILED]:
                self.assertEqual((folder / name).read_bytes(), b"pilot-original\n")

    def test_pilot_and_round_two_filenames_are_disjoint(self):
        self.assertTrue({r2.UNITS, r2.DONE, r2.FAILED}.isdisjoint({hg.UNITS, hg.DONE, hg.FAILED}))


class GenerationPlanTest(unittest.TestCase):
    def test_plan_freezes_source_timeout_and_never_opens_pilot_outputs(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / r2.UNITS).write_bytes(json_bytes(unit()))
            for name in (hg.DONE, hg.FAILED):
                (root / name).write_bytes(b"original pilot bytes")
            with mock.patch.object(r2, "generate_units", return_value=iter([result()])), mock.patch("sys.stdout", new=io.StringIO()):
                self.assertEqual(r2.main(["--paraphrase", "--out", td, "--url", "http://cpu-fixture.invalid", "--latency-observation", str(root / "observation"), "--latency-limit", "8"]), 0)
            plan = json.loads((root / "hegelizer2-generation-plan.json").read_text())
            self.assertEqual(plan["timeout"], 300)
            self.assertEqual(len(plan["source_sha256"]), 3)
            self.assertEqual((root / hg.DONE).read_bytes(), b"original pilot bytes")
            self.assertEqual((root / hg.FAILED).read_bytes(), b"original pilot bytes")

    def test_nonfinite_timeout_or_latency_stops_before_any_request(self):
        for extra in [["--timeout", "nan"], ["--latency-limit", "inf"]]:
            with mock.patch("sys.stderr", new=io.StringIO()), self.assertRaises(SystemExit):
                r2.main(["--paraphrase", "--out", "unused", "--url", "http://unused.invalid", "--latency-observation", "unused", "--latency-limit", "8", *extra])


class GenerationTest(unittest.TestCase):
    class Client:
        before_request = None

        def __init__(self, replies):
            self.replies, self.calls = iter(replies), []

        def chat(self, rid, messages, temperature, tokens, seed):
            self.calls.append((rid, temperature, seed))
            return next(self.replies), "stop"

    def test_two_distinct_versions_have_distinct_seed_and_temperature(self):
        client = self.Client([version("first"), version("second")])
        got = r2.paraphrase_unit(unit(), client)
        self.assertTrue(got["accepted"])
        self.assertEqual(len(client.calls), 2)
        self.assertNotEqual(client.calls[0][1:], client.calls[1][1:])

    def test_copying_is_retried_and_every_canonical_attempt_is_kept(self):
        client = self.Client([original(), version("first"), version("second")])
        got = r2.paraphrase_unit(unit(), client)
        self.assertTrue(got["accepted"])
        self.assertEqual(len(got["versions"][0]["attempts"]), 2)
        self.assertIn("shares", got["versions"][0]["attempts"][0]["reason"])

    def test_duplicate_second_version_uses_only_unused_retry(self):
        client = self.Client([version("first"), version("first"), version("second")])
        got = r2.paraphrase_unit(unit(), client)
        self.assertTrue(got["accepted"])
        self.assertIn("duplicates", got["versions"][1]["attempts"][0]["reason"])

    def test_bounded_workers_stop_submitting_after_a_transport_failure(self):
        client = self.Client([])
        with mock.patch.object(r2, "paraphrase_unit", side_effect=TransportError("offline")) as ask:
            with self.assertRaises(TransportError):
                list(r2.generate_units([unit(i) for i in range(100)], client, 2, 1831))
        self.assertLessEqual(ask.call_count, 2)

    def test_failed_unit_keeps_both_versions_and_all_six_attempts(self):
        client = self.Client([original()] * 6)
        got = r2.paraphrase_unit(unit(), client)
        self.assertFalse(got["accepted"])
        self.assertEqual([len(v["attempts"]) for v in got["versions"]], [3, 3])

    def test_transport_failure_stops_without_fabricating_a_failed_unit(self):
        client = self.Client([])
        with mock.patch.object(client, "chat", side_effect=TransportError("offline")):
            with self.assertRaises(TransportError):
                r2.paraphrase_unit(unit(), client)

    def test_seed_is_reproducible_and_retries_and_variants_differ(self):
        seeds = [r2.request_seed("unit", v, a) for v in range(2) for a in range(3)]
        self.assertEqual(len(set(seeds)), 6)
        self.assertEqual(seeds[0], r2.request_seed("unit", 0, 0))


class GateTest(unittest.TestCase):
    def test_pending_units_cannot_pass(self):
        got = r2.gate([unit(0), unit(1)], [result(0)], [])
        self.assertFalse(got["passed"])
        self.assertEqual(got["pending_units"], 1)

    def test_strict_ten_percent_is_by_units_not_individual_versions(self):
        got = r2.gate([unit(i) for i in range(10)], [result(i) for i in range(9)], [result(9, False)])
        self.assertFalse(got["passed"])
        got = r2.gate([unit(i) for i in range(11)], [result(i) for i in range(10)], [result(10, False)])
        self.assertTrue(got["passed"])
        self.assertEqual(got["accepted_pairs"], 20)

    def test_duplicate_unknown_or_edited_rows_fail(self):
        for rows in [[result(0), result(0)], [result(99)], [dict(result(), original="edited")]]:
            with self.assertRaises(ValueError):
                r2.validate_results([unit()], rows)

    def test_accepted_row_cannot_have_a_missing_version(self):
        row = result()
        row["versions"][1]["plain"] = None
        with self.assertRaises(ValueError):
            r2.validate_results([unit()], [row])

    def test_partial_line_is_preserved_and_never_trimmed(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "rows"
            p.write_bytes(b'{"id":"partial"')
            with self.assertRaises(ValueError):
                r2.strict_rows(p)
            self.assertEqual(p.read_bytes(), b'{"id":"partial"')


class RecordedTransportTest(unittest.TestCase):
    class Response:
        status = 200

        def __init__(self, content="answer"):
            self.raw = json_bytes({"choices": [{"message": {"content": content}, "finish_reason": "stop"}]})

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def read(self):
            return self.raw

    def test_completed_response_replays_without_model_call_and_checks_payload(self):
        with tempfile.TemporaryDirectory() as td:
            opener = mock.Mock(return_value=self.Response())
            client = RecordedClient("http://unused", td, opener=opener, lora=[{"id": 0, "scale": 0.8}])
            args = ("case", [{"role": "user", "content": "plain"}], 0.9, 100, 1831)
            self.assertEqual(client.chat(*args), ("answer", "stop"))
            self.assertEqual(client.chat(*args), ("answer", "stop"))
            self.assertEqual(opener.call_count, 1)
            payload = json.loads(opener.call_args.args[0].data)
            self.assertEqual((payload["id_slot"], payload["lora"][0]["scale"]), (1, 0.8))
            with self.assertRaises(ValueError):
                client.chat(*args[:-1], 1832)

    def test_begin_without_end_is_unknown_and_never_resent(self):
        with tempfile.TemporaryDirectory() as td:
            opener = mock.Mock(side_effect=KeyboardInterrupt)
            client = RecordedClient("http://unused", td, opener=opener)
            with self.assertRaises(KeyboardInterrupt):
                client.post("case", {"messages": []})
            with self.assertRaises(UnknownRequest):
                client.post("case", {"messages": []})
            self.assertEqual(opener.call_count, 1)

    def test_transport_error_is_recorded_and_not_silently_retried(self):
        with tempfile.TemporaryDirectory() as td:
            opener = mock.Mock(side_effect=urllib.error.URLError("offline"))
            client = RecordedClient("http://unused", td, opener=opener)
            for _ in range(2):
                with self.assertRaises(TransportError):
                    client.post("case", {"messages": []})
            self.assertEqual(opener.call_count, 1)

    def test_changed_cached_response_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            client = RecordedClient("http://unused", td, opener=mock.Mock(return_value=self.Response()))
            client.post("case", {})
            Path(str(client.stem("case")) + ".response.bin").write_bytes(b"edited")
            with self.assertRaises(ValueError):
                client.post("case", {})

    def test_slot_zero_is_never_available_to_the_tool(self):
        with self.assertRaises(ValueError):
            RecordedClient("http://unused", ".", slot=0)

    def test_frozen_plan_cannot_be_retuned(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "plan.json"
            freeze_plan(p, {"seed": 1})
            freeze_plan(p, {"seed": 1})
            with self.assertRaises(ValueError):
                freeze_plan(p, {"seed": 2})


class LatencyTest(unittest.TestCase):
    def test_stale_slower_missing_and_changed_limit_stop_new_work(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "observation"
            guard = LatencyGuard(p, clock=lambda: 1000, limit=10)
            for row in [None, {"observed_unix": 600, "latency_s": 9, "limit_s": 10},
                        {"observed_unix": 999, "latency_s": 11, "limit_s": 10},
                        {"observed_unix": 999, "latency_s": 9, "limit_s": 12}]:
                if row is not None:
                    p.write_text(json.dumps(row))
                with self.assertRaises(TransportError):
                    guard()
            p.write_text(json.dumps({"observed_unix": 999, "latency_s": 9, "limit_s": 10}))
            self.assertEqual(guard()["latency_s"], 9)


if __name__ == "__main__":
    unittest.main()


class BoundedBacklogTest(unittest.TestCase):
    """Two workers: finished units that wait behind a slower earlier one hold their place, so no more than two are ever started ahead."""

    def test_no_new_unit_starts_while_finished_ones_wait_behind_a_slow_one(self):
        import threading
        import time as _time
        started, lock = [], threading.Lock()
        first_may_finish = threading.Event()

        def fake(unit, client, seed):
            with lock:
                started.append(unit["id"])
            if unit["id"] == "u0":
                first_may_finish.wait(5)
            return {"id": unit["id"], "accepted": True}

        units = [{"id": f"u{i}"} for i in range(6)]
        original = r2.paraphrase_unit
        r2.paraphrase_unit = fake
        self.addCleanup(setattr, r2, "paraphrase_unit", original)

        class Client:
            before_request = None

        out, rows = [], r2.generate_units(units, Client(), 2, 1)
        reader = threading.Thread(target=lambda: out.extend(rows))
        reader.start()
        _time.sleep(0.3)
        with lock:
            ahead = list(started)
        first_may_finish.set()
        reader.join(5)
        self.assertEqual(ahead, ["u0", "u1"])                          # u1 finished, but waits behind u0: nothing more starts
        self.assertEqual([r["id"] for r in out], [u["id"] for u in units])
