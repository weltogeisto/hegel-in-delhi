"""HEGEL_PAPERS_BODY (pc/PAPERS.md): with the record, the text of a piece the paper itself marks free to read is kept in the state folder and
shown to him; never of a piece not marked free; never in the day file. Pages are patched: no network."""
import json
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_papers import D, PIECES, run, setup  # noqa: E402
from test_world import Sandbox  # noqa: E402

from tools import collect_papers as cp  # noqa: E402
from world import contract, papers  # noqa: E402
from world.config import Config  # noqa: E402
from world.feeds import Feeds, body_of  # noqa: E402

LONG = "".join(f"Sentence number {i} of the long report on the matter. " for i in range(80))      # about 4000 characters, whole sentences


def page(free=True, body=LONG, wrap="object"):
    art = {"@type": "NewsArticle", "headline": "x", "articleBody": body}
    if free is not None:
        art["isAccessibleForFree"] = free
    if wrap == "graph":
        art = {"@context": "https://schema.org", "@graph": [{"@type": "WebPage"}, art]}
    elif wrap == "list":
        art = [{"@type": "Organization"}, art]
    return ('<html><script type="application/ld+json">{not json</script><script type="application/ld+json">'
            + json.dumps(art) + "</script></html>").encode()


def rss(n, lo=0, source="The Daily Test"):
    return ("<rss><channel><title>%s</title>%s</channel></rss>" % (source, "".join(
        f"<item><title>A matter of the day, number {i}, at some length</title><description>Summary {i}.</description>"
        f"<link>https://example.test/{i}</link></item>" for i in range(lo, lo + n)))).encode()


def links(n, **kw):
    return {f"https://example.test/{i}": page(**kw) for i in range(n)}


