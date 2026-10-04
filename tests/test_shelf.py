"""Tests for the shelf: cleaning a corpus, splitting it into passages, BM25 and the English-German table, the section in the prompt,
the shelf in the decisions, the line on the page, and the real shelf (its manifest, its speed, five situations)."""
import gzip
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from test_world import REPO, Sandbox  # noqa: E402  (this also keeps the tests off the Pi's env file)

import corpus  # noqa: E402
from world import contract, shelf  # noqa: E402
from world.mind import StubMind  # noqa: E402

PAGE = (REPO / "docs/index.html").read_text(encoding="utf-8")
LONG = ("The state is the actuality of the ethical idea, and its sentences run on and on; so that a passage made of them is long enough to be cut. " * 12).strip()


def para(n, word):
    """A paragraph of about n characters of sentences about `word`."""
    out = ""
    while len(out) < n:
        out += f"The {word} is what it is, and the {word} becomes what it is not. "
    return out.strip()


class CleaningTest(unittest.TestCase):
    def clean(self, raw, **spec):
        return corpus.clean(raw, spec)

    def test_gutenberg_licence_italics_and_footnote_marks_go(self):
        raw = "Header\n*** START OF THE PROJECT GUTENBERG EBOOK X ***\n\nThe _Notion_ is free[11] and moves.\n\n*** END OF THE PROJECT GUTENBERG EBOOK X ***\nLicence"
        out = self.clean(raw, gutenberg=True)
        self.assertEqual(out.strip(), "The Notion is free and moves.")

    def test_page_numbers_and_running_heads_go_but_the_sentence_is_made_whole(self):
        pages = []
        for i in range(6):
            pages.append(f"and so the second half of sentence {i} goes on to its end here.\n\n{i + 10} THE PHILOSOPHY OF RIGHT.\n\nA new paragraph {i} begins on the next page.\n\n{i + 11}\n\nThe first half of sentence {i} runs until the page")
        out = self.clean("\n\n".join(pages))
        self.assertNotIn("PHILOSOPHY OF RIGHT", out)
        self.assertNotRegex(out, r"\n\n1\d\n\n")
        self.assertIn("The first half of sentence 0 runs until the page and so the second half of sentence 1 goes on", out)

    def test_hyphenated_words_are_joined_and_compounds_keep_their_hyphen(self):
        raw = "The indi-\nvidual wills. Self-consciousness is here, and self-consciousness there; and again self-\nconsciousness, as always, and the self-consciousness of another."
        out = self.clean(raw)
        self.assertIn("The individual wills", out)
        self.assertIn("again self-consciousness, as always", out)

    def test_footnote_paragraphs_and_spacing(self):
        raw = "Text , with spacing ; and a star*.\n\n[1] A footnote of the editor.\n\n* Another footnote.\n\nMore text ( here ) ."
        out = self.clean(raw)
        self.assertEqual(out.strip().split("\n\n"), ["Text, with spacing; and a star.", "More text (here)."])

    def test_numbered_sections_survive_and_spoiled_numbers_are_mended(self):
        paras = [f"{n}. Section {n} says what it says." for n in (101, 102, 103)] + ["1831. A year is no section."] \
            + [f"{n}. Section {n} says what it says." for n in (104, 105)] + ["156. Spoiled number for 106.", "107. After it.", "109. A gap, then 109.", "110. Ten."]
        out = corpus.number_sections(paras, r"^(\d+)\.\s+(?=[A-Z])")
        self.assertEqual([p.split(".")[0] for p in out[:3]], ["§ 101", "§ 102", "§ 103"])
        self.assertTrue(out[3].startswith("1831. "))                                                          # a year runs on from nothing: no section
        self.assertTrue(out[6].startswith("§ 106. Spoiled"))                                                  # 156 where 106 is missing: the scan has spoiled it
        self.assertTrue(out[8].startswith("§ 109. ") and out[9].startswith("§ 110. "))                        # a gap that the numbers after it confirm

    def test_section_signs_are_normalised_and_a_cross_reference_is_no_section(self):
        out = corpus.number_sections(["§. 1. First.", "§ 2. Second.", "§ 100 Anm.) refers here.", "§ 3. Third.", "§ 4. Fourth."], r"^§[.]?\s*(\d{1,3})\.?")
        self.assertEqual([p.split()[1] for p in out[:2]], ["1.", "2."])
        self.assertTrue(out[2].startswith("… §"))
        self.assertTrue(out[3].startswith("§ 3. ") and out[4].startswith("§ 4. "))

    def test_headings_by_a_spec_by_capitals_and_by_running_heads(self):
        raw = "ONE\n\nINTRODUCTION.\n\nText of the introduction.\n\nTHE EAST.\n\nText of the East.\n\nChina\n\nText about China."
        out = self.clean(raw, heads=[(1, r"^INTRODUCTION", "Introduction"), (1, r"^THE EAST", "The East"), (2, r"^China$", "China")], caps=True)
        self.assertEqual([p for p in out.split("\n\n") if p.startswith("#")], ["# Introduction", "# The East", "## China"])
        auto = self.clean("B. ARISTOTLE.\n\nText.\n\n1. THE METAPHYSICS.\n\nMore text.\n\nCHAPTER II\n\nEven more text.", auto=True)
        self.assertEqual([p for p in auto.split("\n\n") if p.startswith("#")], ["# Aristotle", "## The Metaphysics"])
        pages = []
        for i in range(5):
            pages.append(f"Ethical Action {i + 460}\n\nA paragraph on page {i}, long enough to be a paragraph of its own and end properly.")
        out = self.clean("\n\n".join(pages), running=2)
        self.assertEqual([p for p in out.split("\n\n") if p.startswith("#")], ["## Ethical Action"])

    def test_start_end_and_the_lecture_additions(self):
        raw = "Preface\n\nSkip me.\n\nVorrede\n\n§ 1. Der Wille ist frei.\n\n2. Zusatz zu § 1. (Die Idee.) Ein Zusatz.\n\nNamenregister.\n\nNever."
        out = self.clean(raw, start=r"^Vorrede$", end=r"^Namenregister", sections=r"^§\s*(\d+)\.?\s*", zusatz=r"^\d+[.,]\s+Zusatz zu §§?\s*(\d+)\.?")
        self.assertEqual(out.strip().split("\n\n"), ["Vorrede", "§ 1. Der Wille ist frei.", "§ 1 Zusatz. (Die Idee.) Ein Zusatz."])

    def test_a_scan_with_a_blank_line_after_every_line_becomes_paragraphs(self):
        lines = ["Der Geist ist frei, und seine Freiheit besteht darin, bei sich selbst zu sein; er ist"] * 3 + ["nicht abhängig."]
        raw = "\n\n".join(lines + lines)
        out = corpus.lines_to_paragraphs(raw.split("\n\n"), {})
        self.assertEqual(len(out), 2)

    def test_the_works_are_registered_with_their_reasons(self):
        ids = [w["id"] for w in corpus.WORKS]
        self.assertEqual(len(ids), len(set(ids)))
        for w in corpus.WORKS:
            self.assertTrue(w["why"] and w["source"]["page"].startswith("https://"), w["id"])
            self.assertIn(w["lang"], ("en", "de"))
        for must in ("Philosophy of Right", "Philosophy of History", "Philosophy of Mind", "History of Philosophy", "Phenomenology of Mind",
                     "Phänomenologie des Geistes", "Philosophie des Rechts", "Philosophie der Geschichte", "Enzyklopädie"):
            self.assertIn(must, {w["work"] for w in corpus.WORKS})


