"""Tests for pc/run_training4.py with fake processes and temporary files: no GPU, no server, no Pi, no network."""
import json
import tempfile
import time
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from pc import run_training1 as lifecycle
from pc import run_training4 as run
from pc import train_letters

COMMIT = "abc123"


def berlin(text):
    return datetime.fromisoformat(text).replace(tzinfo=run.BERLIN).timestamp()


def fake_git(argv, **kwargs):
    if "status" in argv:
        out = b""
    elif "rev-parse" in argv:
        out = COMMIT.encode() + b"\n"
    elif "ls-files" in argv:
        out = b""
    else:
        raise AssertionError(argv)
    return out.decode() if kwargs.get("text") else out


def letter(i):
    return {"id": "r%d" % i, "prompt": "To a friend %d:\n\n" % i, "target": "Dear friend, letter %d, written at length." % i}


class WindowTest(unittest.TestCase):
    def accepts(self, now, deadline):
        run.check_window(berlin(deadline), berlin(now))

    def refuses(self, now, deadline):
        with self.assertRaisesRegex(ValueError, "window|past"):
            run.check_window(berlin(deadline), berlin(now))

    def test_the_night_window_ends_the_next_morning_by_0815(self):
        self.accepts("2026-11-24T22:30", "2026-11-25T08:15")
        self.accepts("2026-11-24T20:00", "2026-11-25T07:00")
        self.accepts("2026-11-25T01:00", "2026-11-25T08:00")           # started after midnight

    def test_a_deadline_after_0815_is_refused(self):
        self.refuses("2026-11-24T22:30", "2026-11-25T08:16")
        self.refuses("2026-11-24T22:30", "2026-11-25T11:00")
        self.refuses("2026-11-25T01:00", "2026-11-25T09:00")

    def test_other_nights_and_daytime_starts_are_refused(self):
        self.refuses("2026-11-24T22:30", "2026-11-26T07:00")           # two mornings on
        self.refuses("2026-11-24T14:00", "2026-11-25T07:00")           # a daytime start may not run into the night
        self.refuses("2026-11-24T22:30", "2026-11-24T23:50")           # a late evening deadline is neither window
        self.refuses("2026-11-24T22:30", "2026-11-24T21:00")           # in the past

    def test_the_daytime_window_of_training_3_still_holds_for_a_rehearsal(self):
        self.accepts("2026-11-24T10:00", "2026-11-24T19:30")
        self.refuses("2026-11-24T10:00", "2026-11-24T20:30")
        self.refuses("2026-11-24T08:00", "2026-11-24T12:00")

    def test_the_power_cutoff_must_leave_the_reserve(self):
        deadline = berlin("2026-11-25T07:30")
        run.check_power({"deadlineUtc": datetime.fromtimestamp(deadline + 900).astimezone().isoformat()}, deadline)
        with self.assertRaisesRegex(ValueError, "margin"):
            run.check_power({"deadlineUtc": datetime.fromtimestamp(deadline + 899).astimezone().isoformat()}, deadline)

    def test_the_real_run_takes_the_most_steps_the_window_fits(self):
        estimate = dict(step_seconds=30.0, evaluation_seconds=60.0)
        steps = run.fit_steps(estimate, 375, 50, 3 * 3600)
        self.assertTrue(0 < steps < 375)
        self.assertLessEqual(lifecycle.projection(30.0, 60.0, steps, 50), 3 * 3600)
        self.assertGreater(lifecycle.projection(30.0, 60.0, steps + 1, 50), 3 * 3600)
        self.assertEqual(run.fit_steps(estimate, 375, 50, 10), 0)
        self.assertEqual(run.fit_steps(estimate, 375, 50, 10 ** 7), 375)


