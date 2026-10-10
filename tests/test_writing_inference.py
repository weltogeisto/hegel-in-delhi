"""Writing-specific reasoning and adapter settings stay out of other world calls."""
import copy,json,os,threading,unittest
from datetime import datetime
from http.server import BaseHTTPRequestHandler,HTTPServer
from unittest import mock
from world import contract
from world.config import Config
from world.engine import Engine
from world.mind import HTTPMind

WORK = dict(title="At the desk",kind="notes",to=None,continues=False,text="The untouched sheet lies beside the first version.")
class Recorder(BaseHTTPRequestHandler):
    calls=[]
    reject_schema=False
    def log_message(self,*args):pass
    def do_GET(self):
        self.send_response(200);self.end_headers();self.wfile.write(b'{"status":"ok"}')
    def do_POST(self):
        body=json.loads(self.rfile.read(int(self.headers['Content-Length'])));type(self).calls.append(body)
        if type(self).reject_schema and 'response_format' in body:
            self.send_response(422);self.end_headers();return
        answer={'choices':[{'message':{'content':json.dumps(getattr(type(self),'answer',WORK)),'reasoning_content':'PRIVATE PREPARATION MUST NOT BECOME A MANUSCRIPT'}}]}
        self.send_response(200);self.end_headers();self.wfile.write(json.dumps(answer).encode())

