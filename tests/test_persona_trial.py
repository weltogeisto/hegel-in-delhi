"""A persona experiment must isolate its intervention and retain its blind."""
import contextlib
import io
import json
from argparse import Namespace
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch
from pc import persona_trial, writer_trial


class PersonaTrialTest(unittest.TestCase):
    def test_confirmation_has_52_adjacent_letters_with_no_reused_t4c_seed(self):
        jobs = persona_trial.paired_jobs('T4d', 'second-control')
        self.assertEqual(jobs, persona_trial.paired_jobs('T4d', 'second-control'))
        self.assertEqual(52, len(jobs))
        old_seeds = {j['seed'] for j in persona_trial.paired_jobs()}
        self.assertFalse(old_seeds & {j['seed'] for j in jobs})
        self.assertEqual({'karl': 12, 'fare': 20, 'second-control': 20},
            {case: sum(j['case'] == case for j in jobs) for case in {j['case'] for j in jobs}})
        self.assertEqual(52, len({j['id'] for j in jobs}))
        for a, b in zip(jobs[::2], jobs[1::2]):
            self.assertEqual((a['case'], a['seed']), (b['case'], b['seed']))
            self.assertEqual({'A', 'B'}, {a['variant'], b['variant']})

    def test_confirmation_requires_a_distinct_explicit_control(self):
        for control in (None, '', 'karl', 'fare'):
            with self.subTest(control=control), self.assertRaisesRegex(ValueError, 'distinct second'):
                persona_trial.paired_jobs('T4d', control)

    def test_control_must_exist_and_primary_cases_remain_letters(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp); source = base/'cases.json'; out = base/'out'
            cases = [dict(id='karl', kind='letter'), dict(id='fare', kind='letter')]
            args = Namespace(task='T4d', control_case='arch', cases=source, out=out)
            source.write_text(json.dumps(dict(writing_cases=cases)))
            with self.assertRaisesRegex(ValueError, 'Every declared'):
                persona_trial.prepare(args)
            self.assertFalse(out.exists())
            cases.append(dict(id='arch', kind='decision'))
            source.write_text(json.dumps(dict(writing_cases=cases)))
            with self.assertRaisesRegex(ValueError, 'letter or essay'):
                persona_trial.prepare(args)
            self.assertFalse(out.exists())

    def test_changed_confirmation_schedule_never_reaches_the_server(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp); jobs = persona_trial.paired_jobs('T4d', 'second-control')
            jobs[0]['seed'] = 2026101220
            (out/'T4d-jobs.json').write_text(json.dumps(jobs))
            args = Namespace(task='T4d', out=out, t3_root=out, t3_packet=out)
            with patch.object(persona_trial, 'require_t3_finished'), \
                 patch.object(writer_trial, 'verify', return_value=dict(task='T4d', second_control='second-control')), \
                 patch.object(writer_trial, 'api') as api:
                with self.assertRaisesRegex(ValueError, 'predeclared paired'):
                    persona_trial.run(args)
            api.assert_not_called()

    def test_same_ten_karl_and_five_control_seeds_are_adjacent_paired(self):
        jobs = persona_trial.paired_jobs()
        self.assertEqual(jobs, persona_trial.paired_jobs())
        self.assertEqual(30, len(jobs))
        self.assertEqual(set(range(2026101220,2026101230)), {j['seed'] for j in jobs if j['case']=='karl'})
        self.assertEqual(set(range(2026101220,2026101225)), {j['seed'] for j in jobs if j['case']=='fare'})
        first = set()
        for a,b in zip(jobs[::2],jobs[1::2]):
            self.assertEqual((a['case'],a['seed']), (b['case'],b['seed']))
            self.assertEqual({'A','B'},{a['variant'],b['variant']})
            first.add(a['variant'])
        self.assertEqual({'A','B'},first)

    def test_configs_use_the_requested_production_persona_switch_only(self):
        with tempfile.TemporaryDirectory() as temp:
            a=persona_trial.configuration(Path(temp),'A')
            b=persona_trial.configuration(Path(temp),'B')
        self.assertEqual('mind/soul.md',a.values['HEGEL_SOUL_FILE'])
        self.assertEqual('mind/soul-bildung.md',b.values['HEGEL_SOUL_FILE'])
        self.assertEqual({'HEGEL_SOUL_FILE'}, {k for k in a.values if a.values[k]!=b.values[k]})
        self.assertFalse(a.shelf_whole);self.assertFalse(b.shelf_whole)
        self.assertFalse(a.claim_check);self.assertFalse(b.outcome_memory)

    def test_control_keeps_its_addressee_cash_and_unknowns_out_of_retrieval(self):
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)
            case=dict(id='fare',kind='letter',date='2026-10-16',time='17:40',place='home',to='Directorate of Estates',
                present=[],cash_inr=240,events=[dict(id='e1',text='A receipt records eighty rupees.')],
                unknowns=['The reimbursement rules'])
            (out/'cases.json').write_text(json.dumps({'fare':case}))
            captured={}
            class Engine:
                soul='the persona'
                days=SimpleNamespace(load=lambda d:dict(state=dict(wearing='coat',imprest=999)))
                def offer(self,day,sit,ctx,st):
                    captured['query']=sit['event'];return []
                def write_chat(self,messages,raw,ctx,st):
                    captured.update(messages=messages,raw=json.loads(raw),state=st);return dict(text='A letter.')
            with patch.object(persona_trial.shelf,'load',return_value=object()):
                result,evidence=persona_trial.write_case(Engine(),dict(case='fare'),out)
            self.assertEqual('A receipt records eighty rupees.',captured['query'])
            prompt=captured['messages'][1]['content']
            self.assertIn('Unknown: The reimbursement rules',prompt)
            self.assertIn('private, unsent letter to Directorate of Estates',prompt)
            self.assertNotIn('Karl',prompt)
            self.assertEqual(240,captured['state']['imprest'])
            self.assertEqual(case,evidence['case'])

    def test_essay_control_stays_an_essay_without_invented_addressee(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)
            case = dict(id='columns',kind='essay',date='2026-10-16',time='13:10',place='iic',
                present=[],events=[dict(id='e1',text='The columns do not touch the roof.')],
                unknowns=['The designer intention'])
            (out/'cases.json').write_text(json.dumps({'columns':case}))
            captured = {}
            class Engine:
                soul = 'the persona'
                days = SimpleNamespace(load=lambda d:dict(state=dict(wearing='coat',imprest=240)))
                def offer(self,day,sit,ctx,st):
                    captured['query'] = sit['event']; return []
                def write_chat(self,messages,raw,ctx,st):
                    captured.update(messages=messages,raw=json.loads(raw)); return dict(text='An essay.')
            with patch.object(persona_trial.shelf,'load',return_value=object()):
                result,evidence = persona_trial.write_case(Engine(),dict(case='columns'),out)
            prompt = captured['messages'][1]['content']
            self.assertIn('This sitting is an essay',prompt)
            self.assertNotIn('unsent letter',prompt)
            self.assertNotIn('Karl',prompt)
            self.assertEqual('The columns do not touch the roof.',captured['query'])
            self.assertEqual(case,evidence['case'])

    def test_generation_waits_for_completed_verified_and_packaged_t3(self):
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp);packet=base/'packet';run=base/'writer-trial-v3/T3';run.mkdir(parents=True)
            with self.assertRaisesRegex(ValueError,'finish successfully'):
                persona_trial.require_t3_finished(base,packet)
            (base/'T3-v3-job.exit').write_text('0\n');(run/'run.exit').write_text('0\n')
            (run/'complete.json').write_text(json.dumps(dict(jobs=138,frozen_inputs_verified=True)))
            cleanup=dict(frozen_inputs_unchanged=True,shared_server_untouched=True,original_days_unchanged=True)
            (run/'cleanup.json').write_text(json.dumps(cleanup))
            with self.assertRaisesRegex(ValueError,'Package T3'):
                persona_trial.require_t3_finished(base,packet)
            packet.mkdir();(packet/'manifest.json').write_text(json.dumps(dict(task='T3',texts=210)))
            persona_trial.require_t3_finished(base,packet)
            cleanup['frozen_inputs_unchanged']=False;(run/'cleanup.json').write_text(json.dumps(cleanup))
            with self.assertRaisesRegex(ValueError,'cleanup verification'):
                persona_trial.require_t3_finished(base,packet)

    def test_persona_packets_use_v2_guide_and_never_expose_assignments(self):
        for task in ('T4c', 'T4d'):
            with self.subTest(task=task):
                self.check_packet(task)

    def check_packet(self, task):
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp);repo=base/'repo';out=base/'out';job=out/task/'private';job.mkdir(parents=True)
            (out/task/'run.exit').write_text('0\n')
            (job/'result.json').write_text(json.dumps(dict(job=dict(case='fare',variant='B',seed=42),
                result=dict(text='The actual cost is recorded.'),evidence=dict(case={'id':'fare'},shelf=['SECRET OFFER']))))
            key=base/'private/key.json'
            with patch.object(writer_trial,'ROOT',repo),patch.object(writer_trial,'verify'),contextlib.redirect_stdout(io.StringIO()):
                writer_trial.packet(Namespace(out=out,task=task,review='persona',private_key=key))
            target=repo/'mind/results/persona';guide=(target/'guide.md').read_text()
            self.assertIn('His commitments',guide);self.assertNotIn('Fixed-day factual audit',guide)
            text=(target/'packet.md').read_text()
            self.assertNotIn('SECRET OFFER',text);self.assertNotIn('variant',text);self.assertNotIn('soul-bildung',text)
            self.assertFalse((target/'key.json').exists())


if __name__=='__main__':unittest.main()
