"""Training 1 corrections: CPU fixtures, no model/network/rater actions."""
import copy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

from tools import chapter_splits as splits, voice_confirmation as confirm, voice_dashboard as dash
from tools import hegel_test_round2 as bench, hegelizer_round2 as data2
from tools.recorded_llama import json_bytes
from world import restyle, shelf
from pc import restyle_round2 as trainer
from tests.test_hegel_test_round2 import prepared, result, thought, CAST, COPY
from tests.test_restyle_round2 import data_folder


def unit(identity, text, parent=None, kind='full'):
    return {'id': identity, 'parent_id': parent or identity, 'kind': kind,
            'original': text, 'work': 'fixture', 'split': 'train'}


def fresh_days():
    return [{'n': 1, 'state': {'people': ['ramesh']}}] + [
        {'n': n, 'steps': []} for n in [12, 13, 24, 25, 26, 27]] + [
        {'n': n, 'segments': [{'from': '09:00', 'to': '12:00', 'mode': 'awake', 'at': 'home'},
                             {'from': '12:00', 'to': '21:00', 'mode': 'awake', 'at': 'shop'}],
         'steps': [{'t': '10:00' if i % 2 else '13:00', 'present': ['Ramesh'] if i % 2 else [],
                    'mind': {'source': 'mind'}, 'decision': {'thought': thought(n * 100 + i)}}
                   for i in range(8)]} for n in range(14, 24)]


def sealed(root):
    days = root / 'raw'; days.mkdir()
    for day in fresh_days():
        (days / (str(day['n']) + '.json')).write_bytes(json_bytes(day))
    cast = root / 'cast.json'; cast.write_bytes(json_bytes(CAST))
    cases = bench.REPO / 'mind/situations.json'
    soul = bench.REPO / 'mind/soul.md'
    reference = root / 'shelf'; reference.write_bytes(b'fixture shelf')
    out = root / 'confirm'
    legacy = root / 'development'; legacy.mkdir()
    legacy_out, _ = prepared(legacy)
    confirm.preregister(out, 'a' * 40, [legacy_out / 'private/plan.json'])
    receipt = confirm.seal(out, days, cast, cases, soul, reference)
    return out, receipt


