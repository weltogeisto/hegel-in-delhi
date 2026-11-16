"""tools/fork_diff.py on small made-up folders: no rehearsal needed. (The forks of real rehearsals are in test_rehearsal_days.py.)"""
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import fork_diff  # noqa: E402


def folder(root, days):
    (root / "days").mkdir(parents=True)
    (root / "days/index.json").write_text(json.dumps({"format": 1, "days": [{"date": d} for d in days]}), encoding="utf-8")
    for d, steps in days.items():
        day = {"date": d, "state": {"imprest": 100, "place": "home"},
               "steps": [{"t": t, "decision": {"action": a, "place": p, "minutes": 30, "thought": "x"}, "mind": {"latency_s": lat}} for t, a, p, lat in steps]}
        (root / "days" / f"{d}.json").write_text(json.dumps(day), encoding="utf-8")


class ForkDiff(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def run_cli(self, *args):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = fork_diff.main([str(self.root / "a"), str(self.root / "b"), *args])
        return code, buf.getvalue()

    def test_identical_but_for_the_stopwatch(self):
        folder(self.root / "a", {"2026-10-03": [("09:00", "walk", "lodhi", 1.2)]})
        folder(self.root / "b", {"2026-10-03": [("09:00", "walk", "lodhi", 9.9)]})
        code, out = self.run_cli()
        self.assertEqual(code, 0)
        self.assertIn("2026-10-03  same", out)

    def test_names_the_first_moment_they_part(self):
        folder(self.root / "a", {"2026-10-03": [("09:00", "walk", "lodhi", 1), ("09:30", "stay", "lodhi", 1)], "2026-10-04": [("09:00", "rest", "home", 1)]})
        folder(self.root / "b", {"2026-10-03": [("09:00", "walk", "lodhi", 1), ("09:30", "walk", "khan", 1)], "2026-10-04": [("09:00", "rest", "home", 1)]})
        code, out = self.run_cli()
        self.assertEqual(code, 1)
        self.assertIn("first difference: 2026-10-03 09:30", out)
        self.assertIn("A: stay → lodhi", out)
        self.assertIn("B: walk → khan", out)
        code, out = self.run_cli("--json")
        self.assertEqual(json.loads(out)["first"]["t"], "09:30")

    def test_a_day_that_is_missing_on_one_side(self):
        folder(self.root / "a", {"2026-10-03": [("09:00", "walk", "lodhi", 1)]})
        folder(self.root / "b", {"2026-10-03": [("09:00", "walk", "lodhi", 1)], "2026-10-04": []})
        code, out = self.run_cli()
        self.assertEqual(code, 1)
        self.assertIn("exists only in B", out)


if __name__ == "__main__":
    unittest.main()
