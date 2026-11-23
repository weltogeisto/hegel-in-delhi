"""tools/voice4.py: Training 4's instrument: passages, full-fact cards with their symmetry check, the rungs, sheets, particulars."""
import json
import tempfile
import unittest
from pathlib import Path

from tools import voice4 as v


def words(n, tag):
    return " ".join(f"{tag}{i}" for i in range(n - 1)) + " Ende."


def letter(head, *paras):
    return f"## {head}\n\n" + "\n\n".join(paras) + "\n\n"


def fake():
    one = "## Stuttgart, 1785-1807\n\nEinleitung des Herausgebers.\n\n" + "".join(
        letter(f"Hegel an Freund{i}, Jena {1795 + i}", words(120, f"a{i}x"), words(100, f"b{i}x")) for i in range(12))
    two = ("## Berlin, 1817-1831\n\nEinleitung.\n\n"
           + "".join(letter(f"Goethe an Hegel, Weimar {1820 + i}", words(150, f"g{i}x")) for i in range(3))
           + letter("Hegel an Niethammer, Berlin 1821", words(90, "n"))
           + letter("Hegel an seine Frau, Berlin 1823", words(110, "f"))
           + "## Reise nach den Niederlanden, 1822\n\nAus Hegels Briefen an seine Frau\n\nCassel, den 18. Sept. 22.\n\n" + words(95, "w")
           + "\n\n## Reise nach Wien, 1824\n\nAus Hegels Briefen an seine Frau\n\nPrag, den 18. Sept. 24.\n\n"
           + words(100, "k") + "\n\n" + words(30, "kurz") + "\n\nWien, den 21. Sept. 1824.\n\n" + words(400, "c").replace(" c200 ", " c200. C201x ")
           + "\n\nWien, den 25. Sept. 1824.\n\n" + words(95, "v")
           + "\n\n## Reise nach Paris, 1827\n\nParis, den 3. Sept. 27.\n\n" + words(95, "p") + "\n")
    return {"briefe-1": one, "briefe-2": two}


class TextTest(unittest.TestCase):
    def test_footnotes_go_and_a_broken_paragraph_is_joined(self):
        text = "Daß Heller und Ehrhardt?) Professoren geworden, ist zum Lachen nach and\n\nerer Meinung; so ist es.\n\n) Das Eingeklammerte am Rand.\n\n1) Anmerkung.\n\nIhr H."
        self.assertEqual(v.paragraphs(text), ["Daß Heller und Ehrhardt Professoren geworden, ist zum Lachen nach and erer Meinung; so ist es.", "Ihr H."])

    def test_passages_keep_their_bounds(self):
        got = v.chunks([words(50, "a"), words(60, "b"), words(30, "c"), words(700, "d").replace(" d300 ", " d300. D301x ")])
        self.assertTrue(all(n >= v.LO for n in map(v.n_words, got)))
        self.assertEqual(v.n_words(got[0]), 110)                       # two paragraphs make the first passage
        self.assertTrue(any(p.endswith("d300.") for p in got))         # the long paragraph is cut at its sentence end

    def test_particulars_are_numbers_and_names_inside_sentences(self):
        lack = v.lacking("We dined at four with Herr Creuzer and paid 12 francs. Then to Cologne.", "- dined with Creuzer\n- paid twelve francs")
        self.assertEqual(lack, {"numbers": ["4"], "names": ["cologne"]})           # twelve is 12; Creuzer is in the card; Cologne is not
        self.assertEqual(v.lacking("In the evening we saw Rubens.", "- the gallery")["names"], ["rubens"])


