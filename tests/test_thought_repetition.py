"""Quiet-step accounting and the declared minimum for saved-day audits."""
import copy
import unittest
from unittest.mock import patch

from pc.thought_repetition import audit


def saved_day(n):
    entries = [{'k': 'diary', 't': str(i), 'text': 'The garden opens beyond the wall.'} for i in range(n)]
    steps = [{'t': e['t'], 'decision': {'thought': e['text']}, 'mind': {'source': 'mind'}} for e in entries]
    return {'date': '2000-01-01', 'n': 1, 'entries': entries, 'steps': steps}


class ThoughtRepetitionTests(unittest.TestCase):
    def test_null_steps_are_counted_without_changing_thoughts_or_input(self):
        day = saved_day(30)
        for source in ['away', 'away', 'quiet', 'bedtime']:
            day['steps'].append({'t': 'end', 'decision': {'thought': None}, 'mind': {'source': source}})
        original = copy.deepcopy(day)
        result = audit(day, 'synthetic', 'synthetic')
        baseline = audit(saved_day(30), 'synthetic', 'synthetic')
        self.assertEqual(day, original)
        self.assertEqual(result['decisions'], 34)
        self.assertEqual(result['null_thought_decisions'], 4)
        self.assertEqual(result['null_thought_decisions_by_source'], {'away': 2, 'bedtime': 1, 'quiet': 1})
        for field in ['thoughts', 'marked_thoughts', 'share', 'top_ten', 'all_repeated_phrases', 'marked']:
            self.assertEqual(result[field], baseline[field])

    def test_below_floor_does_not_analyze_phrases_or_compute_share(self):
        with patch('pc.thought_repetition.grams', side_effect=AssertionError('must not analyze')):
            result = audit(saved_day(29), 'synthetic', 'synthetic')
        self.assertFalse(result['measurable'])
        self.assertEqual(result['thoughts'], 29)
        self.assertIsNone(result['marked_thoughts'])
        self.assertIsNone(result['share'])
        self.assertEqual(result['top_ten'], [])
        self.assertEqual(result['marked'], [])

    def test_exact_floor_is_measurable(self):
        result = audit(saved_day(30), 'synthetic', 'synthetic')
        self.assertTrue(result['measurable'])
        self.assertEqual(result['thoughts'], 30)
        self.assertEqual(result['marked_thoughts'], 29)

    def test_empty_day_is_not_measurable(self):
        result = audit(saved_day(0), 'synthetic', 'synthetic')
        self.assertFalse(result['measurable'])
        self.assertIsNone(result['share'])

    def test_diary_must_still_match_every_non_null_decision(self):
        day = saved_day(30)
        day['steps'][0]['decision']['thought'] = 'A different thought.'
        with self.assertRaises(AssertionError):
            audit(day, 'synthetic', 'synthetic')

    def test_missing_thought_is_not_silently_treated_as_null(self):
        day = saved_day(30)
        day['steps'].append({'t': 'end', 'decision': {}})
        with self.assertRaises(KeyError):
            audit(day, 'synthetic', 'synthetic')


if __name__ == '__main__':
    unittest.main()
