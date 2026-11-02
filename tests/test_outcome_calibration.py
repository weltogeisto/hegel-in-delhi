import unittest
from pc.outcome_calibration import choose_threshold,summarize


class OutcomeCalibrationTest(unittest.TestCase):
    def test_concrete_supported_retention_cannot_hide_behind_opinion_sentences(self):
        rows=[dict(label=1,claims=[],log_odds=None,concrete_assertion=False) for _ in range(20)]
        rows.append(dict(label=1,claims=['a recorded meal'],log_odds=0.,concrete_assertion=True))
        rows.extend(dict(label=0,claims=['an invented meal'],log_odds=2.,concrete_assertion=True) for _ in range(5))
        threshold=choose_threshold(rows,1)
        self.assertLessEqual(threshold,.5)

    def test_extraction_miss_is_counted_as_false_acceptance_not_a_correct_vote(self):
        rows=[dict(id='missing-premise',sentence='I invented an event.',label=0,claims=[],log_odds=None)]
        result=summarize(rows,1,.5)
        self.assertEqual(1,result['unsupported_accepted'])
        self.assertEqual(1.,result['ece']);self.assertEqual(1.,result['brier'])

    def test_no_eligible_retention_rule_fails_instead_of_deleting_all_supported_facts(self):
        rows=[dict(label=1,claims=['a recorded meal'],log_odds=-50.,concrete_assertion=True),
              dict(label=0,claims=['an invented meal'],log_odds=-60.,concrete_assertion=True)]
        with self.assertRaisesRegex(RuntimeError,'retains'):
            choose_threshold(rows,1)