class FullIntentTest(unittest.TestCase):
    """create() with the git calls faked and everything else real, in a temporary folder."""
    NOW = "2026-11-24T23:00"
    RESTORE = "2026-11-25T07:30:00+01:00"

    def setUp(self):
        self.dir = Path(tempfile.mkdtemp(prefix="training4-intent-"))
        d = self.dir
        for name in ("convert/convert_lora.py", "base/tokenizer_config.json", "converter-base/config.json", "base.gguf", "serve.py", "receipt.json"):
            (d / name).parent.mkdir(parents=True, exist_ok=True)
            (d / name).write_text("original " + name)
        (d / "train.jsonl").write_text("".join(json.dumps(letter(i)) + "\n" for i in range(24)))
        (d / "held.jsonl").write_text("".join(json.dumps(letter(100 + i)) + "\n" for i in range(3)))
        cutoff = datetime.fromtimestamp(berlin("2026-11-25T07:50")).astimezone().isoformat()
        boot = datetime.fromtimestamp(berlin("2026-11-24T20:00")).astimezone().isoformat()
        (d / "power.json").write_text(json.dumps(dict(boot=boot, deadlineUtc=cutoff, lastRequestId="r1", pendingUtc=None)))
        (d / "receipt.json").write_text(json.dumps(dict(status="VERIFIED", state=dict(lastRequestId="r1"))))
        self.config = dict(train=str(d / "train.jsonl"), heldout=str(d / "held.jsonl"), converter=str(d / "convert/convert_lora.py"),
                           base_gguf=str(d / "base.gguf"), power_receipt=str(d / "receipt.json"), power_state=str(d / "power.json"),
                           base_model=str(d / "base"), converter_base=str(d / "converter-base"), original=dict(launcher=str(d / "serve.py")),
                           trial_port=19083, model_alias="qwen", python="/fake/python",
                           estimate=dict(step_seconds=20.0, evaluation_seconds=40.0, phase_c_seconds=900.0))

    def make(self, name, rehearsal=True, restore=None, now=None, config=None):
        with patch.object(run.subprocess, "check_output", side_effect=fake_git):
            return run.create(config or self.config, self.dir / name, restore or self.RESTORE, rehearsal, now=berlin(now or self.NOW))

    def test_a_night_rehearsal_intent_is_written_and_reloads(self):
        path = self.make("job1")
        data = run.load(path)
        self.assertEqual((data["steps"], data["eval_steps"], data["save_steps"], data["dry_run"]), (3, 2, 2, True))
        self.assertEqual(data["adapter_subdir"], "final")
        self.assertIn("--goldfish", data["training_argv"])
        self.assertEqual(data["training_argv"][data["training_argv"].index("--max-steps") + 1], "3")
        self.assertEqual(lifecycle.adapter_dir(data), Path(data["run_dir"]) / "training/final")

    def test_a_too_late_deadline_writes_nothing(self):
        with self.assertRaisesRegex(ValueError, "window"):
            self.make("job2", restore="2026-11-25T09:00:00+01:00")
        self.assertFalse((self.dir / "job2").exists())

    def test_a_cutoff_without_the_margin_is_refused(self):
        with self.assertRaisesRegex(ValueError, "margin"):
            self.make("job3", restore="2026-11-25T07:45:01+01:00")
        self.assertFalse((self.dir / "job3").exists())

    def test_an_existing_job_directory_is_refused(self):
        (self.dir / "job4").mkdir()
        with self.assertRaises(FileExistsError):
            self.make("job4")

    def test_a_real_run_cannot_be_written_without_a_passed_rehearsal(self):
        config = dict(self.config, passed_rehearsal=str(self.dir / "nothing" / "REHEARSAL.json"))
        with self.assertRaises(OSError):
            self.make("job5", rehearsal=False, config=config)
        self.assertFalse((self.dir / "job5").exists())

    def finish_rehearsal(self, path, passed=True, status=run.PASSED):
        """Fabricate the records of a rehearsal that ran: everything the verdict hashes."""
        data = run.load(path)
        root = Path(data["run_dir"])
        lifecycle.write_new(root / "training/RESULT.json", dict(steps_run=3, best_step=2))
        lifecycle.write_new(root / "PHASE-C-END.json", dict(status="TWO_COMPLETION_SERVE_CHECKS", cases=[dict(scale=1), dict(scale=0)]))
        lifecycle.write_new(root / "LETTERS-C-TIMING.json", dict(seconds=100.0))
        lifecycle.write_new(root / "RESTORATION.json", dict(status="ORIGINAL_QWEN_AND_TIMER_RESTORED"))
        verdict = dict(passed=passed, intent_sha256=lifecycle.filehash(path), estimate=dict(step_seconds=20.0, evaluation_seconds=40.0,
                       phase_c_seconds=115.0, rehearsal_c_seconds=115.0))
        for name, key in (("training/RESULT.json", "training_sha256"), ("PHASE-C-END.json", "serve_sha256"),
                          ("LETTERS-C-TIMING.json", "c_timing_sha256"), ("RESTORATION.json", "restoration_sha256")):
            verdict[key] = lifecycle.filehash(root / name)
        lifecycle.write_new(root / "REHEARSAL.json", verdict)
        lifecycle.write_new(root / "RUN-END.json", dict(status=status))
        return root / "REHEARSAL.json"

    def real_config(self, rehearsal):
        return dict(self.config, passed_rehearsal=str(rehearsal))

    def test_a_real_run_after_a_passed_rehearsal_gets_its_steps_from_the_window(self):
        rehearsal = self.finish_rehearsal(self.make("rehearsal"))
        path = self.make("real", rehearsal=False, config=self.real_config(rehearsal))
        data = run.load(path)
        self.assertFalse(data["dry_run"])
        self.assertEqual((data["eval_steps"], data["save_steps"], data["upper_steps"]), (50, 50, 9))      # 24 rows: 3 steps an epoch, 3 epochs
        self.assertEqual(data["estimate"]["step_seconds"], 20.0)
        self.assertLessEqual(data["steps"], 9)

    def test_a_failed_or_unfinished_rehearsal_is_refused(self):
        for options in (dict(passed=False), dict(status="LETTERS_REHEARSAL_FAILED")):
            name = "job-" + "-".join(map(str, options.values()))
            rehearsal = self.finish_rehearsal(self.make(name + "-r"), **options)
            with self.assertRaisesRegex(ValueError, "passed rehearsal"):
                self.make(name, rehearsal=False, config=self.real_config(rehearsal))
            self.assertFalse((self.dir / name).exists())

    def test_changed_bytes_at_the_same_paths_refuse_a_real_run(self):
        for target in ("train.jsonl", "held.jsonl", "base/tokenizer_config.json", "convert/convert_lora.py", "base.gguf"):
            with self.subTest(target=target):
                self.setUp()
                rehearsal = self.finish_rehearsal(self.make("rehearsal"))
                (self.dir / target).write_text("rewritten in place" if target != "train.jsonl" else
                                               "".join(json.dumps(letter(i)) + "\n" for i in range(24)).replace("friend", "foe"))
                with self.assertRaises(ValueError):
                    self.make("real", rehearsal=False, config=self.real_config(rehearsal))
                self.assertFalse((self.dir / "real").exists())

    def test_a_changed_rehearsal_record_is_refused(self):
        rehearsal = self.finish_rehearsal(self.make("rehearsal"))
        (rehearsal.parent / "training/RESULT.json").write_text("{}")
        with self.assertRaisesRegex(ValueError, "changed"):
            self.make("real", rehearsal=False, config=self.real_config(rehearsal))

    def test_source_changed_since_the_rehearsal_is_refused(self):
        rehearsal = self.finish_rehearsal(self.make("rehearsal"))
        with patch.object(run.subprocess, "check_output", side_effect=lambda argv, **kw: "other\n" if "rev-parse" in argv else fake_git(argv, **kw)):
            with self.assertRaisesRegex(ValueError, "source changed"):
                run.validate_rehearsal(self.real_config(rehearsal))


