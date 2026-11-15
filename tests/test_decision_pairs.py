"""Training 3's labeller (tools/decision_pairs.py): the world's verdicts and fixed phrase rules decide, nothing else."""
import json
import re
import tempfile
import unittest
from pathlib import Path

from tools import decision_pairs as dp
from world import contract

LONG = "The file has gone to the wrong desk and the clerk will not look at it until Monday morning comes"
EARLIER = "I felt the friction of the particular against the universal today."
ECHO = "Again the friction of the particular against the universal, and the tea goes cold"
QUIET = "Nothing in particular happens. The morning goes on."


def cand(seed, thought, accepted=True, errors=None, action="stay", place="home", finish="stop"):
    answer = None if thought is None else {"thought": thought, "action": action, "place": place}
    errors = list(errors) if errors is not None else ([] if accepted else ["thought is empty or too short"])
    return {"seed": seed, "raw": json.dumps(answer), "answer": answer, "accepted": accepted, "errors": errors,
            "finish_reason": finish}


def prompt(earlier=(), event=QUIET):
    """A decision prompt rendered by the live contract, with earlier lines in world.situation's format."""
    s = dict(day="Saturday, 7 November 2026", time="10:00", place="Home", weather="clear", aqi=180,
             outfit="the frock coat", imprest_left=1200, present=[], open_now=["Home"], event=event,
             earlier=[f"{t} recorded step: {a} ({p}); you thought: “{text}”" for t, a, p, text in earlier])
    return [{"role": "system", "content": "the soul"}, {"role": "user", "content": contract.render(s)}]


def four(*cands):
    """Fill the frozen seed set; the extra seeds are invalid replies that never pair."""
    used = {c["seed"] for c in cands}
    return list(cands) + [cand(s, None, accepted=False) for s in dp.SEEDS if s not in used]


def row(cands, earlier=(), day=35, source="shadow", rid="shadow:35:1", messages=None, date="2026-11-05"):
    return {"id": rid, "source": source, "day": day, "step": 1, "date": date,
            "messages": messages or prompt(), "earlier_thoughts": list(earlier), "candidates": four(*cands)}


class LegacyLabelTest(unittest.TestCase):
    def test_labels(self):
        earlier = ["I felt the friction of the particular against the universal today"]
        self.assertEqual(dp.label(cand(1, LONG), earlier), "clean")
        self.assertEqual(dp.label(cand(1, "Again the friction of the particular against the universal"), earlier), "repeating")
        self.assertEqual(dp.label(cand(1, LONG, accepted=False), earlier), "refused")
        self.assertEqual(dp.label(cand(1, None, accepted=False), earlier), "invalid")

    def test_stopword_runs_are_not_phrases(self):
        self.assertEqual(dp.label(cand(1, "It is what it is in the end of it all"), ["it is what it is"]), "clean")


class LegacyPairTest(unittest.TestCase):
    def test_first_clean_against_first_length_matched_rejection(self):
        refused = LONG.replace("Monday", "Tuesday")
        r = row([cand(4271, LONG), cand(1831, "No.", accepted=False), cand(2718, refused, accepted=False),
                 cand(3141, LONG + " again")])
        labels, p = dp.pair(r)
        self.assertEqual(p["rejected_seed"], 2718)         # 1831 is refused but far too short to match
        self.assertEqual(p["chosen_seed"], 3141)           # the first clean one in seed order
        self.assertEqual(p["rejected_as"], "refused")
        self.assertEqual(p["view"], "legacy")

    def test_no_clean_candidate_no_pair(self):
        _, p = dp.pair(row([cand(1831, LONG, accepted=False), cand(2718, LONG, accepted=False)]))
        self.assertIsNone(p)

    def test_silence_never_wins(self):
        _, p = dp.pair(row([cand(1831, "Rest."), cand(2718, LONG, accepted=False)]))
        self.assertIsNone(p)                               # 1 word against 20: not length-matched


