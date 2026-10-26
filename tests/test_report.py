"""The day report (T18): Day 12's row must agree with T9's frozen audit, and Day 13's with T10's rule."""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from world import report  # noqa: E402

DAY12 = json.loads((REPO / "tests/data/day12-2026-10-13.json").read_text(encoding="utf-8"))
DAY13 = json.loads((REPO / "tests/data/day13-2026-10-14.json").read_text(encoding="utf-8"))


class ReportTest(unittest.TestCase):
    def test_day12_reproduces_t9(self):
        r = report.row(DAY12)
        self.assertEqual((r["decisions"], r["thoughts"], r["repeated"]), (42, 42, 29))        # T9: 29/42 (69%)
        self.assertEqual(r["phrases"], ["return to the bungalow", "and the air is", "and the heat is"])
        self.assertEqual(r["quiet"], 0)

    def test_day12_shows_the_meal_loop_t7_fixed(self):
        r = report.row(DAY12)
        self.assertTrue(r["loop"])
        self.assertEqual(r["top_refusal"], "No household meal is available now")

    def test_day12_money_people_theses_owl(self):
        r = report.row(DAY12)
        self.assertEqual((r["cash_open"], r["cash"]), (10501, 6891))
        self.assertEqual(r["people"], ["Masterji", "Mr. R. K. Malhotra", "Ramesh", "Shri G. Hegde", "Sunil", "The bookseller"])
        self.assertEqual(r["theses"], ["india: unshaken → shaken"])
        self.assertTrue(r["owl"])

    def test_day13_is_not_measured_and_the_outage_is_not_a_refusal(self):
        r = report.row(DAY13)
        self.assertEqual(r["thoughts"], 4)
        self.assertIsNone(r["repetition"])                              # T10: fewer than 20 thoughts
        self.assertEqual((r["quiet"], r["waking"]), (30, 34))
        self.assertEqual(r["refusals"], 0)                             # "no answer from …/health" is the outage itself

    def test_names_count_each_person_once(self):
        self.assertEqual(report.names(["Ramesh and Shri G. Hegde", "the bookseller", "The bookseller", "Hegel", "Masterji, Sunil"]),
                         ["Masterji", "Ramesh", "Shri G. Hegde", "Sunil", "The bookseller"])

    def test_table_and_text(self):
        rows = [report.row(DAY12), report.row(DAY13)]
        table = report.table(rows)
        self.assertIn("| 12 | 2026-10-13 | 42 | 0% | 4 (4× No household meal is available now, a loop?) | 69% |", table)
        self.assertIn("| 13 | 2026-10-14 | 4 | 88% | 0 | – |", table)
        self.assertIn("not measured (fewer than 20 thoughts)", report.text(rows[1]))


class ReportCommandTest(unittest.TestCase):
    def test_json_over_a_range_skips_the_prologue(self):
        tmp = Path(tempfile.mkdtemp(prefix="hegel-report-"))
        try:
            days = tmp / "days"
            days.mkdir()
            shutil.copy(REPO / "docs/days/2026-10-02.json", days / "2026-10-02.json")
            (days / "2026-10-13.json").write_text(json.dumps(DAY12), encoding="utf-8")
            (days / "2026-10-14.json").write_text(json.dumps(DAY13), encoding="utf-8")
            (days / "index.json").write_text(json.dumps({"format": 1, "days": [{"date": d, "n": n} for d, n in
                                                         (("2026-10-02", 1), ("2026-10-13", 12), ("2026-10-14", 13))]}), encoding="utf-8")
            out = subprocess.run([sys.executable, "-m", "world", "report", "2026-10-01", "2026-10-31", "--docs", str(tmp), "--json"],
                                 cwd=REPO, capture_output=True, text=True, check=True, env={"HEGEL_PUSH": "0", "PATH": "/usr/bin:/bin"}).stdout
            rows = [json.loads(line) for line in out.splitlines()]
            self.assertEqual([r["n"] for r in rows], [12, 13])
            self.assertEqual(rows[0]["repeated"], 29)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
