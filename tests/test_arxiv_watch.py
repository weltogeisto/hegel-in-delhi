"""The literature watch (tools/arxiv_watch.py), offline: arXiv's answers are made up here, nothing is fetched."""
import importlib.util
import shutil
import tempfile
import unittest
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("arxiv_watch", REPO / "tools" / "arxiv_watch.py")
watch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(watch)


def entry(pid, day, title, summary="An abstract."):
    return (f"<entry><id>http://arxiv.org/abs/{pid}</id><published>{day}T12:00:00Z</published>"
            f"<title>{title}</title><summary>{summary}</summary></entry>")


def atom(*entries):
    return ('<?xml version="1.0" encoding="UTF-8"?><feed xmlns="http://www.w3.org/2005/Atom">'
            + "".join(entries) + "</feed>").encode()


ERROR = "<entry><id>http://arxiv.org/api/errors#incorrect_id_format</id><title>Error</title><summary>bad</summary></entry>"
TOPICS = {"Memory": ["q-memory", "q-broken"], "Belief": ["q-belief"]}
ANSWERS = {
    "q-memory": atom(entry("2611.00001v2", "2026-11-04", "Gist  loses\n time"),
                     entry("2611.00002v1", "2026-11-03", "Already cited"),
                     entry("2610.30000v1", "2026-10-20", "Too old"), ERROR),
    "q-belief": atom(entry("2611.00001v2", "2026-11-04", "Gist loses time"),
                     entry("2611.00003v1", "2026-11-05", "Theses move")),
}


def get(q):
    if q == "q-broken":
        raise OSError("connection reset")
    return ANSWERS[q]


class ArxivWatchTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="hegel-arxiv-"))
        (self.tmp / "watch").mkdir()
        (self.tmp / "NOTES.md").write_text("See [it](https://arxiv.org/abs/2611.00002) and ₹1,234.5678 and 12026.11111.\n")
        self.pauses = []

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_parse_drops_versions_and_error_entries(self):
        got = watch.parse(ANSWERS["q-memory"])
        self.assertEqual([x["id"] for x in got], ["2611.00001", "2611.00002", "2610.30000"])
        self.assertEqual(got[0]["title"], "Gist loses time")
        self.assertEqual(got[0]["date"], "2026-11-04")

    def test_known_reads_notes_and_seen_but_not_other_numbers(self):
        (self.tmp / "watch" / "seen.txt").write_text("2611.00009  2026-11-06  Something\n")
        ids = watch.known(self.tmp / "watch" / "seen.txt", self.tmp)
        self.assertEqual(ids, {"2611.00002", "2611.00009"})

    def test_collect_window_skip_merge_and_failure(self):
        cands, failed = watch.collect(get, TOPICS, date(2026, 10, 28), {"2611.00002"}, sleep=self.pauses.append)
        by_id = {c["id"]: c for c in cands}
        self.assertEqual(set(by_id), {"2611.00001", "2611.00003"})       # too old and already cited are gone
        self.assertEqual(by_id["2611.00001"]["topics"], ["Memory", "Belief"])
        self.assertEqual(failed, [("q-broken", "connection reset")])
        self.assertEqual(len(self.pauses), 2)                              # between three queries, not before the first

    def test_render_and_remember(self):
        cands, failed = watch.collect(get, TOPICS, date(2026, 10, 28), set(), sleep=self.pauses.append)
        text = watch.render(cands, failed, TOPICS, date(2026, 10, 28), date(2026, 11, 6))
        self.assertIn("## Memory", text)
        self.assertIn("[Gist loses time](https://arxiv.org/abs/2611.00001) · 2611.00001 (also: Belief)", text)
        self.assertIn("1 of 3 queries failed", text)
        self.assertLess(text.index("2611.00001"), text.index("2611.00002"))   # newest first
        seen = self.tmp / "watch" / "seen.txt"
        watch.remember(cands, date(2026, 11, 6), seen)
        self.assertEqual(watch.known(seen, self.tmp / "nothing"), {c["id"] for c in cands})

    def test_main_updates_seen_and_fails_only_when_all_fail(self):
        seen, out = self.tmp / "watch" / "seen.txt", self.tmp / "out.md"
        args = ["--today", "2026-11-06", "--out", str(out), "--update-seen", "--seen", str(seen), "--research", str(self.tmp)]
        real = watch.TOPICS
        watch.TOPICS = TOPICS
        try:
            self.assertEqual(watch.main(args, get=get, sleep=self.pauses.append), 0)
            self.assertIn("2611.00003", seen.read_text())
            self.assertNotIn("2611.00002", seen.read_text())             # cited in the notes, so never offered
            self.assertEqual(watch.main(args, get=get, sleep=self.pauses.append), 0)
            self.assertIn("not seen before: 0", out.read_text())         # second run offers nothing new
            down = lambda q: (_ for _ in ()).throw(OSError("offline"))   # noqa: E731
            self.assertEqual(watch.main(args, get=down, sleep=self.pauses.append), 1)
        finally:
            watch.TOPICS = real


if __name__ == "__main__":
    unittest.main()