class LauncherTest(unittest.TestCase):
    def root(self):
        return Path(tempfile.mkdtemp(prefix="training4-launcher-test-"))

    def test_admission_uses_a_stdlib_child_before_the_ml_worker(self):
        backend = run.Backend.__new__(run.Backend)
        backend.data = {"python": "/fake/ml/python"}
        backend.path, backend.hash = Path("/fake/INTENT.json"), "abc"
        backend.check_time = lambda: time.time() + 1000
        seen = []

        class Child:
            def __init__(self, backend, name, argv):
                seen.append((name, argv))

            def wait(self, end, training=False):
                seen.append(("wait", training))
        with patch.object(lifecycle, "OwnedChild", Child):
            backend.admission()
            backend.worker("train", time.time() + 1000)
        self.assertEqual(seen[0][1][0], "/usr/bin/python3")
        self.assertEqual(seen[2][1][0], "/fake/ml/python")
        self.assertTrue(seen[0][1][2].endswith("run_training4.py"))
        self.assertEqual((seen[1], seen[3]), (("wait", False), ("wait", True)))

    def pipeline_backend(self, calls, bad=None, steps_run=3):
        """A real Training 4 Backend whose processes are faked: it records the order and may fail at one stage."""
        root = self.root()
        data = dict(run_dir=str(root), dry_run=True, steps=3, eval_steps=2, adapter_subdir="final", phase_b_cap_s=25200,
                    estimate=dict(step_seconds=10.0, evaluation_seconds=10.0, phase_c_seconds=100.0))

        class Fake(run.Backend):
            def __init__(self):
                self.data, self.root, self.paths = data, root, lifecycle.intent_paths(data)
                self.children, self.paused = [], False

            def stage(self, name):
                calls.append(name)
                if name == bad:
                    raise RuntimeError("injected failure at " + name)

            def handover(self):
                self.stage("handover")

            def admission(self):
                self.stage("admission")

            def check_time(self, end=None, reserve=0):
                return time.time() + 10 ** 6

            def sample_memory(self, force=False):
                lifecycle.write_new(root / "telemetry/events.jsonl", b"{}\n", True) if not (root / "telemetry/events.jsonl").exists() else None

            def worker(self, name, end):
                self.stage("worker-" + name)
                lifecycle.write_new(root / "training/RESULT.json", dict(steps_run=steps_run, stopped="x"))
                lifecycle.write_new(root / "training/final/adapter_model.safetensors", b"w", True)

            def c_fits(self):
                return True

            def phase_c(self):
                self.stage("phase_c")

            def restore(self):
                calls.append("restore")
                return dict(status="ORIGINAL_QWEN_AND_TIMER_RESTORED", before_deadline=True)
        return Fake()

    def test_the_order_is_handover_admission_training_conversion_restore(self):
        calls = []
        with patch.object(lifecycle, "rows", return_value=[{}]):
            outcome = lifecycle.run_pipeline(self.pipeline_backend(calls))
        self.assertEqual(outcome["status"], "B_AND_C_COMPLETE", outcome.get("error"))
        self.assertEqual(calls, ["handover", "admission", "worker-train", "phase_c", "restore"])

    def test_every_failing_stage_still_restores_the_original_server_last(self):
        for bad in ("handover", "admission", "worker-train", "phase_c"):
            calls = []
            with patch.object(lifecycle, "rows", return_value=[{}]):
                outcome = lifecycle.run_pipeline(self.pipeline_backend(calls, bad))
            self.assertEqual(outcome["status"], "FAILED", bad)
            self.assertEqual((calls[-1], calls.count("restore")), ("restore", 1), bad)

    def test_a_rehearsal_that_trains_the_wrong_number_of_steps_fails_and_restores(self):
        calls = []
        with patch.object(lifecycle, "rows", return_value=[{}]):
            outcome = lifecycle.run_pipeline(self.pipeline_backend(calls, steps_run=2))
        self.assertEqual(outcome["status"], "FAILED")
        self.assertIn("frozen schedule", outcome["error"])
        self.assertEqual(calls[-1], "restore")

    def test_a_failure_to_restore_is_reported_not_hidden(self):
        backend = self.pipeline_backend([])
        backend.restore = lambda: (_ for _ in ()).throw(RuntimeError("no Qwen"))
        with patch.object(lifecycle, "rows", return_value=[{}]):
            outcome = lifecycle.run_pipeline(backend)
        self.assertEqual(outcome["status"], "RESTORATION_FAILED")


