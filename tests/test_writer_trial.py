"""Fixed-day evaluation must not look into future state or select successful retries."""
import copy
import contextlib
import io
import json
from argparse import Namespace
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
from pc import writer_trial
from pc.writer_trial import paired_jobs, whole_shelf_jobs, shelf_writing, prefix_day, writing_calls, trace_rows, verify


class WriterTrialTest(unittest.TestCase):
    def test_prefix_excludes_future_sittings_owl_steps_and_final_cash(self):
        day=dict(date='2026-10-03',complete=True,records={'future':True},owl={'diary':'future'},
            entries=[dict(t='09:00',k='said',text='earlier'),dict(t='12:00',k='writing',text='future')],
            steps=[dict(t='09:00'),dict(t='12:00')],segments=[dict(to='09:30'),dict(to='12:30')],
            observations=[dict(t='09:00'),dict(t='12:00')],plan=dict(written='13:00'),state=dict(imprest=0))
        frozen=copy.deepcopy(day);before=dict(imprest=100,until='2026-10-03T12:00',place='home')
        result=prefix_day(day,'12:00',before)
        self.assertEqual(day,frozen)
        self.assertEqual(before,result['state'])
        self.assertIsNone(result['owl']);self.assertIsNone(result['plan'])
        self.assertNotIn('records',result);self.assertFalse(result['complete'])
        for key in ('entries','steps','segments','observations'):self.assertEqual(1,len(result[key]))

    def test_first_attempt_is_kept_even_if_a_later_retry_succeeded(self):
        first=dict(messages=[dict(role='system',content='persona'),dict(role='user',content='Saturday, 12:00 Delhi time.'),{},{}],
            response_format={'json_schema':{'schema':{'properties':{'continues':{}}}}},value='failed first')
        second=dict(first,value='successful retry')
        self.assertIs(writing_calls([first,second])['12:00'],first)

    def test_old_native_schema_is_recognized(self):
        row=dict(messages=[{},dict(content='Saturday, 08:30 Delhi time.'),{},{}],json_schema={'properties':{'continues':{}}})
        self.assertEqual({'08:30':row},writing_calls([row]))

    def test_nonwriting_claim_regeneration_is_not_a_sitting(self):
        row=dict(messages=[{},dict(content='Saturday, 08:30 Delhi time.'),{},{}],json_schema={'properties':{'text':{}}})
        self.assertEqual({},writing_calls([row]))

    def test_both_saved_trace_formats_retain_pre_step_state(self):
        for field in ('step','result'):
            with self.subTest(field=field),tempfile.TemporaryDirectory() as temp:
                root=Path(temp);r=dict(date='2026-10-03',before={'imprest':100},**{field:{'t':'12:00'}})
                (root/'step-ledger.jsonl').write_text(json.dumps(r)+'\n')
                rows,_=trace_rows(root,'2026-10-03')
                self.assertEqual({'imprest':100},rows['12:00']['before'])

    def test_changed_source_fails_hash_gate(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);p=root/'source';p.write_text('changed')
            (root/'protocol.json').write_text(json.dumps({'protected_sha256':{str(p):'old'}}))
            with self.assertRaisesRegex(ValueError,'Frozen input changed'):verify(root)

    def test_seeded_schedule_keeps_each_ab_pair_adjacent(self):
        sources = {'one': {'times': ['12:00', '14:00']}, 'two': {'times': []}}
        jobs = paired_jobs(sources)
        self.assertEqual(jobs, paired_jobs(sources))
        self.assertEqual(24, len(jobs))
        first_variants = set()
        for a, b in zip(jobs[::2], jobs[1::2]):
            self.assertEqual({'A', 'B'}, {a['variant'], b['variant']})
            self.assertEqual([a[k] for k in ('day', 'kind', 'time', 'seed')],
                             [b[k] for k in ('day', 'kind', 'time', 'seed')])
            first_variants.add(a['variant'])
        self.assertEqual({'A', 'B'}, first_variants)

    def test_whole_passage_test_pairs_the_same_ten_seeds(self):
        jobs = whole_shelf_jobs()
        self.assertEqual(20, len(jobs))
        self.assertEqual(jobs, whole_shelf_jobs())
        self.assertEqual(set(range(2026101220,2026101230)), {j['seed'] for j in jobs})
        for a,b in zip(jobs[::2],jobs[1::2]):
            self.assertEqual(a['seed'], b['seed'])
            self.assertEqual({'A','B'}, {a['variant'],b['variant']})

    def test_events_only_query_does_not_remove_unknowns_from_writer_input(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            case=dict(id='karl',date='2026-10-03',time='12:00',place='home',
                      events=[dict(text='A boy copied a correction.')],unknowns=['The teacher name'])
            (root/'karl.json').write_text(json.dumps(case))
            engine=Mock();engine.soul='persona'
            engine.days.load.return_value={'state':dict(imprest=100,wearing='coat')}
            queried=[]
            engine.offer.side_effect=lambda day,sit,ctx,st: queried.append(sit['event']) or []
            with patch('pc.writer_trial.shelf.load'):
                shelf_writing(engine,{'variant':'B'},root,events_only=True,version='new')
            self.assertEqual(['A boy copied a correction.'],queried)
            shown=engine.write_chat.call_args.args[0][1]['content']
            self.assertIn('Unknown: The teacher name',shown)
            self.assertIn('private, unsent letter to Karl',shown)

    def test_packet_counts_sentence_iterator_without_revealing_shelf_or_key(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp); repo = base/'repo'; out = base/'run'
            result = out/'T4'/'private-job'; result.mkdir(parents=True)
            (out/'T4'/'run.exit').write_text('0\n')
            text = 'The first assertion follows. The second tests it.'
            (result/'result.json').write_text(json.dumps(dict(job=dict(variant='NEW', seed=42),
                result=dict(text=text), evidence=dict(case={'id':'karl'}, shelf=[{'text':'PRIVATE SHELF'}]))))
            key = base/'private'/'key.json'
            args = Namespace(out=out,task='T4',review='review',private_key=key)
            with patch.object(writer_trial, 'ROOT', repo), patch.object(writer_trial, 'verify'), contextlib.redirect_stdout(io.StringIO()):
                writer_trial.packet(args)
            target = repo/'mind/results/review'
            texts = json.loads((target/'texts.json').read_text())
            self.assertEqual(2, len(texts[0]['sentences']))
            self.assertEqual(text, texts[0]['text'])
            self.assertEqual(2, json.loads((target/'manifest.json').read_text())['sentences'])
            packet = (target/'packet.md').read_text()
            self.assertNotIn('PRIVATE SHELF', packet)
            self.assertNotIn('NEW', packet)
            self.assertEqual('NEW', json.loads(key.read_text())['keys'][texts[0]['id']]['variant'])
            self.assertFalse((target/'key.json').exists())


if __name__=='__main__':unittest.main()
