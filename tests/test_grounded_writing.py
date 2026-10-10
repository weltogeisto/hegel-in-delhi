"""Writing requests preserve the simulation date and the supplied manuscript state."""
import copy
import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from world import contract, works


class GroundedWritingTests(unittest.TestCase):
    def test_simulation_date_is_used_across_the_year_boundary(self):
        ask = works.ask({}, date(2027, 1, 1))
        self.assertTrue(ask.startswith(contract.WRITE_ASK))
        self.assertIn('Date of this sitting: 1 January 2027.', ask)
        self.assertTrue(ask.endswith(contract.WRITE_FORMAT))

    def test_request_does_not_change_manuscripts_or_turn_a_plan_into_a_sitting(self):
        state = {'works': [{'title': 'An unfinished letter', 'kind': 'letter', 'sittings': 1}],
                 'plan': [{'intention': 'Visit the tailor'}]}
        before = copy.deepcopy(state)
        text = works.ask(state, date(2026, 10, 7))
        self.assertIn('An unfinished letter', text)
        self.assertEqual(state, before)
        self.assertNotIn('Visit the tailor', text)

    def test_legacy_call_does_not_invent_a_calendar_date(self):
        self.assertNotIn('Date of this sitting:', works.ask({}))


if __name__ == '__main__':
    unittest.main()