class ServeChecksTest(unittest.TestCase):
    def setup_root(self):
        root = Path(tempfile.mkdtemp(prefix="training4-serve-"))
        d = root
        (d / "train.jsonl").write_text("".join(json.dumps(letter(i)) + "\n" for i in range(3)))
        (d / "held.jsonl").write_text(json.dumps(letter(100)) + "\n")
        lifecycle.write_new(root / "ADAPTER-READY.json", {"identity": {"synthetic": True}})
        data = dict(run_dir=str(root), train=str(d / "train.jsonl"), heldout=str(d / "held.jsonl"), trial_port=19083)
        return root, data

    def patches(self, data, http):
        return (patch.object(run, "load", return_value=data), patch.object(lifecycle, "deadline", return_value=time.time() + 1000),
                patch.object(lifecycle, "same_process", return_value=True), patch.object(lifecycle, "http", side_effect=http))

    def test_both_scales_are_asked_of_the_plain_completion_endpoint_per_request(self):
        root, data = self.setup_root()
        seen = []

        def http(port, path, payload, timeout):
            seen.append((port, path, json.loads(payload)))
            scale = json.loads(payload)["lora"][0]["scale"]
            return 200, json.dumps({"content": "letter at scale %s" % scale}).encode()
        a, b, c, d = self.patches(data, http)
        with a, b, c, d:
            run.serve_checks(data, root / "INTENT.json", "synthetic")
        self.assertEqual([s[2]["lora"] for s in seen], [[{"id": 0, "scale": 1}], [{"id": 0, "scale": 0}]])
        self.assertTrue(all(s[:2] == (19083, "/completion") for s in seen))
        self.assertTrue(all(s[2]["prompt"] == letter(100)["prompt"] and s[2]["temperature"] == 0 and s[2]["id_slot"] == 1 for s in seen))
        end = lifecycle.read(root / "PHASE-C-END.json")
        self.assertEqual((end["status"], [c["scale"] for c in end["cases"]], end["texts_differ"]), ("TWO_COMPLETION_SERVE_CHECKS", [1, 0], True))
        events = lifecycle.rows(root / "http-windows.jsonl")
        self.assertEqual([e["event"] for e in events], ["http_begin", "http_end", "http_begin", "http_end"])

    def test_an_unknown_reply_stops_before_the_second_scale_and_is_never_resent(self):
        root, data = self.setup_root()
        a, b, c, d = self.patches(data, TimeoutError("unknown"))
        with a, b, c, d as http:
            with self.assertRaises(RuntimeError):
                run.serve_checks(data, root / "INTENT.json", "synthetic")
        self.assertEqual(http.call_count, 1)
        self.assertTrue((root / "unknown/1.json").exists())
        self.assertFalse((root / "PHASE-C-END.json").exists())

    def test_empty_text_fails_the_check(self):
        root, data = self.setup_root()
        a, b, c, d = self.patches(data, lambda *args: (200, b'{"content": "  "}'))
        with a, b, c, d:
            with self.assertRaisesRegex(RuntimeError, "no text"):
                run.serve_checks(data, root / "INTENT.json", "synthetic")