class RevisedLabelTest(unittest.TestCase):
    def test_the_prompt_shows_first_sentences_of_earlier_steps(self):
        messages = prompt([("09:00", "stay", "home", EARLIER)])
        self.assertEqual(dp.shown(messages), [("09:00", "stay", "home", EARLIER)])
        self.assertTrue(dp.quiet(messages))
        self.assertFalse(dp.quiet(prompt(event="Ramesh says: “Sir, the tea.”")))

    def test_the_parser_follows_world_situation_format(self):
        source = (Path(__file__).resolve().parents[1] / "world/world.py").read_text(encoding="utf-8")
        self.assertIn("line = f\"{s['t']} recorded step: {dec['action']} ({dec['place']})\"", source)
        self.assertIn("line += f\"; you thought: “{first}”\"", source)
        self.assertIn("\"Nothing in particular happens. The {part} goes on.\"", source)

    def test_a_loop_repeats_words_action_and_place_where_nothing_happened(self):
        steps = dp.shown(prompt([("09:00", "stay", "home", EARLIER)]))
        self.assertEqual(dp.revised_label(cand(1831, ECHO), steps, True), "loop")
        self.assertEqual(dp.revised_label(cand(1831, ECHO), steps, False), "clean")          # something happened
        self.assertEqual(dp.revised_label(cand(1831, ECHO, action="walk", place="lodhi"), steps, True), "clean")
        self.assertEqual(dp.revised_label(cand(1831, LONG), steps, True), "clean")

    def test_refusals_count_only_where_the_prompt_shows_how_to_avoid_them(self):
        steps = dp.shown(prompt([("09:00", "stay", "home", EARLIER)]))
        shown_repeat = cand(1831, LONG, accepted=False, errors=["this repeats what you thought at 09:00; think something new"])
        old_repeat = cand(1831, LONG, accepted=False, errors=["this repeats what you thought at 07:40; think something new"])
        closed = cand(1831, LONG, accepted=False, errors=["Lodhi Garden is closed when you would arrive (19:10)"])
        opens = cand(1831, LONG, accepted=False, errors=["Safdarjung's Tomb opens at 07:00; walking there you would arrive at 06:20"])
        gate = cand(1831, LONG, accepted=False, errors=["you have not met 'Marx' in Delhi; in 1831 you could not know it"])
        both = cand(1831, LONG, accepted=False, errors=[closed["errors"][0], "speaks_to requires spoken words in says"])
        self.assertEqual([dp.revised_label(c, steps, True) for c in (shown_repeat, old_repeat, closed, opens, gate, both)],
                         ["refused", "hidden", "hidden", "hidden", "refused", "refused"])

    def test_truncated_and_invalid_never_pair(self):
        self.assertEqual(dp.revised_label(cand(1831, LONG, finish="length"), [], True), "truncated")
        self.assertEqual(dp.revised_label(cand(1831, None, accepted=False), [], True), "invalid")


