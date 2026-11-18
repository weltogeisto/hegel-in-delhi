import copy,json,tempfile,unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools import voice_screen as v
from tools.decision_sampler import digest,json_bytes
ROOT=Path(__file__).resolve().parents[1]
class VoiceScreenTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.folder=ROOT/"pc/exports/voice-screen-20261117-final";cls.rows=v.contexts(cls.folder)
 def answer(self,raw):
  b=json_bytes({"choices":[{"message":{"content":raw},"finish_reason":"stop"}]})
  return json.loads(b),{"response_sha256":digest(b)}
 def test_complete_cohort_and_cache_off(self):
  req=v.requests(self.folder)
  self.assertEqual(len(req),576)
  self.assertEqual(len({k for k,*_ in req}),576)
  self.assertTrue(all(p["cache_prompt"] is False and p["id_slot"]==1 and p["max_tokens"]==250 for *_,p in req))
  m=v.checked(self.folder/"MANIFEST.json");self.assertEqual(len(m["excluded"]),7);self.assertLessEqual(m["poor_days"],20)
 def test_initial_requests_use_engine_voice_without_mutating_context(self):
  row=copy.deepcopy(self.rows[0]);original=copy.deepcopy(row);calls=[]
  def post(k,p):
   calls.append(p);return self.answer('{"says":"I do not know.","does":"He shakes his head."}')
  result=v.exercise(row,"F",1831,post)
  self.assertEqual(row,original);self.assertEqual(len(calls),1)
  self.assertEqual(calls[0]["messages"][0]["content"],row["voice_prompt"])
  self.assertIsNotNone(result["heard"])
 def test_real_promise_refusal_keeps_second_request_and_reason(self):
  row=next(copy.deepcopy(r) for r in self.rows if r["cid"]=="ramesh");calls=[]
  def post(k,p):
   calls.append(p)
   if len(calls)==1:return self.answer('{"says":"I will bring it.","does":"He nods.","act":{"kind":"not-on-the-menu","in_minutes":1}}')
   return self.answer('{"says":"I cannot promise that.","does":"He shakes his head."}')
  rec=v.exercise(row,"P",1831,post)
  self.assertEqual(len(calls),2)
  self.assertIn("world refuses",calls[1]["messages"][-1]["content"])
  self.assertEqual(len(rec["calls"]),2)
 def test_missing_durable_receipt_stops(self):
  def post(k,p):return {"choices":[{"message":{"content":"{}"}}]},{}
  with self.assertRaises(ValueError):v.exercise(self.rows[0],"A",1831,post)
 def test_packet_refuses_partial_screen(self):
  with tempfile.TemporaryDirectory() as td:
   from unittest.mock import patch
   with patch.object(v,"contexts",return_value=self.rows):
    with self.assertRaises(ValueError):v.packet(td,Path(td)/"sheet.json",Path(td)/"key.json")
if __name__=="__main__":unittest.main()