class LivesTest(unittest.TestCase):
    """The lives of him (Rosenkranz, Caird) go into the training corpus, never onto his shelf."""

    def test_no_life_is_in_the_index_he_reads_from(self):
        lives = {w["id"] for w in corpus.WORKS if not w["shelf"]}
        self.assertEqual(lives, {"rosenkranz-leben", "rosenkranz-urkunden", "caird"})
        self.assertTrue(all(not w["shelf"] for w in corpus.WORKS if w["author"] != "Hegel"))      # a book about him is never on his shelf
        index = json.loads(gzip.open(shelf.INDEX, "rt", encoding="utf-8").read())
        self.assertFalse(lives & {w["id"] for w in index["works"]})

    def test_a_built_life_is_cut_at_his_death(self):
        for w in corpus.WORKS:
            if not w["shelf"] and corpus.path_of(w).exists():
                text = corpus.read_work(w)
                self.assertGreater(len(text), 100000, w["id"])
                tail = text[-3000:].lower()
                self.assertFalse(re.search(r"begräbnis|begraben|beerdig|funeral|buried|grave", tail), w["id"])


class PassageTest(unittest.TestCase):
    def test_passages_stay_within_the_size_and_the_cuts_fall_at_sentence_ends(self):
        text = "# Part\n\n" + "\n\n".join([para(300, "state"), para(2500, "spirit"), para(700, "family"), para(150, "king"), para(1200, "war")])
        got = shelf.split_passages(text)
        self.assertTrue(all(len(p) <= shelf.MAX_CHARS for _, p in got), [len(p) for _, p in got])
        long = [len(p) for _, p in got if len(p) >= shelf.MIN_CHARS]
        self.assertGreaterEqual(len(long), len(got) - 1)
        self.assertTrue(all(re.search(r"[.!?]$", p) for _, p in got))
        self.assertEqual(" ".join(p for _, p in got).count("The state is what it is"), para(300, "state").count("The state is what it is"))     # nothing lost

    def test_refs_follow_headings_and_a_passage_does_not_cross_a_heading(self):
        text = "# Oriental World\n\n## India\n\n" + para(800, "caste") + "\n\n# Greek World\n\n" + para(800, "freedom")
        refs = [r for r, _ in shelf.split_passages(text)]
        self.assertEqual(refs, ["Oriental World, India", "Greek World"])

    def test_sections_give_the_ref_and_a_long_path_is_cut(self):
        text = "# Preface\n\n" + para(600, "owl") + "\n\n§ 189. " + para(700, "need") + "\n\n§ 190. " + para(700, "want")
        refs = [r for r, _ in shelf.split_passages(text, "sec")]
        self.assertEqual(refs[0], "Preface")
        self.assertEqual(refs[1:], ["§189", "§190"])
        long = "# " + "Very long heading " * 6 + "\n\n## Short one\n\n" + para(600, "x")
        self.assertEqual(shelf.split_passages(long)[0][0], "Short one")

    def test_sentences_do_not_end_at_abbreviations(self):
        ss = shelf.sentences("Mr. Hugo says so (cf. § 53). The twelve tables are old; Cicero praises them. Is that so? Yes.")
        self.assertEqual(len(ss), 4)

    def test_labels(self):
        self.assertEqual(shelf.label("Philosophy of Right", "§189"), "Philosophy of Right §189")
        self.assertEqual(shelf.label("Philosophie der Geschichte", "Einleitung"), "Philosophie der Geschichte, Einleitung")
        self.assertEqual(shelf.label("Phänomenologie", ""), "Phänomenologie")