class VerdictTest(unittest.TestCase):
    def setup_root(self, peak=23, ratio_step=11):
        root = Path(tempfile.mkdtemp(prefix="training4-verdict-"))
        lifecycle.write_new(root / "INTENT.json", {"synthetic": True})
        lifecycle.write_new(root / "training/RESULT.json", dict(steps_run=3, best_step=2))
        lifecycle.write_new(root / "training/final/adapter_model.safetensors", b"w", True)
        (root / "training/checkpoint-2").mkdir()
        lifecycle.write_new(root / "RESTORATION.json", {"synthetic": True})
        lifecycle.write_new(root / "PHASE-C-END.json", dict(status="TWO_COMPLETION_SERVE_CHECKS", cases=[{"scale": 1}, {"scale": 0}], texts_differ=True))
        lifecycle.write_new(root / "LETTERS-C-TIMING.json", dict(seconds=120))
        log = [dict(event="step", step=n, seconds=s, peak_reserved=peak * 1024 ** 3) for n, s in ((1, 15), (2, 10), (3, ratio_step))]
        log += [dict(event="evaluate_end", step=2, seconds=20), dict(event="checkpoint", step=2, seconds=3)]
        (root / "timing.jsonl").write_text("".join(json.dumps(x) + "\n" for x in log))
        result = dict(restoration=dict(status="ORIGINAL_QWEN_AND_TIMER_RESTORED", pi_probe={"status": "PI_HEALTH_AND_ONE_TOKEN_VERIFIED"}))
        return dict(run_dir=str(root)), result

    def test_all_gates_pass_and_the_estimate_is_measured(self):
        data, result = self.setup_root()
        report = run.verdict(data, result)
        self.assertTrue(report["passed"], report["gates"])
        self.assertEqual(report["estimate"]["phase_c_seconds"], 138.0)
        self.assertEqual(report["estimate"]["step_seconds"], 11)

    def test_each_gate_can_fail(self):
        data, result = self.setup_root(peak=24)
        self.assertFalse(run.verdict(data, result)["gates"]["within_card"])
        data, result = self.setup_root(ratio_step=40)
        self.assertFalse(run.verdict(data, result)["gates"]["post_eval_speed"])
        data, result = self.setup_root()
        result["restoration"]["pi_probe"] = {}
        self.assertFalse(run.verdict(data, result)["gates"]["route"])
        data, result = self.setup_root()
        (Path(data["run_dir"]) / "training/final/adapter_model.safetensors").unlink()
        self.assertFalse(run.verdict(data, result)["gates"]["final_adapter"])


