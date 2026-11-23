"""tools/voice4_train.py: Training 4's training set: passages, the OCR rule, the leak check, the pairs; and world/works.letter4_prompt."""
import json
import tempfile
import unittest
from pathlib import Path

from tests.test_voice4 import fake, letter, words
from tools import voice4 as v
from tools import voice4_train as t
from world import works

GERMAN = " ".join(["Ich machte die Bemerkung, daß der Lehrer nicht kam und wir zu Hause blieben."] * 8)
DIARY = ("## Hegel's Tagebuch aus der Gymnasialzeit\n\n" + GERMAN + "\n\n" + GERMAN.replace("Lehrer", "Vater") + "\n\n"
         + " ".join(["Primo intersui hodie divino cultui orationique sacrae quam concionatus est."] * 12)
         + "\n\n## Anderes\n\n" + words(100, "zz") + "\n")


def volumes(extra=""):
    vol = fake()
    vol["briefe-1"] += extra
    vol["rosenkranz-urkunden"] = DIARY
    return vol


class PromptTest(unittest.TestCase):
    def test_a_new_letter(self):
        self.assertEqual(works.letter4_prompt("Hegel an Niethammer, Berlin 1821", ["- arrived at 11", "- saw the gallery"]),
                         "Hegel an Niethammer, Berlin 1821\n\n[The record:\n- arrived at 11\n- saw the gallery]\n\n")

    def test_a_letter_that_goes_on(self):
        self.assertEqual(works.letter4_prompt("Cassel, den 18. Sept. 22.", ["- dined"], goes_on=True),
                         "Cassel, den 18. Sept. 22.\n\n[The record:\n- dined]\n[The letter goes on.]\n\n")

    def test_the_text_ends_where_the_target_begins(self):
        for goes_on in (False, True):
            self.assertTrue(works.letter4_prompt("H", ["- a", "- b"], goes_on).endswith("]\n\n"))


