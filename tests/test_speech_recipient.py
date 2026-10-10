"""Speech routing must not confuse a third-person mention with an explicit addressee."""
import copy,json,tempfile,unittest
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from unittest import mock
from world import contract,voices
from world.engine import Engine
from world.world import World,at_dt
R=Path(__file__).resolve().parents[1]

def answer(**kw):
 a=dict(thought='Masterji sent me to ask the bookseller about a book.',action='talk',place='khan',minutes=15,says='Masterji has sent me to you. Have you a history of Delhi?',buys=[],revision=None)
 a.update(kw);return a

class RecipientTests(unittest.TestCase):
 def setUp(self):
  self.w=World();self.present=['masterji','sunil','bookseller']
 def test_explicit_background_recipient_beats_third_person_name(self):
  self.assertEqual(voices.pick(self.w.cast,answer()['says'],self.present,recipient='bookseller'),'bookseller')
 def test_legacy_omitted_and_null_retain_existing_fallback(self):
  self.assertEqual(voices.pick(self.w.cast,answer()['says'],self.present),'masterji')
  self.assertEqual(voices.pick(self.w.cast,answer()['says'],self.present,recipient=None),'masterji')
  self.assertFalse(contract.check_shape(answer())[0]);self.assertFalse(contract.check_shape(answer(speaks_to=None))[0])
 def test_unknown_or_absent_id_cannot_silently_pick_someone_else(self):
  for recipient in ['unknown','ramesh']:
   with self.subTest(recipient=recipient),self.assertRaises(ValueError):voices.pick(self.w.cast,'Masterji is here.',self.present,recipient=recipient)
 def test_nonstring_optional_recipient_fails_shape(self):
  for value in [False,3,[],{}]:
   with self.subTest(value=value):self.assertTrue(contract.check_shape(answer(speaks_to=value))[0])
 def fixture(self):
  day=json.loads((R/'docs/days/2026-10-02.json').read_text());day.update(date='2026-10-03',n=2,steps=[],entries=[],segments=[],complete=False)
  st=day['state'];st.update(place='khan',asleep=False,today={},people=list(self.w.cast),beats=[b['id'] for b in self.w.beats]);self.w.ledger(st)
  t=at_dt(date(2026,10,3),19*60);st['until']=t.isoformat(timespec='minutes')
  sit=dict(day='Saturday 3 October',time='19:00',place='khan',weather='30 °C, clear',aqi='unknown',outfit='white cotton kurta',imprest_left=st['imprest'],present=[self.w.short(c) for c in self.present],open_now=['home','khan','iic'],event='The bookseller is here.')
  ctx=dict(t=t,present=list(self.present),beat=None,public=[],recent=[],known_text='Masterji, Sunil and the bookseller have met him.')
  return day,st,t,sit,ctx
 def test_world_refuses_unknown_absent_and_empty_recipient(self):
  _,st,_,sit,ctx=self.fixture()
  for cid in ['unknown','ramesh','']:
   with self.subTest(cid=cid):
    errors,_,_=self.w.check(answer(speaks_to=cid),sit,ctx,st);self.assertTrue(any('speaks_to' in e for e in errors))
 def test_recipient_requires_words_and_is_valid_at_origin_before_move(self):
  _,st,_,sit,ctx=self.fixture()
  for speech in [None,'','   ']:
   with self.subTest(speech=speech):self.assertTrue(self.w.check(answer(speaks_to='bookseller',says=speech),sit,ctx,st)[0])
  a=answer(speaks_to='bookseller',action='walk',place='home');errors,_,rep=self.w.check(a,sit,ctx,st)
  self.assertFalse(errors);self.assertEqual(rep[0]['speaks_to'],'bookseller')
 def test_render_lists_ids_without_altering_legacy_scene(self):
  _,_,_,sit,_=self.fixture();legacy=contract.render(sit);self.assertNotIn('Recipient IDs here:',legacy)
  sit['speakers']=[dict(id=c,name=self.w.short(c)) for c in self.present];rendered=contract.render(sit)
  self.assertIn('bookseller = the bookseller',rendered);self.assertIn('before any move',rendered);self.assertTrue(rendered.endswith(contract.ASK))
 def test_applied_speech_and_activity_name_only_the_explicit_recipient(self):
  day,st,_,sit,ctx=self.fixture();a=answer(speaks_to='bookseller');errors,_,rep=self.w.check(a,sit,ctx,st);self.assertFalse(errors)
  self.w.apply(*rep,sit,ctx,st,day)
  spoken=next(e for e in day['entries'] if e['k']=='said' and e['text']==a['says'])
  self.assertEqual(spoken['to'],'the bookseller');self.assertEqual(spoken['to_id'],'bookseller')
  self.assertTrue(any('Talking with the bookseller' in s.get('now','') for s in day['segments']))
  self.assertFalse(any('Talking with Masterji' in s.get('now','') for s in day['segments']))
 def test_reply_routes_to_explicit_id(self):
  e=Engine.__new__(Engine);e.world=self.w;e.voice=mock.Mock(return_value={'by':'The bookseller','says':'A school history, sir.','does':None})
  result=e.reply({}, {},dict(present=self.present),answer()['says'],recipient='bookseller')
  self.assertEqual(e.voice.call_args.args[0],'bookseller');self.assertEqual(result['by'],'The bookseller')
 def test_actual_step_passes_recipient_and_preserves_spoken_provenance(self):
  day,st,t,_,_=self.fixture()
  with tempfile.TemporaryDirectory(prefix='hegel-recipient-test-') as tmp:
   cfg=SimpleNamespace(repo=R,docs=Path(tmp)/'docs',soul_file=R/'mind/soul-v2.md',shelf=False)
   mind=mock.Mock();mind.source='stub';mind.ready=True;mind.decide.return_value=json.dumps(answer(speaks_to='bookseller'))
   e=Engine(cfg,self.w,mind);e.greet=mock.Mock(return_value=True);e.memory.recall=mock.Mock(return_value=[]);e.memory.recent_thoughts=mock.Mock(return_value=[]);e.memory.known_text=mock.Mock(return_value='Masterji, Sunil and the bookseller have met him.')
   e.voice=mock.Mock(return_value={'by':'The bookseller','says':'School histories, sir.','does':None})
   with mock.patch.object(self.w,'present_ids',return_value=self.present):step=e.step(day,t)
   self.assertEqual(step['mind']['source'],'stub');self.assertEqual(step['mind']['attempts'],1)
   self.assertEqual(step['voice']['by'],'The bookseller');self.assertEqual(e.voice.call_args.args[0],'bookseller')
   self.assertEqual(next(x for x in day['entries'] if x['k']=='said' and x['text']==answer()['says'])['to_id'],'bookseller')
   self.assertIn('Recipient IDs here:',mind.decide.call_args.args[0][-1]['content'])

if __name__=='__main__':unittest.main()
