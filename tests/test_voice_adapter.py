"""Per-request NPC adapter isolation through the real HTTP and Engine paths."""
import json,os,threading,unittest
from http.server import BaseHTTPRequestHandler,HTTPServer
from unittest import mock
from world.config import Config
from world.mind import HTTPMind
from world.engine import Engine
from world.world import World
from world import contract

class Recorder(BaseHTTPRequestHandler):
    calls=[]
    reject_schema=False
    def log_message(self,*args): pass
    def do_GET(self):
        self.send_response(200);self.end_headers();self.wfile.write(b'{"status":"ok"}')
    def do_POST(self):
        body=json.loads(self.rfile.read(int(self.headers['Content-Length'])));type(self).calls.append((self.path,body))
        if type(self).reject_schema and 'response_format' in body:
            self.send_response(422);self.end_headers();return
        self.send_response(200);self.end_headers();self.wfile.write(json.dumps({'choices':[{'message':{'content':'{"says":"One chai, ji.","does":null}'}}]}).encode())

class VoiceAdapterTests(unittest.TestCase):
    def setUp(self):
        Recorder.calls=[];Recorder.reject_schema=False
        self.server=HTTPServer(('127.0.0.1',0),Recorder)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.url=f'http://127.0.0.1:{self.server.server_port}'
        self.messages=[{'role':'system','content':'NPC role'},{'role':'user','content':'First encounter.'}]
    def tearDown(self):
        self.server.shutdown();self.thread.join();self.server.server_close()
    def test_base_voice_does_not_disable_lora_on_the_next_character_call(self):
        mind=HTTPMind(self.url,voice_adapter_scale=0)
        mind.chat_voice(self.messages,contract.VOICE_SCHEMA)
        mind.chat([{'role':'user','content':'Hegel decision'}],contract.SCHEMA)
        self.assertEqual(Recorder.calls[0][1]['lora'],[{'id':0,'scale':0}])
        self.assertEqual(Recorder.calls[1][1]['lora'],[{'id':0,'scale':1}])
        self.assertEqual([p for p,_ in Recorder.calls],['/v1/chat/completions']*2)
        self.assertFalse(Recorder.calls[0][1]['chat_template_kwargs']['enable_thinking'])
    def test_schema_fallback_preserves_the_base_role_override(self):
        Recorder.reject_schema=True
        HTTPMind(self.url,voice_adapter_scale=0).chat_voice(self.messages,contract.VOICE_SCHEMA)
        self.assertEqual(len(Recorder.calls),2)
        self.assertIn('response_format',Recorder.calls[0][1]);self.assertNotIn('response_format',Recorder.calls[1][1])
        self.assertTrue(all(body['lora']==[{'id':0,'scale':0}] for _,body in Recorder.calls))
    def test_unset_voice_policy_retains_existing_http_payload(self):
        HTTPMind(self.url).chat_voice(self.messages,contract.VOICE_SCHEMA)
        self.assertNotIn('lora',Recorder.calls[0][1])
    def test_engine_routes_only_the_voice_call_to_the_voice_method(self):
        e=Engine.__new__(Engine);e.world=World();e.mind=HTTPMind(self.url,voice_adapter_scale=0)
        e.memory=mock.Mock();e.memory.before.return_value=[];e.memory.moments.return_value=[];e.voice_prompt='Delhi NPC'
        sit=dict(day='Saturday 3 October',time='08:17',place='lodhi',outfit='white cotton kurta',event='Sunil is here; you have not met.')
        result=e.voice('sunil',{'date':'2026-10-03'},sit,'One chai, please.')
        self.assertEqual(result['says'],'One chai, ji.')
        self.assertEqual(Recorder.calls[-1][1]['lora'],[{'id':0,'scale':0}])
        self.assertIn('You are Sunil',Recorder.calls[-1][1]['messages'][-1]['content'])
    def test_invalid_scales_fail_before_any_network_call(self):
        for value in [-1,.5,2,float('nan'),'0']:
            with self.assertRaises(ValueError):HTTPMind(self.url,voice_adapter_scale=value)
        mind=HTTPMind(self.url)
        with self.assertRaises(ValueError):mind.chat(self.messages,adapter_scale=2)
        self.assertEqual(Recorder.calls,[])
    def test_config_requires_explicit_opt_in_and_cli_preserves_it(self):
        from world.__main__ import make_mind
        with mock.patch.dict(os.environ,{'HEGEL_ENV':os.devnull},clear=True):
            self.assertIsNone(Config().voice_adapter_scale)
            cfg=Config({'MIND_URL':self.url,'HEGEL_VOICE_ADAPTER_SCALE':'0'})
            self.assertEqual(make_mind(cfg,None).voice_adapter_scale,0)
            with self.assertRaisesRegex(ValueError,'HEGEL_VOICE_ADAPTER_SCALE'):Config({'HEGEL_VOICE_ADAPTER_SCALE':'0.5'})

if __name__=='__main__':unittest.main()
