"""T19's automatic publication, crash retry and preservation contract; no model."""
import json
import subprocess
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from world import nightly_report
from world.__main__ import cmd_tick
from world.publish import GitError

REPO = Path(__file__).resolve().parents[1]
NOW = datetime.fromisoformat("2026-10-25T22:00:00+05:30")


class GitRecorder:
    def __init__(self):
        self.committed = None
        self.calls = []
        self.fail = False

    def sync(self):
        self.calls.append("sync")

    def publish(self, paths, message):
        self.calls.append((list(paths), message))
        if self.fail:
            self.fail = False
            raise GitError("injected commit failure")
        raw = paths[0].read_bytes()
        changed = raw != self.committed
        self.committed = raw
        return changed


class NightlyReportTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="hegel-nightly-report-")
        root = Path(self.tmp.name)
        self.cfg = SimpleNamespace(repo=REPO, docs=root / "docs", state=root / "state",
                                   owl_url=None, mind_url=None, clock_shift_min=0)
        (self.cfg.docs / "days").mkdir(parents=True)
        self.path = self.cfg.docs / "days/reports.jsonl"
        self.day_path = self.cfg.docs / "days/2026-10-24.json"
        self.day = {"date": "2026-10-24", "n": 23, "complete": True,
                    "owl": {"written": "01:30", "theses": []}, "entries": [],
                    "steps": [{"decision": {"action": "rest", "place": "home", "thought": None},
                               "mind": {"source": "away"}}]}
        self.write_day()
        self.git = GitRecorder()

    def tearDown(self):
        self.tmp.cleanup()

    def write_day(self):
        self.day_path.write_text(json.dumps(self.day), encoding="utf-8")
        (self.cfg.docs / "days/index.json").write_text(
            json.dumps({"days": [{"date": self.day["date"], "n": self.day["n"]}]}), encoding="utf-8")

    def publish(self):
        return nightly_report.publish_yesterday(self.cfg, NOW, self.git)

    def command_result(self, row=None, code=0):
        row = row or {"date": "2026-10-24", "n": 23, "complete": True, "owl": True}
        return SimpleNamespace(returncode=code, stdout=json.dumps(row) + "\n", stderr="injected report failure")

    def test_normal_tick_appends_real_cli_row_after_owl(self):
        self.day.pop("owl")
        self.write_day()

        def natural_owl(_):
            self.day["owl"] = {"written": "01:30", "theses": []}
            self.write_day()

        engine = SimpleNamespace(git=self.git, tick=Mock(side_effect=natural_owl))
        args = SimpleNamespace(now=NOW.isoformat(), mind=None, no_git=False)
        with patch("world.__main__.make_mind"), patch("world.__main__.World"), patch("world.__main__.Feeds"), \
                patch("world.__main__.Git", return_value=self.git), patch("world.__main__.Engine", return_value=engine):
            self.assertEqual(cmd_tick(self.cfg, args), 0)
        row = json.loads(self.path.read_text())
        self.assertEqual((row["date"], row["thoughts"], row["sources"]), ("2026-10-24", 0, {"away": 1}))
        self.assertIsNone(row["repetition"])
        self.assertTrue(row["owl"])
        self.assertEqual(self.git.committed, self.path.read_bytes())
        self.assertEqual(self.git.calls[-1], ([self.path], "Day 23: nightly report"))

    def test_unfinished_or_without_owl_never_runs_command(self):
        for complete, owl in [(False, True), (True, False)]:
            with self.subTest(complete=complete, owl=owl):
                self.day["complete"] = complete
                self.day["owl"] = {"written": "01:30"} if owl else None
                self.write_day()
                with patch("world.nightly_report.subprocess.run") as command:
                    self.assertFalse(self.publish())
                    command.assert_not_called()
                self.assertFalse(self.path.exists())
        self.assertEqual(self.git.calls, [])

    def test_only_yesterday_is_considered_no_gap_backfill(self):
        self.day_path.rename(self.day_path.with_name("2026-10-14.json"))
        with patch("world.nightly_report.subprocess.run") as command:
            self.assertFalse(self.publish())
            command.assert_not_called()
        self.assertFalse(self.path.exists())

    def test_duplicate_preserves_every_existing_byte_and_no_second_cli(self):
        raw = b'{ "date": "2026-10-23", "original": true }\r\n'
        self.path.write_bytes(raw)
        day_raw = self.day_path.read_bytes()
        self.assertTrue(self.publish())
        first = self.path.read_bytes()
        self.assertTrue(first.startswith(raw))
        with patch("world.nightly_report.subprocess.run") as command:
            self.assertFalse(self.publish())
            command.assert_not_called()
        self.assertEqual(self.path.read_bytes(), first)
        self.assertEqual(self.day_path.read_bytes(), day_raw)
        self.assertEqual(len(first.splitlines()), 2)

    def test_commit_failure_retries_saved_row_without_rerunning_report(self):
        self.git.fail = True
        with self.assertRaises(GitError):
            self.publish()
        first = self.path.read_bytes()
        with patch("world.nightly_report.subprocess.run") as command:
            self.assertTrue(self.publish())
            command.assert_not_called()
        self.assertEqual(self.path.read_bytes(), first)
        self.assertEqual(self.git.committed, first)

    def test_command_failure_preserves_ledger_and_day(self):
        raw = b'{"date":"2026-10-23"}\n'
        self.path.write_bytes(raw)
        day_raw = self.day_path.read_bytes()
        with patch("world.nightly_report.subprocess.run", return_value=self.command_result(code=1)):
            with self.assertRaises(nightly_report.ReportError):
                self.publish()
        self.assertEqual(self.path.read_bytes(), raw)
        self.assertEqual(self.day_path.read_bytes(), day_raw)
        self.assertEqual(self.git.calls, ["sync"])

    def test_wrong_row_is_rejected_before_writing(self):
        for value in [{"date": "2026-10-23", "n": 23, "complete": True, "owl": True},
                      {"date": "2026-10-24", "n": 23, "complete": False, "owl": True},
                      {"date": "2026-10-24", "n": 23, "complete": True, "owl": False}]:
            with self.subTest(value=value), patch("world.nightly_report.subprocess.run", return_value=self.command_result(value)):
                with self.assertRaises(nightly_report.ReportError):
                    self.publish()
            self.assertFalse(self.path.exists())

    def test_atomic_replace_failure_preserves_prior_ledger(self):
        raw = b'{"date":"2026-10-23"}'
        self.path.write_bytes(raw)
        with patch("world.nightly_report.os.replace", side_effect=OSError("injected disk failure")):
            with self.assertRaises(OSError):
                self.publish()
        self.assertEqual(self.path.read_bytes(), raw)
        self.assertEqual(list(self.path.parent.glob(".reports-*.tmp")), [])

    def test_duplicate_or_corrupt_ledger_is_preserved(self):
        for raw in [b'{"date":"2026-10-23"}\n{"date":"2026-10-23"}\n', b'broken json\n']:
            with self.subTest(raw=raw):
                self.path.write_bytes(raw)
                with patch("world.nightly_report.subprocess.run") as command:
                    with self.assertRaises((ValueError, nightly_report.ReportError)):
                        self.publish()
                    command.assert_not_called()
                self.assertEqual(self.path.read_bytes(), raw)

    def test_sync_can_supply_row_without_duplicate_command(self):
        def sync():
            self.path.write_text('{"date":"2026-10-24"}\n', encoding="utf-8")
        self.git.sync = sync
        with patch("world.nightly_report.subprocess.run") as command:
            self.assertTrue(self.publish())
            command.assert_not_called()
        self.assertEqual(len(self.path.read_text().splitlines()), 1)

    def test_report_failure_makes_tick_fail_without_repeating_natural_work(self):
        engine = SimpleNamespace(git=self.git, tick=Mock(return_value=[]))
        args = SimpleNamespace(now=NOW.isoformat(), mind=None, no_git=False)
        with patch("world.__main__.make_mind"), patch("world.__main__.World"), patch("world.__main__.Feeds"), \
                patch("world.__main__.Git", return_value=self.git), patch("world.__main__.Engine", return_value=engine), \
                patch("world.__main__.nightly_report.publish_yesterday", side_effect=OSError("injected failure")):
            self.assertEqual(cmd_tick(self.cfg, args), 1)
        engine.tick.assert_called_once_with(NOW)

    # W1 (T54): the day's world-health line rides inside the day's row, and never decides whether the row is written.

    def health_result(self, line=None, code=0, stdout=None):
        line = line if line is not None else {"date": "2026-10-24", "n": 23, "thoughts": 33, "answered": 0.5}
        out = stdout if stdout is not None else json.dumps(line) + "\n"
        return SimpleNamespace(returncode=code, stdout=out, stderr="")

    def run_with(self, health):
        """publish() with the day report mocked as the row it prints and the health command as `health` (a result or an exception)."""
        row = {"date": "2026-10-24", "n": 23, "complete": True, "owl": True, "thoughts": 33}
        printed = json.dumps(row, ensure_ascii=False)
        calls = []

        def run(cmd, **kw):
            calls.append(cmd)
            if "--health" in cmd:
                if isinstance(health, BaseException):
                    raise health
                return health
            return SimpleNamespace(returncode=0, stdout=printed + "\n", stderr="")

        with patch("world.nightly_report.subprocess.run", side_effect=run):
            self.assertTrue(self.publish())
        return printed, calls

    def test_health_line_is_added_to_the_row_as_a_field(self):
        printed, calls = self.run_with(self.health_result())
        row = json.loads(self.path.read_text())
        self.assertEqual(row["health"], {"date": "2026-10-24", "n": 23, "thoughts": 33, "answered": 0.5})
        self.assertEqual({k: v for k, v in row.items() if k != "health"}, json.loads(printed))
        self.assertEqual(len(self.path.read_text().splitlines()), 1)
        health_cmd = [c for c in calls if "--health" in c][0]          # the day report's command, plus --health
        self.assertEqual(health_cmd[1:], ["-m", "world", "report", "2026-10-24", "--health", "--docs", str(self.cfg.docs), "--json"])
        self.assertEqual(len(calls), 2)

    def test_any_health_failure_leaves_the_row_exactly_as_the_report_printed_it(self):
        failures = {"no full day": self.health_result(stdout="no full day among them: a day counts from 20 thoughts\n"),
                    "exit 1": self.health_result(code=1),
                    "two lines": self.health_result(stdout='{"date":"2026-10-24"}\n{"date":"2026-10-24"}\n'),
                    "not json": self.health_result(stdout="Traceback (most recent call last)\n"),
                    "other day": self.health_result({"date": "2026-10-23"}),
                    "not an object": self.health_result(stdout="[1, 2]\n"),
                    "timeout": subprocess.TimeoutExpired("report", 120),
                    "no python": OSError("exec failed")}
        for name, health in failures.items():
            with self.subTest(name):
                self.path.unlink(missing_ok=True)
                self.git.committed = None
                printed, _ = self.run_with(health)
                self.assertEqual(self.path.read_bytes(), printed.encode("utf-8") + b"\n")
                self.assertNotIn("health", json.loads(self.path.read_text()))


if __name__ == "__main__":
    unittest.main()