class ChapterTest(unittest.TestCase):
    def test_crossing_and_ambiguous_chapters_unite_with_short_parent(self):
        units = [unit('a', 'alpha'), unit('b', 'beta'), unit('c', 'gamma'),
                 unit('a/short1', 'alpha', 'a', 'short')]
        got = splits.assign(units, {'a': ['one', 'two'], 'b': ['two', 'three'], 'c': ['four']})
        self.assertEqual(got['group_count'], 2)
        self.assertEqual(got['assignments']['a'], got['assignments']['a/short1'])
        self.assertEqual(got['assignments']['a']['split'], got['assignments']['b']['split'])
        self.assertEqual(units[0]['split'], 'train')
        self.assertEqual(got, splits.assign(list(reversed(units)), {'c': ['four'], 'b': ['two', 'three'], 'a': ['one', 'two']}))

    def test_source_matches_include_every_repeated_occurrence_and_boundary(self):
        passages = ['Same authentic words.', 'Next authentic words.', 'Same authentic words.']
        units = [unit('repeat', 'Same authentic words.'), unit('bridge', 'Same authentic words. Next authentic words.')]
        got = splits.memberships(units, passages, ['A', 'B', 'C'])
        self.assertEqual(got['repeat'], ['A', 'C'])
        self.assertEqual(got['bridge'], ['A', 'B'])
        with self.assertRaises(ValueError):
            splits.memberships([unit('bad', 'invented target')], passages, ['A', 'B', 'C'])

    def test_heading_reconstruction_and_unheaded_work_are_conservative(self):
        text = '# Chapter One\n\nFirst sentence.\n\n## Subsection\n\nSecond sentence.\n\n# Chapter Two\n\nThird sentence.'
        expected = shelf.split_passages(text, 'head')
        passages, chapters, _ = splits.chapter_passages('book', text, expected, 'head')
        self.assertEqual(passages, [t for _, t in expected])
        self.assertEqual(chapters[0], chapters[1])
        self.assertNotEqual(chapters[1], chapters[2])
        bare = 'A whole unheaded work.'
        _, chapters, _ = splits.chapter_passages('book', bare, shelf.split_passages(bare), 'head')
        self.assertEqual(len(set(chapters)), 1)
        with self.assertRaises(ValueError):
            splits.chapter_passages('book', text, [('wrong', 'text')], 'head')

    def test_historical_index_filter_and_mending_are_mapped_without_new_targets(self):
        cleaned = '# One\n\nA scanned wOrd.\n\n# Two\n\nDropped text.\n\n# Three\n\nKept text.'
        expected = [('One', 'A scanned word.'), ('Three', 'Kept text.')]
        texts, chapters, _ = splits.chapter_passages('book', cleaned, expected, 'head', lambda t: t.replace('wOrd', 'word'))
        self.assertEqual(texts, [t for _, t in expected])
        self.assertNotEqual(chapters[0], chapters[1])
        with self.assertRaises(ValueError):
            splits.chapter_passages('book', cleaned, expected, 'head')

    def test_split_uses_full_unit_weight_not_percentage_of_unequal_groups(self):
        units = [unit('u' + str(i), 'text' + str(i)) for i in range(100)]
        membership = {u['id']: ['g' + str(i // 10)] for i, u in enumerate(units)}
        got = splits.assign(units, membership, share=0.20)
        self.assertEqual(got['held_full_target'], 20)
        self.assertEqual(got['held_full_selected'], 20)
        self.assertEqual(sum(a['split'] == 'held' for a in got['assignments'].values()), 20)

    def test_one_group_unknown_parent_and_rewritten_short_are_refused(self):
        with self.assertRaises(ValueError):
            splits.assign([unit('a', 'alpha')], {'a': ['only']})
        for broken in [unit('short', 'alpha', 'missing', 'short'), unit('short', 'changed', 'a', 'short')]:
            with self.assertRaises(ValueError):
                splits.assign([unit('a', 'alpha'), unit('b', 'beta'), broken], {'a': ['one'], 'b': ['two']})

    def test_trainer_projects_splits_without_rewriting_any_frozen_data(self):
        with tempfile.TemporaryDirectory() as td:
            folder = data_folder(Path(td))
            before = {p.name: p.read_bytes() for p in folder.iterdir()}
            units = data2.strict_rows(folder / data2.UNITS)
            assignments = {u['id']: {'split': 'held' if i < 20 else 'train', 'group': 'group' + str(i)} for i, u in enumerate(units)}
            with mock.patch.object(splits, 'load_manifest', return_value=({'assignments': assignments}, 'b' * 64)):
                rows, gate = trainer.load_data(folder, folder / 'manifest.json')
            self.assertEqual(len(rows['held']), 40)
            self.assertEqual(gate['chapter_splits_sha256'], 'b' * 64)
            self.assertTrue(any(r['original_split'] != r['split'] for r in rows['held']))
            self.assertEqual(before, {p.name: p.read_bytes() for p in folder.iterdir()})


class ConfirmationTest(unittest.TestCase):
    def test_day_balance_scene_spread_and_order_independence(self):
        days = fresh_days()
        selected, report = confirm.select(days, CAST, [confirm.text_hash(thought(i)) for i in range(40)])
        self.assertEqual(len(selected), 40)
        self.assertEqual(set(report['by_day'].values()), {4})
        self.assertEqual(report['scene_count'], 2)
        self.assertEqual(selected, confirm.select(list(reversed(days)), CAST, [confirm.text_hash(thought(i)) for i in range(40)])[0])
        self.assertFalse(set(r['day'] for r in selected) & {12, 13, 24, 25, 26, 27})

    def test_actual_mind_names_development_duplicates_and_short_are_excluded(self):
        days = fresh_days()
        development = next(d for d in days if d['n'] == 12)
        target = next(d for d in days if d['n'] == 14)
        development['steps'] = [copy.deepcopy(target['steps'][0])]
        target['steps'][0]['decision']['thought'] = thought(0)
        target['steps'][1]['mind']['source'] = 'stub'
        target['steps'][2]['decision']['thought'] = 'Mrs. Kapoor ' + thought(888)
        target['steps'][3]['decision']['thought'] = 'short'
        selected, report = confirm.select(days, CAST, [confirm.text_hash(thought(i)) for i in range(40)])
        self.assertFalse({'14:0', '14:1', '14:2', '14:3'} & {r['id'] for r in selected})
        self.assertTrue(all(report['excluded'][reason] >= 1 for reason in
                            ['development_or_duplicate', 'not_actual_mind', 'later_name', 'under40words']))

    def test_unused_thought_on_a_legacy_source_day_remains_eligible(self):
        days = fresh_days()
        legacy_day = next(d for d in days if d['n'] == 12)
        legacy_day['steps'] = [dict(t='10:00', present=[], mind={'source': 'mind'},
                             decision={'thought': thought(i)}) for i in [0, 90001]]
        selected, _ = confirm.select(days, CAST, [confirm.text_hash(thought(0))])
        ids = {r['id'] for r in selected}
        self.assertNotIn('12:0', ids)
        self.assertIn('12:1', ids)

    def test_underfilled_or_missing_provenance_does_not_relax_rule(self):
        for days in [fresh_days()[:-9], fresh_days()[1:], fresh_days() + [fresh_days()[-1]]]:
            with self.assertRaises(ValueError):
                confirm.select(days, CAST, [confirm.text_hash(thought(i)) for i in range(40)])

    def test_seal_validates_inputs_and_key_and_refuses_reselection(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            out, receipt = sealed(root)
            verified, checksum = confirm.verify_seal(out / 'SEAL.json')
            self.assertEqual(json_bytes(verified), json_bytes(receipt))
            self.assertNotIn('cohort', receipt)
            self.assertNotIn('key', receipt)
            self.assertEqual(len(checksum), 64)
            with self.assertRaises(FileExistsError):
                confirm.seal(out, root / 'raw', root / 'cast.json', bench.REPO / 'mind/situations.json', bench.REPO / 'mind/soul.md', root / 'shelf')
            (out / 'private/inputs/day-14.json').write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError, 'source changed'):
                confirm.verify_seal(out / 'SEAL.json')

    def test_confirmation_refuses_run_until_one_post_tuning_profile_is_frozen(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            out, _ = sealed(root)
            client = SimpleNamespace(model='qwen', lora=[{'id': 1, 'scale': 0.8}])
            with self.assertRaises(FileNotFoundError):
                confirm.verify_release(out, 'adapter', 'fixed', client)
            legacy = root / 'legacy'; legacy.mkdir()
            legacy_out, plan = prepared(legacy)
            weights = root / 'adapter.gguf'; weights.write_bytes(b'fake weights')
            confirm.lock_profile(out, weights, 'fixed', 1, 0.8, legacy_out, result(plan, 'control'), result(plan))
            self.assertEqual(len(confirm.verify_release(out, 'adapter', 'fixed', client)), 64)
            with self.assertRaises(ValueError):
                confirm.verify_release(out, 'adapter', 'another', client)
            weights.write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError, 'adapter changed'):
                confirm.verify_release(out, 'adapter', 'fixed', client)


class DashboardTest(unittest.TestCase):
    def test_retention_counts_mentions_numbers_and_negations_not_just_sets(self):
        got = dash.retention('Ramesh said Ramesh cannot pay 12.50 and will not pay twenty.',
                             'Ramesh can pay 12.50 and twenty.', CAST)
        self.assertEqual(got['names']['retained'], 1)
        self.assertEqual(got['names']['required'], 2)
        self.assertEqual(got['numbers']['retained'], 2)
        self.assertEqual(got['negations']['retained'], 0)
        self.assertEqual(got['negations']['required'], 2)

    def test_proposition_call_is_plain_temperature_zero_and_invalid_is_unknown(self):
        client = SimpleNamespace(model='qwen', lora=None, chat=mock.Mock(return_value=('{"added":["a claim"],"omitted":[]}', 'stop')))
        got = dash.meaning_propositions(client, 'input', 'output', 'id', 1831)
        self.assertTrue(got['format_valid'])
        self.assertEqual(client.chat.call_args.args[2], 0.0)
        for raw, finish in [('{"added":[],"added":[],"omitted":[]}', 'stop'),
                            ('{"added":[],"omitted":[]}', 'length'), ('{"added":true,"omitted":[]}', 'stop'),
                            ('```' + 'json\n{"added":[],"added":[],"omitted":[]}\n' + '```', 'stop'),
                            ('<think>reasoning</think>\n' + '```' + 'json\n{"added":[],"added":[],"omitted":[]}\n' + '```', 'stop'),
                            ('```' + 'json\n{"added":[],"omitted":[]}\n' + '```', 'length'),
                            ('```' + 'json\n{"added":[],"omitted":\n' + '```', 'stop')]:
            client.chat.return_value = (raw, finish)
            value = dash.meaning_propositions(client, 'input', 'output', 'id', 1831)
            self.assertFalse(value['format_valid'])
            self.assertIsNone(value['added'])
        client.lora = [{'id': 0, 'scale': 1}]
        with self.assertRaises(ValueError):
            dash.meaning_propositions(client, 'input', 'output', 'id', 1831)

    def test_wrapped_propositions_keep_dashboard_totals_available(self):
        payload = '{"added":["a new claim"],"omitted":["a missing claim"]}'
        wrappers = [
            '```' + 'json\n' + payload + '\n' + '```',
            '```' + '\n' + payload + '\n' + '```',
            '<think>Reasoning\nabout the texts.</think>\n' + payload,
            ' \n<think>Reasoning\nabout the texts.</think>\n' + '```' + 'json\n' + payload + '\n' + '```' + '\n ',
        ]
        client = SimpleNamespace(model='qwen', lora=None, chat=mock.Mock())
        with tempfile.TemporaryDirectory() as td:
            _, plan = prepared(Path(td))
            for raw in wrappers:
                with self.subTest(raw=raw):
                    client.chat.return_value = (raw, 'stop')
                    detail = dash.meaning_propositions(client, 'input', 'output', 'id', 1831)
                    self.assertTrue(detail['format_valid'])
                    self.assertEqual(detail['added'], ['a new claim'])
                    self.assertEqual(detail['omitted'], ['a missing claim'])
                    self.assertEqual(detail['raw'], raw)
                    self.assertFalse(detail['gating'])
                    control, adapter = result(plan, 'control'), result(plan)
                    for row in control['voice'] + adapter['voice']:
                        row['meaning_propositions'] = {'format_valid': True, 'added': [], 'omitted': []}
                    adapter['voice'][0]['meaning_propositions'] = detail
                    report = dash.dashboard(plan, control, adapter, restyle.ShelfGuard([COPY]), CAST, lambda text: 0.34)
                    self.assertEqual(report['summary']['adapter']['propositions_valid_cases'], 40)
                    self.assertEqual(report['summary']['adapter']['propositions_added'], 1)
                    self.assertEqual(report['summary']['adapter']['propositions_omitted'], 1)
                    self.assertNotIn('unavailable', dash.render_html(report))

    def test_guard_before_after_fallback_and_equal_length_delta_preserve_outputs(self):
        with tempfile.TemporaryDirectory() as td:
            _, plan = prepared(Path(td))
            control, adapter = result(plan, 'control'), result(plan)
            adapter['voice'][0]['restyle']['attempts'][0]['raw'] = COPY
            adapter['voice'][0]['restyle'].update(fallback=True, text=adapter['voice'][0]['plain'])
            for row in adapter['voice'] + control['voice']:
                row['meaning_propositions'] = {'format_valid': True, 'added': [], 'omitted': []}
            adapter['voice'][1]['meaning_propositions'] = {'format_valid': False, 'added': None, 'omitted': None}
            before = json_bytes([control, adapter])
            lengths = []
            def delta(text):
                lengths.append(len(text.split()))
                return 0.34
            report = dash.dashboard(plan, control, adapter, restyle.ShelfGuard([COPY]), CAST, delta)
            self.assertEqual(len(set(lengths)), 1)
            self.assertEqual(report['summary']['adapter']['copied12_before'], 1)
            self.assertEqual(report['summary']['adapter']['copied12_after'], 0)
            self.assertEqual(report['summary']['adapter']['fallback_count'], 1)
            self.assertIsNone(report['summary']['adapter']['propositions_added'])
            self.assertEqual(report['summary']['adapter']['propositions_valid_cases'], 39)
            self.assertEqual(before, json_bytes([control, adapter]))
            self.assertFalse(report['gating'])
            self.assertIn('unavailable', dash.render_html(report))

    def test_diagnostic_details_do_not_change_canonical_five_kpis(self):
        with tempfile.TemporaryDirectory() as td:
            _, plan = prepared(Path(td))
            saved = result(plan)
            before = bench.automatic_metrics(saved, lambda text: 0.34)
            for row in saved['voice']:
                row['meaning_propositions'] = {'format_valid': True, 'added': ['diagnostic disagreement'], 'omitted': []}
            self.assertEqual(before, bench.automatic_metrics(saved, lambda text: 0.34))


if __name__ == '__main__':
    unittest.main()