class WritingInferenceTests(unittest.TestCase):
    def setUp(self):
        Recorder.calls=[];Recorder.reject_schema=False
        self.server=HTTPServer(('127.0.0.1',0),Recorder)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.url=f'http://127.0.0.1:{self.server.server_port}'
        self.messages=[{'role':'system','content':'Hegel.\n## Your answer\nReturn thought/action.'},{'role':'user','content':'At home; a sheet on the desk.'}]
    def tearDown(self):
        self.server.shutdown();self.thread.join();self.server.server_close()
    def test_writing_budget_preserves_final_allowance_and_only_returns_final(self):
        mind=HTTPMind(self.url,writing_reasoning_tokens=768,writing_adapter_scale=0)
        result=mind.chat_writing(self.messages,contract.WRITE_SCHEMA,max_tokens=1100)
        self.assertEqual(json.loads(result),WORK)
        self.assertNotIn('PRIVATE',result)
        body=Recorder.calls[-1]
        self.assertEqual(body['max_tokens'],1868)
        self.assertEqual(body['reasoning_budget_tokens'],768)
        self.assertTrue(body['chat_template_kwargs']['enable_thinking'])
        self.assertEqual(body['lora'],[{'id':0,'scale':0}])
    def test_writing_does_not_change_next_decision_or_npc_request(self):
        mind=HTTPMind(self.url,voice_adapter_scale=0,writing_reasoning_tokens=768,writing_adapter_scale=0)
        mind.chat_writing(self.messages,contract.WRITE_SCHEMA)
        mind.decide(self.messages,{})
        mind.chat_voice(self.messages,contract.VOICE_SCHEMA)
        self.assertEqual([x['lora'][0]['scale'] for x in Recorder.calls],[0,1,0])
        self.assertEqual([x['chat_template_kwargs']['enable_thinking'] for x in Recorder.calls],[True,False,False])
        self.assertNotIn('reasoning_budget_tokens',Recorder.calls[1])
    def test_schema_fallback_preserves_budget_and_adapter(self):
        Recorder.reject_schema=True
        HTTPMind(self.url,writing_reasoning_tokens=512,writing_adapter_scale=0).chat_writing(self.messages,contract.WRITE_SCHEMA)
        self.assertEqual(len(Recorder.calls),2)
        self.assertNotIn('response_format',Recorder.calls[-1])
        self.assertTrue(all(x['reasoning_budget_tokens']==512 and x['lora']==[{'id':0,'scale':0}] for x in Recorder.calls))
    def test_existing_defaults_unchanged(self):
        HTTPMind(self.url).chat_writing(self.messages,contract.WRITE_SCHEMA,max_tokens=1100)
        body=Recorder.calls[-1]
        self.assertEqual(body['max_tokens'],1100)
        self.assertFalse(body['chat_template_kwargs']['enable_thinking'])
        self.assertNotIn('lora',body);self.assertNotIn('reasoning_budget_tokens',body)
    def test_engine_writing_uses_setting_without_mutating_state_or_messages(self):
        e=Engine.__new__(Engine);e.mind=HTTPMind(self.url,writing_reasoning_tokens=768,writing_adapter_scale=0)
        e.world=mock.Mock();e.world.unmet.return_value=[]
        before=copy.deepcopy(self.messages);state={};ctx={'t':datetime(2026,10,8,14),'known_text':'At home.'}
        work=e.write_chat(self.messages,'{"action":"write"}',ctx,state)
        self.assertEqual(work,dict(WORK,mode='chat'));self.assertEqual(state,{})
        self.assertEqual(self.messages,before)
        self.assertTrue(Recorder.calls[-1]['chat_template_kwargs']['enable_thinking'])
        self.assertNotIn('PRIVATE',json.dumps(work))
    def test_prior_manuscripts_reach_writer_but_not_factual_name_validator(self):
        e=Engine.__new__(Engine);e.mind=HTTPMind(self.url,writing_reasoning_tokens=768,writing_adapter_scale=0)
        e.world=mock.Mock();e.world.unmet.return_value=[]
        draft="Earlier manuscripts: previous claims, not independent evidence. I once guessed the register named me."
        ctx={'t':datetime(2026,10,8,14),'known_text':'The file remains unopened.','manuscripts':draft}
        work=e.write_chat(self.messages,'{"action":"write"}',ctx,{})
        self.assertIsNotNone(work)
        self.assertIn(draft,Recorder.calls[-1]['messages'][-1]['content'])
        self.assertEqual(e.world.unmet.call_args.args[1],'The file remains unopened.')
        self.assertNotIn('PRIVATE',str(work))

    def test_optional_nightly_reasoning_preserves_output_allowance_and_privacy(self):
        from types import SimpleNamespace
        from pathlib import Path
        from world import owl
        cfg=SimpleNamespace(repo=Path(__file__).resolve().parents[1],owl_reasoning_tokens=768)
        day=dict(n=2,title='Saturday',holiday=None,entries=[],segments=[],state={})
        result=dict(diary='I considered the day carefully, and recorded only what its evidence permits. The outstanding question remains open.',revision_log='',theses=[])
        with mock.patch.object(Recorder,'answer',result,create=True):
            output=owl.write(cfg,day,{},HTTPMind(self.url))
        self.assertEqual(output['diary'],result['diary']);self.assertNotIn('PRIVATE',str(output))
        self.assertEqual(Recorder.calls[-1]['max_tokens'],1968)
        self.assertEqual(Recorder.calls[-1]['reasoning_budget_tokens'],768)
        with mock.patch.dict(os.environ,{'HEGEL_ENV':os.devnull},clear=True):
            self.assertEqual(Config().owl_reasoning_tokens,0)
            self.assertTrue(Config().thesis_reminders)
            self.assertFalse(Config({'HEGEL_THESIS_REMINDERS':'0'}).thesis_reminders)
            self.assertEqual(Config({'HEGEL_OWL_REASONING_TOKENS':'768'}).owl_reasoning_tokens,768)
            with self.assertRaises(ValueError):Config({'HEGEL_OWL_REASONING_TOKENS':'2049'})

    def test_invalid_configuration_fails_before_network(self):
        for budget in [-1,2049,0.5,'768',True]:
            with self.assertRaises(ValueError):HTTPMind(self.url,writing_reasoning_tokens=budget)
        for scale in [-1,0.5,2,'0']:
            with self.assertRaises(ValueError):HTTPMind(self.url,writing_adapter_scale=scale)
        self.assertEqual(Recorder.calls,[])
    def test_default_preserves_recording_subclasses_with_legacy_chat_signature(self):
        class RecordingMind(HTTPMind):
            def chat(self, messages, schema=None, max_tokens=700, temperature=None):
                self.recorded=(messages,schema,max_tokens)
                return 'recorded without HTTP'
        mind=RecordingMind(self.url)
        self.assertEqual(mind.chat_writing(self.messages,contract.WRITE_SCHEMA), 'recorded without HTTP')
        self.assertEqual(mind.recorded,(self.messages,contract.WRITE_SCHEMA,1100))
        self.assertEqual(Recorder.calls,[])

    def test_cli_configuration_is_opt_in(self):
        from world.__main__ import make_mind
        with mock.patch.dict(os.environ,{'HEGEL_ENV':os.devnull},clear=True):
            self.assertEqual(Config().writing_reasoning_tokens,0)
            self.assertIsNone(Config().writing_adapter_scale)
            cfg=Config({'MIND_URL':self.url,'HEGEL_WRITE_REASONING_TOKENS':'768','HEGEL_WRITE_ADAPTER_SCALE':'0'})
            mind=make_mind(cfg,None)
            self.assertEqual(mind.writing_reasoning_tokens,768);self.assertEqual(mind.writing_adapter_scale,0)
            for val in ['-1','2049','1.5']:
                with self.assertRaises(ValueError):Config({'HEGEL_WRITE_REASONING_TOKENS':val})
            with self.assertRaises(ValueError):Config({'HEGEL_WRITE_ADAPTER_SCALE':'0.5'})

    def test_decision_profile_switches_roles_without_changing_writing_or_reports(self):
        mind=HTTPMind(self.url,voice_adapter_scale=0,decision_reasoning_tokens=768,decision_adapter_scale=0)
        mind.decide(self.messages,{})
        mind.chat_voice(self.messages,contract.VOICE_SCHEMA)
        mind.chat_writing(self.messages,contract.WRITE_SCHEMA)
        mind.chat(self.messages)
        self.assertEqual([x['lora'][0]['scale'] for x in Recorder.calls],[0,0,1,1])
        self.assertEqual([x['chat_template_kwargs']['enable_thinking'] for x in Recorder.calls],[True,False,False,False])
        self.assertEqual(Recorder.calls[0]['max_tokens'],1468)
        self.assertEqual(Recorder.calls[0]['reasoning_budget_tokens'],768)

    def test_actual_engine_morning_plan_uses_decision_profile(self):
        e=Engine.__new__(Engine);e.mind=HTTPMind(self.url,decision_reasoning_tokens=768,decision_adapter_scale=0)
        e.soul='Hegel.\n## Your answer\nReturn a decision.'
        e.world=mock.Mock();e.world.plan_items.side_effect=lambda answer,ctx:answer['plan']
        sit=dict(day='Thursday 8 October',time='07:00',place='home',weather='clear',aqi=80,outfit='coat',imprest_left=1000,present=[],open_now=['home'],event='Waking.')
        answer={'plan':[{'time':'08:00','intention':'Read at home.'}]};day={};ctx={}
        with mock.patch.object(Recorder,'answer',answer,create=True):
            self.assertTrue(e.make_plan(day,datetime(2026,10,8,7),sit,ctx))
        self.assertEqual(day['plan']['items'],answer['plan'])
        self.assertEqual(Recorder.calls[-1]['max_tokens'],1268)
        self.assertTrue(Recorder.calls[-1]['chat_template_kwargs']['enable_thinking'])
        self.assertEqual(Recorder.calls[-1]['lora'],[{'id':0,'scale':0}])
        self.assertNotIn('PRIVATE',json.dumps(day))

    def test_decision_config_rejects_invalid_and_preserves_defaults(self):
        from world.__main__ import make_mind
        with mock.patch.dict(os.environ,{'HEGEL_ENV':os.devnull},clear=True):
            cfg=Config({'MIND_URL':self.url});mind=make_mind(cfg,None)
            self.assertEqual(mind.decision_reasoning_tokens,0);self.assertIsNone(mind.decision_adapter_scale)
            cfg=Config({'MIND_URL':self.url,'HEGEL_DECISION_REASONING_TOKENS':'768','HEGEL_DECISION_ADAPTER_SCALE':'0'})
            mind=make_mind(cfg,None)
            self.assertEqual(mind.decision_reasoning_tokens,768);self.assertEqual(mind.decision_adapter_scale,0)
            for val in ['-1','2049','1.5']:
                with self.assertRaises(ValueError):Config({'HEGEL_DECISION_REASONING_TOKENS':val})
            with self.assertRaises(ValueError):Config({'HEGEL_DECISION_ADAPTER_SCALE':'0.5'})
        for budget in [-1,2049,True,'768']:
            with self.assertRaises(ValueError):HTTPMind(self.url,decision_reasoning_tokens=budget)
        with self.assertRaises(ValueError):HTTPMind(self.url,decision_adapter_scale=.5)


if __name__=='__main__':unittest.main()
