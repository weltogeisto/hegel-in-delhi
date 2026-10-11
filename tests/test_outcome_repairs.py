"""Execution/evidence and repayment regressions from the failed first smoke."""
import copy
import json
import unittest
from datetime import date
from unittest.mock import Mock, patch

from world import contract, records, voices
from world.claim_check import (ClaimExtractor, ClaimProtocolError, SupportVerifier,
                               claim_evidence, score_extracted)
from world.world import World, at_dt
from test_world import answer, state


class ExecutionEvidenceTest(unittest.TestCase):
    def execute(self, *, place='lodhi', time=727, **decision):
        world = World()
        st = state()
        st.update(place=place, until=f'2026-10-03T{time//60:02d}:{time%60:02d}')
        day = dict(date='2026-10-03', entries=[], steps=[], segments=[], state=st)
        sit, ctx = world.situation(at_dt(date(2026,10,3), time), st, day)
        before = copy.deepcopy(st)
        ans = answer(place=place, **decision)
        errors, _, rep = world.check(ans, sit, ctx, st)
        self.assertEqual([], errors)
        step = world.apply(*rep, sit, ctx, st, day)
        day['steps'].append(step)
        return world, before, day, sit, ctx, rep

    def test_catalogue_snack_is_recorded_when_the_state_consumes_it(self):
        _, before, day, _, _, _ = self.execute(action='buy', buys=[dict(item='Corn',price_inr=40)])
        self.assertEqual(before.get('snacks',0)+1, day['state']['snacks'])
        consumed = [r for r in records.project(day)['records'] if r.get('type')=='consumption']
        self.assertEqual(1, len(consumed))
        receipt = next(e for e in day['entries'] if e['k']=='bag')
        self.assertEqual(receipt['charge_id'], consumed[0]['charge_id'])
        self.assertEqual(('12:07','lodhi','snack'),
                         (consumed[0]['time'],consumed[0]['place'],consumed[0]['food']))
        self.assertIn('eating occurred', records.line(consumed[0]))
        self.assertIn(consumed[0]['id'], records.relevant(records.project(day), limit=3000))

    def test_household_meal_records_service_name_at_execution(self):
        _, _, day, _, _, _ = self.execute(place='home', time=480, action='eat')
        row = next(r for r in records.project(day)['records'] if r.get('type')=='consumption')
        self.assertEqual(('breakfast','meal','home','08:00'),
                         (row['item'],row['food'],row['place'],row['time']))
        self.assertIsNone(row['charge_id'])
        self.assertEqual(at_dt(date(2026,10,3),480).isoformat(timespec='minutes'),day['state']['last_meal'])

    def test_nonfood_purchase_does_not_become_consumption(self):
        _, before, day, _, _, _ = self.execute(place='khan', time=690, action='buy',
                                             buys=[dict(item='Notebook',price_inr=80)])
        self.assertEqual(before.get('snacks'),day['state'].get('snacks'))
        self.assertFalse(any(e['k']=='consumed' for e in day['entries']))

    def test_receipt_replay_does_not_record_or_execute_a_second_snack(self):
        world, _, day, sit, ctx, rep = self.execute(action='buy', buys=[dict(item='Corn',price_inr=40)])
        snacks = day['state']['snacks']
        with self.assertLogs('world','WARNING'):
            world.apply(*rep, sit, ctx, day['state'], day)
        self.assertEqual(snacks,day['state']['snacks'])
        self.assertEqual(1,len([e for e in day['entries'] if e['k']=='consumed']))

    def test_legacy_purchase_never_infers_the_missing_consumption(self):
        day=dict(date='2026-10-03',entries=[dict(k='bag',t='12:07',item='Corn',price=40)],state={})
        self.assertFalse(any(r.get('type')=='consumption' for r in records.project(day)['records']))

    def test_plan_is_evidence_of_intention_and_keeps_its_source(self):
        day=dict(date='2026-10-03',entries=[],state={},
                 plan=dict(written='05:57',items=[dict(time='07:30',intention='Walk to Lodhi Gardens')]))
        before=copy.deepcopy(day)
        row=next(r for r in records.project(day)['records'] if r.get('type')=='intention')
        self.assertEqual('plan.items',row['source']['collection'])
        self.assertEqual('07:30',row['intended_time'])
        self.assertIn('not evidence of execution',records.line(row))
        self.assertEqual(before,day)

    def test_current_location_is_not_its_old_or_planned_location(self):
        day=dict(date='2026-10-03',entries=[],steps=[],state=dict(place='lodhi',until='2026-10-03T06:27'))
        sit=dict(time='06:27',place='lodhi',present=['Sunil'],weather='clear',aqi=50)
        store=records.current(day,sit,dict(public=[],observations=[]))
        text=records.relevant(store,limit=3000)
        self.assertIn('06:27 at lodhi',text)
        self.assertIn('Current location: lodhi. People present now: Sunil.',text)
        self.assertNotIn('at home',text)
        row=next(r for r in store['records'] if r.get('type')=='location')
        old=row['id']; day['state'].update(place='home',until='2026-10-03T09:00')
        self.assertIsNone(records.resolve(day,old))