class RevisedPairTest(unittest.TestCase):
    def test_every_clean_candidate_gets_its_turn(self):
        refused = LONG.replace("Monday", "Tuesday")
        r = row([cand(1831, "Short and clean, nothing more."), cand(2718, LONG),
                 cand(3141, refused, accepted=False, errors=["speaks_to requires spoken words in says"])])
        _, legacy = dp.pair(r)
        _, revised = dp.revised_pair(r)
        self.assertIsNone(legacy)                          # the first clean one had no length match
        self.assertEqual((revised["chosen_seed"], revised["rejected_seed"], revised["rejected_as"]), (2718, 3141, "refused"))
        self.assertEqual(revised["view"], "revised")

    def test_shared_phrases_alone_are_diagnostics_not_rejections(self):
        earlier = [EARLIER]                                # in the day, but no longer shown in the prompt
        r = row([cand(1831, LONG), cand(2718, ECHO)], earlier=earlier)
        legacy_labels, legacy = dp.pair(r)
        revised_labels, revised = dp.revised_pair(r)
        self.assertEqual(legacy_labels[1], "repeating")
        self.assertEqual(revised_labels[1], "clean")
        self.assertIsNone(revised)
        _, stats = dp.build([r])
        self.assertEqual(stats["diagnostics"]["clean_sharing_a_phrase_with_the_day"], 1)
        self.assertEqual(stats["diagnostics"]["clean_sharing_a_phrase_with_what_is_shown"], 0)

    def test_a_shown_loop_is_rejected(self):
        loop = "Again the friction of the particular against the universal, and the clerk will not look at it until Monday"
        r = row([cand(1831, LONG), cand(2718, loop)], messages=prompt([("09:00", "stay", "home", EARLIER)]))
        labels, p = dp.revised_pair(r)
        self.assertEqual(labels[:2], ["clean", "loop"])
        self.assertEqual((p["chosen_seed"], p["rejected_seed"], p["rejected_as"]), (1831, 2718, "loop"))

    def test_hidden_refusals_never_reject(self):
        r = row([cand(1831, LONG), cand(2718, LONG, accepted=False, errors=["Lodhi Garden is closed when you would arrive (19:10)"])])
        labels, p = dp.revised_pair(r)
        self.assertEqual(labels[1], "hidden")
        self.assertIsNone(p)


class FilterEstimateTest(unittest.TestCase):
    """T49: choosing among his own answers, with no training."""

    def test_the_filter_prefers_a_fresh_answer_and_counts_its_calls(self):
        shown_prompt = prompt([("09:00", "stay", "home", EARLIER)])
        r = row([cand(1831, ECHO), cand(2718, LONG)], messages=shown_prompt, earlier=[EARLIER])
        arms = dp.filter_estimate([r])["arms"]
        self.assertEqual((arms["first"]["echo_of_shown"], arms["first"]["loops"], arms["first"]["mean_calls"]), (1, 1, 1.0))
        for arm in ("no_echo_shown", "no_echo_day", "no_loop"):
            self.assertEqual((arms[arm]["echo_of_shown"], arms[arm]["loops"], arms[arm]["changed_from_first"],
                              arms[arm]["mean_calls"], arms[arm]["no_passing_answer"]), (0, 0, 1, 2.0, 0), arm)
        self.assertEqual(arms["accepted"]["changed_from_first"], 0)          # the echo was accepted by the world

    def test_when_every_answer_repeats_the_first_accepted_one_stands(self):
        shown_prompt = prompt([("09:00", "stay", "home", EARLIER)])
        r = row([cand(1831, LONG, accepted=False), cand(2718, ECHO), cand(3141, ECHO + " again")], messages=shown_prompt)
        est = dp.filter_estimate([r])
        arm = est["arms"]["no_echo_shown"]
        self.assertEqual((arm["no_passing_answer"], arm["accepted"], arm["echo_of_shown"], arm["mean_calls"]), (1, 1, 1, 4.0))
        self.assertEqual(est["arms"]["accepted"]["mean_calls"], 2.0)         # the refusal costs one more call
        self.assertEqual(est["arms"]["first"]["accepted"], 0)

    def test_any_number_of_answers_and_the_stats_carry_the_estimate(self):
        three = {"id": "t39:1", "messages": prompt(), "candidates": [cand(1831, LONG), cand(2718, LONG), cand(3141, LONG)]}
        est = dp.filter_estimate([three])
        self.assertEqual((est["situations"], est["answers_per_situation"]), (1, {"3": 1}))
        _, stats = dp.build([row([cand(1831, LONG)])])
        self.assertEqual(stats["filter_estimate"]["answers_per_situation"], {"4": 1})
        _, legacy = dp.build([row([cand(1831, LONG)])], view="legacy")
        self.assertNotIn("filter_estimate", legacy)

    def test_cli_reads_any_candidate_file(self):
        from tools import decision_filter
        folder = Path(tempfile.mkdtemp())
        src = folder / "arm-a.jsonl"
        src.write_text(json.dumps({"id": "t39:1", "messages": prompt(), "candidates": [cand(1831, LONG), cand(2718, LONG)]}) + "\n")
        out = folder / "estimate.json"
        self.assertEqual(decision_filter.main(["--candidates", str(src), "--out", str(out)]), 0)
        self.assertEqual(json.loads(out.read_text())["situations"], 1)


