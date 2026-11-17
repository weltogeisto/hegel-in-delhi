#!/usr/bin/env python3
import argparse,copy,datetime,hashlib,importlib.util,json,os,random,shutil,statistics,sys,threading,time,traceback,urllib.request,urllib.error
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
START=time.monotonic();HERE=Path(__file__).resolve().parent;P=json.loads((HERE/'PLAN.json').read_text());ROOT=Path(P['mirror']);SOURCE=Path(P['source'])
sys.dont_write_bytecode=True;sys.path.insert(0,str(SOURCE));os.environ['HEGEL_ENV']=os.devnull;os.environ['HEGEL_REPO']=str(SOURCE)
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(n,v):
 for base in [HERE,ROOT]:
  t=base/n;tmp=t.with_name(t.name+'.tmp');tmp.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n');os.replace(tmp,t)
def rows(p):return [json.loads(s) for s in p.read_text().splitlines() if s]
def verify():
 m=json.loads((HERE/'SOURCE-MANIFEST.json').read_text())
 for n,v in m.items():assert hashlib.sha256((SOURCE/n).read_bytes()).hexdigest()==v['sha256'],n
 for n,d in P['immutable_inputs'].items():assert hashlib.sha256((HERE/n).read_bytes()).hexdigest()==d,n
 policy=json.loads((HERE/'NO-CUTOFF-POLICY.json').read_text());assert policy['human_message']=='no cutoff' and policy['absolute_deadline_utc'] is None and policy['maximum_total_GPU_work_seconds']==7200
 return len(m)
spec=importlib.util.spec_from_file_location('canonical_hegelizer',SOURCE/'tools/hegelizer.py');h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
assert h.RECIPE==2 and (h.GATE_FAILED,h.GATE_RATIO,h.RUN)==(0.1,(0.8,1.2),8)
units=rows(HERE/'input-data/hegelizer-units.jsonl');cohort=json.loads((HERE/'COHORT.json').read_text());ids=[u['id'] for u in cohort]
oldok=rows(HERE/'input-data/hegelizer.jsonl');oldbad=rows(HERE/'input-data/hegelizer-failed.jsonl');done={r['id'] for r in oldok};failed={r['id'] for r in oldbad}
order=list(units);random.Random(h.SPLIT_SEED).shuffle(order);assert [u['id'] for u in order if u['id'] not in done][:40]==ids
prior=rows(HERE/'prior-recipe2-accepted.jsonl')+rows(HERE/'prior-recipe2-failed.jsonl');cache={r['id']:r for r in prior};assert len(cache)==10 and set(cache)<=set(ids)
byid={u['id']:u for u in units}
for r in prior:
 assert all(r[k]==byid[r['id']][k] for k in ['original','work','ref','split'])
 if 'plain' in r:assert h.judge(r['original'],r['plain'],'stop')==(r['plain'],None)
 else:assert r['id']=='haldane-3:405'
assert len(set(ids)-set(cache))==30 and len(set(ids)&failed)==27
if '--preflight' in sys.argv:
 print(json.dumps({'status':'PASS','source_files':verify(),'canonical_fixed_cohort':40,'old_recipe1_pairs':len(oldok),'old_recipe1_failures':len(oldbad),'existing_recipe2_retained':len(cache),'new_cases':30,'first_new_seed':(P['base_seed']+10007*(P['generation_offset']+1))%(2**31-1),'model_calls':0,'source_or_checker_change':False}));sys.exit(0)
test=json.loads((ROOT.parent/'UNIT-RUN.json').read_text());assert test['status']=='DONE' and test['process_exit']==0 and test['source_verified_after']==472
assert P['prior_GPU_work_seconds']+P['maximum_wall_seconds']+P['restoration_reserve_seconds']<=P['maximum_total_GPU_work_seconds']
assert not (HERE/'RUN-start.json').exists()
run={'started_utc':utc(),'status':'RUNNING','phase':'T25_RECIPE2_40_CASE_DIAGNOSTIC','pid':os.getpid(),'tmux':P['tmux'],'source_tree':P['source_tree'],'source_verified_before':verify(),'total_cases':40,'preserved_recipe2_cases':10,'new_cases_maximum':30,'training_started':False,'server_timer_changed':False,'absolute_deadline_utc':None}
save('RUN-start.json',run);save('RUN.json',run)
(HERE/'http').mkdir(exist_ok=False);(HERE/'data').mkdir(exist_ok=False)
for n in ['hegelizer-units.jsonl','hegelizer.jsonl','hegelizer-failed.jsonl']:shutil.copyfile(HERE/'input-data'/n,HERE/'data'/n)
state_lock=threading.Lock();upstream_lock=threading.Lock();count=0;health_count=0;call_index=0;seen=set();finished={};calls=(HERE/'http.jsonl').open('x');provenance=(HERE/'unit-results.jsonl').open('x')
message_ids={h.PARAPHRASE_ASK.format(original=u['original']):u['id'] for u in units};assert len(message_ids)==220
def record_call(method,path,body=b''):
 global count,health_count,call_index
 with upstream_lock:
  start=time.monotonic();call_index+=1;i=call_index;uid=None;b=None;seed=None;sent=body;error=None;forwarded=False
  prefix=HERE/'http'/f'{i:04d}';prefix.with_suffix('.request.bin').write_bytes(body)
  try:
   if method=='POST':
    a=json.loads(body);uid=message_ids[a['messages'][1]['content']];assert uid in set(ids)-set(cache)
    count+=1;b=copy.deepcopy(a);b['id_slot']=1;b['seed']=(P['base_seed']+10007*(P['generation_offset']+count))%(2**31-1);seed=b['seed'];sent=json.dumps(b,ensure_ascii=False).encode()
    assert path=='/v1/chat/completions' and count<=P['maximum_generation_calls']
   else:
    health_count+=1;assert method=='GET' and path=='/health' and health_count==1
   prefix.with_suffix('.forwarded.bin').write_bytes(sent)
   elapsed=time.monotonic()-START
   if elapsed+300>P['maximum_wall_seconds'] or P['prior_GPU_work_seconds']+elapsed+300+P['restoration_reserve_seconds']>P['maximum_total_GPU_work_seconds']:raise RuntimeError('Predeclared cumulative GPU budget exhausted')
   req=urllib.request.Request(P['model_url']+path,data=sent if method=='POST' else None,headers={'Content-Type':'application/json'},method=method)
   forwarded=True
   with urllib.request.urlopen(req,timeout=300) as r:raw,status=r.read(),r.status
  except urllib.error.HTTPError as e:raw,status,error=e.read(),e.code,str(e)
  except BaseException as e:raw,status,error=json.dumps({'error':str(e)}).encode(),502,str(e)
  prefix.with_suffix('.response.bin').write_bytes(raw)
  r={'index':i,'utc':utc(),'method':method,'path':path,'unit_id':uid,'generation_index':count if method=='POST' else None,'slot':1 if method=='POST' else None,'seed':seed,'forwarded':forwarded,'status':status,'error':error,'wall_seconds':time.monotonic()-start,'response_bytes':len(raw),'response_sha256':hashlib.sha256(raw).hexdigest()}
  calls.write(json.dumps(r)+'\n');calls.flush();os.fsync(calls.fileno());return status,raw
