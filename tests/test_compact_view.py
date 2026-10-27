"""The compact evidence view: the day's records grouped and short for the writers (no ML packages)."""
import re
import unittest

from world import records
from world.config import Config


def day():
    return dict(
        date="2026-10-03", n=2, title="Saturday", complete=True,
        segments=[{"from": "08:00", "to": "08:30", "mode": "inside", "at": "home"},
                  {"from": "11:00", "to": "11:20", "mode": "walk", "a": "home", "b": "khan"},
                  {"from": "11:20", "to": "12:00", "mode": "inside", "at": "khan"}],
        entries=[dict(k="said", t="08:10", by="Ramesh", to="Hegel", text="The gate was bolted all night."),
                 dict(k="said", t="08:12", text="Then I shall not walk at night."),
                 dict(k="bag", t="11:30", item="Chai", price=20),
                 dict(k="consumed", t="11:35", item="Chai", food="snack", source="feed"),
                 dict(k="writing", t="15:00", title="On the gate", kind="letter", to="Karl", text="My dear Karl, " + "the gate " * 40),
                 dict(k="world", t="11:25", text="Dust over the market; the bookseller is open.")],
        plan={"written": "06:00", "items": [{"time": "17:00", "intention": "Visit the India International Centre"}]},
        steps=[{"t": "11:00", "end": "11:20", "decision": {"action": "walk", "place": "khan"}},
               {"t": "11:20", "end": "12:00", "decision": {"action": "eat", "place": "khan"}}],
        state={"imprest": 9980, "until": "2026-10-03T24:00", "place": "home"})


class CompactViewTest(unittest.TestCase):
    def view(self, d=None, **kw):
        return records.compact(records.project(d or day()), **kw)

    def section(self, text, title):
        m = re.search(re.escape(title) + r"\n(.*?)(?:\n\n|\Z)", text, re.S)
        return m.group(1) if m else ""

    def test_statements_stand_apart_from_facts_and_are_marked_unverified(self):
        v = self.view()
        said = self.section(v, "Said (not verified):")
        facts = self.section(v, "Facts:")
        self.assertIn("Ramesh to Hegel: “The gate was bolted all night.”", said)
        self.assertIn("Hegel to someone: “Then I shall not walk at night.”", said)
        self.assertNotIn("bolted", facts)

    def test_facts_payments_plans_and_drafts_each_in_their_place(self):
        v = self.view()
        facts, pays = self.section(v, "Facts:"), self.section(v, "Payments:")
        self.assertIn("11:00–11:20 walked from home to khan", facts)
        self.assertIn("ate Chai (snack)", facts)
        self.assertIn("cash at the close of the day: ₹9980", facts)
        self.assertIn("₹20 Chai: paid", pays)
        self.assertIn("planned for 17:00: Visit the India International Centre", self.section(v, "Plans (intentions, not done):"))
        drafts = self.section(v, "Drafts (not sent):")
        self.assertIn("letter “On the gate” to Karl", drafts)
        self.assertNotIn("the gate the gate", drafts)                     # a draft's text is in his manuscripts, not here

    def test_no_record_ids_and_far_shorter_than_the_full_view(self):
        store = records.project(day())
        v = records.compact(store)
        self.assertNotRegex(v, r"2026-10-03:(event|statement|payment|work):[0-9a-f]{16}")
        self.assertLess(len(v), len(records.render(store)) * 0.6)

    def test_unpaid_debt_and_income_are_named_as_such(self):
        d = day()
        d["entries"] += [dict(k="income", t="16:00", item="Lesson", amount=300, **{"from": "Mrs Kapoor"}),
                         dict(k="world", t="16:30", text="The dhobi leaves his bill.", owe={"amount": 90, "item": "washing", "to": "dhobi"})]
        pays = self.section(self.view(d), "Payments:")
        self.assertIn("₹300 Lesson from Mrs Kapoor: received", pays)
        self.assertIn("₹90 washing to dhobi: owed, not paid", pays)

    def test_a_long_day_keeps_every_fact_and_payment_and_says_what_was_left_out(self):
        d = day()
        d["entries"] += [dict(k="said", t=f"13:{i:02d}", by="Vendor", text="A very long speech about the market. " * 20) for i in range(40)]
        d["entries"] += [dict(k="world", t=f"14:{i:02d}", text="An observation of the street, its colours and sounds. " * 6) for i in range(40)]
        v = self.view(d, limit=3000)
        self.assertLessEqual(len(v), 3000)
        for must in ("walked from home to khan", "ate Chai", "₹20 Chai: paid", "cash at the close of the day"):
            self.assertIn(must, v)
        self.assertIn("leaving out proves nothing", v)

    def test_facts_that_cannot_fit_fail_loudly(self):
        d = day()
        d["entries"] += [dict(k="bag", t="12:00", item=f"Item {i}", price=i) for i in range(200)]
        with self.assertRaises(records.RecordBudgetError):
            self.view(d, limit=800)

    def test_earlier_days_only_when_they_match_the_subject(self):
        store = records.project(day())
        old = dict(day(), date="2026-10-02")
        old["entries"] = [dict(k="said", t="09:00", by="Saxena", text="Your allotment file is with the Joint Secretary."),
                          dict(k="world", t="10:00", text="Rain on the verandah.")]
        store["records"] += records.project(old)["records"]
        v = records.compact(store, query="the allotment file")
        self.assertIn("allotment file", v)
        self.assertNotIn("verandah", v)

    def test_relevant_hands_over_to_the_compact_view_when_asked(self):
        store = records.project(day())
        self.assertEqual(records.relevant(store, view="compact"), records.compact(store))
        self.assertLessEqual(len(records.relevant(store, limit=24000, view="compact")), records.COMPACT_CHARS)
        self.assertIn("[", records.relevant(store))                      # the full view is unchanged by default

    def test_the_flag(self):
        self.assertEqual(Config({}).evidence_view, "full")
        self.assertEqual(Config({"HEGEL_EVIDENCE_VIEW": "compact"}).evidence_view, "compact")
        self.assertEqual(Config({"HEGEL_EVIDENCE_VIEW": "anything"}).evidence_view, "full")


if __name__ == "__main__":
    unittest.main()
