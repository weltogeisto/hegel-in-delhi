"""Fixed-day evaluation must not look into future state or select successful retries."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from pc.writer_trial import prefix_day, writing_calls, trace_rows, verify


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


if __name__=='__main__':unittest.main()
