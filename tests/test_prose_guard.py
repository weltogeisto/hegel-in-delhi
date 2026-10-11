"""The guard edits prose only; source evidence and executed actions stay intact."""
import json
import math
import unittest
from unittest.mock import Mock, patch
from world import records
from world.claim_check import ClaimExtractor, ClaimProtocolError, ProseGuard, sentence_spans


class Extractor:
    def extract(self,text,context=''):
        return [dict(index=i,span=[a,b],sentence=text[a:b],claims=[text[a:b]])
                for i,(a,b) in enumerate(sentence_spans(text))]


class Verifier:
    def score(self,claim,evidence):
        return dict(log_odds=math.log(99) if claim.startswith('Good') else -math.log(99))


class ProseGuardTest(unittest.TestCase):
    def guard(self,extractor=None):
        self.audit=[]
        return ProseGuard(extractor or Extractor(),Verifier(),1,.5,self.audit.append)

    def test_supported_prose_is_byte_identical_and_never_regenerated(self):
        text='  Good first.\n\nGood second. '
        regenerate=Mock(side_effect=AssertionError('must not regenerate'))
        self.assertEqual(text,self.guard().protect(text,'records',regenerate,label='diary'))
        regenerate.assert_not_called()
        self.assertEqual(text,self.audit[0]['original'])
        self.assertEqual('records',self.audit[0]['records'])

    def test_one_regeneration_then_only_the_unsupported_sentence_is_removed(self):
        original='Bad journey. Good opinion.'
        regenerate=Mock(return_value='Good correction.\n\nBad meal. Good ending.')
        result=self.guard().protect(original,'statements and actions',regenerate,label='letter')
        self.assertEqual('Good correction.\n\n Good ending.',result)
        regenerate.assert_called_once_with(['Bad journey.'])
        self.assertEqual(['Bad meal.'],self.audit[-1]['dropped'])
        self.assertEqual(original,self.audit[-1]['original'])
        self.assertIn('Bad meal.',self.audit[-1]['regenerated'])

    def test_a_successful_regeneration_is_not_edited(self):
        regenerate=Mock(return_value='Good now.')
        self.assertEqual('Good now.',self.guard().protect('Bad before.','proof',regenerate,label='owl'))
        self.assertEqual([],self.audit[-1]['dropped'])

    def test_no_factual_claims_preserves_the_argument_without_a_fake_vote(self):
        extractor=Mock();extractor.extract.return_value=[dict(index=0,span=[0,18],sentence='An interpretation.',claims=[])]
        guard=self.guard(extractor);guard.verifier=Mock(side_effect=AssertionError('no claim to check'))
        self.assertEqual('An interpretation.',guard.protect('An interpretation.','proof',Mock(),label='essay'))
        guard.verifier.score.assert_not_called()

    def test_protocol_failure_propagates_without_publishing_unchecked_prose(self):
        guard=self.guard();guard.verifier.score=Mock(side_effect=ClaimProtocolError('missing vote'))
        with self.assertRaisesRegex(ClaimProtocolError,'missing vote'):
            guard.protect('Bad claim.','proof',Mock(),label='diary')

    def test_malformed_regeneration_does_not_become_a_false_verdict(self):
        with self.assertRaisesRegex(ClaimProtocolError,'no text'):
            self.guard().protect('Bad claim.','proof',lambda bad:None,label='diary')

    def test_extractor_keeps_speech_attribution_and_checks_every_sentence(self):
        response=dict(choices=[dict(message=dict(content=json.dumps({'sentences':[
            {'index':0,'claims':['Ramesh said breakfast was ready.']},
            {'index':1,'claims':[]}]})))])
        with patch('world.claim_check.api',return_value=response) as api:
            rows=ClaimExtractor('http://test').extract('Ramesh said breakfast was ready. Freedom requires determination.')
        self.assertEqual(['Ramesh said breakfast was ready.'],rows[0]['claims'])
        self.assertEqual([],rows[1]['claims'])
        self.assertEqual([],api.call_args.args[2]['lora'])
        self.assertFalse(api.call_args.args[2]['chat_template_kwargs']['enable_thinking'])

    def test_extractor_rejects_missing_or_duplicate_sentence_rows(self):
        response=dict(choices=[dict(message=dict(content='{"sentences":[]}'))])
        with patch('world.claim_check.api',return_value=response),self.assertRaises(ClaimProtocolError):
            ClaimExtractor('http://test').extract('A fact.')


class TypedBudgetTest(unittest.TestCase):
    def test_selected_view_reserves_the_cash_and_every_meal_and_warns_about_omissions(self):
        day=dict(date='2026-10-03',entries=[],steps=[],segments=[],state=dict(imprest=60,until='2026-10-03T19:00'))
        day['entries']=[dict(t='08:00',k='said',by='Ramesh',text='A claim. '*200) for _ in range(80)]
        day['steps']=[dict(t='13:00',end='13:30',decision=dict(action='eat',place='home'))]
        view=records.relevant(records.project(day),limit=3000)
        self.assertLessEqual(len(view),3000)
        self.assertIn('cash ₹60',view);self.assertIn('executed eat',view)
        self.assertIn('omissions do not establish absence',view)

    def test_pre_action_view_does_not_authorize_future_eating_or_manuscript_events(self):
        day=dict(date='2026-10-03',entries=[],steps=[],segments=[],state=dict(imprest=60,until='2026-10-03T08:00'))
        sit=dict(time='08:00',place='home',weather='clear',aqi=100)
        ctx=dict(public=[],observations=['Breakfast is laid out.'],greeting=dict(by='Ramesh',says='Everyone has eaten.'))
        store=records.current(day,sit,ctx)
        self.assertFalse(any(r.get('action')=='eat' for r in store['records']))
        self.assertTrue(any(r['kind']=='statement' and not r['verified'] for r in store['records']))
        self.assertEqual([],day['entries']);self.assertEqual([],day['steps'])


