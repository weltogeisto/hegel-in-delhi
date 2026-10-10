"""Nightly reflection receives executed eating actions separately from food offers."""
import unittest
from world import owl


class OwlMealsTest(unittest.TestCase):
    def day(self):
        return dict(n=2, title="Saturday", complete=True, segments=[],
                    entries=[dict(k="said", t="06:15", by="Ramesh", text="Breakfast will be ready at seven."),
                             dict(k="bag", t="07:15", item="Chai", price=20)],
                    state=dict(imprest=100, wearing="kurta"),
                    steps=[dict(t="06:55", end="07:15", decision=dict(action="walk", place="lodhi")),
                           dict(t="07:15", end="07:25", decision=dict(action="buy", place="lodhi")),
                           dict(t="13:00", end="13:45", decision=dict(action="eat", place="home"))])

    def test_offer_and_purchase_are_not_rendered_as_executed_eating(self):
        text = owl.record(self.day())
        self.assertIn("Recorded eating actions: 13:00–13:45 at home.", text)
        self.assertIn("Offers, plans and purchases alone do not establish an eating action.", text)
        self.assertNotIn("Recorded eating actions: 07:15", text)
        self.assertIn("Breakfast will be ready at seven.", text)
        self.assertIn("07:15 bought: Chai", text)

    def test_complete_step_log_can_state_no_eating_action_was_recorded(self):
        day = self.day()
        day["steps"] = day["steps"][:2]
        self.assertIn("Recorded eating actions: none in this completed day's step log.", owl.record(day))

    def test_legacy_day_without_steps_does_not_invent_absence_of_eating(self):
        day = self.day()
        del day["steps"]
        self.assertNotIn("Recorded eating actions:", owl.record(day))

    def test_partial_day_does_not_claim_complete_negative_evidence(self):
        day = self.day()
        day["complete"] = False
        day["steps"] = day["steps"][:2]
        self.assertNotIn("none in this completed day's step log", owl.record(day))

    def test_old_eating_step_without_end_time_keeps_only_known_time(self):
        day = self.day()
        del day["steps"][-1]["end"]
        self.assertIn("Recorded eating actions: 13:00 at home.", owl.record(day))


if __name__ == "__main__":
    unittest.main()
