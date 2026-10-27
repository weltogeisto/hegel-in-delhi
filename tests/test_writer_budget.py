"""Compact writers count the server's template, retain facts, and never turn on the checker."""
import json
import unittest
from unittest.mock import Mock, patch
from world import owl, prompt_budget, records
from world.config import Config
from world.mind import HTTPMind
from test_compact_view import day


class WriterBudgetTest(unittest.TestCase):
    def test_shrinks_only_evidence_and_checks_the_final_prompt(self):
        mind = Mock()
        mind.prompt_tokens.side_effect = lambda text, thinking=False: len(text)
        fixed = 'unchanged system and task' * 200
        build = lambda n: fixed + 'e' * n
        value = prompt_budget.fit(mind, build, 4000, thinking=True)
        self.assertTrue(value.startswith(fixed))
        self.assertLessEqual(len(value), 7263)
        self.assertTrue(mind.prompt_tokens.call_args.kwargs['thinking'])

    def test_impossible_fixed_prompt_fails_without_generation(self):
        mind = Mock()
        mind.prompt_tokens.return_value = 10000
        with self.assertRaises(prompt_budget.PromptBudgetError):
            prompt_budget.fit(mind, lambda n: 'fixed', 400)
        mind.chat.assert_not_called()

    def test_required_record_overflow_is_not_silently_truncated(self):
        mind = Mock()
        mind.prompt_tokens.return_value = 8000
        def build(n):
            if n < 1500:
                raise records.RecordBudgetError('required food and payments do not fit')
            return 'prompt'
        with self.assertRaises(records.RecordBudgetError):
            prompt_budget.fit(mind, build, 3000)
        mind.chat.assert_not_called()

    def test_server_template_and_special_tokens_are_used(self):
        values = [{'prompt': '<special>hello'}, {'tokens': [1, 2, 3]}]
        responses = []
        for value in values:
            response = Mock()
            response.read.return_value = json.dumps(value).encode()
            response.__enter__ = Mock(return_value=response)
            response.__exit__ = Mock(return_value=False)
            responses.append(response)
        mind = HTTPMind('http://server'); mind.ready = True
        with patch('urllib.request.urlopen', side_effect=responses) as opened:
            self.assertEqual(3, mind.prompt_tokens([{'role': 'user', 'content': 'hello'}], thinking=True))
        template, tokenizer = [json.loads(x.args[0].data) for x in opened.call_args_list]
        self.assertTrue(template['chat_template_kwargs']['enable_thinking'])
        self.assertTrue(tokenizer['add_special']); self.assertTrue(tokenizer['parse_special'])

    def test_cheque_is_not_spendable_cash(self):
        d = day()
        d['entries'].append(dict(k='income', t='13:00', amount=500, item='Lesson', cheque=True))
        self.assertIn('cheque received, not cashed', records.compact(records.project(d)))

    def test_earlier_matched_statement_keeps_its_date(self):
        store = records.project(day()); earlier = day(); earlier['date'] = '2026-10-02'
        store['records'] += records.project(earlier)['records']
        self.assertIn('2026-10-02 08:10', records.compact(store, query='gate bolted'))

    def test_runtime_never_constructs_the_failed_checker(self):
        from world.engine import Engine
        from world.world import World
        cfg = Config({'HEGEL_CLAIM_CHECK': '1', 'HEGEL_OUTCOME_MEMORY': '1', 'HEGEL_SHELF': '0'})
        with patch('world.claim_check.from_config', side_effect=AssertionError('audit only')):
            engine = Engine(cfg, World(), Mock())
        self.assertIsNone(engine.claim_guard)

    def test_compact_owl_keeps_thoughts_even_when_evidence_allowance_shrinks(self):
        d = day()
        thought = 'The promise binds the speaker without making its object actual.'
        d['entries'].append(dict(k='diary', t='17:00', text=thought))
        cfg = Config({'HEGEL_OUTCOME_MEMORY': '1', 'HEGEL_EVIDENCE_VIEW': 'compact'})
        seen = []
        def count(messages, thinking=False):
            seen.append(messages[1]['content'])
            return 8000 if len(seen) == 1 else 1000
        mind = Mock()
        mind.prompt_tokens.side_effect = count
        mind.chat.return_value = json.dumps(dict(diary='A considered diary sentence. ' * 8,
                                                revision_log='', theses=[]))
        owl.write(cfg, d, d['state'], mind)
        self.assertGreaterEqual(len(seen), 2)
        for prompt in seen:
            self.assertIn(thought, prompt)
            self.assertIn('[interpretation, not event evidence]', prompt)
            self.assertIn('₹20 Chai: paid', prompt)
        self.assertIn(thought, mind.chat.call_args.args[0][1]['content'])


if __name__ == '__main__':
    unittest.main()