class TimedBackendTest(unittest.TestCase):
    def test_the_trainer_loop_writes_the_events_the_guards_read_and_checks_the_deadline_each_step(self):
        from tests.test_train_letters import Backend, data as make_data, make_args
        root = Path(tempfile.mkdtemp(prefix="training4-timed-"))
        make_data(root, 4, 2)
        inner, checks = Backend([1.0, 0.9]), []
        inner.held_total = 2
        timed = run.TimedBackend(inner, root / "timing.jsonl", lambda: checks.append(1), peaks=lambda: dict(peak_reserved=5, peak_allocated=4))
        train_letters.train(make_args(root, max_steps=3, eval_steps=2, save_steps=2), timed, say=lambda *a: None)
        log = lifecycle.rows(root / "timing.jsonl")
        self.assertEqual([e["event"] for e in log],
                         ["step_begin", "step", "step_begin", "step", "checkpoint", "evaluate_begin", "evaluate_end",
                          "step_begin", "step", "evaluate_begin", "evaluate_end"])
        self.assertEqual(len(checks), 3)
        steps = [e for e in log if e["event"] == "step"]
        self.assertTrue(all(e["seconds"] >= 0 and e["peak_reserved"] == 5 for e in steps))
        self.assertEqual(lifecycle.guard_reason(log, time.time(), time.time() + 10 ** 6, 3, 2, dict(step_seconds=1, evaluation_seconds=1)), None)

    def test_a_missed_deadline_stops_the_trainer(self):
        from tests.test_train_letters import Backend, data as make_data, make_args
        root = Path(tempfile.mkdtemp(prefix="training4-timed-"))
        make_data(root, 4, 2)

        def late():
            raise TimeoutError("trainer deadline")
        timed = run.TimedBackend(Backend([1.0]), root / "timing.jsonl", late)
        with self.assertRaises(TimeoutError):
            train_letters.train(make_args(root, max_steps=3), timed, say=lambda *a: None)


if __name__ == "__main__":
    unittest.main()