class Proxy(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_GET(self):
  status,raw=record_call('GET',self.path);self.send_response(status);self.end_headers();self.wfile.write(raw)
 def do_POST(self):
  body=self.rfile.read(int(self.headers['Content-Length']));status,raw=record_call('POST',self.path,body);self.send_response(status);self.end_headers();self.wfile.write(raw)
original=h.paraphrase_one
def preserving_one(unit,url,timeout):
 uid=unit['id']
 with state_lock:assert uid in ids and uid not in seen;seen.add(uid)
 if uid in cache:
  prior=cache[uid];plain,why=prior.get('plain'),prior.get('reason');origin='preserved_prior_recipe2'
 else:plain,why=original(unit,url,timeout);origin='new_recipe2_request'
 row={**unit,'recipe':2,'provenance':origin,**({'plain':plain} if plain else {'reason':why})}
 with state_lock:
  assert uid not in finished;finished[uid]=row;provenance.write(json.dumps(row,ensure_ascii=False)+'\n');provenance.flush();os.fsync(provenance.fileno())
  save('PROGRESS.json',{'utc':utc(),'status':'RUNNING','completed':len(finished),'accepted':sum('plain' in r for r in finished.values()),'failed':sum('plain' not in r for r in finished.values()),'preserved':sum(r['provenance']=='preserved_prior_recipe2' for r in finished.values()),'new_generation_calls':count,'total':40,'last_id':uid})
 return plain,why
h.paraphrase_one=preserving_one
proxy=ThreadingHTTPServer(('127.0.0.1',0),Proxy);thread=threading.Thread(target=proxy.serve_forever,daemon=True);thread.start();error=None;rc=1
try:
 a=argparse.Namespace(url=f'http://127.0.0.1:{proxy.server_port}',workers=2,retry_failed=True,limit=40,timeout=300)
 rc=h.cmd_paraphrase(a,HERE/'data')
 assert rc==0 and set(finished)==set(ids),(rc,len(finished))
 accepted=[finished[i] for i in ids if 'plain' in finished[i]];bad=[finished[i] for i in ids if 'plain' not in finished[i]];ratio=statistics.mean(h.words_of(r['plain'])/h.words_of(r['original']) for r in accepted) if accepted else None
 gate={'total':40,'accepted':len(accepted),'failed':len(bad),'recipe1_failed_subgroup_total':27,'recipe1_failed_subgroup_failures':sum(r['id'] in failed for r in bad),'next13_subgroup_failures':sum(r['id'] not in failed for r in bad),'mean_word_ratio':ratio,'maximum_failures':3,'pass':len(bad)<=3 and ratio is not None and 0.8<=ratio<=1.2,'preserved_prior_recipe2_results':10,'new_cases':30,'gate_is_distinct_from_human_15_percent_corpus_policy':True}
 save('DIAGNOSTIC-GATE.json',gate)
except BaseException as e:error={'type':type(e).__name__,'message':str(e)};rc=1;traceback.print_exc()
finally:
 proxy.shutdown();thread.join(5);proxy.server_close();calls.close();provenance.close()
 try:after=verify()
 except BaseException as e:after=None;error=error or {'type':type(e).__name__,'message':str(e)};rc=1
 for n in ['http','data']:shutil.copytree(HERE/n,ROOT/n,dirs_exist_ok=True)
 for n in ['http.jsonl','unit-results.jsonl']:shutil.copyfile(HERE/n,ROOT/n)
 final={**run,'finished_utc':utc(),'status':'DONE' if rc==0 else 'STOPPED','process_exit':rc,'error':error,'completed':len(finished),'generation_calls':count,'normal_readiness_calls':health_count,'wall_seconds':time.monotonic()-START,'source_verified_after':after,'diagnostic_gate':locals().get('gate'),'cumulative_GPU_work_seconds':P['prior_GPU_work_seconds']+time.monotonic()-START}
 save('RUN-end.json',final);save('RUN.json',final);print(json.dumps(final),flush=True)
sys.exit(rc)

