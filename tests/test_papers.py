"""HEGEL_PAPERS_RECORD and HEGEL_PAPERS (pc/PAPERS.md): the day's papers kept in full in the state folder; `read` at home gives him the next
piece; the day file never holds a newspaper's text; his own line after each piece is kept; a story that runs on is marked once; what he read
counts as met. Off, none of it happens."""
import json
import sys
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_economy import There  # noqa: E402
from test_world import Sandbox, answer  # noqa: E402

from world import contract, papers  # noqa: E402
from world.config import Config  # noqa: E402
from world.engine import Engine  # noqa: E402
from world.feeds import Feeds  # noqa: E402
from world.mind import StubMind  # noqa: E402
from world.world import World, at_dt  # noqa: E402

D = date(2026, 11, 24)
PIECES = [
    {"title": "Supreme Court reserves verdict on the Aravalli mining pleas", "source": "The Hindu", "link": "https://example.test/a",
     "summary": "ZEBRAQUARTZ the bench heard the last of the arguments on mining in the Aravalli hills. The verdict will follow in weeks."},
    {"title": "Delhi air quality turns severe as stubble smoke drifts in", "source": "Indian Express", "link": "https://example.test/b",
     "summary": "ZEBRAQUARTZ-TWO readings crossed four hundred at several stations."},
    {"title": "Rupee steadies against the dollar after central bank remarks", "source": "The Hindu", "link": "https://example.test/c",
     "summary": "ZEBRAQUARTZ-THREE the currency closed little changed."},
]
THOUGHTS = ["The court weighs the hills against the quarries; reason hesitates here. And I have more to say of it.",
            "Smoke over the city is a nature that does not obey the law, I think, and I breathe it all the same.",
            "A rupee that steadies is a certainty that the market grants only for a day, as it seems to me.",
            "Nothing more is left on the table, and the tea has gone cold while the hills and the smoke and the coin were weighed."]


class Reader(StubMind):
    """A mind that reads at home, with a thought for each step; the thoughts it gives are kept."""
    source = "stub"

    def __init__(self, thoughts=THOUGHTS):
        self.thoughts, self.n, self.sits = list(thoughts), 0, []

    def decide(self, messages, sit):
        self.sits.append(sit)
        thought = self.thoughts[self.n] if self.n < len(self.thoughts) else f"Another quiet reflection number {self.n}, wholly unlike the last."
        self.n += 1
        return json.dumps(answer(action="read", place="home", minutes=30, thought=thought))


def keep(box, d=D, pieces=PIECES, news=True):
    """The papers of day d as the record would have kept them, and their headlines."""
    feeds = box.cfg.state / "feeds"
    feeds.mkdir(parents=True, exist_ok=True)
    (feeds / f"papers-{d.isoformat()}.json").write_text(json.dumps(pieces), encoding="utf-8")
    if news:
        (feeds / f"news-{d.isoformat()}.json").write_text(json.dumps([p["title"] for p in pieces]), encoding="utf-8")


def setup(on=True, mind=None, d=D, pieces=PIECES, **sets):
    """(sandbox, engine, mind, day) with him at home, awake at nine, and the papers of the day kept."""
    box = Sandbox()
    box.cfg = Config({"HEGEL_PUSH": "0", "HEGEL_STATE": str(box.tmp / "state"), "HEGEL_FEEDS": "0", "HEGEL_PAPERS": "1" if on else "0", **sets})
    box.cfg.docs = box.tmp / "docs"
    keep(box, d, pieces)
    mind = mind or Reader()
    e = Engine(box.cfg, World(Feeds(box.cfg), papers=on), mind)
    prev = box.days.load(date(2026, 10, 2))
    prev["state"]["asleep"] = False
    day = e.new_day(prev, d)
    day["state"].update(place="home", today={"woke": "06:00"})
    return box, e, mind, day


def run(e, day, steps, d=D, start=9 * 60):
    """Steps of thirty minutes from `start`, at home; the steps returned."""
    out = []
    with There(home=[]):
        for i in range(steps):
            out.append(e.step(day, at_dt(d, start + 30 * i)))
    return out


