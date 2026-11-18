"""The file's next act, part 1 (HEGEL_FILE_ACT, pc/FILE-NEXT-ACT.md): Mr. Saxena's representation, Shri Hegde's letter or his
copy, and Mr. Malhotra's voucher. Off, the four beats do not exist and the world is as it was."""
import json
import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_economy import D, There, fresh, look, offer  # noqa: E402

from world import __main__ as cli  # noqa: E402
from world.config import Config  # noqa: E402
from world.world import World, at_dt  # noqa: E402

IDS = ["saxena_reply", "hegde_letter", "malhotra_vouch", "hegde_copy"]
SAT = D(21, 11)                  # 21 November, the day the file moves
FILE = lambda: json.loads((Path(__file__).resolve().parent.parent / "world/data/plot_file_act.json").read_text(encoding="utf-8"))["beats"]


def state_on(day=SAT, lodger=True, **kw):
    st = fresh(settled=day.isoformat(), **kw)
    if lodger:
        st["flags"]["hegde_lodger"] = True
    return st


def which(w, st, pid, who, hour=10, day=SAT):
    """The beat that would fire at hour:00 on day, him at pid with `who` there."""
    with There(**{pid: who}):
        return (look(w, at_dt(day, hour * 60), st, pid)[1]["beat"] or {}).get("id")


class Switch(unittest.TestCase):
    def test_off_by_default(self):
        self.assertFalse(Config().file_act)
        self.assertTrue(Config({"HEGEL_FILE_ACT": "1"}).file_act)
        self.assertFalse(cli.make_world(Config()).file_act)
        self.assertTrue(cli.make_world(Config({"HEGEL_FILE_ACT": "1"})).file_act)

    def test_off_none_of_the_four_exists(self):
        ids = {b["id"] for b in World().beats}
        self.assertFalse(ids & set(IDS))
        self.assertEqual({b["id"] for b in World(file_act=True).beats} - ids, set(IDS))

    def test_off_a_stand_in_month_is_unchanged(self):
        w = World()
        st = state_on(D(21, 11))
        with There(estates=["saxena"], home=["ramesh", "hegde"], lodhi=["malhotra"]):
            for n in range(21, 31):
                for pid in ("estates", "home", "lodhi"):
                    st["met_days"]["malhotra"] = ["a", "b", "c"]
                    self.assertIsNone(look(w, at_dt(D(n, 11), 20 * 60), st, pid)[1]["beat"], (n, pid))

    def test_the_file_matches_the_draft_and_validates(self):
        draft = Path(__file__).resolve().parent.parent / "pc/FILE-NEXT-ACT.md"
        text = draft.read_text(encoding="utf-8")
        for b in FILE()[:3]:                                  # the first three verbatim; hegde_copy's words come from the brief
            for k in ("prompt", "public"):
                if b.get(k):
                    self.assertIn(json.dumps(b[k], ensure_ascii=False)[1:-1], text, (b["id"], k))
        self.assertEqual([b["id"] for b in FILE()], ["saxena_reply", "hegde_letter", "malhotra_vouch", "hegde_copy"])
        w = World(file_act=True)
        self.assertEqual(cli.economy_problems(w), [])


