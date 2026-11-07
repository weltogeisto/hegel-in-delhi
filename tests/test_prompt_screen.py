"""M1's prompt screen (tools/prompt_screen.py): frozen contexts, 144 replayable calls, a blind sheet, the pass rule."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from tools import prompt_screen as ps

FROZEN = Path(__file__).resolve().parents[1] / "pc/exports/m1-screen-20261107"


def copy():
    tmp = Path(tempfile.mkdtemp(prefix="m1-screen-test-")) / "screen"
    shutil.copytree(FROZEN, tmp)
    return tmp


def fake_post(calls):
    def post(key, payload):
        calls.append(key)
        text = json.dumps({"thought": "The tea is cold again, and I would rather walk than wait for another pot.",
                           "action": "stay", "place": "home", "minutes": 30, "says": None, "buys": [], "revision": None})
        return {"choices": [{"message": {"content": text}, "finish_reason": "stop"}]}, {"response_sha256": "a" * 64}
    return post


class ScreenTest(unittest.TestCase):
    def test_the_frozen_screen_has_24_contexts_and_two_arms(self):
        manifest, souls, rows = ps.contexts(FROZEN)
        self.assertEqual([r["kind"] for r in rows].count("ordinary"), 16)
        self.assertEqual([r["kind"] for r in rows].count("encounter"), 8)
        self.assertFalse({r["day"] for r in rows} - set(ps.DAYS))
        self.assertNotEqual(souls["A"], souls["B"])
        self.assertFalse(manifest["training_eligible"])

    def test_144_calls_differ_only_in_the_system_prompt(self):
        calls = ps.requests(FROZEN)
        self.assertEqual(len(calls), 144)
        self.assertEqual(len({c[0] for c in calls}), 144)
        by = {}
        for key, row, arm, seed, payload in calls:
            by.setdefault((row["id"], seed), {})[arm] = payload
        for pair in by.values():
            a, b = pair["A"], pair["B"]
            self.assertEqual(a["messages"][1], b["messages"][1])
            self.assertNotEqual(a["messages"][0], b["messages"][0])
            self.assertEqual({k: v for k, v in a.items() if k != "messages"}, {k: v for k, v in b.items() if k != "messages"})

    def test_run_records_once_and_replays(self):
        folder, calls = copy(), []
        done = ps.run(folder, fake_post(calls))
        self.assertEqual((len(done), len(calls)), (144, 144))
        self.assertFalse(any(r["training_eligible"] for r in done))
        ps.run(folder, lambda *a: self.fail("a saved reply was sent again"))

    def test_blind_sheet_and_pass_rule(self):
        folder = copy()
        ps.run(folder, fake_post([]))
        sheet, key = folder / "SHEET.jsonl", folder / "KEY.json"
        ps.packet(folder, sheet, key)
        with self.assertRaises(FileExistsError):
            ps.packet(folder, sheet, key)
        rows = [json.loads(x) for x in sheet.read_text().splitlines()]
        self.assertEqual(len(rows), 24)
        self.assertTrue(all(len(r["X"]) == 3 and len(r["Y"]) == 3 for r in rows))
        self.assertFalse(any("arm" in o for r in rows for o in r["X"] + r["Y"]))
        self.assertEqual(set(rows[0]), {"id", "kind", "situation", "X", "Y"})
        k = json.loads(key.read_text())

        def judged(n_b, b_regression=False):
            out = []
            for i, r in enumerate(rows):
                b_slot = "X" if k[r["id"]]["X"] == "B" else "Y"
                a_slot = "Y" if b_slot == "X" else "X"
                out.append({"id": r["id"], "prefer": b_slot if i < n_b else a_slot,
                            "regression": {b_slot: b_regression and i == 0, a_slot: False}, "reason": "test"})
            path = folder / f"J-{n_b}-{b_regression}.jsonl"
            path.write_text("".join(json.dumps(x) + "\n" for x in out))
            return ps.verdict(folder, path, key)
        self.assertTrue(judged(16)["passed"])
        self.assertFalse(judged(15)["passed"])
        self.assertFalse(judged(20, b_regression=True)["passed"])


if __name__ == "__main__":
    unittest.main()
