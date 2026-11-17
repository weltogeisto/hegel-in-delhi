"""The Paris backtest's first read (tools/travel_register.py): his travel letters against his treatise and the simulation."""
import unittest

from tools import travel_register as tr


class FirstRead(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.read = tr.read(thoughts=["The universal is mediated by the particular.", "Sunil counts his change twice.", ""])

    def test_the_three_journeys_are_found_and_sized(self):
        self.assertEqual({k: v["words"] for k, v in self.read["journeys"].items()},
                         {"Netherlands 1822": 7130, "Vienna 1824": 8571, "Paris 1827": 8978})
        trips = tr.journeys(tr.work("briefe-2"))
        self.assertIn("Paris! d. 3. Sptbr. 1827.", trips["Paris 1827"])
        self.assertNotIn("Reise nach Paris", trips["Vienna 1824"])

    def test_abroad_he_wrote_like_a_traveller_and_the_treatise_like_a_treatise(self):
        letters = self.read["letters_from_three_journeys"]
        self.assertEqual((letters["words"], letters["per_100_words"]), (24679, 0.17))
        self.assertEqual((letters["sentences"], letters["sentences_with_a_term"]), (807, 38))
        de = self.read["anchor_philosophie_des_rechts_german_list"]["per_100_words"]
        en = self.read["anchor_philosophy_of_right_english_list"]["per_100_words"]
        self.assertEqual((de, en), (2.55, 2.03))
        self.assertLess(abs(de - en) / de, 0.25)                 # the two lists agree within a quarter on the same book

    def test_the_simulation_is_counted_with_the_declared_english_list(self):
        sim = self.read["simulation"]
        self.assertEqual((sim["texts"], sim["texts_with_a_term"], sim["terms"]), (2, 1, 3))
        self.assertNotIn("simulation", tr.read())

    def test_the_lists_name_the_same_notions(self):
        self.assertTrue(all(tr.DE.search(w) for w in ("Dialektik", "das Allgemeine", "Besonderheit", "Geist", "sittliche", "Negation", "vermittelt",
                                                      "aufheben", "Wirklichkeit", "absolut", "Substanz", "abstrakt", "Begriff", "die Idee",
                                                      "bürgerliche Gesellschaft", "System der Bedürfnisse")))
        self.assertIsNone(tr.DE.search("Guten Morgen, meine liebe! Wir haben Cotelets gegessen und eine Bouteille Wein getrunken."))


if __name__ == "__main__":
    unittest.main()
