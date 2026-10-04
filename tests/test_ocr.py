"""Tests for tools/ocr.py: the letters of a Fraktur print, the running heads taken off, the chapters marked. No Tesseract needed."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import ocr  # noqa: E402


class NormalizeTest(unittest.TestCase):
    def test_the_letters_of_the_print_become_modern_ones(self):
        self.assertEqual(ocr.normalize("Geburtsſtätte aͤ uͤber läͤßt Hof⸗Rath"), "Geburtsstätte ä über läßt Hof-Rath")

    def test_a_word_broken_at_a_line_end_keeps_a_plain_hyphen(self):
        self.assertEqual(ocr.normalize("Philo—\nsophie und Frank=\nfurt"), "Philo-\nsophie und Frank-\nfurt")

    def test_a_one_inside_a_word_is_an_i_but_numbers_stay(self):
        self.assertEqual(ocr.normalize("a pun1shment 1s not 1831, nor 3,1 or 1."), "a punishment is not 1831, nor 3,1 or 1.")

    def test_a_smudge_read_as_a_hash_is_no_heading(self):
        self.assertEqual(ocr.normalize("#® repulsion for that\n## x"), "repulsion for that\nx")


class AssembleTest(unittest.TestCase):
    def test_rules_and_smudges_are_not_text(self):
        for line in ("en i, re ——————— — i ——————— a — _ - —", "*«", "+ >"):
            self.assertTrue(ocr.rule(line), line)
        for line in ("Philo-", "gegen die Philosophie —, so", "„Molitor, von dem ich", "1785 Sonntags den 26. Juni."):
            self.assertFalse(ocr.rule(line), line)

    def test_misreadings_of_one_heading_are_one_heading(self):
        self.assertTrue(ocr.same("Hegel's Verheirathung, Herbst 1811", "Hegel's Verheirathung, Herbst 181I"))
        self.assertTrue(ocr.same("Urkunden", "Arkunden"))
        self.assertFalse(ocr.same("Fragmente theologischer Studien", "Fragmente historischer Studien"))
        self.assertFalse(ocr.same("machen", "Umgang"))

    def test_running_heads_go_and_chapters_are_marked_where_they_begin(self):
        pages = [
            "Herkunft.\n\nDie Familie stammt aus Kärnthen.",
            "4 Erstes Buch.\n\nund blieb im Bürgerstande.",
            "Herkunft. 5\n\nNoch der Pfarrer war ein Hegel.\n\nDas Gymnasium.\n\nIn Stuttgart besuchte er das Gymnasium.",
            "6 Erstes Buch.\n\nEr las viel.",
            "Das Gymnasium. 7\n\nUnd schrieb Auszüge.",
            "8 Erstes Buch.\n\nAus der Schulzeit.",
            "Das Gymnasinm. 9\n\nEr blieb fleißig.",
        ]
        text = ocr.assemble(pages)
        self.assertNotIn("Erstes Buch", text)                     # the left-hand head names the book: it marks nothing
        self.assertNotIn(" 5", text)
        self.assertEqual([x for x in text.split("\n\n") if x.startswith("@@ ")], ["@@ Herkunft", "@@ Das Gymnasium"])
        self.assertLess(text.index("Noch der Pfarrer"), text.index("@@ Das Gymnasium"))      # marked at its own heading, mid-page
        self.assertLess(text.index("@@ Das Gymnasium"), text.index("In Stuttgart"))

    def test_a_head_misread_once_next_to_its_chapter_is_no_new_chapter(self):
        pages = ["Das System. 3\n\nEins.", "4 Erstes Buch.\n\nZwei.", "Das Sysienn. 5\n\nDrei.", "6 Erstes Buch.\n\nVier.",
                 "Das System. 7\n\nFünf.", "8 Erstes Buch.\n\nSechs.", "Das System. 9\n\nSieben."]
        marks = [x for x in ocr.assemble(pages).split("\n\n") if x.startswith("@@ ")]
        self.assertEqual(marks, ["@@ Das System"])

    def test_a_numbered_section_heading_is_read_as_its_heading(self):
        pages = ["I.\nTagebuch.\n\nSonntags.", "Tagebuch. 3\n\nMontags.", "4 Urkunden.\n\nDienstags.", "Tagebuch. 5\n\nMittwochs.",
                 "II.\nAuszüge.\n\nEines.", "Auszüge. 7\n\nZweites."]
        marks = [x for x in ocr.assemble(pages).split("\n\n") if x.startswith("@@ ")]
        self.assertEqual(marks, ["@@ Tagebuch", "@@ Auszüge"])


if __name__ == "__main__":
    unittest.main()