class CorpusTest(unittest.TestCase):
    def setUp(self):
        self.letters = v.letters(fake())

    def test_letters_are_his_or_another_and_no_journey(self):
        self.assertEqual(sum(l["by"] == "hegel" for l in self.letters), 14)
        self.assertEqual(sum(l["by"] == "other" for l in self.letters), 3)
        self.assertFalse(any("Reise" in l["head"] for l in self.letters))

    def test_the_training_journey_and_the_diaries_join_the_pool(self):
        journey = v.training_journey(fake())
        self.assertEqual([(p["head"], p["near"], p["year"]) for p in journey], [("Hegel an seine Frau, Cassel, den 18. Sept. 22", True, 1822)])
        book = {"rosenkranz-urkunden": "## Tagebuch der Reise in die Berner Oberalpen\n\n" + " ".join(["Wir gingen und der Weg war steil und das Tal lag tief."] * 12)
                + "\n\n## Hegel's Tagebuch aus der Gymnasialzeit\n\n" + " ".join(["Primo intersui hodie divino cultui orationique sacrae quam concionatus est."] * 12)
                + "\n\n" + " ".join(["Ich machte die Bemerkung, daß der Lehrer nicht kam und wir zu Hause blieben."] * 8)
                + "\n\n## Fragmente\n\n" + words(100, "x")}
        got = v.diaries(book)
        self.assertEqual([(d["head"][:8], d["near"]) for d in got], [("Tagebuch", True), ("Hegel's ", False)])
        self.assertFalse(any("Primo" in d["text"] for d in got))        # the Latin entries stay out
        self.assertEqual(v.diaries(fake()), [])

    def test_every_tenth_of_his_letters_is_held_out(self):
        pool, held, others = v.split(self.letters)
        self.assertEqual((len(pool), len(held), len(others)), (13, 1, 3))
        self.assertFalse({l["id"] for l in pool} & {l["id"] for l in held})

    def test_the_development_passages_fall_under_their_date_lines_and_leave_paris_out(self):
        dev = v.development(fake())
        self.assertEqual({p["journey"] for p in dev}, set(v.DEVELOPMENT))
        prag = [p for p in dev if p["dated"].startswith("Prag")]
        self.assertEqual([p["words"] for p in prag], [130])             # the short paragraph joins the one before it
        self.assertEqual(len([p for p in dev if p["dated"].startswith("Wien, den 21")]), 2)
        self.assertTrue(all(v.LO <= p["words"] <= v.HI for p in dev))