class SaxenaReply(unittest.TestCase):
    def setUp(self):
        self.w = World(file_act=True)

    def test_only_after_the_query_at_the_directorate_with_mr_saxena(self):
        st = state_on(lodger=False)
        self.assertEqual(which(self.w, st, "estates", ["saxena"]), "saxena_reply")
        self.assertIsNone(which(self.w, state_on(lodger=False), "estates", []))                  # no Mr. Saxena
        self.assertIsNone(which(self.w, state_on(lodger=False), "khan", ["saxena"]))             # not at the Directorate
        early = state_on(lodger=False)
        early["beats"].remove("saxena_query")
        self.assertNotEqual(which(self.w, early, "estates", ["saxena"]), "saxena_reply")         # the query has not come

    def test_yes(self):
        st = state_on(lodger=False)
        with There(estates=["saxena"]):
            bid, out = offer(self.w, at_dt(SAT, 600), st, "estates", yes=True)
        self.assertEqual(bid, "saxena_reply")
        self.assertEqual(st["flags"]["file_reply"], "own_name")
        self.assertEqual(st["file"], "His representation is on the file, in his own name: he is not Shri G. Hegde. Put up.")
        self.assertEqual(out[-1]["text"], "He writes it at the counter and signs it G. W. F. Hegel. Mr. Saxena stamps it received.")

    def test_no(self):
        st = state_on(lodger=False)
        with There(estates=["saxena"]):
            offer(self.w, at_dt(SAT, 600), st, "estates", yes=False)
        self.assertNotIn("file_reply", st["flags"])
        self.assertEqual(st["file"], "The query stands unanswered: proof of identity as Shri G. Hegde.")

    def test_again_after_a_no_not_after_a_yes(self):
        """As the engine stands: a no with again_days takes the beat back off the list for ten days; a yes leaves it fired."""
        st = state_on(lodger=False)
        with There(estates=["saxena"]):
            offer(self.w, at_dt(SAT, 600), st, "estates", yes=False)
            self.assertIsNone(which(self.w, st, "estates", ["saxena"], day=D(30, 11)))                  # nine days on
            self.assertEqual(which(self.w, st, "estates", ["saxena"], day=D(1, 12)), "saxena_reply")    # ten days on
            st2 = state_on(lodger=False)
            offer(self.w, at_dt(SAT, 600), st2, "estates", yes=True)
            self.assertIn("saxena_reply", st2["beats"])
            self.assertIsNone(which(self.w, st2, "estates", ["saxena"], day=D(15, 12)))                  # a yes does not come back


class HegdeLetter(unittest.TestCase):
    def setUp(self):
        self.w = World(file_act=True)

    def test_conditions(self):
        self.assertEqual(which(self.w, state_on(), "home", ["hegde"], 19), "hegde_letter")
        self.assertIsNone(which(self.w, state_on(), "home", ["hegde"], 19, day=D(20, 11)))       # before its date
        self.assertIsNone(which(self.w, state_on(), "home", ["hegde"], 18))                      # before its window
        self.assertIsNone(which(self.w, state_on(), "home", ["hegde"], 21))                      # after it
        self.assertIsNone(which(self.w, state_on(), "home", [], 19))                             # Shri Hegde is out
        self.assertIsNone(which(self.w, state_on(), "khan", ["hegde"], 19))                      # not at home
        self.assertNotEqual(which(self.w, state_on(lodger=False), "home", ["hegde"], 19), "hegde_letter")   # he is no lodger

    def test_yes(self):
        st = state_on()
        with There(home=["hegde"]):
            offer(self.w, at_dt(SAT, 19 * 60), st, "home", yes=True)
        self.assertEqual(st["flags"]["file_hegde"], "with_guest")
        self.assertEqual(st["file"], "Shri Hegde asks for the allotment in his name, the Professor on record as his guest.")

    def test_no(self):
        st = state_on()
        with There(home=["hegde"]):
            offer(self.w, at_dt(SAT, 19 * 60), st, "home", yes=False)
        self.assertEqual(st["flags"]["file_hegde"], "alone")
        self.assertEqual(st["file"], "Shri Hegde asks for the allotment in his name.")


