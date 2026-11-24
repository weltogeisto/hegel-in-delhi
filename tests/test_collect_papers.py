"""tools/collect_papers.py: one day's papers into a folder of their own, for a rehearsal's archive."""
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

from tools import collect_papers as cp

RSS = "<rss><channel><title>The Daily Test</title>{}</channel></rss>".format("".join(
    f"<item><title>A matter of the day, number {i}, at some length</title><description>Body {i}.</description>"
    f"<link>https://example.test/{i}</link></item>" for i in range(5)))


class CollectTest(unittest.TestCase):
    def test_it_keeps_every_piece_of_the_pass_in_its_own_folder_and_fetches_a_day_once(self):
        with tempfile.TemporaryDirectory() as td:
            with mock.patch("world.feeds.get", return_value=RSS.encode()) as get:
                heads, pieces = cp.collect(td, date(2026, 11, 26), "https://example.test/rss")
                self.assertEqual((len(heads), len(pieces), get.call_count), (3, 5, 1))
                self.assertEqual(pieces[4], {"title": "A matter of the day, number 4, at some length", "summary": "Body 4.",
                                             "link": "https://example.test/4", "source": "The Daily Test"})
                cp.collect(td, date(2026, 11, 26), "https://example.test/rss")
                self.assertEqual(get.call_count, 1)                                  # the day is there: not fetched again
            kept = json.loads((Path(td) / "feeds/papers-2026-11-26.json").read_text(encoding="utf-8"))
            self.assertEqual(len(kept), 5)

    def test_the_command_line_says_what_it_kept_and_fails_when_nothing_came(self):
        with tempfile.TemporaryDirectory() as td:
            with mock.patch("world.feeds.get", return_value=RSS.encode()):
                self.assertEqual(cp.main(["--state", td, "--date", "2026-11-26", "--feeds", "https://example.test/rss"]), 0)
            with mock.patch("world.feeds.get", side_effect=OSError("down")):
                self.assertEqual(cp.main(["--state", td, "--date", "2026-11-27", "--feeds", "https://example.test/rss"]), 1)


if __name__ == "__main__":
    unittest.main()
