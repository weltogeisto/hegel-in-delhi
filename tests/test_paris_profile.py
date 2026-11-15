"""The Paris backtest, stage 1 (tools/paris_profile.py): the frozen sample, the second coder's requests and the profile."""
import json
import tempfile
import unittest
from pathlib import Path

from tools import paris_profile as pp


def day(date, diary=None, writing=None, thoughts=(), complete=True):
    entries = [{"k": "diary", "text": t, "t": "09:00"} for t in thoughts]
    if writing:
        entries.append({"k": "writing", "text": writing, "t": "10:00"})
    return {"date": date, "complete": complete, "owl": {"diary": diary} if diary else {}, "entries": entries}


class Pieces(unittest.TestCase):
    def test_short_paragraphs_and_editor_lines_are_left_out(self):
        text = "## Reise\n\nParis! d. 3. Sptbr. 1827.\n\naus Briefen Hegels an seine Frau. Wir sind gestern Abend in Paris angekommen und sehr müde.\n\nKurz."
        self.assertEqual(pp.split(text), ["Wir sind gestern Abend in Paris angekommen und sehr müde."])

    def test_the_simulated_pools_take_the_owl_the_writings_and_the_thoughts(self):
        days = {"2026-10-13": day("2026-10-13", diary="The day began with tea and the papers on the step. Short one.",
                                  writing="13 October.\n\nI sat with the vouchers for an hour and counted the cash twice.",
                                  thoughts=["Ramesh brings the tea before I ask for it. Good."])}
        evening, thoughts = pp.simulated_pools(days)
        self.assertEqual([s for _, s in evening], ["The day began with tea and the papers on the step.",
                                                   "I sat with the vouchers for an hour and counted the cash twice."])
        self.assertEqual(thoughts, [("2026-10-13", "Ramesh brings the tea before I ask for it.")])


class Measures(unittest.TestCase):
    def test_kappa_parse_shares_and_distance(self):
        self.assertEqual(pp.kappa([1, 2, 3, 1], [1, 2, 3, 1]), 1.0)
        self.assertEqual(pp.kappa([1, 1, 2, 2], [1, 2, 1, 2]), 0.0)
        self.assertEqual(pp.parse("3"), 3)
        self.assertEqual(pp.parse("Code: 10."), 10)
        self.assertIsNone(pp.parse("none fits"))
        p, q = pp.shares([1, 1, 9, 9]), pp.shares([9, 9, 9, 9])
        self.assertEqual((p[1], p[9], q[9]), (0.5, 0.5, 1.0))
        self.assertEqual(pp.distance(p, q), 0.5)
        self.assertEqual(pp.distance(p, p), 0.0)

    def test_requests_carry_the_codebook_and_ask_for_a_number(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "SHEET.jsonl").write_text(json.dumps({"id": "a", "text": "Wir aßen Cotelets."}) + "\n", encoding="utf-8")
            (Path(d) / "CODEBOOK.md").write_text(pp.CODEBOOK, encoding="utf-8")
            r = pp.requests(d)[0]
            self.assertEqual(r["id"], "a")
            self.assertIn("Philosophy proper", r["messages"][0]["content"])
            self.assertEqual(r["messages"][1]["content"], "Wir aßen Cotelets.")
            self.assertEqual(r["settings"]["temperature"], 0)


class Frozen(unittest.TestCase):
    """The sample on main, as frozen on 15 November."""
    FOLDER = Path(__file__).resolve().parents[1] / "pc/exports/paris-stage1-20261115"

    def setUp(self):
        if not (self.FOLDER / "MANIFEST.json").exists():
            self.skipTest("not frozen yet")

    def test_the_frozen_sheet_is_whole_and_keyed(self):
        m = json.loads((self.FOLDER / "MANIFEST.json").read_text(encoding="utf-8"))
        for name, want in m["files"].items():
            self.assertEqual(pp.digest((self.FOLDER / name).read_bytes()), want, name)
        key = json.loads((self.FOLDER / "KEY.json").read_text(encoding="utf-8"))
        sheet = pp.read_sheet(self.FOLDER)
        self.assertEqual(len(sheet), 750)
        self.assertEqual({r["id"] for r in sheet}, set(key))
        groups = [k["group"] for k in key.values()]
        self.assertEqual({g: groups.count(g) for g in pp.SIZES}, pp.SIZES)
        self.assertEqual(m["seed"], 1831)

    def test_the_sample_is_drawn_again_byte_for_byte(self):
        m = json.loads((self.FOLDER / "MANIFEST.json").read_text(encoding="utf-8"))
        repo = Path(__file__).resolve().parents[1]
        import subprocess
        try:
            subprocess.run(["git", "-C", str(repo), "cat-file", "-e", m["shadow"]], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            self.skipTest("the shadow commit is not in this clone")
        with tempfile.TemporaryDirectory() as d:
            pp.sample(repo, m["shadow"], Path(d) / "again")
            for name in ("SHEET.jsonl", "KEY.json", "CODEBOOK.md"):
                self.assertEqual((Path(d) / "again" / name).read_bytes(), (self.FOLDER / name).read_bytes(), name)


if __name__ == "__main__":
    unittest.main()