class HegdeCopy(unittest.TestCase):
    def setUp(self):
        self.w = World(file_act=True)

    def test_only_without_the_lodger(self):
        self.assertEqual(which(self.w, state_on(lodger=False), "home", ["ramesh"]), "hegde_copy")
        self.assertIsNone(which(self.w, state_on(), "home", ["ramesh"]))                         # a lodger gets the letter instead
        self.assertIsNone(which(self.w, state_on(lodger=False), "home", ["ramesh"], day=D(20, 11)))   # before its date
        self.assertIsNone(which(self.w, state_on(lodger=False), "home", []))                     # no Ramesh to bring it
        self.assertIsNone(which(self.w, state_on(lodger=False), "khan", ["ramesh"]))
        early = state_on(lodger=False)
        early["beats"].remove("hegde_gate")
        self.assertIsNone(which(self.w, early, "home", ["ramesh"]))                              # the gate has not happened

    def test_fires_without_a_choice(self):
        st = state_on(lodger=False)
        with There(home=["ramesh"]):
            bid, out = offer(self.w, at_dt(SAT, 600), st, "home")
        self.assertEqual(bid, "hegde_copy")
        self.assertEqual(st["flags"]["file_hegde"], "alone")
        self.assertEqual(st["file"], "Shri Hegde asks for the allotment in his name.")
        self.assertEqual(out[0]["text"], "A copy comes from the guest house: Shri Hegde has asked the Directorate for the allotment in his name.")

    def test_letter_and_copy_never_both(self):
        for lodger in (True, False):
            st = state_on(lodger=lodger)
            fired = set()
            with There(home=["ramesh", "hegde"]):
                for n in range(21, 31):
                    for hour in (7, 10, 19, 20):
                        bid, _ = offer(self.w, at_dt(D(n, 11), hour * 60), st, "home", yes=False)
                        if bid:
                            fired.add(bid)
            self.assertEqual(fired & {"hegde_letter", "hegde_copy"}, {"hegde_letter"} if lodger else {"hegde_copy"})


class MalhotraVouch(unittest.TestCase):
    def setUp(self):
        self.w = World(file_act=True)

    def met(self, n, **kw):
        st = state_on(lodger=False, **kw)
        st["met_days"]["malhotra"] = [D(i, 11).isoformat() for i in range(1, n + 1)]
        return st

    def test_from_the_third_day_met(self):
        self.assertIsNone(which(self.w, self.met(0), "lodhi", ["malhotra"]))                     # today is his first day
        self.assertIsNone(which(self.w, self.met(1), "lodhi", ["malhotra"]))                     # today is his second
        self.assertEqual(which(self.w, self.met(2), "lodhi", ["malhotra"]), "malhotra_vouch")    # today is his third
        self.assertEqual(which(self.w, self.met(3), "lodhi", ["malhotra"]), "malhotra_vouch")
        self.assertEqual(which(self.w, self.met(3), "gym", ["malhotra"], 18), "malhotra_vouch")
        self.assertEqual(which(self.w, self.met(5), "lodhi", ["malhotra"]), "malhotra_vouch")

    def test_the_third_day_is_counted_by_the_engine(self):
        st = state_on(lodger=False)
        st["met_days"]["malhotra"] = [D(2, 11).isoformat(), D(3, 11).isoformat()]
        with There(lodhi=["malhotra"]):
            sit, ctx = look(self.w, at_dt(SAT, 600), st, "lodhi")
        self.assertEqual(ctx["beat"]["id"], "malhotra_vouch")             # the day itself is the third
        self.assertEqual(len(st["met_days"]["malhotra"]), 3)

    def test_only_in_the_garden_or_the_gymkhana_with_him_after_the_query(self):
        self.assertIsNone(which(self.w, self.met(3), "lodhi", []))
        self.assertIsNone(which(self.w, self.met(3), "home", ["malhotra"]))
        early = self.met(3)
        early["beats"].remove("saxena_query")
        self.assertIsNone(which(self.w, early, "lodhi", ["malhotra"]))

    def test_yes_and_no(self):
        st = self.met(3)
        with There(lodhi=["malhotra"]):
            offer(self.w, at_dt(SAT, 600), st, "lodhi", yes=True)
        self.assertEqual(st["flags"]["file_vouched"], "malhotra")
        self.assertEqual(st["file"], "A letter from Shri R. K. Malhotra, IAS (retired), is on the file: he knows the occupant.")
        st = self.met(3)
        before = st["file"] if "file" in st else None
        with There(lodhi=["malhotra"]):
            _, out = offer(self.w, at_dt(SAT, 600), st, "lodhi", yes=False)
        self.assertNotIn("file_vouched", st["flags"])
        self.assertEqual(st.get("file"), before)
        self.assertEqual(out[-1]["text"], "He declines, with thanks.")


if __name__ == "__main__":
    unittest.main()
