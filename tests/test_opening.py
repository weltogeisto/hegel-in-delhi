"""The page for opening night: sharing tags, the image they point to, "Previously" and the about panel."""
import re
import struct
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PAGE = (REPO / "docs/index.html").read_text(encoding="utf-8")
SITE = "https://weltogeisto.github.io/hegel-in-delhi/"


def meta(attr, key):
    m = re.search(rf'<meta {attr}="{re.escape(key)}" content="([^"]*)">', PAGE)
    return m.group(1) if m else None


class SharingTest(unittest.TestCase):
    def test_a_shared_link_has_a_title_a_line_and_a_picture(self):
        self.assertEqual(meta("property", "og:title"), "Hegel in Delhi")
        self.assertEqual(meta("property", "og:url"), SITE)
        self.assertEqual(meta("property", "og:image"), SITE + "og.png")
        self.assertEqual(meta("name", "twitter:card"), "summary_large_image")
        self.assertEqual(meta("name", "twitter:image"), SITE + "og.png")
        line = meta("name", "description")
        self.assertTrue(line.startswith("G. W. F. Hegel, fifty, wakes up in a Lutyens bungalow"))
        self.assertEqual(meta("property", "og:description"), line)
        self.assertLessEqual(len(line), 200)

    def test_the_picture_is_there_and_the_size_the_tags_say(self):
        head = (REPO / "docs/og.png").read_bytes()[:24]
        self.assertEqual(head[:8], b"\x89PNG\r\n\x1a\n")
        self.assertEqual(struct.unpack(">II", head[16:24]), (1200, 630))
        self.assertEqual((meta("property", "og:image:width"), meta("property", "og:image:height")), ("1200", "630"))


class PreviouslyTest(unittest.TestCase):
    def test_previously_opens_the_today_tab_only(self):
        self.assertIn("html = (tab === 'today' ? previouslyHtml() : '')", PAGE)
        self.assertEqual(len(re.findall(r"(?<!function )previouslyHtml\(\)", PAGE)), 1)          # called in one place

    def test_it_quotes_the_owl_and_is_not_shown_on_an_old_day(self):
        body = PAGE.split("function previouslyHtml(){")[1].split("\nfunction owlHtml")[0]
        self.assertIn("if (!D || dayMode === 'archive') return '';", body)
        self.assertIn("firstSentences(o.diary)", body)                                   # the owl's own words, cut at a sentence
        self.assertIn("vz(`${prev.date}|owl|diary`", body)                               # a sensitive diary stays under its band


class AboutTest(unittest.TestCase):
    def test_the_about_panel_says_how_to_reach_earlier_days_and_where_the_record_is(self):
        about = PAGE.split('<div class="about">')[1].split("</div>")[0]
        self.assertIn("Use the arrows by the date to read earlier days, Day 1 among them.", about)
        self.assertIn("https://github.com/weltogeisto/hegel-in-delhi", about)
        self.assertIn("When the mind is away, he keeps the household and the page shows no thoughts.", about)
        self.assertIn("the living are invented, the dead are on his shelf, the news is real", about)


if __name__ == "__main__":
    unittest.main()
