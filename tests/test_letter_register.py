"""HEGEL_LETTER_REGISTER (DECISIONS 60): the writing request carries a short block on how a private letter is written. Off, the request is
the request it was."""
import unittest

from world import works
from world.config import Config


class LetterRegisterTest(unittest.TestCase):
    def test_off_by_default_and_off_unchanged(self):
        self.assertFalse(Config({}).letter_register)
        self.assertTrue(Config({"HEGEL_LETTER_REGISTER": "1"}).letter_register)
        st = {"works": []}
        self.assertEqual(works.ask(st), works.ask(st, letter_register=False))
        self.assertNotIn("sharp-eyed traveller", works.ask(st))

    def test_on_the_block_comes_before_the_format(self):
        on = works.ask({"works": []}, letter_register=True)
        self.assertIn(works.LETTER_REGISTER, on)
        self.assertTrue(on.endswith(works.WRITE_FORMAT))
        self.assertIn("never as the subject", on)


if __name__ == "__main__":
    unittest.main()