class NightTest(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.f = Path(self.td.name) / "f"
        self.res = v.cmd_passages(self.f, fake())
        self.dev = v.rows(self.f / "PASSAGES.jsonl")

    def tearDown(self):
        self.td.cleanup()

    def reply(self, name, answer):
        reqs = v.rows(self.f / f"REQUESTS-{name}.jsonl")
        (self.f / f"REPLIES-{name}.jsonl").write_text("".join(json.dumps({"id": r["id"], "reply": answer(r)}) + "\n" for r in reqs))
        return reqs

    def cards(self):
        """Cards for the four development passages: the first is complete, the second gains a line, the third is dropped."""
        v.cmd_cards(self.f)
        self.reply("cards", lambda r: "- arrived at 11\n- saw the gallery")
        v.cmd_check(self.f, 1)
        ids = [p["id"] for p in self.dev]
        self.reply("check1", lambda r: "NONE" if r["id"].endswith(ids[0]) or r["id"].endswith(ids[3]) else "- paid 3 thalers")
        one = v.cmd_merge(self.f, 1)
        v.cmd_check(self.f, 2)
        self.reply("check2", lambda r: "None." if r["id"].endswith(ids[1]) else "- met Creuzer")
        return ids, one, v.cmd_merge(self.f, 2)

    def test_the_folder_holds_the_three_sets(self):
        self.assertEqual(self.res["letters"], {"pool": 13, "held": 1, "others": 3})
        pool = v.rows(self.f / "POOL.jsonl")
        self.assertTrue(all(p["kind"] == "hegel" for p in pool))
        self.assertEqual({p["kind"] for p in v.rows(self.f / "CONTROLS.jsonl")}, {"hegel", "other"})

    def test_a_card_gains_what_it_lacked_and_is_dropped_if_it_still_lacks(self):
        ids, one, two = self.cards()
        self.assertEqual((one["complete"], one["open"]), (2, 2))
        self.assertEqual((two["complete"], two["open"], two["dropped"]), (3, 0, 1))
        cards = {c["id"]: c for c in v.rows(self.f / "CARDS.jsonl")}
        self.assertEqual(set(cards), {ids[0], ids[1], ids[3]})
        self.assertEqual(cards[ids[1]]["card"], "- arrived at 11\n- saw the gallery\n- paid 3 thalers")
        self.assertEqual(json.loads((self.f / "DROPPED.json").read_text())["lacking_after_two_rounds"][0]["id"], ids[2])
        self.assertEqual(len(v.rows(self.f / "REQUESTS-check2.jsonl")), 2)          # only the open cards are checked again

    def test_the_arms_ask_alike_and_differ_in_what_stands_in_front(self):
        self.cards()
        souls = {j: f"soul {y}" for j, y in v.YEAR.items()}
        v.cmd_arms(self.f, souls)
        reqs = {r["id"]: r for r in v.rows(self.f / "REQUESTS-arms.jsonl")}
        card = v.rows(self.f / "CARDS.jsonl")[0]
        asks = {arm: reqs[f"letter|{arm}|{card['id']}"]["messages"][1]["content"] for arm in v.ARMS}
        tail = asks["P0"]
        self.assertIn("The day's record:\n- arrived at 11", tail)
        self.assertIn(v.FACTS, tail)
        self.assertTrue(asks["P1"].endswith(tail) and asks["P2"].endswith(tail))
        plan = json.loads((self.f / "EXEMPLARS.json").read_text())
        self.assertEqual((len(plan[f"P0|{card['id']}"]), len(plan[f"P1|{card['id']}"])), (0, 3))
        near = {p["id"] for p in v.rows(self.f / "POOL.jsonl") if p["near"]}
        self.assertEqual(len(near), 2)                                                 # his letter to his wife, and the training journey
        self.assertTrue(near <= set(plan[f"P1|{card['id']}"]))                         # what is of the journeys' kind stands first
        self.assertGreater(len(plan[f"P2|{card['id']}"]), 3)
        pool = {p["id"]: p["letter"] for p in v.rows(self.f / "POOL.jsonl")}
        shown = plan[f"P2|{card['id']}"]
        self.assertEqual(len({pool[x] for x in shown}), len(shown))                  # from different letters, all of the pool
        self.assertIn(f"real|{card['id']}", reqs)
        self.assertEqual(sum(k.startswith("control|") for k in reqs), len(v.rows(self.f / "CONTROLS.jsonl")))

    def test_sheets_hide_the_side_and_the_rule_counts_what_a_card_lacks(self):
        self.cards()
        v.cmd_arms(self.f, {j: "soul" for j in v.YEAR})
        self.reply("arms", lambda r: "Wir kamen um 11 an." if r["id"].startswith("letter|") else "We arrived at 11 and saw the gallery.")
        v.cmd_translate(self.f)
        self.reply("translate", lambda r: "We arrived at 11 and dined with Herr Schulze for 9 francs.")
        keys = Path(self.td.name) / "keys"
        a = v.cmd_sheet(self.f, "P1", keys)
        b = v.cmd_sheet(self.f, "P1", keys, mirror=True)
        self.assertEqual(a["pairs"], 3)
        ka, kb = json.loads((keys / "KEY-P1.json").read_text()), json.loads((keys / "KEY-P1-mirror.json").read_text())
        self.assertTrue(all(ka[p]["real"] != kb[p]["real"] for p in ka))             # the mirror shows each pair the other way round
        self.assertFalse(any(p.name.startswith("KEY") for p in self.f.iterdir()))
        self.assertEqual(set(v.rows(self.f / "SHEET-P1.jsonl")[0]), {"pair", "X", "Y"})
        got = v.cmd_classify(self.f)
        self.assertIn("qualification", got)
        self.assertEqual(set(got["arms"]), set(v.ARMS))
        table = v.cmd_particulars(self.f)
        self.assertEqual(table["real"]["per_letter"], 0)
        self.assertEqual(table["P0"]["per_letter"], 2)                                # 9 francs and Schulze are in no card
        self.assertEqual(table["P0"]["with_any"], 3)


class MeasureTest(unittest.TestCase):
    def test_delta_tells_two_writers_apart_and_not_one_from_himself(self):
        a = [f"the house and the garden ; we went , and the sun was on the wall {i}" for i in range(12)]
        b = [f"of which nevertheless ! of which moreover ? thereof whereas hence {i}" for i in range(12)]
        self.assertEqual(v.delta_accuracy(a, b)["accuracy"], 1.0)
        same = v.delta_accuracy(a[:6], a[6:])
        self.assertLess(same["accuracy"], 0.8)
        self.assertIsNone(v.delta_accuracy(a[:1], b))
        self.assertEqual([v.n_words(x) for x in v.bundles(["a b c", "d e", "f g h i", "j"], size=5)], [5, 5])   # the remainder is left out

    def test_the_marked_rewrites_are_the_ones_on_record(self):
        from collections import Counter
        got = Counter((x["set"], x["label"]) for x in v.marked())
        self.assertEqual((got[("forty", "substantive")], got[("forty", "minor")], got[("forty", "clean")]), (9, 7, 64))
        self.assertEqual((got[("w8", "substantive")], got[("w8", "minor")]), (8, 17))       # as pc/exports/.../DEFECTS.md counts them
        self.assertEqual(sum(got.values()), 80 + 216)

    def test_the_judge_gates_only_if_it_finds_the_defects_and_spares_the_clean(self):
        items = ([{"id": f"s{i}", "set": "x", "source": "a", "rewrite": "b", "label": "substantive"} for i in range(10)]
                 + [{"id": f"c{i}", "set": "x", "source": "a", "rewrite": "a", "label": "clean"} for i in range(20)])
        with tempfile.TemporaryDirectory() as d:
            f = Path(d)
            self.assertEqual(v.cmd_judge(f, items)["rows"], 30)
            req = v.rows(f / "REQUESTS-judge.jsonl")[0]
            self.assertIn("Source:\na\n\nRewrite:\nb", req["messages"][1]["content"])

            def answer(found, alarms):
                out = []
                for x in items:
                    hit = x["label"] == "substantive" and int(x["id"][1:]) < found or x["label"] == "clean" and int(x["id"][1:]) < alarms
                    out.append({"id": "judge|" + x["id"], "reply": "- noon becomes one o'clock" if hit else "NONE"})
                (f / "REPLIES-judge.jsonl").write_text("".join(json.dumps(r) + "\n" for r in out))
                return v.cmd_judge_score(f)
            good = answer(9, 2)
            self.assertEqual((good["substantive"]["rate"], good["clean"]["rate"], good["gates"]), (0.9, 0.1, True))
            self.assertFalse(answer(7, 0)["gates"])            # it misses too many
            self.assertFalse(answer(10, 3)["gates"])           # it cries wolf too often


class ShelfTest(unittest.TestCase):
    def test_the_real_shelf_gives_the_sets_and_keeps_paris_sealed(self):
        with tempfile.TemporaryDirectory() as d:
            res = v.cmd_passages(d)
            dev = v.rows(Path(d) / "PASSAGES.jsonl")
            self.assertEqual({p["journey"] for p in dev}, set(v.DEVELOPMENT))
            self.assertGreater(len(dev), 30)
            self.assertGreater(res["pool"]["rows"], 500)
            self.assertGreater(res["passages"]["journey"], 20)
            texts = {p["text"] for p in v.rows(Path(d) / "POOL.jsonl")} | {p["text"] for p in v.rows(Path(d) / "CONTROLS.jsonl")}
            kept = {p["text"] for p in v.development(names=("Vienna 1824", "Paris 1827"))}
            self.assertFalse(texts & kept)                                            # Vienna and Paris are in no pool and no control
            joined = " ".join(texts)
            self.assertFalse(any(p[:60] in joined for p in kept))


if __name__ == "__main__":
    unittest.main()
