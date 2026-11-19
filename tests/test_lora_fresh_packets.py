"""tools/lora_fresh_packets.py: W8's packets, shuffled per reader, keys apart, nothing lost or labelled."""
import json
import tempfile
import unittest
from pathlib import Path

from tools import lora_fresh_packets as lp


def fixture(d, fallback=False):
    cases = [{"id": f"D{44 + i // 4}-S{i}", "day": 44 + i // 4, "group": "occasion" if i % 2 else "ordinary", "i": i,
              "set": "confirmation" if i < 4 else "development", "thought": f"thought {i}"} for i in range(12)]
    (d / "plan.json").write_text(json.dumps({"cases": cases, "seed": 1831}))
    rows = [{"id": c["id"], "version": v, "output": f"{v} of {c['id']}", "fallback": fallback and v == "adapter" and c["i"] == 3}
            for c in cases for v in lp.REWRITES]
    (d / "outputs.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    return cases


class PacketsTest(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.d = Path(self.td.name)
        self.cases = fixture(self.d)
        self.out, self.keys = self.d / "repo/packets", self.d / "outside"
        self.h = lp.build(self.d / "plan.json", self.d / "outputs.jsonl", self.out, self.keys)

    def tearDown(self):
        self.td.cleanup()

    def load(self, name):
        return json.loads((self.out / name).read_text()) if name.startswith("packet") else json.loads((self.keys / name).read_text())

    def test_the_marking_readers_get_every_thought_with_its_three_rewrites(self):
        for reader in ("sol", "claude"):
            items, key = self.load(f"packet-{reader}.json"), self.load(f"key-{reader}.json")
            self.assertEqual(len(items), 12)
            for it in items:
                k = key[it["id"]]
                self.assertEqual(sorted(k[x] for x in "ABC"), sorted(lp.REWRITES))
                for lab in "ABC":
                    self.assertEqual(it[lab], f"{k[lab]} of {k['case']}")
                self.assertEqual(set(it), {"id", "source", "A", "B", "C"})            # no day, set or group shown
            sets = [key[it["id"]]["set"] for it in items]
            self.assertEqual(sets, ["development"] * 8 + ["confirmation"] * 4)

    def test_orders_and_ids_differ_between_readers(self):
        sol, claude = self.load("packet-sol.json"), self.load("packet-claude.json")
        self.assertNotEqual([i["source"] for i in sol], [i["source"] for i in claude])
        self.assertTrue(all(i["id"].startswith("S") for i in sol) and all(i["id"].startswith("K") for i in claude))

    def test_welt_chooses_among_the_thought_and_two_rewrites_on_the_held_back(self):
        items, key = self.load("packet-welt.json"), self.load("key-welt.json")
        self.assertEqual(len(items), 4)
        for it in items:
            k = key[it["id"]]
            self.assertEqual(k["set"], "confirmation")
            self.assertEqual(sorted(k[x] for x in "XYZ"), sorted(lp.WELT))
            self.assertEqual(set(it), {"id", "X", "Y", "Z"})

    def test_keys_stay_outside_and_their_hashes_inside(self):
        self.assertFalse(any(p.name.startswith("key") for p in self.out.iterdir()))
        self.assertEqual(set(self.h["readers"]), {"sol", "claude", "welt"})
        recorded = json.loads((self.out / "HASHES.json").read_text())
        self.assertEqual(recorded["readers"]["sol"]["key_sha256"], self.h["readers"]["sol"]["key_sha256"])
        self.assertTrue((self.out / "BALLOT.md").exists())

    def test_the_same_inputs_give_the_same_packets(self):
        again = lp.build(self.d / "plan.json", self.d / "outputs.jsonl", self.d / "again", self.d / "again-keys")
        self.assertEqual(again["readers"], self.h["readers"])

    def test_a_fallback_is_refused(self):
        d = self.d / "fb"
        d.mkdir()
        fixture(d, fallback=True)
        with self.assertRaises(ValueError):
            lp.build(d / "plan.json", d / "outputs.jsonl", d / "o", d / "k")


if __name__ == "__main__":
    unittest.main()