class PassagesTest(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.f = Path(self.td.name) / "f"

    def tearDown(self):
        self.td.cleanup()

    def test_train_and_held_are_split_and_the_first_chunk_is_marked(self):
        t.cmd_passages(self.f, volumes())
        rows = v.rows(self.f / "PASSAGES.jsonl")
        by = {s: [r for r in rows if r["set"] == s] for s in ("train", "held")}
        self.assertTrue(by["train"] and by["held"])
        self.assertFalse({r["letter"] for r in by["train"]} & {r["letter"] for r in by["held"]})
        self.assertEqual({r["source"] for r in by["train"]}, {"letter", "journey", "diary"})
        self.assertEqual({r["source"] for r in by["held"]}, {"letter"})
        journey = [r for r in rows if r["source"] == "journey"]
        self.assertTrue(all(r["head"].startswith("Hegel an seine Frau, ") and r["near"] for r in journey))
        self.assertFalse(any(r.get("journey") in t.SEALED for r in rows))
        for letter_id in {r["letter"] for r in rows}:
            mine = [r for r in rows if r["letter"] == letter_id]
            self.assertEqual([r["first"] for r in mine], [True] + [False] * (len(mine) - 1))
        self.assertTrue(all(r["first"] for r in rows if r["source"] == "diary"))
        self.assertEqual(sum(r["source"] == "diary" for r in rows), 2)               # German entries only; the other section is no diary
        self.assertFalse(any("Primo" in r["text"] for r in rows))
        self.assertTrue(any(r["source"] == "letter" and not r["first"] for r in rows))   # a letter of 220 words has a second chunk
        self.assertTrue(all("head" in r and "year" in r for r in rows))

    def test_a_garbage_passage_is_dropped_and_a_clean_one_kept(self):
        clean = " ".join(["Wir gingen heute in die Stadt und sprachen mit dem Freunde über die Sache."] * 12)
        garbage = " ".join(f"xq{'zk' * (i % 7 + 1)}vj{'wq' * (i % 5 + 1)}" for i in range(90)) + " Ende."
        extra = letter("Hegel an Freund99, Jena 1799", clean) + letter("Hegel an Freund98, Jena 1798", garbage)
        res = t.cmd_passages(self.f, volumes(extra))
        rows = v.rows(self.f / "PASSAGES.jsonl")
        self.assertTrue(any("Wir gingen heute" in r["text"] for r in rows))
        self.assertFalse(any("xqzk" in r["text"] for r in rows))
        dropped = json.loads((self.f / "DROPPED-OCR.json").read_text())["dropped"]
        self.assertEqual(len(dropped), 1)
        self.assertEqual(res["dropped_ocr"], 1)
        self.assertGreater(dropped[0]["share"], t.OCR_SHARE)
        self.assertTrue(dropped[0]["start"].startswith("xqzk") and len(dropped[0]["start"]) <= 80)

    def test_a_passage_from_vienna_or_paris_is_refused(self):
        for name in ("v", "p"):                                      # a passage of Vienna, and one of Paris
            vol = fake()
            vol["rosenkranz-urkunden"] = DIARY
            vol["briefe-1"] += letter("Hegel an Freund77, Jena 1790", words(95, name))     # the sealed passage, copied into a letter
            with self.assertRaises(ValueError):
                t.cmd_passages(self.f, vol)

    def test_the_same_input_gives_the_same_bytes(self):
        a = t.cmd_passages(self.f, volumes())
        b = t.cmd_passages(Path(self.td.name) / "g", volumes())
        self.assertEqual(a, b)


class BuildTest(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.f = Path(self.td.name) / "f"
        t.cmd_passages(self.f, volumes())
        self.rows = v.rows(self.f / "PASSAGES.jsonl")

    def tearDown(self):
        self.td.cleanup()

    def reply(self, name, answer):
        reqs = v.rows(self.f / f"REQUESTS-{name}.jsonl")
        (self.f / f"REPLIES-{name}.jsonl").write_text("".join(json.dumps({"id": r["id"], "reply": answer(r)}) + "\n" for r in reqs))

    def run_cards(self):
        """Every passage gets three lines; the first passage is dropped for lacking a line after two rounds."""
        v.cmd_cards(self.f)
        self.reply("cards", lambda r: "- arrived at 11\n- saw the gallery\n- paid 3 thalers")
        v.cmd_check(self.f, 1)
        first = self.rows[0]["id"]
        self.reply("check1", lambda r: "- met Creuzer" if r["id"].endswith(first) else "NONE")
        v.cmd_merge(self.f, 1)
        v.cmd_check(self.f, 2)
        self.reply("check2", lambda r: "- still more")
        return first, v.cmd_merge(self.f, 2)

    def test_two_rows_a_training_passage_and_one_a_held_passage(self):
        first, merged = self.run_cards()
        self.assertEqual((merged["complete"], merged["dropped"]), (len(self.rows) - 1, 1))
        man = t.cmd_build(self.f, volumes())
        train, held = v.rows(self.f / "TRAIN.jsonl"), v.rows(self.f / "HELDOUT.jsonl")
        passages = {r["id"]: r for r in self.rows}
        n_train = sum(r["set"] == "train" for r in self.rows) - 1
        b_rows = sum(r["id"].endswith("|b") for r in train)
        self.assertEqual((man["passages"], man["pairs"], man["held"]), (n_train, n_train + b_rows, sum(r["set"] == "held" for r in self.rows)))
        self.assertGreater(b_rows, n_train // 2)               # a shuffle of three lines is the original one time in six, and then has no second row
        self.assertNotIn(first, {r["id"].split("|")[0] for r in train})                 # the dropped passage is absent
        for r in train + held:
            p = passages[r["id"].split("|")[0]]
            self.assertEqual(r["target"], p["text"])                                       # his words, byte for byte
            lines = r["prompt"].split("[The record:\n")[1].split("]\n")[0].split("\n")
            self.assertEqual(sorted(lines), ["- arrived at 11", "- paid 3 thalers", "- saw the gallery"])
            self.assertEqual("[The letter goes on.]" in r["prompt"], not p["first"])
            self.assertTrue(r["prompt"].startswith(p["head"] + "\n\n[The record:\n") and r["prompt"].endswith("]\n\n"))
        a = {r["id"][:-2]: r for r in train if r["id"].endswith("|a")}
        b = {r["id"][:-2]: r for r in train if r["id"].endswith("|b")}
        self.assertEqual(len(a), n_train)
        self.assertLessEqual(set(b), set(a))
        self.assertTrue(all(a[k]["prompt"] != b[k]["prompt"] and a[k]["target"] == b[k]["target"] for k in b))
        self.assertEqual({r["id"] for r in held}, {r["id"] for r in self.rows if r["set"] == "held"})

    def test_the_manifest_counts_and_hashes(self):
        self.run_cards()
        man = t.cmd_build(self.f, volumes())
        self.assertEqual(man["dropped"], {"ocr": 0, "no_card": 0, "lacking_after_two_rounds": 1})
        self.assertEqual(man["sha256"]["TRAIN.jsonl"], t.sha(self.f / "TRAIN.jsonl"))
        self.assertEqual(man["sha256"]["HELDOUT.jsonl"], t.sha(self.f / "HELDOUT.jsonl"))
        self.assertEqual(man["note"], t.SENTENCE)
        self.assertEqual(man["constants"]["OCR_SHARE"], t.OCR_SHARE)
        self.assertEqual(json.loads((self.f / "TRAIN-MANIFEST.json").read_text()), man)
        again = t.cmd_build(self.f, volumes())
        self.assertEqual(again, man)                                                        # same input, same bytes

    def test_a_card_of_one_line_has_one_row(self):
        v.cmd_cards(self.f)
        self.reply("cards", lambda r: "- one thing")
        v.cmd_check(self.f, 1)
        self.reply("check1", lambda r: "NONE")
        v.cmd_merge(self.f, 1)
        man = t.cmd_build(self.f, volumes())
        self.assertEqual(man["pairs"], man["passages"])

    def test_the_build_refuses_a_leak(self):
        self.run_cards()
        rows = v.rows(self.f / "PASSAGES.jsonl")
        vienna = v.development(volumes(), names=("Vienna 1824",))[0]["text"]
        rows[1]["text"] = vienna
        v.put(self.f / "PASSAGES.jsonl", rows)
        with self.assertRaises(ValueError):
            t.cmd_build(self.f, volumes())


class ShelfTest(unittest.TestCase):
    def test_the_real_shelf_gives_the_passages_and_no_leak(self):
        with tempfile.TemporaryDirectory() as d:
            res = t.cmd_passages(d)                                # raises if any passage shares 12 words with Vienna or Paris
            self.assertGreater(res["train"]["passages"], 500)
            self.assertGreater(res["held"]["passages"], 0)
            rows = v.rows(Path(d) / "PASSAGES.jsonl")
            self.assertEqual({r["source"] for r in rows}, {"letter", "journey", "diary"})
            self.assertEqual(res["train"]["by_source"]["journey"], 34)             # the Netherlands journey, whole
            pool = {p["id"] for p in v.passages_of(v.split(v.letters())[0], "hegel")} | {p["id"] for p in v.training_journey()} | {p["id"] for p in v.diaries()}
            self.assertLessEqual({r["id"] for r in rows if r["set"] == "train"}, pool)   # the instrument's pool, less what the OCR rule drops
            self.assertFalse(any(r.get("journey") in t.SEALED for r in rows))


if __name__ == "__main__":
    unittest.main()
