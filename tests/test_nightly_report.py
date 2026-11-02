"""T19's automatic publication, crash retry and preservation contract; no model."""
import json
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


if __name__ == "__main__":
    unittest.main()