def tiny_shelf():
    """A shelf of a few passages in both languages, with a small table."""
    works = [
        {"id": "hist-en", "work": "Philosophy of History", "lang": "en", "passages": [
            ("India", "The castes of India are fixed like nature: the Brahmins stand above the rest, and each caste keeps to its trade, so that the state of India is a dream. " * 2),
            ("Greece", "The Greeks knew that some are free, the Orientals that one is free; freedom is the end of the history of the world. " * 2)]},
        {"id": "hist-de", "work": "Philosophie der Geschichte", "lang": "de", "passages": [
            ("Indien", "Die Kasten Indiens sind wie die Natur befestigt: die Brahmanen stehen über den übrigen, und jede Kaste bleibt bei ihrem Gewerbe. " * 2),
            ("Griechenland", "Die Griechen wußten, daß einige frei sind, die Orientalen, daß einer frei ist; die Freiheit ist der Zweck der Weltgeschichte. " * 2)]},
        {"id": "right-en", "work": "Philosophy of Right", "lang": "en", "passages": [
            ("§189", "The system of needs is the first moment of civil society: wants are multiplied, and labour satisfies them in the market. " * 2),
            ("§257", "The state is the actuality of the ethical idea; the monarch stands at its summit and his name is weighty. " * 2)]},
    ]
    terms = shelf.Terms([["caste", "Kaste"], ["state", "Staat"], ["freedom", "Freiheit"], ["system of needs", "Bedürfnisse", "civil society"]],
                        [{"when": ["grocer", "tailor"], "add": ["system of needs", "civil society"]}])
    return shelf.Shelf(shelf.build_index(works), terms)


