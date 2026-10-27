"""CPU fixtures only: no real endpoint, model, rater, or live-world action."""
import contextlib
import copy
import io
import json
from pathlib import Path
import re
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

from tools import hegel_test as old
from tools import hegel_test_round2 as r2
from tools.recorded_llama import RecordedClient, TransportError, UnknownRequest, json_bytes
from world import restyle


CAST = {"cast": {"ramesh": {"name": "Ramesh"}, "kapoor": {"name": "Mrs. Kapoor"},
                  "bookseller": {"name": "the bookseller"}}}
COPY = "one two three four five six seven eight nine ten eleven twelve thirteen fourteen"


def thought(i=0, count=40):
    return " ".join("word" + str(j) for j in range(count - 1)) + " thought" + str(i)


def days():
    return [{"n": 1, "state": {"people": ["ramesh"]}}] + [
        {"n": n, "steps": [{"decision": {"thought": thought(i)}} for i in range(40)] if n == 12 else []}
        for n in r2.DAYS]


def prepared(root):
    raw = root / "days"
    raw.mkdir()
    for day in days():
        (raw / (str(day["n"]) + ".json")).write_bytes(json_bytes(day))
    cast = root / "cast.json"
    cast.write_bytes(json_bytes(CAST))
    shelf = root / "shelf-fixture.bin"
    shelf.write_bytes(b"shelf fixture, never a model")
    out = root / "job"
    plan = r2.prepare(raw, cast, out, shelf_path=shelf)
    return out, plan


def rewritten(text="a different sentence", seconds=1.0):
    return {"text": text, "seconds": seconds, "fallback": False,
            "attempts": [{"copied": [], "raw": text}]}


def result(plan, arm="adapter", profile="fixture"):
    return {"arm": arm, "profile": profile, "cohort_sha256": plan["cohort_sha256"],
            "key_commitment": plan["key_commitment"],
            "voice": [{"id": row["id"], "plain": row["plain"], "restyle": rewritten(arm + " " + row["plain"]),
                       "meaning": {"everything": True, "nothing_added": True, "format_valid": True}, "copied12": False}
                      for row in plan["cohort"]],
            "behaviour": [{"id": c["id"], "valid": True, "refused": False, "leaks": [],
                           "restyle": rewritten(), "restyle_applied": True} for c in plan["cases"]]}


def choices(plan, count=14, judge="welt"):
    return {"judge": judge, "cohort_sha256": plan["cohort_sha256"], "key_commitment": plan["key_commitment"],
            "choices": {identity: plan["key"][identity]["adapter"] if i < count else "tie"
                        for i, identity in enumerate(plan["assigned"][judge])}}


