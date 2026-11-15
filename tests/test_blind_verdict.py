"""T36's truth and quality gates from a sealed blind judgment and its key (tools/blind_verdict.py)."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tools import blind_verdict

R = Path(__file__).resolve().parents[1]


def dump(path, rows):
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Export:
    """A tiny export: four thoughts per arm on two days, two scored thoughts per arm."""

    def __init__(self, root, flags=None, scores=None, key_shape="list"):
        self.root = Path(root)
        pkt, jud = self.root / "for-claude", self.root / "judgment"
        (pkt / "evidence").mkdir(parents=True)
        jud.mkdir()
        self.arm, review, audit = {}, [], []
        flags = flags or {}
        for n in range(8):
            i, arm, ref = f"id{n}", "AD"[n % 2], f"case{n // 2}"
            self.arm[i] = arm
            sentences = [] if n == 7 else [{"n": k, "text": f"s{k}"} for k in (1, 2, 3, 4, 5)]
            review.append(dict(id=i, reference=ref, sentences=sentences, text="" if n == 7 else "x"))
            c, f = flags.get(i, (0, 0))
            audit.append(dict(id=i, sentences=len(sentences), contradictions=c, statements_as_fact=f, uncertain=0))
        for k in range(4):
            (pkt / "evidence" / f"e{k}.json").write_text(
                json.dumps(dict(reference=f"case{k}", date="2026-10-13" if k < 2 else "2026-10-28")), encoding="utf-8")
        dump(pkt / "truth-review.jsonl", review)
        dump(jud / "TRUTH-AUDIT.jsonl", audit)
        scores = scores or {"id0": (3, 3), "id1": (3, 3), "id2": (3, 3), "id3": (3, 3)}
        dump(jud / "VOICE-ARGUMENT-SCORES.jsonl", [dict(id=i, argument=a, voice=v, reason="r") for i, (a, v) in scores.items()])
        self.key = self.root / "KEY.json"
        if key_shape == "list":
            self.key.write_text(json.dumps([dict(id=i, arm=a, seed=1831) for i, a in self.arm.items()]), encoding="utf-8")
        elif key_shape == "map":
            self.key.write_text(json.dumps({"entries": {i: {"arm": a} for i, a in self.arm.items()}}), encoding="utf-8")
        else:
            dump(self.key, [dict(opaque_id=i, arm=a) for i, a in self.arm.items()])
        self.seal()

    def seal(self):
        jud = self.root / "judgment"
        (jud / "SEALED.json").write_text(json.dumps(dict(
            study="test", key_sha256_as_published_by_astra=sha(self.key),
            inputs={"for-claude/truth-review.jsonl": sha(self.root / "for-claude/truth-review.jsonl")},
            judgments={n: sha(jud / n) for n in ("TRUTH-AUDIT.jsonl", "VOICE-ARGUMENT-SCORES.jsonl")})), encoding="utf-8")


class Verdict(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)

    def test_rates_per_arm_and_a_pass(self):
        e = Export(self.dir / "a", flags={"id0": (1, 0), "id1": (1, 1)})
        v = blind_verdict.verdict(e.root, e.key)
        a, d = v["arms"]["A"], v["arms"]["D"]
        self.assertEqual((a["thoughts"], a["sentences"], a["empty"]), (4, 20, 0))
        self.assertEqual((d["thoughts"], d["sentences"], d["empty"]), (4, 15, 1))
        self.assertEqual(a["contradictions_per_100"], 5.0)
        self.assertEqual(d["contradictions_per_100"], 6.667)
        self.assertEqual(d["statements_as_fact_per_100"], 6.667)
        self.assertEqual(sorted(a["by_day"]), ["2026-10-13", "2026-10-28"])
        self.assertFalse(v["gates"]["contradictions_per_100"]["passed"])
        self.assertFalse(v["passed"])
        clean = Export(self.dir / "b")
        self.assertTrue(blind_verdict.verdict(clean.root, clean.key)["passed"])

    def test_the_bars_sit_where_T36_put_them(self):
        # 0.25 lower passes, more fails: A scores 3.0 and 3.0; D 2.75 on argument, then 2.5
        ok = Export(self.dir / "ok", scores={"id0": (3, 3), "id2": (3, 3), "id1": (3, 3), "id3": (3, 3),
                                             "id4": (3, 3), "id6": (3, 3), "id5": (3, 3), "id7": (2, 3)})
        g = blind_verdict.verdict(ok.root, ok.key)["gates"]["argument"]
        self.assertEqual((g["difference"], g["passed"]), (-0.25, True))
        low = Export(self.dir / "low", scores={"id0": (3, 3), "id1": (2, 3), "id2": (3, 3), "id3": (3, 3)})
        g = blind_verdict.verdict(low.root, low.key)["gates"]["argument"]
        self.assertEqual((g["difference"], g["passed"]), (-0.5, False))

    def test_any_key_shape_that_puts_an_arm_beside_each_id(self):
        for shape in ("list", "map", "jsonl"):
            e = Export(self.dir / shape, key_shape=shape)
            self.assertEqual(blind_verdict.verdict(e.root, e.key)["arms"]["D"]["thoughts"], 4)

    def test_refuses_another_key_and_anything_changed_after_sealing(self):
        e = Export(self.dir / "a")
        other = self.dir / "OTHER.json"
        other.write_text(e.key.read_text().replace('"A"', '"D"', 1), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "not the sealed key"):
            blind_verdict.verdict(e.root, other)
        audit = e.root / "judgment/TRUTH-AUDIT.jsonl"
        audit.write_text(audit.read_text().replace('"contradictions": 0', '"contradictions": 1', 1), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "changed after sealing"):
            blind_verdict.verdict(e.root, e.key)

    def test_refuses_a_key_that_misses_an_id_or_names_another_arm(self):
        e = Export(self.dir / "a")
        rows = json.loads(e.key.read_text())
        e.key.write_text(json.dumps(rows[:-1]), encoding="utf-8")
        e.seal()
        with self.assertRaisesRegex(ValueError, "names no arm for 1 IDs"):
            blind_verdict.verdict(e.root, e.key)
        rows[0]["arm"] = "B"
        e.key.write_text(json.dumps(rows), encoding="utf-8")
        e.seal()
        with self.assertRaisesRegex(ValueError, "expected arms A and D"):
            blind_verdict.verdict(e.root, e.key)

    def test_chance_needs_no_key_and_repeats_itself(self):
        clean = Export(self.dir / "clean")
        clean.key.unlink()
        c = blind_verdict.chance(clean.root, runs=200)
        self.assertEqual(c["gates"]["contradictions_per_100"]["fails_by_chance"], 0.0)
        self.assertEqual(c["gates"]["contradictions_per_100"]["middle_90_percent"], [0.0, 0.0])
        e = Export(self.dir / "e", flags={"id0": (3, 0), "id5": (0, 2)},
                   scores={"id0": (1, 3), "id1": (5, 3), "id2": (1, 3), "id3": (5, 3)})
        one, two = blind_verdict.chance(e.root, runs=300), blind_verdict.chance(e.root, runs=300)
        self.assertEqual(one, two)
        self.assertGreater(one["gates"]["contradictions_per_100"]["fails_by_chance"], 0.2)
        self.assertGreater(one["gates"]["argument"]["fails_by_chance"], 0.1)
        self.assertEqual(one["gates"]["voice"]["fails_by_chance"], 0.0)
        self.assertEqual((one["cases"], one["thoughts"], one["scored_thoughts"]), (4, 8, 4))

    def test_the_sealed_judgment_on_main_is_whole(self):
        export = R / "pc/exports/t49-arm-d-20261114"
        sealed = json.loads((export / "judgment/SEALED.json").read_text(encoding="utf-8"))
        for name, want in sealed["judgments"].items():
            self.assertEqual(sha(export / "judgment" / name), want, name)
        for name, want in sealed["inputs"].items():
            self.assertEqual(sha(export / name), want, name)
        audit = blind_verdict.jsonl(export / "judgment/TRUTH-AUDIT.jsonl")
        self.assertEqual((len(audit), sum(a["sentences"] for a in audit)), (942, 2770))


if __name__ == "__main__":
    unittest.main()