class RankingTest(unittest.TestCase):
    def setUp(self):
        self.s = tiny_shelf()
        patch = mock.patch.object(shelf, "FLOOR", 0.5)             # six passages give every term a low idf: the floor of a real shelf is too high here
        patch.start()
        self.addCleanup(patch.stop)

    def best(self, query, **kw):
        return [(h["work"], h["ref"]) for h in self.s.search([(query, 1.0)], **kw)]

    def test_bm25_puts_the_passage_about_the_words_first(self):
        self.assertEqual(self.best("the caste and the Brahmins")[0], ("Philosophy of History", "India"))
        self.assertEqual(self.best("who is free in the Greek world")[0], ("Philosophy of History", "Greece"))
        self.assertEqual(self.best("the monarch")[0], ("Philosophy of Right", "§257"))

    def test_the_table_carries_a_word_into_the_other_language(self):
        got = self.best("Kaste")
        self.assertIn(("Philosophy of History", "India"), got[:2])               # 'Kaste' is found in the English passage by the table
        self.assertEqual(self.best("Kaste")[0][1], "Indien")                     # and the German one is found directly
        self.assertEqual(self.best("Freiheit")[0][1] in ("Griechenland", "Greece"), True)

    def test_a_word_of_delhi_calls_up_the_system_of_needs(self):
        self.assertEqual(self.best("The grocer and the tailor are open")[0], ("Philosophy of Right", "§189"))
        without = shelf.Shelf(self.s.data, shelf.Terms([]))
        self.assertNotEqual([(h["work"], h["ref"]) for h in without.search([("The grocer and the tailor are open", 1.0)])][:1], [("Philosophy of Right", "§189")])

    def test_the_terms_of_the_table_are_stemmed_and_phrases_match(self):
        t = shelf.Terms([["civil society", "bürgerliche Gesellschaft"], ["Bedürfnisse", "needs"]])
        terms, phrases = t.expand(shelf.tokens("The Civil Society of the market"))
        self.assertIn(tuple(shelf.tokens("bürgerliche Gesellschaft")), phrases)
        self.assertIn(shelf.stem("gesellschaft"), terms)
        self.assertEqual(t.expand(shelf.tokens("Nothing matches"))[0], {})
        self.assertEqual(shelf.tokens("Bedürfnisse"), shelf.tokens("Bedürfnis"))
        self.assertEqual(shelf.tokens("states"), shelf.tokens("state"))
        self.assertEqual(shelf.tokens("Kasten"), shelf.tokens("Kaste"))
        self.assertEqual(shelf.fold("Bedürfnis ß"), "bedurfnis ss")

    def test_pick_one_german_and_one_english_else_the_best_two(self):
        got = self.s.pick([("the castes of India and the Brahmins; die Kasten Indiens", 1.0)])
        self.assertEqual(sorted(x["lang"] for x in got), ["de", "en"])
        english = self.s.pick([("the monarch of the state; the market, labour and wants", 1.0)])
        self.assertEqual({x["lang"] for x in english}, {"en"})
        self.assertEqual(len(english), 2)                                          # §189 and §257 lie side by side: the second is a passage elsewhere

    def test_works_held_out_and_passages_avoided_are_left_out(self):
        got = self.s.pick([("the castes of India and the Brahmins; die Kasten Indiens", 1.0)], hold=["hist-en", "hist-de"])
        self.assertTrue(all(x["work"] == "Philosophy of Right" for x in got))
        first = self.s.pick([("the castes of India", 1.0)])
        again = self.s.pick([("the castes of India", 1.0)], avoid=[first[0]["id"]])
        self.assertNotIn(first[0]["id"], [x["id"] for x in again])
        self.assertEqual(self.s.pick([("zzzz qqqq", 1.0)]), [])                    # nothing fits: nothing is shown

    def test_neighbouring_passages_are_not_both_offered(self):
        works = [{"id": "w", "work": "W", "lang": "en", "passages": [("a", para(600, "freedom")), ("b", para(600, "freedom")), ("c", para(600, "freedom") + " Elsewhere, the monarch.")]}]
        got = shelf.Shelf(shelf.build_index(works), shelf.Terms([])).pick([("freedom freedom freedom", 1.0)])
        docs = sorted(int(x["id"].split(":")[1]) for x in got)
        self.assertTrue(len(docs) < 2 or docs[1] - docs[0] > 1, docs)

    def test_excerpts_end_at_a_sentence_end_within_the_limit_and_keep_the_best_sentences(self):
        text = "Filler comes first, and nothing in it matters. " * 6 + "The caste is the nature of the Brahmin. " + "More filler follows, and it matters less. " * 6
        out = shelf.excerpt(text, {"caste": 1.0, "brahmin": 1.0})
        self.assertLessEqual(len(out), shelf.LIMIT)
        self.assertIn("caste", out)
        self.assertRegex(out, r"[.!?]$")
        cut = shelf.excerpt(LONG.replace(";", ","), {}, limit=100)
        self.assertLessEqual(len(cut), 100)
        self.assertTrue(cut.endswith("…") or re.search(r"[.!?]$", cut))

    def test_the_section_fits_its_budget_and_section_signs_do_not_show(self):
        works = [{"id": "w", "work": "A Rather Long Title of a Work", "lang": "en", "passages": [("§1", "§ 1. " + LONG[:870]), ("§5", "§ 5. " + LONG[:870] + " The caste.")]},
                 {"id": "v", "work": "Another Long Title", "lang": "de", "passages": [("§2", LONG[:880] + " Die Kaste.")]}]
        s = shelf.Shelf(shelf.build_index(works), shelf.Terms([["caste", "Kaste"]]))
        got = s.pick([("the state caste Kaste", 1.0)])
        self.assertTrue(got)
        self.assertLessEqual(shelf.section_size(got), shelf.MAX_SECTION)
        self.assertTrue(all(not x["text"].startswith("§") for x in got))

    def test_the_index_round_trips_through_a_file_and_loads_once(self):
        tmp = Path(tempfile.mkdtemp(prefix="hegel-shelf-"))
        try:
            shelf.save_index(self.s.data, tmp / "index.json.gz")
            (tmp / "terms.json").write_text(json.dumps({"groups": [["caste", "Kaste"]], "brings": []}), encoding="utf-8")
            a, b = shelf.load(tmp / "index.json.gz", tmp / "terms.json"), shelf.load(tmp / "index.json.gz", tmp / "terms.json")
            self.assertIs(a, b)
            self.assertEqual(a.n, self.s.n)
            self.assertEqual(a.search([("caste", 1.0)])[0]["ref"], "India")
            self.assertIsNone(shelf.load(tmp / "missing.json.gz"))
            self.assertEqual(a.doc_of(a.ident(3)), 3)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class RenderTest(unittest.TestCase):
    SIT = {"day": "Saturday 3 October", "time": "11:20", "place": "khan", "weather": "32 °C", "aqi": 150, "imprest_left": 600, "outfit": "a kurta",
           "present": [], "open_now": ["home", "khan"], "event": "You arrive."}

    def test_the_section_appears_only_when_there_is_a_shelf_and_sits_before_what_happens(self):
        plain = contract.render(self.SIT)
        self.assertEqual(plain, contract.render({**self.SIT, "shelf": []}))
        self.assertNotIn("From your shelf", plain)
        with_shelf = contract.render({**self.SIT, "earlier": ["10:00 stay (khan): A thought."],
                                      "shelf": [{"label": "Philosophy of Right §189", "text": "The system of needs."}, {"label": "Philosophie der Geschichte, Einleitung", "text": "Der Geist."}]})
        self.assertIn("\nFrom your shelf:\n- Philosophy of Right §189: “The system of needs.”\n- Philosophie der Geschichte, Einleitung: “Der Geist.”\n\nWhat happens:", with_shelf)
        self.assertLess(with_shelf.index("Earlier today:"), with_shelf.index("From your shelf:"))

    def test_bakeoff_situations_render_byte_identically(self):
        for s in json.loads((REPO / "mind/situations.json").read_text(encoding="utf-8"))["situations"]:
            self.assertNotIn("From your shelf", contract.render(s))
            self.assertEqual(contract.render(s), contract.render({**s, "shelf": None}))

    def test_the_soul_says_what_the_shelf_is_for(self):
        soul = (REPO / "mind/soul.md").read_text(encoding="utf-8")
        know = soul.split("## What you know")[1].split("\n## ")[0]
        self.assertIn("From your shelf", know)
        self.assertIn("not to quote at length", know)


class EngineTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.box = Sandbox()
        cls.prompts = []

        class Spy(StubMind):
            def decide(self, messages, sit):
                if not any("refuses" in x["content"] for x in messages):
                    EngineTest.prompts.append((messages[1]["content"], sit.get("shelf")))
                return super().decide(messages, sit)
        cls.engine = cls.box.engine(Spy())
        cls.days = [cls.box.run_day(date(2026, 10, 3) + timedelta(days=i), cls.engine) for i in range(2)]

    @classmethod
    def tearDownClass(cls):
        cls.box.close()

    def steps(self):
        return [s for d in self.days for s in d["steps"] if "decision" in s]

    def test_most_decisions_have_passages_and_the_step_and_the_diary_say_which(self):
        steps = self.steps()
        shown = [s for s in steps if s.get("shelf")]
        self.assertGreater(len(shown), 0.7 * len(steps))
        for s in shown:
            self.assertTrue(1 <= len(s["shelf"]) <= 2)
            self.assertTrue(all(set(x) == {"work", "ref", "id"} and ":" in x["id"] for x in s["shelf"]))
        for d in self.days:
            diary = [e for e in d["entries"] if e["k"] == "diary" and e.get("shelf")]
            self.assertTrue(diary)
            for e in diary:
                self.assertTrue(all(set(x) == {"work", "ref"} for x in e["shelf"]))
            first = next(e for e in d["entries"] if e["k"] == "diary")
            step = next(s for s in d["steps"] if s.get("decision", {}).get("thought") == first["text"])
            self.assertEqual(first.get("shelf"), [{"work": x["work"], "ref": x["ref"]} for x in step.get("shelf", [])] or None)

    def test_a_passage_is_not_offered_again_within_six_steps_of_the_day(self):
        for d in self.days:
            steps = [s for s in d["steps"] if "decision" in s]
            for i, s in enumerate(steps):
                recent = {x["id"] for p in steps[max(0, i - 6):i] for x in p.get("shelf", [])}
                self.assertFalse(recent & {x["id"] for x in s.get("shelf", [])}, (d["date"], s["t"]))

    def test_the_section_in_the_prompt_is_within_its_budget(self):
        sections = [re.search(r"From your shelf:\n(?:- .*\n)+", p) for p, _ in self.prompts]
        sizes = [len(m.group(0)) for m in sections if m]
        self.assertTrue(sizes)
        self.assertLessEqual(max(sizes), shelf.MAX_SECTION)
        for p, sh in self.prompts:
            if sh:
                self.assertTrue(all(len(x["text"]) <= shelf.LIMIT for x in sh))
                self.assertTrue(all(f"- {x['label']}: “{x['text']}”" in p for x in sh))

    def test_with_the_shelf_off_the_days_are_whole_and_carry_no_passages(self):
        box = Sandbox()
        try:
            box.cfg.shelf = False
            e = box.engine(StubMind())
            self.assertIsNone(e.shelf)
            day = box.run_day(date(2026, 10, 3), e)
            self.assertFalse(any(s.get("shelf") for s in day["steps"]))
            self.assertFalse(any(x.get("shelf") for x in day["entries"]))
            self.assertTrue(day["complete"])
        finally:
            box.close()

    def test_no_index_no_shelf(self):
        self.assertIsNone(shelf.load(Path(tempfile.gettempdir()) / "no-such-shelf.json.gz"))