class GuardTest(unittest.TestCase):
    def test_exact_twelve_boundary_and_typography(self):
        guard = restyle.ShelfGuard([COPY])
        self.assertFalse(guard.matches(" ".join(COPY.split()[:11])))
        self.assertTrue(guard.matches(", ".join(COPY.upper().split()[:12])))
        self.assertEqual(guard.matches(COPY), [COPY])

    def test_all_works_and_languages_are_included(self):
        greek = "ένα δύο τρία τέσσερα πέντε έξι επτά οκτώ εννέα δέκα έντεκα δώδεκα"
        books = SimpleNamespace(works=[{"start": 0, "n": 2}, {"start": 2, "n": 1}],
                                data={"texts": [" ".join(COPY.split()[:7]), " ".join(COPY.split()[7:]), greek]})
        guard = restyle.ShelfGuard.from_shelf(books)
        self.assertTrue(guard.matches(COPY))
        self.assertTrue(guard.matches(greek.upper()))

    def test_passages_join_within_book_but_not_across_books(self):
        guard = restyle.ShelfGuard([" ".join(COPY.split()[:7]), " ".join(COPY.split()[7:])])
        self.assertFalse(guard.matches(COPY))

    def test_hash_collision_cannot_report_a_copy(self):
        guard = restyle.ShelfGuard([COPY])
        other = " ".join("other" + str(i) for i in range(12))
        guard.hashes.add(guard._hash(restyle.folded_words(other)))
        self.assertFalse(guard.matches(other))

    def test_missing_shelf_does_not_disable_guard(self):
        for texts in [[], [""]]:
            with self.assertRaises(ValueError):
                restyle.ShelfGuard(texts)

    def test_original_prompt_is_preserved_and_copy_retried_once(self):
        asks = []
        def fetch(messages, attempt):
            asks.append(copy.deepcopy(messages))
            return {"text": COPY if attempt == 0 else "an independently stated thought", "finish_reason": "stop", "seconds": 2}
        got = restyle.guarded_restyle("plain original", fetch, restyle.ShelfGuard([COPY]))
        self.assertFalse(got["fallback"])
        self.assertEqual(len(asks), 2)
        self.assertEqual(asks[0], restyle.messages("plain original"))
        self.assertIn(COPY, asks[1][-1]["content"])
        self.assertEqual([a["reason"] for a in got["attempts"]], ["copied", None])
        self.assertGreaterEqual(got["seconds"], 4)

    def test_second_copy_or_cutoff_uses_exact_plain(self):
        for reply in [{"text": COPY, "finish_reason": "stop"}, {"text": "short", "finish_reason": "length"}, {"text": "", "finish_reason": "stop"}]:
            fetch = mock.Mock(return_value=dict(reply, seconds=1))
            plain = "  plain text stays exactly as supplied\n"
            got = restyle.guarded_restyle(plain, fetch, restyle.ShelfGuard([COPY]))
            self.assertTrue(got["fallback"])
            self.assertEqual(got["text"], plain)
            self.assertEqual(fetch.call_count, 2)

    def test_recorded_wall_time_survives_fast_cached_transport(self):
        got = restyle.guarded_restyle("plain", lambda *a: {"text": "fresh wording", "seconds": 8.5}, restyle.ShelfGuard([COPY]))
        self.assertGreaterEqual(got["seconds"], 8.5)

    def test_unknown_transport_is_not_retried_and_bad_timing_stops(self):
        fetch = mock.Mock(side_effect=UnknownRequest("fixture unknown"))
        with self.assertRaises(UnknownRequest):
            restyle.guarded_restyle("plain", fetch, restyle.ShelfGuard([COPY]))
        self.assertEqual(fetch.call_count, 1)
        with self.assertRaises(ValueError):
            restyle.guarded_restyle("plain", lambda *a: {"text": "fresh", "seconds": float("nan")}, restyle.ShelfGuard([COPY]))


class CohortTest(unittest.TestCase):
    def test_first_forty_in_fixed_day_order_not_input_file_order(self):
        raw = days()
        raw[1]["steps"] = raw[1]["steps"][:30]
        raw[2]["steps"] = [{"decision": {"thought": thought(100 + i)}} for i in range(20)]
        got, meta = r2.select_thoughts(list(reversed(raw)), CAST)
        self.assertEqual([r["day"] for r in got], [12] * 30 + [24] * 10)
        self.assertEqual(got[-1]["plain"], thought(109))

    def test_excludes_later_person_short_null_and_resume_but_keeps_day_one_person(self):
        raw = days()
        prefix = [{"resumed": True}, {"decision": {"thought": None}}, {"decision": {"thought": thought(0, 39)}},
                  {"decision": {"thought": "Mrs. Kapoor " + thought()}},
                  {"decision": {"thought": "Ramesh " + thought()}}]
        raw[1]["steps"] = prefix + raw[1]["steps"]
        got, meta = r2.select_thoughts(raw, CAST)
        self.assertEqual(got[0]["id"], "12:4")
        self.assertEqual([e["reason"] for e in meta["excluded"]], ["under40words", "person met after Day1"])
        self.assertNotIn("bookseller", r2.later_names(raw[0], CAST))

    def test_not_enough_missing_duplicate_or_stand_in_data_stops(self):
        raw = days()
        for bad in [raw[:-1], raw + [raw[1]], raw[:1] + [dict(raw[1], steps=raw[1]["steps"][:39])] + raw[2:]]:
            with self.assertRaises(ValueError):
                r2.select_thoughts(bad, CAST)
        raw[1]["steps"][0]["mind"] = {"source": "stub"}
        with self.assertRaisesRegex(ValueError, "stand-in"):
            r2.select_thoughts(raw, CAST)

    def test_key_is_frozen_before_generation_and_reprepare_cannot_reshuffle(self):
        with tempfile.TemporaryDirectory() as td:
            out, plan = prepared(Path(td))
            self.assertEqual(r2.load_plan(out)["key"], plan["key"])
            self.assertEqual(len(plan["key"]), 40)
            before = (out / "private/plan.json").read_bytes()
            with self.assertRaises(FileExistsError):
                r2.prepare(Path(td) / "days", Path(td) / "cast.json", out)
            self.assertEqual((out / "private/plan.json").read_bytes(), before)
            self.assertFalse((out / "private/selected").exists())

    def test_duplicate_pair_or_overlapping_judges_cannot_load(self):
        with tempfile.TemporaryDirectory() as td:
            out, plan = prepared(Path(td))
            plan["assigned"]["claude"][0] = plan["assigned"]["welt"][0]
            (out / "private/plan.json").write_bytes(json_bytes(plan))
            with self.assertRaises(ValueError):
                r2.load_plan(out)