class Record(unittest.TestCase):
    RSS = "<rss><channel><title>The Daily Test</title>{}</channel></rss>".format("".join(
        f"<item><title>{p['title']}</title><description>&lt;p&gt;{p['summary']}  &lt;b&gt;more&lt;/b&gt;&lt;/p&gt;</description>"
        f"<link>{p['link']}</link></item>" for p in PIECES))

    def headlines(self, **sets):
        box = Sandbox()
        self.addCleanup(box.close)
        cfg = Config({"HEGEL_PUSH": "0", "HEGEL_STATE": str(box.tmp / "state"), "HEGEL_FEEDS": "1", "NEWS_FEEDS": "https://example.test/rss", **sets})
        f = Feeds(cfg)
        with mock.patch("world.feeds.get", return_value=self.RSS.encode()) as get:
            got = f.headlines(D)
        return f, got, cfg, get

    def test_recording_keeps_the_pieces_of_the_same_headlines_from_one_download(self):
        f, got, cfg, get = self.headlines(HEGEL_PAPERS_RECORD="1")
        self.assertEqual(got, [p["title"] for p in PIECES])
        self.assertEqual(get.call_count, 1)
        kept = json.loads((cfg.state / "feeds/papers-2026-11-24.json").read_text(encoding="utf-8"))
        self.assertEqual([k["title"] for k in kept], got)
        self.assertEqual(kept[0]["link"], "https://example.test/a")
        self.assertEqual(kept[0]["source"], "The Daily Test")
        self.assertNotIn("<", kept[0]["summary"])
        self.assertIn("more", kept[0]["summary"])
        self.assertNotIn("  ", kept[0]["summary"])

    def test_the_inside_pages_are_kept_too(self):
        more = [{"title": f"A fifth and further matter of the day, number {i} of them", "summary": f"Body {i}.", "link": f"https://example.test/{i}"}
                for i in range(2)]
        rss = "<rss><channel><title>The Daily Test</title>{}</channel></rss>".format("".join(
            f"<item><title>{p['title']}</title><description>{p['summary']}</description><link>{p['link']}</link></item>" for p in PIECES + more))
        box = Sandbox()
        self.addCleanup(box.close)
        cfg = Config({"HEGEL_PUSH": "0", "HEGEL_STATE": str(box.tmp / "state"), "HEGEL_FEEDS": "1", "NEWS_FEEDS": "https://example.test/rss",
                      "HEGEL_PAPERS_RECORD": "1"})
        with mock.patch("world.feeds.get", return_value=rss.encode()):
            got = Feeds(cfg).headlines(D)
        kept = json.loads((cfg.state / "feeds/papers-2026-11-24.json").read_text(encoding="utf-8"))
        self.assertEqual(got, [p["title"] for p in PIECES])                     # he is shown three
        self.assertEqual([k["title"] for k in kept], [p["title"] for p in PIECES + more])      # and may read on through five

    def test_a_long_summary_is_cut_at_a_sentence_end(self):
        long = " ".join(f"Sentence number {i} of the report." for i in range(60))
        rss = self.RSS.replace(PIECES[0]["summary"], long)
        box = Sandbox()
        self.addCleanup(box.close)
        cfg = Config({"HEGEL_PUSH": "0", "HEGEL_STATE": str(box.tmp / "state"), "HEGEL_FEEDS": "1", "NEWS_FEEDS": "https://example.test/rss",
                      "HEGEL_PAPERS_RECORD": "1"})
        with mock.patch("world.feeds.get", return_value=rss.encode()):
            Feeds(cfg).headlines(D)
        s = json.loads((cfg.state / "feeds/papers-2026-11-24.json").read_text(encoding="utf-8"))[0]["summary"]
        self.assertLessEqual(len(s), 600)
        self.assertTrue(s.endswith("report."), s[-20:])

    def test_off_the_headlines_are_the_same_and_no_pieces_are_kept(self):
        f, got, cfg, get = self.headlines()
        on, got_on, _, _ = self.headlines(HEGEL_PAPERS_RECORD="1")
        self.assertEqual(got, got_on)
        self.assertEqual(sorted(p.name for p in (cfg.state / "feeds").iterdir()), ["news-2026-11-24.json"])
        self.assertEqual(json.loads((cfg.state / "feeds/news-2026-11-24.json").read_text(encoding="utf-8")), got)


