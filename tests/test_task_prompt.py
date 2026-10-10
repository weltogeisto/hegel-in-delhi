import copy
import json
from unittest import mock
import unittest
from pathlib import Path
from world.task_prompt import for_task


class TaskPromptTests(unittest.TestCase):
    def test_switch_removes_decision_fields_but_retains_identity_evidence_and_history(self):
        soul = ('Hegel, born 1770.\n\n## Evidence\nA plan is an intention.\n\n'
                '## Your answer\nReply with thought/action/minutes.\n\n'
                '## Later rule\nA received assertion is not automatically true.\n')
        messages = [{'role': 'system', 'content': soul}, {'role': 'user', 'content': 'Observed: the fan stopped.'},
                    {'role': 'assistant', 'content': '{"action":"write"}'}]
        before = copy.deepcopy(messages)
        out = for_task(messages, 'writing')
        self.assertEqual(messages, before)
        self.assertEqual(out[1:], before[1:])
        self.assertIn('Hegel, born 1770.', out[0]['content'])
        self.assertIn('A plan is an intention.', out[0]['content'])
        self.assertIn('A received assertion is not automatically true.', out[0]['content'])
        self.assertNotIn('thought/action/minutes', out[0]['content'])
        self.assertIn('title, kind, to, continues, text', out[0]['content'])

    def test_custom_persona_receives_explicit_task_override(self):
        original = [{'role': 'system', 'content': 'A custom character.'}]
        out = for_task(original, 'planning')
        self.assertTrue(out[0]['content'].startswith('A custom character.'))
        self.assertIn('continues, about', out[0]['content'])
        self.assertNotIn('continues, text', out[0]['content'])

    def test_day_plan_has_its_own_contract(self):
        out = for_task([{'role':'system','content':'Hegel.\n## Your answer\nReturn thought/action.'}], 'day-planning')
        self.assertNotIn('Return thought/action.', out[0]['content'])
        self.assertIn('times and intentions', out[0]['content'])
        self.assertNotIn('title, kind', out[0]['content'])

    def test_no_silent_fallback_for_missing_system_or_unknown_task(self):
        with self.assertRaises(ValueError): for_task([], 'writing')
        with self.assertRaises(ValueError): for_task([{'role': 'user', 'content': 'a'}], 'writing')
        with self.assertRaises(ValueError): for_task([{'role': 'system', 'content': 'a'}], 'unknown')

    def test_real_personas_preserve_all_content_before_the_answer_section(self):
        root = Path(__file__).resolve().parents[1]
        for name in ['soul.md', 'soul-v2.md']:
            soul = (root/'mind'/name).read_text()
            identity = soul.split('## Your answer\n')[0].rstrip()
            for task in ['writing', 'planning', 'argument', 'day-planning', 'choice']:
                self.assertTrue(for_task([{'role':'system','content':soul}], task)[0]['content'].startswith(identity))


class EngineTaskRoutingTests(unittest.TestCase):
    def engine(self, reply):
        from world.engine import Engine
        from world.world import World
        e = Engine.__new__(Engine)
        e.soul = 'Hegel, born 1770.\n\n## Evidence\nA thought is not an event.\n\n## Your answer\nReturn thought, action and minutes.\n'
        e.world = World()
        e.mind = mock.Mock(spec=["chat"])  # legacy mind: optional task methods really are absent
        e.mind.chat.return_value = reply
        return e

    def system(self, e, required):
        messages = e.mind.chat.call_args.args[0]
        self.assertTrue(messages[0]['content'].startswith('Hegel, born 1770.'))
        self.assertIn('A thought is not an event.', messages[0]['content'])
        self.assertNotIn('Return thought, action and minutes.', messages[0]['content'])
        self.assertIn(required, messages[0]['content'])
        return messages

    def test_real_day_plan_call_uses_intentions_contract(self):
        from datetime import date
        from world.world import at_dt
        e = self.engine(json.dumps({'plan':[{'time':'10:00','intention':'Write a letter'}]}))
        sit = {'on_mind':[]}; day = {}; ctx = {'known_text':''}
        with mock.patch('world.engine.contract.render', return_value='Present: nobody. Plan the day.'):
            self.assertTrue(e.make_plan(day, at_dt(date(2026,10,3), 420), sit, ctx))
        m = self.system(e, 'times and intentions')
        self.assertEqual(m[1]['content'], 'Present: nobody. Plan the day.')
        self.assertEqual(day['plan']['items'], [{'time':'10:00','intention':'Write a letter'}])

    def test_plain_outline_call_preserves_prior_decision_and_requests_about(self):
        e = self.engine('unusable outline')
        messages = [{'role':'system','content':e.soul},{'role':'user','content':'Observed: the fan stopped.'}]
        before = copy.deepcopy(messages)
        self.assertIsNone(e.write_plain(messages, '{"action":"write"}', {}, {}))
        m = self.system(e, 'title, kind, to, continues, about')
        self.assertEqual(messages, before)
        self.assertEqual(m[1:3], [before[1], {'role':'assistant','content':'{"action":"write"}'}])
        self.assertNotIn('continues, text', m[0]['content'])

    def test_real_choice_call_preserves_the_question_and_prior_decision(self):
        from world.engine import CHOICE_SCHEMA
        e = self.engine('{"answer":"yes"}')
        messages = [{'role':'system','content':e.soul},{'role':'user','content':'Hegde asks for the second bedroom.'}]
        self.assertTrue(e.ask_choice(messages, '{"action":"stay"}', {'choice':{'question':'Will you share the room?'}}))
        m = self.system(e, 'answer yes or no')
        self.assertEqual(m[1:3], [messages[1], {'role':'assistant','content':'{"action":"stay"}'}])
        self.assertIn('Will you share the room?',m[-1]['content'])
        self.assertIs(e.mind.chat.call_args.args[1], CHOICE_SCHEMA)
        self.assertEqual(e.mind.chat.call_args.kwargs, {'max_tokens':20,'temperature':0})


if __name__ == '__main__': unittest.main()