class JudgeAndSheetsTest(unittest.TestCase):
    def test_meaning_is_plain_qwen_and_exact_booleans_without_retries(self):
        client = SimpleNamespace(model="qwen", lora=None, chat=mock.Mock(return_value=('{"everything":true,"nothing_added":true}', "stop")))
        self.assertTrue(r2.meaning_check(client, "before", "after", "m1", 1831)["format_valid"])
        call = client.chat.call_args.args
        self.assertEqual(call[2:], (0.0, 120, 1831))
        for reply in ['{"everything":"yes","nothing_added":true}', '{"everything":true}', '{"everything":true,"nothing_added":true,"extra":1}', "not JSON"]:
            client.chat.return_value = (reply, "stop")
            got = r2.meaning_check(client, "before", "after", "m2", 1831)
            self.assertFalse(got["format_valid"])
            self.assertFalse(got["everything"])
        client.model = "claude"
        with self.assertRaises(ValueError):
            r2.meaning_check(client, "before", "after", "m3", 1831)
        client.model, client.lora = "qwen", [{"id": 0, "scale": 0.8}]
        with self.assertRaises(ValueError):
            r2.meaning_check(client, "before", "after", "m4", 1831)

    def test_option_only_sheets_have_disjoint_twenty_and_correct_frozen_orders(self):
        with tempfile.TemporaryDirectory() as td:
            out, plan = prepared(Path(td))
            control, adapter = result(plan, "control"), result(plan)
            sheets = [r2.public_sheet(plan, control, adapter, j) for j in ("welt", "claude")]
            self.assertFalse({q["id"] for q in sheets[0]["questions"]} & {q["id"] for q in sheets[1]["questions"]})
            self.assertEqual([len(s["questions"]) for s in sheets], [20, 20])
            for sheet in sheets:
                self.assertEqual(set(sheet), {"judge", "questions", "cohort_sha256", "key_commitment"})
                for q in sheet["questions"]:
                    self.assertEqual(set(q), {"id", "plain", "options"})
                    self.assertEqual(list(q["options"]), ["A", "B"])
                    self.assertTrue(q["options"][plan["key"][q["id"]]["adapter"]].startswith("adapter "))
            paths = r2.export_sheets(out, control, adapter, Path(td) / "handouts")
            self.assertEqual(len(paths), 4)
            page = (Path(td) / "handouts/welt-pairs.html").read_text()
            self.assertNotIn('"source_id"', page)
            self.assertNotIn('"arm"', page)
            self.assertNotIn("Show key", page)
            self.assertIn("Export choices", page)
            self.assertNotIn("checked=", page)

    def test_swapped_roles_duplicated_input_and_another_profile_export_stop(self):
        with tempfile.TemporaryDirectory() as td:
            out, plan = prepared(Path(td))
            control, adapter = result(plan, "control"), result(plan)
            with self.assertRaises(ValueError):
                r2.public_sheet(plan, adapter, control, "welt")
            bad = copy.deepcopy(adapter)
            bad["voice"][0] = bad["voice"][1]
            with self.assertRaises(ValueError):
                r2.public_sheet(plan, control, bad, "welt")
            r2.export_sheets(out, control, adapter, Path(td) / "sheets")
            adapter["profile"] = "different-scale"
            with self.assertRaises(ValueError):
                r2.export_sheets(out, control, adapter, Path(td) / "other-sheets")

    def test_preference_bar_needs_twenty_each_and_twelve_each(self):
        with tempfile.TemporaryDirectory() as td:
            _, plan = prepared(Path(td))
            js = {j: choices(plan, 14, j) for j in ("welt", "claude")}
            self.assertTrue(r2.preference_score(plan, js)["passed"])
            js = {"welt": choices(plan, 20), "claude": choices(plan, 11, "claude")}
            self.assertFalse(r2.preference_score(plan, js)["passed"])
            js["claude"] = choices(plan, 12, "claude")
            js["claude"]["choices"].pop(next(iter(js["claude"]["choices"])))
            with self.assertRaises(ValueError):
                r2.preference_score(plan, js)

    def test_labeled_meaning_review_requires_actual_choices_in_actual_git_commit(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            out, plan = prepared(root)
            adapter = result(plan)
            with self.assertRaises(ValueError):
                r2.meaning_review(out, adapter, "not-a-commit")
            inputs = {}
            for j in ("welt", "claude"):
                inputs[j] = root / (j + ".json")
                inputs[j].write_bytes(json_bytes(choices(plan, 14, j)))
            r2.freeze_judgments(out, inputs)
            git = root / "fixture-repo"
            git.mkdir()
            subprocess.run(["git", "init", "-q", str(git)], check=True)
            for j in inputs:
                (git / (j + ".json")).write_bytes(inputs[j].read_bytes())
            subprocess.run(["git", "add", "."], cwd=git, check=True)
            subprocess.run(["git", "-c", "user.name=CPU fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", "synthetic choices only"], cwd=git, check=True)
            commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=git, text=True).strip()
            with mock.patch.object(r2, "REPO", git):
                self.assertEqual([r["id"] for r in r2.meaning_review(out, adapter, commit)], plan["meaning_review_ids"])
            inputs["welt"].write_bytes(json_bytes(choices(plan, 15)))
            with self.assertRaises(ValueError):
                r2.freeze_judgments(out, inputs)