class RepaymentContractTest(unittest.TestCase):
    def check(self, buy, *, reconcile=True):
        world=World(); st=state(); st.update(place='lodhi',settled_charges=['charge:2'])
        sit,ctx=world.situation(at_dt(date(2026,10,3),540),st,
                                dict(date='2026-10-03',entries=[],steps=[]))
        sit['reconcile_payments']=reconcile
        before=copy.deepcopy(st)
        result=world.check(answer(action='buy',place='lodhi',buys=[buy]),sit,ctx,st)
        self.assertEqual(before,st)
        return result

    def test_existing_settled_charge_cannot_be_paid_under_a_new_purchase_id(self):
        errors,_,rep=self.check(dict(item='Water',price_inr=20,purpose='settlement',source_charge_id='charge:2'))
        self.assertTrue(any('already settled' in e for e in errors))
        self.assertEqual([],rep[1]['buys'])

    def test_different_amount_or_item_cannot_reopen_the_same_charge(self):
        errors,_,_=self.check(dict(item='Corn',price_inr=40,purpose='settlement',source_charge_id='charge:2'))
        self.assertTrue(any('already settled' in e for e in errors))

    def test_unrecorded_vendor_demand_cannot_create_a_debt(self):
        for reference in (None,'invented-charge'):
            errors,_,rep=self.check(dict(item='Water',price_inr=20,purpose='settlement',source_charge_id=reference))
            self.assertTrue(errors);self.assertEqual([],rep[1]['buys'])

    def test_second_legitimate_new_purchase_remains_allowed(self):
        errors,_,rep=self.check(dict(item='Water',price_inr=20,purpose='purchase',source_charge_id=None))
        self.assertEqual([],errors);self.assertEqual(1,len(rep[1]['buys']))

    def test_new_purchase_cannot_also_reference_an_old_charge(self):
        errors,_,_=self.check(dict(item='Water',price_inr=20,purpose='purchase',source_charge_id='charge:2'))
        self.assertTrue(any('source_charge_id=null' in e for e in errors))

    def test_active_contract_rejects_missing_purpose_but_legacy_contract_does_not(self):
        buy=dict(item='Water',price_inr=20)
        self.assertTrue(self.check(buy)[0])
        self.assertEqual([],self.check(buy,reconcile=False)[0])

    def test_schema_is_conditional_and_does_not_mutate_shared_legacy_schema(self):
        before=copy.deepcopy(contract.SCHEMA)
        schema=contract.decision_schema(dict(reconcile_payments=True))
        self.assertIn('purpose',schema['properties']['buys']['items']['required'])
        self.assertIn('source_charge_id',schema['properties']['buys']['items']['required'])
        self.assertEqual(before,contract.SCHEMA)
        self.assertIs(contract.SCHEMA,contract.decision_schema({}))

    def test_npc_receipts_exclude_dialogue_other_places_and_unsettled_bills(self):
        day=dict(entries=[dict(k='said',place='lodhi',text='You owe sixty rupees.'),
            dict(k='bag',place='lodhi',t='06:27',item='Water',price=20,charge_id='charge:2'),
            dict(k='expense',place='lodhi',item='Debt',amount=99,settles=False),
            dict(k='bag',place='khan',item='Secret book',price=300)])
        before=copy.deepcopy(day);text=' '.join(voices.recorded_receipts(day,'lodhi'))
        self.assertIn('charge:2',text);self.assertIn('Water ₹20, settled',text)
        self.assertNotIn('sixty',text);self.assertNotIn('Debt',text);self.assertNotIn('Secret',text)
        self.assertEqual(before,day)


class TypedClaimEvidenceTest(unittest.TestCase):
    def evidence(self):
        day=dict(date='2026-10-03',state={},entries=[
            dict(k='said',t='14:00',by='Ramesh',text='The gate is bolted.'),
            dict(k='writing',t='15:00',title='A draft',text='The gate is bolted.'),
            dict(k='read',t='16:00',title='Newspaper',source='paper',text='The gate is bolted.')],
            plan=dict(written='06:00',items=[dict(time='19:00',intention='Bolt the gate')]))
        return records.render(records.project(day))

    def test_unattributed_event_cannot_use_a_statement_draft_or_plan_as_proof(self):
        evidence=self.evidence();projection=claim_evidence(evidence,'event')
        self.assertNotIn('gate is bolted',projection)
        self.assertNotIn('Bolt the gate',projection)
        self.assertIn('Newspaper',projection)
        self.assertIn('exposure only',projection)
        self.assertIn('gate is bolted',evidence)

    def test_attributed_report_and_plan_keep_their_labelled_source(self):
        evidence=self.evidence()
        self.assertEqual(evidence,claim_evidence(evidence,'statement'))
        self.assertEqual(evidence,claim_evidence(evidence,'intention'))

    def test_verification_receives_original_modal_sentence_as_non_evidence(self):
        verifier=Mock();verifier.score.return_value={'log_odds':1.}
        row=dict(sentence='I shall let the matter of his visit wait.',
                 claims=['He visited.'],claim_kinds=['event'])
        score_extracted(row,self.evidence(),verifier)
        self.assertEqual(row['sentence'],verifier.score.call_args.kwargs['source_sentence'])
        self.assertNotIn('gate is bolted',verifier.score.call_args.args[1])

    def test_extractor_does_not_accept_missing_or_misaligned_kinds(self):
        for kinds in (None,[],['statement','event'],['anything']):
            row=dict(index=0,claims=['Ramesh said the gate was bolted.'])
            if kinds is not None:row['claim_kinds']=kinds
            response=dict(choices=[dict(message=dict(content=json.dumps(dict(sentences=[row]))))])
            with patch('world.claim_check.api',return_value=response),self.assertRaisesRegex(ClaimProtocolError,'claim kinds'):
                ClaimExtractor('http://test').extract('Ramesh said the gate was bolted.')


if __name__=='__main__':unittest.main()
