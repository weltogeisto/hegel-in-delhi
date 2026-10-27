"""Provenance and budget regressions for typed daily evidence (no ML packages)."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from world import records
from world.engine import Days


class RecordsTest(unittest.TestCase):
    def day(self):
        return dict(date="2026-10-03", n=2, title="Saturday", complete=False,
                    entries=[], steps=[], segments=[], state=dict(imprest=100, until="2026-10-03T08:00"))

    def rows(self, day, kind=None):
        return [r for r in records.project(day)["records"] if kind is None or r["kind"] == kind]

    def test_projection_never_mutates_the_source(self):
        day = self.day()
        before = copy.deepcopy(day)
        records.project(day)
        self.assertEqual(before, day)

    def test_appending_keeps_existing_ids_and_same_minute_entries_distinct(self):
        day = self.day()
        e = dict(k="bag", t="08:00", item="Chai", price=20)
        day["entries"] = [e, copy.deepcopy(e)]
        before = self.rows(day, "payment")
        day["entries"].append(dict(k="world", t="08:00", text="Rain begins."))
        after = self.rows(day, "payment")
        self.assertEqual([r["id"] for r in before], [r["id"] for r in after])
        self.assertNotEqual(before[0]["id"], before[1]["id"])
        self.assertEqual([0, 1], [r["source"]["index"] for r in before])

    def test_corrected_source_invalidates_old_id(self):
        day = self.day()
        day["entries"] = [dict(k="said", t="08:00", by="Ramesh", text="Breakfast soon.")]
        old = self.rows(day, "statement")[0]["id"]
        self.assertIsNotNone(records.resolve(day, old))
        day["entries"][0]["text"] = "Lunch soon."
        self.assertIsNone(records.resolve(day, old))

    def test_a_statement_stays_unverified_and_has_speaker_recipient_time_place(self):
        day = self.day()
        day["segments"] = [dict(mode="inside", at="home", **{"from":"08:00", "to":"09:00"})]
        e = dict(k="said", t="08:00", by="Ramesh", to="Hegel", text="The river is the Ganges.")
        day["entries"] = [e]
        r = self.rows(day, "statement")[0]
        self.assertEqual((r["speaker"],r["recipient"],r["time"],r["place"]), ("Ramesh","Hegel","08:00","home"))
        self.assertFalse(r["verified"])
        self.assertEqual(r["source"]["sha256"], records.digest(e))
        self.assertFalse(any(x.get("text") == e["text"] for x in self.rows(day, "event")))
        self.assertIn("unverified", records.render(records.project(day)))

    def test_own_words_are_attributed_to_hegel(self):
        day = self.day(); day["entries"] = [dict(k="said", t="08:00", text="I have eaten.")]
        r = self.rows(day, "statement")[0]
        self.assertEqual("Hegel", r["speaker"])
        self.assertIsNone(r["recipient"])
        self.assertFalse(r["verified"])

    def test_midwalk_location_is_unknown_and_start_is_origin(self):
        day = self.day()
        day["segments"] = [dict(mode="walk", a="home", b="lodhi", **{"from":"08:00", "to":"08:30"})]
        self.assertEqual("home", records.location(day, "08:00"))
        self.assertIsNone(records.location(day, "08:15"))

    def test_explicit_entry_location_takes_precedence(self):
        day = self.day(); day["entries"] = [dict(k="said", t="08:00", place="home", text="Good morning.")]
        self.assertEqual("home", self.rows(day, "statement")[0]["place"])

    def test_thoughts_plans_summaries_and_mixed_legacy_event_are_not_observations(self):
        day = self.day()
        day["entries"] = [dict(k="diary",t="08:00",text="I ate an omelette."),
                          dict(k="plan",t="08:00",items=[dict(time="09:00",intention="Send the letter")])]
        day["steps"] = [dict(t="08:00",end="09:00",event="Ramesh says the river is the Ganges.",
                             decision=dict(action="rest",place="home",minutes=60,thought="I ate an omelette."))]
        day["owl"] = dict(diary="I sent the letter.")
        text = records.render(records.project(day))
        self.assertNotIn("omelette", text); self.assertNotIn("Ganges", text); self.assertNotIn("sent the letter", text)
        self.assertIn("executed rest", text)

    def test_new_observations_have_exact_source_pointers(self):
        day = self.day()
        day["steps"] = [dict(t="08:00",end="09:00",observed_at="home",observations=["Breakfast is laid out."],
                             decision=dict(action="read",place="home",minutes=60))]
        r = next(r for r in self.rows(day, "event") if r.get("type") == "observation")
        self.assertEqual([0,0], r["source"]["index"])
        self.assertEqual(records.digest(day["steps"][0]["observations"][0]), r["source"]["sha256"])
        self.assertEqual(("08:00","home"), (r["time"],r["place"]))

    def test_accepted_meal_uses_arrival_not_decision_time(self):
        day = self.day()
        day["segments"] = [dict(mode="walk",a="home",b="khan", **{"from":"12:00","to":"12:25"}),
                           dict(mode="inside",at="khan", **{"from":"12:25","to":"13:00"})]
        step = dict(t="12:00",end="13:00",decision=dict(action="eat",place="khan",minutes=35))
        day["steps"] = [step]
        r = next(r for r in self.rows(day, "event") if r.get("type") == "action")
        self.assertEqual(("12:25","13:00","khan"), (r["time"],r["end"],r["place"]))
        self.assertEqual(records.digest(step), r["source"]["sha256"])

    def test_walk_records_a_route_and_never_places_him_at_the_destination_before_arrival(self):
        for with_segment in (False, True):
            with self.subTest(with_segment=with_segment):
                day=self.day()
                day["steps"]=[dict(t="08:00",end="08:30",decision=dict(action="walk",place="lodhi",minutes=30))]
                if with_segment:
                    day["segments"]=[dict(mode="walk",a="home",b="lodhi",**{"from":"08:00","to":"08:30"})]
                r=next(r for r in self.rows(day) if r.get("action")=="walk")
                self.assertIsNone(r["place"])
                self.assertEqual("home" if with_segment else None,r["origin"])
                self.assertEqual("lodhi",r["destination"])
                self.assertNotIn("08:00 at lodhi",records.line(r))
                self.assertIn("arrival at interval end",records.line(r))

    def test_offer_purchase_and_read_do_not_manufacture_eating(self):
        day = self.day()
        day["entries"] = [dict(k="bag",t="08:00",item="Breakfast",price=50),
                          dict(k="said",t="08:00",by="Ramesh",text="Breakfast is ready."),
                          dict(k="read",t="08:00",title="Breakfast",source="paper",text="Everyone ate.")]
        self.assertFalse(any(r.get("action") == "eat" for r in self.rows(day)))
        r = next(r for r in self.rows(day, "event") if r.get("type") == "read")
        self.assertFalse(r["content_verified"])

    def test_manuscript_is_a_draft_even_when_addressed_as_a_letter(self):
        day = self.day(); day["entries"] = [dict(k="writing",t="08:00",work="w1",title="To Marie",kind="letter",
                                                to="Marie",text="We met the emperor.",sitting=1)]
        r = self.rows(day, "work")[0]
        self.assertEqual(("draft","w1","Marie"), (r["status"],r["work_id"],r["recipient"]))
        self.assertIn("not sent", records.line(r))
        self.assertFalse(any("emperor" in x.get("text", "") for x in self.rows(day, "event")))

    def test_cash_snapshot_does_not_assert_a_balance_at_prior_hours(self):
        day = self.day(); r = next(r for r in self.rows(day) if r.get("type") == "cash")
        self.assertEqual("08:00",r["time"]); self.assertFalse(r["at_close"])
        day["complete"] = True
        r = next(r for r in self.rows(day) if r.get("type") == "cash")
        self.assertEqual("24:00",r["time"]); self.assertTrue(r["at_close"])

    def test_uncashed_cheque_is_not_settled_cash(self):
        day = self.day(); day["entries"] = [dict(k="income",t="08:00",item="Fee",amount=500,cheque=True)]
        r = self.rows(day, "payment")[0]
        self.assertEqual((False,"cheque","in"), (r["settled"],r["medium"],r["direction"]))

    def test_duplicate_detection_uses_canonical_identity_not_name_price_or_minute(self):
        day = self.day(); e=dict(k="bag",t="08:00",item="Chai",price=20)
        day["entries"] = [e, copy.deepcopy(e)]
        self.assertEqual([],records.payment_duplicates(records.project(day)))
        bill=dict(k="expense",t="09:00",item="Laundry",amount=300,cost="dhobi",since="2026-10-03")
        day["entries"] += [bill, dict(bill,t="10:00")]
        dup = records.payment_duplicates(records.project(day))
        self.assertEqual(1,len(dup));self.assertEqual("cost:dhobi:2026-10-03",dup[0]["canonical_id"])

    def test_different_due_dates_are_distinct_bills(self):
        day = self.day(); e=dict(k="expense",t="08:00",item="Laundry",amount=300,cost="dhobi",since="2026-10-03")
        day["entries"] = [e,dict(e,since="2026-10-10")]
        self.assertEqual([],records.payment_duplicates(records.project(day)))

    def test_explicit_charge_identity_is_retained(self):
        self.assertEqual("charge-9", records.charge_id(dict(charge_id="charge-9")))
        self.assertIsNone(records.charge_id(dict(to="Ramesh",amount=300,since="2026-10-03",why="Laundry")))

    def test_unpaid_obligation_is_not_settled(self):
        day = self.day(); day["entries"]=[dict(k="world",t="08:00",text="A bill fell due.",
                                               owe=dict(to="Ramesh",amount=300,why="Laundry",since="2026-10-03"))]
        r=self.rows(day,"payment")[0]
        self.assertFalse(r["settled"]);self.assertTrue(r["obligation"])

    def test_legacy_missing_steps_never_establishes_absence(self):
        day = self.day(); del day["steps"]; day["complete"] = True
        store = records.project(day)
        self.assertFalse(store["steps_present"])
        self.assertNotIn("none in", records.render(store))
        self.assertIn("Omitted records prove no absence",records.render(store))

    def test_renderer_preserves_every_meal_and_quantity_under_budget_pressure(self):
        day = self.day()
        day["entries"]=[dict(k="said",t="08:00",by="Ramesh",to="Hegel",text="Long claim. "*1000),
                        dict(k="expense",t="09:00",item="Laundry",amount=300,charge_id="laundry-1")]
        day["steps"]=[dict(t=t,end=t[:2]+":30",decision=dict(action="eat",place="home",minutes=30))
                      for t in ["07:00","13:00","19:00"]]
        store=records.project(day); text=records.render(store,limit=1500)
        self.assertLessEqual(len(text),1500)
        for r in store["records"]:
            self.assertIn(r["id"],text)
            if records.critical(r):self.assertIn(records.line(r),text)
        self.assertIn("[excerpt]",text)

    def test_impossible_budget_fails_explicitly_without_hiding_records(self):
        with self.assertRaises(records.RecordBudgetError):records.render(records.project(self.day()),20)

    def test_save_replaces_one_store_and_loading_does_not_rewrite_a_legacy_day(self):
        with tempfile.TemporaryDirectory() as tmp:
            days=Days(Path(tmp)); day=self.day(); days.dir.mkdir()
            days.path(day["date"]).write_text(json.dumps(day))
            before=days.path(day["date"]).read_bytes()
            loaded=days.load(day["date"])
            self.assertNotIn("records",loaded); records.project(loaded)
            self.assertEqual(before,days.path(day["date"]).read_bytes())
            days.save(loaded); a=days.load(day["date"])["records"]
            days.save(loaded); b=days.load(day["date"])["records"]
            self.assertEqual(a,b)
            self.assertEqual(a,records.project(loaded))


class RecordIntegrationTest(unittest.TestCase):
    def setUp(self):
        from test_world import Sandbox
        from datetime import date
        self.box = Sandbox()
        self.engine = self.box.engine()
        self.day = self.engine.new_day(self.box.days.load("2026-10-02"), date(2026,10,3))

    def tearDown(self):
        self.box.close()

    def test_npc_reply_never_enters_new_observation_channel(self):
        from datetime import date
        from world.world import at_dt
        prev=dict(end="07:00",voice=dict(by="Ramesh",says="The river is the Ganges.",does=None))
        sit,ctx=self.engine.world.situation(at_dt(date(2026,10,3),420),self.day["state"],self.day,prev)
        self.assertIn("Ganges",sit["event"])
        self.assertNotIn("Ganges"," ".join(ctx["observations"]))
        self.assertEqual(self.day["state"]["place"],ctx["observed_at"])

    def test_executed_step_and_save_retain_observations_and_entry_places(self):
        from datetime import date
        from world.world import at_dt
        step=self.engine.step(self.day,at_dt(date(2026,10,3),420))
        self.assertIn("observations",step)
        self.assertTrue(step["observations"])
        attributed = [e for e in self.day["entries"] if e["k"] != "plan"]
        self.assertTrue(attributed)
        self.assertTrue(all("place" in e for e in attributed))
        self.box.days.save(self.day)
        loaded=self.box.days.load("2026-10-03")
        self.assertEqual(records.project(loaded),loaded["records"])
        self.assertTrue(any(r.get("type")=="action" for r in loaded["records"]["records"]))

    def test_settlement_retains_the_recurring_bill_due_date(self):
        from datetime import date
        from world.world import at_dt
        st=self.day["state"]
        st["owed"]=[dict(to="Ramesh",amount=100,why="Laundry",cost="laundry",since="2026-10-03",at="home")]
        st["imprest"]=1000
        _,entries=self.engine.world.settle(at_dt(date(2026,10,3),420),st,"home",["ramesh"],{})
        self.assertEqual(1,len(entries))
        self.assertEqual("cost:laundry:2026-10-03",records.charge_id(entries[0]))
        self.assertEqual(900,st["imprest"])


if __name__ == "__main__":
    unittest.main()