class Reading(unittest.TestCase):
    def tearDown(self):
        for box in getattr(self, "boxes", []):
            box.close()

    def go(self, steps=4, **kw):
        box, e, mind, day = setup(**kw)
        self.boxes = getattr(self, "boxes", []) + [box]
        return box, e, mind, day, run(e, day, steps)

    def test_read_at_home_gives_the_next_unread_piece_and_then_behaves_as_before(self):
        box, e, mind, day, steps = self.go(5)
        self.assertEqual([s["read"]["title"] for s in steps[:3]], [p["title"] for p in PIECES])
        self.assertNotIn("read", steps[3])                    # the papers are read: `read` is as it was
        self.assertEqual(day["state"]["today"]["papers_read"], [0, 1, 2])
        for i in (1, 2, 3, 4):                                # a piece opens the next moment, with its summary in his prompt
            self.assertEqual("read" in steps[i]["opened"], i < 4)
        self.assertIn("ZEBRAQUARTZ ", contract.render(mind.sits[1]))
        self.assertIn("ZEBRAQUARTZ-TWO", contract.render(mind.sits[2]))
        self.assertIn("ZEBRAQUARTZ-THREE", contract.render(mind.sits[3]))
        self.assertNotIn("ZEBRAQUARTZ", contract.render(mind.sits[4]))
        self.assertIn("The Hindu", steps[1]["event"])

    def test_off_a_read_returns_nothing(self):
        box, e, mind, day, steps = self.go(2, on=False)
        self.assertTrue(all("read" not in s for s in steps))
        self.assertNotIn("readings", day["state"])
        self.assertNotIn("papers_read", day["state"]["today"])

    def test_away_from_home_he_has_no_papers(self):
        box, e, mind, day = setup()
        self.boxes = [box]
        day["state"]["place"] = "khan"
        with There(khan=[]):
            step = e.step(day, at_dt(D, 9 * 60))
        self.assertNotIn("read", step)

    def test_the_day_file_holds_no_newspaper_text(self):
        box, e, mind, day, steps = self.go(4)
        text = json.dumps(day, ensure_ascii=False)
        for p in PIECES:
            self.assertNotIn("ZEBRAQUARTZ", text)
            self.assertNotIn(p["summary"][:40], text)
        entry = next(x for x in day["entries"] if x["k"] == "read")
        self.assertEqual((entry["title"], entry["source"], entry["url"], entry["date"], entry["i"]),
                         (PIECES[0]["title"], "The Hindu", "https://example.test/a", "2026-11-24", 0))

    def test_the_trace_takes_his_line_from_the_next_thought(self):
        box, e, mind, day, steps = self.go(4)
        r = day["state"]["readings"]            # the thought of each step that opened with a piece
        self.assertEqual([x["title"] for x in r], [p["title"] for p in PIECES])
        self.assertEqual(r[0]["line"], "Smoke over the city is a nature that does not obey the law, I think, and I breathe it all the same.")
        self.assertEqual(r[2]["line"], "Nothing more is left on the table, and the tea has gone cold while the hills and the smoke and the coin were weighed.")
        self.assertEqual({k: r[0][k] for k in ("date", "title", "source")}, {"date": "2026-11-24", "title": PIECES[0]["title"], "source": "The Hindu"})

    def test_first_line_and_keep(self):
        self.assertEqual(papers.first_line("One. Two."), "One.")
        self.assertLessEqual(len(papers.first_line("word " * 100)), 160)
        st = {}
        for i in range(45):
            papers.trace(st, {"date": "2026-11-24", "title": f"t{i}", "source": "s", "piece": ["2026-11-24", 0]}, "A line.")
        self.assertEqual((len(st["readings"]), st["readings"][0]["title"]), (40, "t5"))

    def test_what_he_read_is_met_and_among_the_manuscripts(self):
        box, e, mind, day, steps = self.go(4)
        known = e.memory.known_text(day, {"day": "x", "time": "t", "place": "home", "weather": "", "aqi": 0, "outfit": "", "imprest_left": 0,
                                          "present": [], "open_now": [], "event": ""})
        self.assertIn("ZEBRAQUARTZ-THREE", known)
        self.assertIn(PIECES[1]["title"], known)
        block = e.memory.manuscripts(day)
        self.assertIn("What you have read lately:", block)
        self.assertIn("Smoke over the city", block)
        self.assertNotIn("ZEBRAQUARTZ", block)
        self.assertEqual(block.count("\n- "), 3)

    def test_off_nothing_is_added_to_known_text_or_manuscripts(self):
        box, e, mind, day, steps = self.go(2, on=False)
        day["state"]["readings"] = [{"date": "2026-11-23", "title": "Odd Title", "source": "s", "line": "L.", "piece": ["2026-11-24", 0]}]
        self.assertEqual(e.memory.manuscripts(day), "")
        self.assertNotIn("ZEBRAQUARTZ", e.memory.known_text(day, mind.sits[0]))

    def test_the_waking_line_says_the_papers_can_be_read_once(self):
        box, e, mind, day = setup()
        self.boxes = [box]
        day["state"].update(asleep=True, today={})
        sit, ctx = e.world.situation(at_dt(D, 6 * 60), day["state"], day)
        self.assertIn("Headlines: " + "; ".join(p["title"] for p in PIECES) + ". ", sit["event"])
        self.assertEqual(sit["event"].count("verandah table") + sit["event"].count("on the step, there to be read"), 1)
        self.assertEqual(ctx["opened"][0], "papers")
        self.assertNotIn("story", ctx["opened"])
        off, e2, _, day2 = setup(on=False)
        self.boxes.append(off)
        day2["state"].update(asleep=True, today={})
        sit2, _ = e2.world.situation(at_dt(D, 6 * 60), day2["state"], day2)
        self.assertNotIn("papers are on", sit2["event"])

    def test_a_story_that_runs_on_is_marked_once_with_his_line(self):
        tomorrow = D + timedelta(days=1)
        later = [{"title": "Aravalli mining verdict awaited as the Supreme Court bench rises", "source": "The Hindu", "link": "x", "summary": "s"},
                 {"title": "Aravalli mining case: Supreme Court hears the plea again", "source": "The Hindu", "link": "y", "summary": "s"},
                 {"title": "Metro fares to rise from December", "source": "The Hindu", "link": "z", "summary": "s"}]
        box, e, mind, day = setup()
        self.boxes = [box]
        run(e, day, 4)
        keep(box, tomorrow, later)
        st = day["state"]
        st.update(asleep=True, today={})
        sit, ctx = e.world.situation(at_dt(tomorrow, 6 * 60), st, day)
        note = '(You read of this on 24 November: "' + st["readings"][0]["line"] + '")'
        self.assertEqual(sit["event"].count("You read of this on"), 1)           # two headlines continue it; one note
        self.assertIn(later[0]["title"] + " " + note + ";", sit["event"])
        self.assertEqual(ctx["opened"][:2], ["papers", "story"])
        self.assertNotIn("You read of this", json.dumps(day["entries"]))         # the public entry carries the headlines only

    def test_a_story_needs_two_words_and_fourteen_days(self):
        reading = [{"date": "2026-11-10", "title": "Aravalli mining verdict", "line": "L.", "source": "s"}]
        self.assertIsNone(papers.story(reading, ["Aravalli rally in Gurugram"], date(2026, 11, 12)))
        self.assertIsNone(papers.story(reading, ["Aravalli mining verdict again"], date(2026, 11, 25)))
        self.assertEqual(papers.story(reading, ["Aravalli mining verdict again"], date(2026, 11, 24))[0], 0)

    def test_off_a_continuing_story_is_not_marked(self):
        box, e, mind, day = setup(on=False)
        self.boxes = [box]
        day["state"].update(asleep=True, today={}, readings=[{"date": "2026-11-23", "title": PIECES[0]["title"], "line": "L.", "source": "s"}])
        sit, ctx = e.world.situation(at_dt(D, 6 * 60), day["state"], day)
        self.assertNotIn("You read of this", sit["event"])
        self.assertNotIn("story", ctx["opened"])