class Body(unittest.TestCase):
    def feeds(self, n=3, **sets):
        box = Sandbox()
        self.addCleanup(box.close)
        self.n, self.nfeeds = n, -(-n // 5)
        self.cfg = Config({"HEGEL_PUSH": "0", "HEGEL_STATE": str(box.tmp / "state"), "HEGEL_FEEDS": "1", "NEWS_FEEDS": ",".join(f"https://example.test/rss{k}" for k in range(self.nfeeds)),
                           "HEGEL_PAPERS_RECORD": "1", "HEGEL_PAPERS_BODY": "1", **sets})
        return Feeds(self.cfg)

    def run_day(self, f, pages):
        """Headlines for D, the pages given by link (bytes, or an exception to raise); the headlines and the pieces kept."""
        def get(url, timeout=15):
            if url.startswith("https://example.test/rss"):       # a feed keeps six at most: more pieces come from more feeds
                k = int(url[-1])
                return rss(min(self.n - 5 * k, 5), 5 * k)
            got = pages[url]
            if isinstance(got, Exception):
                raise got
            return got
        with mock.patch("world.feeds.get", side_effect=get) as g, mock.patch("world.feeds.time.sleep") as sleep:
            heads = f.headlines(D)
        self.g, self.sleep = g, sleep
        return heads, f.pieces(D)

    def test_a_free_article_gives_a_body_cut_at_a_sentence_end(self):
        heads, pieces = self.run_day(self.feeds(), links(3))
        self.assertEqual(len(heads), 3)
        for p in pieces:
            self.assertTrue(p["free"])
            self.assertTrue(1500 < len(p["body"]) <= 1800)
            self.assertTrue(p["body"].endswith("matter."), p["body"][-20:])
            self.assertEqual(p["summary"][:7], "Summary")
        self.assertEqual([c.args for c in self.sleep.call_args_list], [(1.5,), (1.5,)])      # a pause between pages, none before the first

    def test_only_what_the_paper_marks_free(self):
        for free in (False, "False", "false", None):
            _, pieces = self.run_day(self.feeds(), links(3, free=free))
            self.assertTrue(all("body" not in p and "free" not in p for p in pieces), free)
        for free in (True, "True", "true"):
            _, pieces = self.run_day(self.feeds(), links(3, free=free))
            self.assertTrue(all(p.get("body") for p in pieces), free)

    def test_one_article_saying_not_free_is_enough(self):
        both = [{"@type": "NewsArticle", "articleBody": LONG, "isAccessibleForFree": "True"},
                {"@type": "Article", "isAccessibleForFree": "False"}]
        self.assertIsNone(body_of('<script type="application/ld+json">' + json.dumps(both) + "</script>"))

    def test_graph_and_list_forms_are_read(self):
        for wrap in ("graph", "list"):
            got = body_of(page(wrap=wrap).decode())
            self.assertTrue(got and got.endswith("matter."), wrap)

    def test_the_body_is_made_plain(self):
        got = body_of(page(body="  Fish &amp; chips,\n\n <b>and</b>   more. " * 30).decode())
        self.assertIn("Fish & chips, and more.", got)
        for bad in ("&amp;", "<b>", "  ", "\n"):
            self.assertNotIn(bad, got)

    def test_a_failing_page_a_missing_block_or_a_short_body_gives_none_and_the_rest_are_kept(self):
        pages = {"https://example.test/0": OSError("down"), "https://example.test/1": b"<html>no block</html>",
                 "https://example.test/2": page(body="Too short to count."), "https://example.test/3": page()}
        heads, pieces = self.run_day(self.feeds(4), pages)
        self.assertEqual((len(heads), len(pieces)), (3, 4))
        self.assertEqual([bool(p.get("body")) for p in pieces], [False, False, False, True])
        self.assertTrue(all(p["summary"] for p in pieces))

    def test_at_most_twelve_pages_and_a_cached_day_is_not_fetched_again(self):
        f = self.feeds(15)
        pages = links(15)
        _, pieces = self.run_day(f, pages)
        self.assertEqual(self.g.call_count, 3 + 12)               # the three feeds, then twelve pages
        self.assertEqual(sum(1 for p in pieces if p.get("body")), 12)
        self.assertEqual(self.sleep.call_count, 11)
        self.run_day(Feeds(self.cfg), pages)
        self.assertEqual(self.g.call_count, 0)                    # the day is cached: nothing at all
        self.assertEqual(len(f.pieces(D)), 15)

    def test_off_no_page_is_fetched_and_the_pieces_are_as_today(self):
        _, pieces = self.run_day(self.feeds(HEGEL_PAPERS_BODY="0"), {})
        self.assertEqual(self.g.call_count, 1)
        self.assertEqual([sorted(p) for p in pieces], [["link", "source", "summary", "title"]] * 3)

    def test_the_switch_without_the_record_does_nothing(self):
        _, pieces = self.run_day(self.feeds(HEGEL_PAPERS_RECORD="0"), {})
        self.assertEqual((self.g.call_count, pieces), (1, []))


class Reading(unittest.TestCase):
    WITH = [dict(PIECES[0], body="BODYMARKER-ONE the court heard the pleas at length, and the hills were weighed. " * 3, free=True),
            PIECES[1],
            dict(PIECES[2], body="BODYMARKER-THREE the rupee closed flat on the day. " * 3, free=True)]

    def go(self, steps=4):
        box, e, mind, day = setup(pieces=self.WITH)
        self.addCleanup(box.close)
        return e, mind, day, run(e, day, steps)

    def test_he_is_shown_the_body_and_a_piece_without_one_shows_its_summary(self):
        e, mind, day, steps = self.go()
        self.assertIn("BODYMARKER-ONE", contract.render(mind.sits[1]))
        self.assertNotIn("ZEBRAQUARTZ ", contract.render(mind.sits[1]))
        self.assertIn("ZEBRAQUARTZ-TWO", contract.render(mind.sits[2]))
        self.assertIn("BODYMARKER-THREE", contract.render(mind.sits[3]))
        self.assertEqual([s["read"]["title"] for s in steps[:3]], [p["title"] for p in PIECES])      # the order is the papers'

    def test_the_body_counts_as_met_and_the_day_file_holds_no_body_text(self):
        e, mind, day, steps = self.go()
        met = papers.read_text(day["state"]["readings"], e.world.feeds)
        self.assertIn("BODYMARKER-ONE", met)
        self.assertIn("ZEBRAQUARTZ-TWO", met)
        text = json.dumps(day, ensure_ascii=False) + json.dumps(steps, ensure_ascii=False)
        self.assertNotIn("BODYMARKER", text)
        for p in self.WITH:
            self.assertNotIn((p.get("body") or p["summary"])[:40], text)

    def test_a_rehearsal_archive_gives_the_pieces_as_stored_body_and_all(self):
        with tempfile.TemporaryDirectory() as td:
            (Path(td) / "papers-2026-11-20.json").write_text(json.dumps(self.WITH), encoding="utf-8")
            cfg = Config({"HEGEL_PUSH": "0", "HEGEL_STATE": td + "/state", "HEGEL_PAPERS": "1", "HEGEL_PAPERS_ARCHIVE": td})
            self.assertEqual(Feeds(cfg).piece(date(2026, 12, 1), 0), self.WITH[0])


class Collector(unittest.TestCase):
    def test_body_sets_the_switch_for_its_own_run_and_the_line_counts_bodies(self):
        def get(url, timeout=15):
            return rss(3) if url.endswith("rss") else page()
        for flag, want in ((["--body"], 3), ([], 0)):
            with tempfile.TemporaryDirectory() as td, mock.patch("world.feeds.get", side_effect=get), \
                    mock.patch("world.feeds.time.sleep"), mock.patch("builtins.print") as pr:
                self.assertEqual(cp.main(["--state", td, "--date", "2026-11-26", "--feeds", "https://example.test/rss", *flag]), 0)
                self.assertEqual(json.loads(pr.call_args.args[0])["with_body"], want)
                kept = json.loads((Path(td) / "feeds/papers-2026-11-26.json").read_text(encoding="utf-8"))
                self.assertEqual(sum(1 for p in kept if p.get("body")), want)


if __name__ == "__main__":
    unittest.main()