class ProseIntegrationTest(unittest.TestCase):
    def setUp(self):
        from test_world import Sandbox
        from datetime import date
        self.box=Sandbox();self.box.cfg.outcome_memory=True;self.engine=self.box.engine()
        self.day=self.engine.new_day(self.box.days.load('2026-10-02'),date(2026,10,3))

    def tearDown(self):
        self.box.close()

    def test_manuscript_guard_changes_only_text_and_receives_typed_evidence(self):
        from datetime import date
        from world.world import at_dt
        guard=Mock();guard.protect.return_value='Good corrected manuscript.'
        self.engine.claim_guard=guard
        manuscript=dict(title='On a case',text='Bad invented events.',kind='essay',to=None,continues=False)
        ctx=dict(t=at_dt(date(2026,10,3),480),records=records.project(self.day))
        result=self.engine.check_writing(manuscript,ctx)
        self.assertEqual('Bad invented events.',manuscript['text'])
        self.assertEqual(dict(manuscript,text='Good corrected manuscript.'),result)
        self.assertIn('[event ',guard.protect.call_args.args[1])

    def test_owl_passes_each_prose_field_to_guard_and_retains_interpretations_as_such(self):
        from world import owl
        self.day['entries'].append(dict(k='diary',t='08:00',text='I interpret this difficulty as freedom.'))
        self.day['entries'].append(dict(k='said',t='09:00',by='Ramesh',text='Everyone ate dinner.'))
        guard=Mock();guard.protect.side_effect=lambda text,*a,**kw:text
        mind=Mock();mind.chat.return_value=json.dumps(dict(diary='Good diary. '*12,
            revision_log='A judgment.',depesche='A dispatch.',theses=[]))
        owl.write(self.box.cfg,self.day,self.day['state'],mind,depesche_n=1,claim_guard=guard)
        self.assertEqual(3,guard.protect.call_count)
        for call in guard.protect.call_args_list:
            self.assertIn('[statement ',call.args[1]);self.assertIn('unverified',call.args[1])
            self.assertNotIn('I interpret this difficulty',call.args[1])
        request=mind.chat.call_args.args[0][1]['content']
        self.assertIn('[interpretation, not event evidence]',request)
        self.assertIn('I interpret this difficulty',request)

    def test_replayed_canonical_bill_cannot_charge_again_across_a_day_boundary(self):
        from datetime import date
        from world.world import at_dt
        st=self.day['state'];st['imprest']=1000
        bill=dict(to='Ramesh',why='Laundry',amount=100,charge_id='one-bill',at='home')
        st['owed']=[dict(bill)]
        _,first=self.engine.world.settle(at_dt(date(2026,10,3),480),st,'home',['ramesh'],{})
        self.assertEqual(1,len(first));self.assertEqual(900,st['imprest'])
        nextday=self.engine.new_day(self.day,date(2026,10,4));st=nextday['state'];st['owed']=[dict(bill)]
        with self.assertLogs('world','WARNING'):
            _,replayed=self.engine.world.settle(at_dt(date(2026,10,4),480),st,'home',['ramesh'],{})
        self.assertEqual([],replayed);self.assertEqual(900,st['imprest'])
        self.assertEqual([],st['owed'])

    def test_two_identical_unidentified_purchases_remain_distinct(self):
        from datetime import date
        from world.world import at_dt
        st=self.day['state'];st['imprest']=1000
        bill=dict(to='Ramesh',why='Chai',amount=20,at='home')
        st['owed']=[dict(bill),dict(bill)]
        _,paid=self.engine.world.settle(at_dt(date(2026,10,3),480),st,'home',['ramesh'],{})
        self.assertEqual(960,st['imprest']);self.assertEqual(2,len(paid))
        self.assertNotEqual(paid[0]['charge_id'],paid[1]['charge_id'])

    def test_replayed_purchase_does_not_charge_cash_or_create_a_second_voucher(self):
        from datetime import date
        from world.world import at_dt
        from test_world import answer
        st=self.day['state'];st['place']='lodhi'
        sit,ctx=self.engine.world.situation(at_dt(date(2026,10,3),540),st,self.day)
        ans=answer(action='buy',place='lodhi',minutes=5,buys=[dict(item='Chai',price_inr=20)])
        errors,_,rep=self.engine.world.check(ans,sit,ctx,st);self.assertEqual([],errors)
        self.engine.world.apply(rep[0],rep[1],sit,ctx,st,self.day)
        cash=st['imprest'];vouchers=len(st['account']['vouchers'])
        with self.assertLogs('world','WARNING'):
            self.engine.world.apply(rep[0],rep[1],sit,ctx,st,self.day)
        self.assertEqual(cash,st['imprest'])
        self.assertEqual(vouchers,len(st['account']['vouchers']))

    def test_new_counter_does_not_reuse_a_legacy_settled_charge(self):
        st=self.day['state'];st['charge_seq']=0;st['settled_charges']=['charge:1','charge:2']
        self.assertEqual('charge:3',self.engine.world.new_charge(st))


if __name__=='__main__':unittest.main()
