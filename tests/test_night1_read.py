"""tools/night1_read.py: night 1's runs read as declared, from folders the PC seat pushes."""
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from tools import night1_read as nr


def step(place, act="stay", opened=("reply",), attempts=1, refused=0):
    return {"t": "10:00", "event": "x", "opened": list(opened),
            "decision": {"thought": "The universal stands in the particular.", "action": act, "place": place, "minutes": 15},
            "mind": {"source": "mind", "attempts": attempts, "draws": {"n": attempts, "refused": refused}}}


def day(date, home, away, venue=None, spent=0, galleries=0):
    steps = [step("home") for _ in range(home)] + [step(venue or "lodhi", opened=("beat",)) for _ in range(away)]
    vouchers = [{"date": date, "item": "Ticket", "price": spent}, {"date": "2000-01-01", "item": "old", "price": 999}]
    today = {"sights": {venue: galleries} if venue else {}, "stage": {}, "tickets": [venue] if venue else []}
    return {"n": 50, "date": date, "steps": steps, "entries": [], "state": {"account": {"vouchers": vouchers}, "today": today}}


def put(root, name, d, run=None, nested=True):
    f = root / name
    (f / "days" if nested else f).mkdir(parents=True)
    (f / ("days" if nested else "") / f"{d['date']}.json").write_text(json.dumps(d))
    if run is not None:
        (f / "RUN.json").write_text(json.dumps(run))


class Night1Test(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.root = Path(self.td.name) / "runs"
        self.root.mkdir()
        for m, date in (("50", "2026-11-20"), ("51", "2026-11-21")):
            for i, seed in enumerate((1831, 2718, 3141)):
                put(self.root, f"{m}-off-{seed}", day(date, 20 + i, 10))
                put(self.root, f"{m}-on-{seed}", day(date, 10 + i, 20, venue="national_museum", spent=650, galleries=3))

    def tearDown(self):
        self.td.cleanup()

    def test_each_run_is_measured_from_its_own_day(self):
        runs = {r["run"]: r for r in nr.load(self.root)}
        self.assertEqual(len(runs), 12)
        off, on = runs["50-off-1831"], runs["50-on-1831"]
        self.assertAlmostEqual(off["home_share"], 20 / 30)
        self.assertAlmostEqual(on["home_share"], 10 / 30)
        self.assertEqual((on["cash_spent"], on["galleries"], on["tickets"], on["venue_moments"]), (650, 3, 1, 20))
        self.assertEqual(on["venues"], ["national_museum"])
        self.assertEqual(off["cash_spent"], 0)                       # only the day's own vouchers count
        self.assertEqual(off["brought"], 10)
        self.assertFalse(off["under_floor"])

    def test_the_effect_is_the_mean_of_within_morning_differences(self):
        runs = nr.load(self.root)
        e = nr.effect(runs, "home_share", boot=500)
        self.assertAlmostEqual(e["diff"], sum(-10 / (30 + i) for i in range(3)) / 3)   # each seed: 10 fewer at home of 30 + i
        self.assertLessEqual(e["lo"], e["diff"])
        self.assertGreaterEqual(e["hi"], e["diff"])
        self.assertEqual(e["p_on_greater"], 0.0)
        self.assertEqual((e["n_on"], e["n_off"]), (6, 6))

    def test_a_morning_with_one_arm_only_is_left_out_of_the_effect(self):
        put(self.root, "52-off-1831", day("2026-11-22", 30, 0))
        e = nr.effect(nr.load(self.root), "home_share", boot=200)
        self.assertEqual(e["mornings"], ["50", "51"])

    def test_run_json_names_the_arm_and_a_flat_folder_is_read(self):
        put(self.root, "x-y-z", day("2026-11-22", 5, 5), run={"morning": "52", "seed": 1414, "switches": {"HEGEL_CULTURE": "1"}},
            nested=False)
        r = {x["run"]: x for x in nr.load(self.root)}["x-y-z"]
        self.assertEqual((r["morning"], r["arm"], r["seed"]), ("52", "on", 1414))
        self.assertTrue(r["under_floor"])

    def test_the_report_names_regimes_and_writes_the_database(self):
        put(self.root, "52-on-1831", day("2026-11-22", 29, 1))
        runs = nr.load(self.root)
        text, _ = nr.report(runs, boot=200)
        self.assertIn("share of moments at home (primary)", text)
        self.assertIn("| 52-on-1831 | 52 | on | 1831 | 30 | 97% |", text)
        self.assertIn("at home |", text)
        db = Path(self.td.name) / "runs.sqlite"
        nr.write_db(db, runs)
        nr.write_db(db, runs)                                          # again: rows replaced, not doubled
        con = sqlite3.connect(db)
        self.assertEqual(con.execute("select count(*) from runs").fetchone()[0], 13)
        con.close()

    def test_block_2_reads_the_act_against_the_museums_alone(self):
        d = day("2026-11-21", 12, 18, venue="national_museum")
        d["state"].update({"beats": ["saxena_query", "hegde_letter"], "flags": {"file_reply": "own_name", "other": 1},
                           "file": "His representation is on the file."})
        put(self.root, "51-act-1831", d, run={"morning": "51", "seed": 1831,
                                               "switches": {"HEGEL_CULTURE": "1", "HEGEL_FILE_ACT": "1"}})
        runs = nr.load(self.root)
        r = {x["run"]: x for x in runs}["51-act-1831"]
        self.assertEqual(r["arm"], "act")
        self.assertEqual(r["act_beats"], ["hegde_letter"])
        self.assertEqual(r["act_flags"], {"file_reply": "own_name"})
        text, eff = nr.report(runs, boot=200)
        self.assertIn("## Block 2", text)
        self.assertIn("`hegde_letter` fired in 1 of 1", text)
        self.assertEqual(eff["act"]["home_share"]["mornings"], ["51"])
        self.assertNotIn("pooled", eff)

    def test_block_3_seeds_are_pooled_and_block_1_stays_alone(self):
        put(self.root, "50-off-2027", day("2026-11-20", 30, 0))
        put(self.root, "50-on-2027", day("2026-11-20", 0, 30))
        text, eff = nr.report(nr.load(self.root), boot=200)
        self.assertEqual(eff["block1"]["home_share"]["n_on"], 6)
        self.assertEqual(eff["pooled"]["home_share"]["n_on"], 7)
        self.assertIn("Blocks 1 and 3 pooled", text)

    def test_the_command_line_writes_the_result(self):
        out = Path(self.td.name) / "out"
        self.assertEqual(nr.main(["--runs", str(self.root), "--out", str(out), "--boot", "100"]), 0)
        self.assertTrue((out / "RESULT.md").exists())
        self.assertEqual(len(json.loads((out / "result.json").read_text())["runs"]), 12)


if __name__ == "__main__":
    unittest.main()