class Archive(unittest.TestCase):
    def test_a_rehearsal_reads_the_archive_by_the_days_since_its_first_day(self):
        box = Sandbox()
        self.addCleanup(box.close)
        arch = box.tmp / "archive"
        arch.mkdir()
        for name in ("2026-11-01", "2026-11-02", "2026-11-03"):
            (arch / f"papers-{name}.json").write_text(json.dumps([{"title": "Title of " + name, "summary": "s", "link": "l", "source": "S"}]))
        cfg = Config({"HEGEL_PUSH": "0", "HEGEL_STATE": str(box.tmp / "state"), "HEGEL_FEEDS": "0", "HEGEL_PAPERS": "1",
                      "HEGEL_PAPERS_ARCHIVE": str(arch), "HEGEL_PAPERS_FROM": "2026-11-30"})
        f = Feeds(cfg)
        titles = [f.pieces(date(2026, 11, 30) + timedelta(days=i))[0]["title"] for i in range(5)]
        self.assertEqual(titles, ["Title of 2026-11-01", "Title of 2026-11-02", "Title of 2026-11-03", "Title of 2026-11-01", "Title of 2026-11-02"])
        self.assertEqual(f.headlines(date(2026, 12, 1)), ["Title of 2026-11-02"])      # the archive's titles are the headlines of a day with no feed

    def test_without_the_switch_or_the_folder_the_archive_is_not_read(self):
        box = Sandbox()
        self.addCleanup(box.close)
        arch = box.tmp / "archive"
        arch.mkdir()
        (arch / "papers-2026-11-01.json").write_text(json.dumps([{"title": "T", "summary": "s", "link": "l", "source": "S"}]))
        for sets in ({"HEGEL_PAPERS_ARCHIVE": str(arch)}, {"HEGEL_PAPERS": "1"}):
            f = Feeds(Config({"HEGEL_PUSH": "0", "HEGEL_STATE": str(box.tmp / "state"), "HEGEL_FEEDS": "0", **sets}))
            self.assertEqual((f.pieces(D), f.headlines(D)), ([], []))

    def test_a_rehearsal_start_names_the_first_day(self):
        from world.__main__ import rehearsal_setup
        box = Sandbox()
        self.addCleanup(box.close)
        cfg = Config({"HEGEL_PUSH": "0", "HEGEL_STATE": str(box.tmp / "state")})
        cfg.docs = box.tmp / "docs"
        sim = rehearsal_setup(cfg, "2026-10-05", box.tmp / "rehearsal", sets={"HEGEL_PAPERS_ARCHIVE": "/x"})
        self.assertEqual(sim.get("HEGEL_PAPERS_FROM"), "2026-10-05")


if __name__ == "__main__":
    unittest.main()