class MetricsTest(unittest.TestCase):
    def test_boundaries_and_human_steps_still_pending(self):
        with tempfile.TemporaryDirectory() as td:
            _, plan = prepared(Path(td))
            row = result(plan)
            for voice in row["voice"][:4]:
                voice["meaning"]["everything"] = False
            row["voice"][0]["copied12"] = True
            row["behaviour"][0]["restyle"]["seconds"] = 8
            got = r2.automatic_metrics(row, lambda text: 0.38)
            self.assertTrue(got["automatic_passed"])
            self.assertFalse(got["all_five_KPIs_passed"])
            self.assertEqual(got["meaning_both_yes"], 36)
            self.assertEqual(got["Welt_meaning_spotcheck10"], "pending")
            row["voice"][4]["meaning"]["nothing_added"] = False
            row["voice"][1]["copied12"] = True
            row["behaviour"][0]["restyle"]["seconds"] = 8.01
            got = r2.automatic_metrics(row, lambda text: 0.38001)
            self.assertFalse(any(got["automatic_tests"].values()))

    def test_missing_duplicate_nonfinite_invalid_and_leaking_cases_do_not_pass(self):
        with tempfile.TemporaryDirectory() as td:
            _, plan = prepared(Path(td))
            for value in [None, float("nan"), float("inf")]:
                with self.assertRaises(ValueError):
                    r2.automatic_metrics(result(plan), lambda text: value)
            row = result(plan)
            row["voice"][0] = row["voice"][1]
            with self.assertRaises(ValueError):
                r2.automatic_metrics(row, lambda text: 0.34)
            row = result(plan)
            row["behaviour"][0].update(valid=False, leaks=["fixture leak"])
            self.assertFalse(r2.automatic_metrics(row, lambda text: 0.34)["automatic_tests"]["world_fit"])
            row = result(plan)
            row["behaviour"][0]["restyle"] = None
            self.assertFalse(r2.automatic_metrics(row, lambda text: 0.34)["automatic_tests"]["world_fit"])

    def test_diagnostic_excludes_runs_already_in_plain_input(self):
        self.assertFalse(old.recall_beyond_input(COPY, COPY, COPY))
        self.assertTrue(old.recall_beyond_input(COPY, COPY, "a wholly different input"))
        self.assertFalse(old.recall_beyond_input("no recall", COPY, "plain"))