class BuildTest(unittest.TestCase):
    def test_test_days_duplicates_and_t9_rehearsals_refused(self):
        with self.assertRaisesRegex(ValueError, "test day"):
            dp.build([row([cand(1831, LONG)], day=27, rid="shadow:27:1")])
        with self.assertRaisesRegex(ValueError, "duplicate"):
            dp.build([row([cand(1831, LONG)]), row([cand(1831, LONG)])])
        with self.assertRaisesRegex(ValueError, "10 November"):
            dp.build([row([cand(1831, LONG)], source="rehearsal", rid="rehearsal:27:1", day=27, date="2026-10-30")])
        pairs, stats = dp.build([row([cand(1831, LONG)], day=27, source="rehearsal", rid="rehearsal:27:1", date="2026-11-10")])
        self.assertEqual(stats["situations"], 1)           # a rehearsal's day number is not a shadow test day

    def test_inconsistent_rows_are_refused(self):
        bad_seeds = row([cand(1831, LONG)])
        bad_seeds["candidates"][-1]["seed"] = 42
        disagree = row([cand(1831, LONG, accepted=False, errors=[])])
        reparsed = row([cand(1831, LONG)])
        reparsed["candidates"][0]["answer"]["thought"] = "a repaired thought the reply never contained"
        one_message = row([cand(1831, LONG)])
        one_message["messages"] = one_message["messages"][1:]
        from tests.test_decision_split import HELD
        held = row([cand(1831, LONG)])
        held["messages"][1]["content"] += "\nYou remember: " + HELD
        for r, why in ((bad_seeds, "frozen seeds"), (disagree, "disagree"), (reparsed, "parsed raw"), (one_message, "two-message"),
                       (held, "held-related")):
            with self.subTest(why=why):
                with self.assertRaisesRegex(ValueError, why):
                    dp.build([r])

    def test_stats_report_both_views(self):
        refused = LONG.replace("Monday", "Tuesday")
        r = row([cand(1831, "Short and clean, nothing more."), cand(2718, LONG),
                 cand(3141, refused, accepted=False, errors=["speaks_to requires spoken words in says"])])
        _, stats = dp.build([r])
        self.assertEqual((stats["view"], stats["pairs"], stats["legacy_view"]["pairs"]), ("revised", 1, 0))
        self.assertEqual(stats["refusal_kinds"], {"contract": 2})      # the seeded refusal and one invalid filler
        _, legacy = dp.build([r], view="legacy")
        self.assertEqual((legacy["view"], legacy["pairs"]), ("legacy", 0))

    def test_cli_writes_new_files_only(self):
        folder = Path(tempfile.mkdtemp())
        src = folder / "candidates.jsonl"
        src.write_text(json.dumps(row([cand(1831, LONG), cand(2718, LONG + " too", accepted=False)])) + "\n")
        out = folder / "pairs.jsonl"
        self.assertEqual(dp.main(["--candidates", str(src), "--out", str(out)]), 0)
        self.assertEqual(len(out.read_text().splitlines()), 1)
        stats = json.loads(out.with_suffix(".stats.json").read_text())
        self.assertEqual((stats["pairs"], stats["view"]), (1, "revised"))
        with self.assertRaises(FileExistsError):
            dp.main(["--candidates", str(src), "--out", str(out)])


if __name__ == "__main__":
    unittest.main()