class PageTest(unittest.TestCase):
    def node(self, entry):
        if not shutil.which("node"):
            self.skipTest("node is not installed")
        js = """
        const h = require('fs').readFileSync(process.argv[1], 'utf8');
        const grab = (a, b) => { const i = h.indexOf(a); return h.slice(i, h.indexOf(b, i)); };
        const src = [grab("const esc = s =>", "\\n"), grab("const rupees", "\\n"), grab("function line(e){", "function wiki")].join("\\n");
        const f = new Function(src + "; return {line, shelfLine, shelfLabel};")();
        const e = JSON.parse(process.argv[2]);
        console.log(JSON.stringify([f.line(e), e.shelf && e.shelf.length ? f.shelfLine(e) : null]));
        """
        got = subprocess.run(["node", "-e", js, str(REPO / "docs/index.html"), json.dumps(entry)], capture_output=True, text=True)
        self.assertEqual(got.returncode, 0, got.stderr)
        return json.loads(got.stdout)

    def test_a_thought_carries_a_small_muted_line_with_the_books_he_had_open(self):
        line, shelf_line = self.node({"k": "diary", "text": "A <thought>.", "shelf": [{"work": "Philosophy of Right", "ref": "§189"}, {"work": "Philosophie der Geschichte", "ref": "Einleitung"}]})
        self.assertEqual(shelf_line, "From his shelf: Philosophy of Right §189 · Philosophie der Geschichte, Einleitung")
        self.assertEqual(line, 'A &lt;thought&gt;.<small class="src">From his shelf: Philosophy of Right §189 · Philosophie der Geschichte, Einleitung</small>')

    def test_a_thought_without_a_shelf_is_what_it_was(self):
        self.assertEqual(self.node({"k": "diary", "text": "Plain."})[0], "Plain.")
        self.assertEqual(self.node({"k": "diary", "text": "Plain.", "shelf": []})[0], "Plain.")

    def test_the_box_under_the_thought_is_in_the_page_and_follows_the_veil(self):
        self.assertIn('<p class="shelf" id="nowShelf" hidden></p>', PAGE)
        self.assertRegex(PAGE, r"nowShelf\.hidden = !\(th && th\.shelf && th\.shelf\.length\) \|\| veiled")
        self.assertIn(".src{display:block", PAGE)


class RealShelfTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        t0 = time.time()
        shelf._loaded.clear()
        cls.shelf = shelf.load()
        cls.load_s = time.time() - t0

    def test_the_index_loads_fast_and_is_not_huge(self):
        self.assertIsNotNone(self.shelf)
        self.assertLess(self.load_s, 3)
        self.assertLess(shelf.INDEX.stat().st_size, 12e6)
        self.assertGreater(self.shelf.n, 10000)

    def test_passages_are_sized_and_labelled(self):
        sizes = [len(t) for t in self.shelf.data["texts"]]
        self.assertLessEqual(max(sizes), shelf.MAX_CHARS)
        self.assertGreater(sum(400 <= n <= 900 for n in sizes) / len(sizes), 0.9)
        langs = {w["lang"] for w in self.shelf.works}
        self.assertEqual(langs, {"en", "de"})
        self.assertTrue(all(len(r) <= shelf.REF_CHARS for r in self.shelf.data["refs"]))

    def test_the_manifest_lists_every_text_with_its_reason_and_the_total(self):
        manifest = (REPO / "mind/shelf/MANIFEST.md").read_text(encoding="utf-8")
        files = sorted(p.name[:-len(".txt.gz")] for p in (REPO / "mind/shelf").glob("*.txt.gz"))
        self.assertEqual(files, sorted(w["id"] for w in corpus.WORKS))
        for w in corpus.WORKS:
            self.assertIn(f"`{w['id']}`", manifest)
            self.assertIn(w["source"]["page"], manifest)
        self.assertRegex(manifest, r"\*\*Total:\*\* 17 texts, [\d.]+ MB of text, [\d.]+ MB gzipped")
        self.assertIn("Left out, and why", manifest)
        self.assertIn("Rosenkranz", manifest)
        total = sum(p.stat().st_size for p in (REPO / "mind/shelf").iterdir())
        self.assertLess(total, 25e6)

    def test_nothing_from_after_1831_and_no_editor_is_on_the_shelf(self):
        from world.world import wordlist
        later = wordlist("after_1831.txt", "s?")
        hits = [t for t in self.shelf.data["texts"] if later.search(t)]
        self.assertEqual(hits, [])
        for w in corpus.WORKS:
            text = corpus.read_work(w)
            self.assertNotIn("Verlag von Felix Meiner", text)
            self.assertNotIn("Project Gutenberg", text)
            self.assertNotIn("Digitized by", text)

    def pick(self, event, place, roles=(), thoughts=(), theses=("India stands outside world history", "The state is the actuality of the ethical idea")):
        return self.shelf.pick(shelf.query_parts(event, place, list(roles), list(thoughts), list(theses)))

    def test_five_situations(self):
        market = self.pick("You arrive at Khan Market. The grocer, the tailor, the stationer and the bookseller are all open.", "Khan Market", ["the bookseller"])
        self.assertTrue(any(re.search(r"bürgerlich|civic|civil|want|need|Bedürf", x["text"]) for x in market), market)
        caste = self.pick("Mrs. Kapoor speaks of caste: her cook will not eat from the same pot as the sweeper. The conversation turns to India.", "Lodhi Gardens", ["retired schoolteacher"])
        self.assertTrue(any("India" in x["label"] or "Indien" in x["label"] for x in caste), caste)
        file = self.pick("Mr. Saxena finds the file. It has gone up for orders. Come after fifteen days, he says. Your occupation is irregular.", "Directorate of Estates",
                         ["section officer, Directorate of Estates"])
        self.assertTrue(any(re.search(r"public servant|Beamt|official", x["text"]) for x in file), file)
        refusal = self.pick("At Gandhi Smriti you read the inscription on the spot where a man refused. You stand in silence.", "Gandhi Smriti", [])
        self.assertTrue(any(re.search(r"negative freedom|Furie|fury", x["text"]) for x in refusal), refusal)
        for got in (market, caste, file, refusal):
            self.assertLessEqual(shelf.section_size(got), shelf.MAX_SECTION)

    def test_retrieval_is_fast(self):
        parts = shelf.query_parts("You arrive at Khan Market. Masterji is here. You are hungry.", "Khan Market", ["tailor, Khan Market"],
                                  ["The shutters are half down, and the other half sell what the first half would have."], ["India stands outside world history"])
        self.shelf.pick(parts)                                   # the first query reads the postings it needs
        t0 = time.time()
        for _ in range(20):
            self.shelf.pick(parts)
        self.assertLess((time.time() - t0) / 20, 0.15)

    def test_the_cleaned_texts_keep_their_sections(self):
        by = {w["id"]: corpus.read_work(w) for w in corpus.WORKS}
        right = by["dyde-right"]
        m = re.search(r"^§ 257\. (The state is the realized ethical idea[^\n]{0,60})", right, re.M)
        self.assertTrue(m)
        self.assertRegex(by["rechts"], r"(?m)^§ 257\. Der Staat ist die Wirklichkeit der sittlichen Idee")
        self.assertRegex(by["rechts"], r"(?m)^§ 189 Zusatz\. \(Die Nationalökonomie\.\)")
        self.assertRegex(by["wallace-mind"], r"(?m)^§ 430\. Here there is a self-consciousness for a self-consciousness")
        self.assertIn("Lordship and Bondage", by["baillie-1"])


if __name__ == "__main__":
    unittest.main()