class ReconstructionDiagnosticTest(unittest.TestCase):
    def test_only_saved_outputs_and_beyond_input_runs_count_without_a_gate(self):
        rows = [{"id": "saved-a", "original": COPY, "plain": COPY, "answers": [COPY, ""]},
                {"id": "saved-b", "original": COPY, "plain": "new input", "answers": [COPY, "independent"]}]
        got = r2.reconstruction_diagnostic(rows)
        self.assertEqual((got["answers"], got["recall_beyond_input"], got["gating"]), (4, 1, False))
        with self.assertRaises(ValueError):
            r2.reconstruction_diagnostic(rows + [rows[0]])

    def test_diagnostic_cli_freezes_report_without_contacting_a_model(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path = root / "saved.json"
            path.write_bytes(json_bytes({"restyle": [{"id": "saved", "original": COPY, "plain": "new input", "answers": [COPY]}]}))
            with mock.patch.object(RecordedClient, "post", side_effect=AssertionError("no endpoint allowed")), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(r2.main(["--diagnostic", str(path), "--out", str(root / "job")]), 0)
            report = json.loads((root / "job/private/RECONSTRUCTION-DIAGNOSTIC.json").read_text())
            self.assertEqual(report["recall_beyond_input"], 1)
            self.assertFalse(report["gating"])


class RunnerTest(unittest.TestCase):
    def test_both_arms_complete_without_endpoint_and_reuse_twenty_base_decisions(self):
        with tempfile.TemporaryDirectory() as td:
            out, plan = prepared(Path(td))
            calls = []
            def opener(request, timeout):
                payload = json.loads(request.data)
                calls.append(payload)
                if payload.get("response_format"):
                    prompt = payload["messages"][-1]["content"]
                    place = re.search(r"You are at: (\w+)\.", prompt)[1]
                    content = json.dumps({"thought": thought(), "action": "stay", "place": place,
                                          "minutes": 30, "says": None, "buys": [], "revision": None})
                elif payload["messages"][0]["content"].startswith("Judge meaning"):
                    content = '{"everything":true,"nothing_added":true}'
                else:
                    content = "a fixture restyle in independent words " + payload["messages"][-1]["content"][-20:]
                data = json_bytes({"choices": [{"message": {"content": content}, "finish_reason": "stop"}]})
                return contextlib.closing(SimpleNamespace(read=lambda: data, close=lambda: None, status=200))
            clients = lambda path, lora=None: RecordedClient("http://cpu-fixture.invalid", out / path, lora=lora, opener=opener)
            base, judge = clients("raw-base"), clients("raw-judge")
            guard = restyle.ShelfGuard([COPY])
            control = r2.run_arm(out, "control", "test", clients("raw-control"), judge, base, guard)
            adapter_client = clients("raw-adapter", [{"id": 0, "scale": 0.8}])
            adapter = r2.run_arm(out, "adapter", "test", adapter_client, judge, base, guard)
            self.assertEqual(len(calls), 220)  # 2*(40 restyles + 40 meanings + 20 contract restyles) + 20 shared base
            self.assertEqual(sum("response_format" in p for p in calls), 20)
            r2.validate_result(plan, control, "control")
            r2.validate_result(plan, adapter, "adapter")
            n = len(calls)
            self.assertEqual(r2.run_arm(out, "adapter", "test", adapter_client, judge, base, guard), adapter)
            self.assertEqual(len(calls), n)
            selected = next((out / "private/selected/adapter-test").glob("voice-*.json"))
            value = json.loads(selected.read_text())
            value["result"]["restyle"]["text"] = "changed"
            selected.write_bytes(json_bytes(value))
            with self.assertRaises(ValueError):
                r2.run_arm(out, "adapter", "test", adapter_client, judge, base, guard)
            self.assertEqual(len(calls), n)
            meaning = [p for p in calls if p["messages"][0]["content"].startswith("Judge meaning")]
            self.assertTrue(all(not p.get("lora") and p["temperature"] == 0 for p in meaning))
            self.assertTrue(all(p["id_slot"] == 1 for p in calls))

    def test_adapter_requires_positive_scale_control_and_judge_stay_plain(self):
        with tempfile.TemporaryDirectory() as td:
            out, _ = prepared(Path(td))
            c = RecordedClient("http://unused.invalid", Path(td) / "raw")
            with self.assertRaisesRegex(ValueError, "positive"):
                r2.run_arm(out, "adapter", "scale0", c, c, c, restyle.ShelfGuard([COPY]))

    def test_selected_cache_is_exact_and_never_reruns_unknown_work(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "row.json"
            build = mock.Mock(side_effect=UnknownRequest("fixture"))
            with self.assertRaises(UnknownRequest):
                r2.case_result(p, {"job": 1}, build)
            self.assertFalse(p.exists())
            self.assertEqual(build.call_count, 1)
            r2.case_result(p, {"job": 1}, lambda: {"good": True})
            with self.assertRaises(ValueError):
                r2.case_result(p, {"job": 2}, lambda: self.fail("must not run"))

    def test_cli_dispatch_and_run_require_real_frozen_latency_guard(self):
        with mock.patch.object(r2, "main", return_value=17) as main:
            self.assertEqual(old.main(["--round-two", "--prepare", "--out", "fixture"]), 17)
            main.assert_called_once_with(["--prepare", "--out", "fixture"])
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                r2.main(["--run", "--out", "fixture", "--url", "http://unused.invalid", "--arm", "control"])


if __name__ == "__main__":
    unittest.main()
