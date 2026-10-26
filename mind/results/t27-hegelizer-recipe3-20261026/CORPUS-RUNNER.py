#!/usr/bin/env python3
import argparse,contextlib,io,subprocess,copy,datetime,hashlib,importlib.util,json,os,random,shutil,statistics,sys,threading,time,traceback,urllib.request,urllib.error
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
START=time.monotonic();HERE=Path(__file__).resolve().parent;P=json.loads((HERE/'PLAN.json').read_text());ROOT=Path(P['mirror']);SOURCE=Path(P['source'])
sys.dont_write_bytecode=True;sys.path.insert(0,str(SOURCE));os.environ['HEGEL_ENV']=os.devnull;os.environ['HEGEL_REPO']=str(SOURCE)
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(n,v):
 for base in [HERE,ROOT]:
  f=base/n;t=f.with_name(f.name+'.tmp');t.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n');os.replace(t,f)
def rows(p):return [json.loads(s) for s in p.read_text().splitlines() if s]
def verify():
 m=json.loads((HERE/'SOURCE-MANIFEST.json').read_text())
 for n,v in m.items():assert hashlib.sha256((SOURCE/n).read_bytes()).hexdigest()==v['sha256'],n
 for n,d in P['immutable_inputs'].items():assert hashlib.sha256((HERE/n).read_bytes()).hexdigest()==d,n
 policy=json.loads((HERE/'NO-CUTOFF-POLICY.json').read_text());assert policy['human_message']=='no cutoff' and policy['absolute_deadline_utc'] is None
 return len(m)
spec=importlib.util.spec_from_file_location('canonical_hegelizer',SOURCE/'tools/hegelizer.py');h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
assert h.RECIPE==3 and h.ASKS==3 and (h.GATE_FAILED,h.GATE_RATIO,h.RUN)==(0.1,(0.8,1.2),8)
units=rows(HERE/'input-data/hegelizer-units.jsonl');cohort=json.loads((HERE/'COHORT.json').read_text());ids=[u['id'] for u in cohort];hard=set(P['hard_case_ids']);fresh=set(ids)-hard
oldok=rows(HERE/'input-data/hegelizer.jsonl');oldbad=rows(HERE/'input-data/hegelizer-failed.jsonl');done={r['id'] for r in oldok};failed={r['id'] for r in oldbad}-done
order=list(units);random.Random(h.SPLIT_SEED).shuffle(order);assert [u['id'] for u in order if u['id'] not in done and u['id'] not in failed]==ids
assert not hard and len(ids)==125 and len(done)==92 and len(failed)==3 and not set(ids).intersection(P['all_prior_requested_ids'])
if '--preflight' in sys.argv:
 print(json.dumps({'status':'PASS','source_files':verify(),'exact_cohort':125,'retained_complete_cases':95,'globally_never_requested_cases':125,'canonical_recipe':h.RECIPE,'asks':h.ASKS,'old_done_pairs':len(oldok),'old_failure_rows':len(oldbad),'first_new_seed':(P['base_seed']+10007*(P['generation_offset']+1))%(2**31-1),'model_calls':0}));sys.exit(0)
test=json.loads((ROOT.parent/'UNIT-RUN.json').read_text());assert test['status']=='DONE' and test['process_exit']==0 and test['source_verified_after']==492
assert P['prior_GPU_work_charged_upper_bound_seconds']+P['maximum_wall_seconds']+P['restoration_reserve_seconds']<=P['maximum_total_GPU_work_seconds']
assert not (HERE/'RUN-start.json').exists()
run={'started_utc':utc(),'status':'RUNNING','phase':'ORIGINAL220_RECIPE3_CORPUS_COMPLETION','pid':os.getpid(),'tmux':P['tmux'],'source_tree':P['source_tree'],'source_verified_before':verify(),'total_targets':220,'initial_accepted':92,'initial_failed':3,'new_cases':125,'training_started':False,'server_timer_changed':False,'absolute_deadline_utc':None}
save('RUN-start.json',run);save('RUN.json',run)
(HERE/'http').mkdir(exist_ok=False);(HERE/'data').mkdir(exist_ok=False)
for n in ['hegelizer-units.jsonl','hegelizer.jsonl','hegelizer-failed.jsonl']:(HERE/'data'/n).write_bytes((HERE/'input-data'/n).read_bytes())
state_lock=threading.Lock();upstream_lock=threading.Lock();count=0;health_count=0;call_index=0;seen=set();finished={};calls=(HERE/'http.jsonl').open('x');provenance=(HERE/'unit-results.jsonl').open('x')
message_ids={h.PARAPHRASE_ASK.format(original=u['original']):u['id'] for u in units};assert len(message_ids)==220
def record_call(method,path,body=b''):
 global count,health_count,call_index
 with upstream_lock:
  start=time.monotonic();call_index+=1;i=call_index;uid=None;seed=None;sent=body;error=None;forwarded=False
  prefix=HERE/'http'/f'{i:04d}';prefix.with_suffix('.request.bin').write_bytes(body)
  try:
   if method=='POST':
    a=json.loads(body);uid=message_ids[a['messages'][1]['content']];assert uid in ids;count+=1;b=copy.deepcopy(a);b['id_slot']=1;b['seed']=(P['base_seed']+10007*(P['generation_offset']+count))%(2**31-1);seed=b['seed'];sent=json.dumps(b,ensure_ascii=False).encode();assert path=='/v1/chat/completions' and count<=P['maximum_generation_calls']
   else:health_count+=1;assert method=='GET' and path=='/health' and health_count==1
   prefix.with_suffix('.forwarded.bin').write_bytes(sent);elapsed=time.monotonic()-START
   if elapsed+300>P['maximum_wall_seconds'] or P['prior_GPU_work_charged_upper_bound_seconds']+elapsed+300+P['restoration_reserve_seconds']>P['maximum_total_GPU_work_seconds']:raise RuntimeError('Predeclared cumulative GPU budget exhausted')
   req=urllib.request.Request(P['model_url']+path,data=sent if method=='POST' else None,headers={'Content-Type':'application/json'},method=method);forwarded=True
   with urllib.request.urlopen(req,timeout=300) as r:raw,status=r.read(),r.status
  except urllib.error.HTTPError as e:raw,status,error=e.read(),e.code,str(e)
  except BaseException as e:raw,status,error=json.dumps({'error':str(e)}).encode(),502,str(e)
  prefix.with_suffix('.response.bin').write_bytes(raw);r={'index':i,'utc':utc(),'method':method,'path':path,'unit_id':uid,'generation_index':count if method=='POST' else None,'slot':1 if method=='POST' else None,'seed':seed,'forwarded':forwarded,'status':status,'error':error,'wall_seconds':time.monotonic()-start,'response_bytes':len(raw),'response_sha256':hashlib.sha256(raw).hexdigest()}
  calls.write(json.dumps(r)+'\n');calls.flush();os.fsync(calls.fileno());return status,raw
class Proxy(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_GET(self):
  status,raw=record_call('GET',self.path);self.send_response(status);self.end_headers();self.wfile.write(raw)
 def do_POST(self):
  body=self.rfile.read(int(self.headers['Content-Length']));status,raw=record_call('POST',self.path,body);self.send_response(status);self.end_headers();self.wfile.write(raw)
original=h.paraphrase_one
def traced_one(unit,url,timeout):
 uid=unit['id']
 with state_lock:assert uid in ids and uid not in seen;seen.add(uid)
 plain,why=original(unit,url,timeout);r={**unit,'recipe':3,'group':'new_original_pilot',**({'plain':plain} if plain else {'reason':why})}
 with state_lock:
  assert uid not in finished;finished[uid]=r;provenance.write(json.dumps(r,ensure_ascii=False)+'\n');provenance.flush();os.fsync(provenance.fileno())
  save('PROGRESS.json',{'utc':utc(),'status':'RUNNING','phase':'ORIGINAL220_RECIPE3_CORPUS_COMPLETION','new_completed':len(finished),'new_accepted':sum('plain' in x for x in finished.values()),'new_failed':sum('plain' not in x for x in finished.values()),'initial_accepted':92,'initial_active_failed':3,'generation_calls':count,'new_total':125,'total_targets':220,'last_id':uid})
 return plain,why
h.paraphrase_one=traced_one
proxy=ThreadingHTTPServer(('127.0.0.1',0),Proxy);thread=threading.Thread(target=proxy.serve_forever,daemon=True);thread.start();error=None;rc=1;gate=None
try:
 a=argparse.Namespace(url=f'http://127.0.0.1:{proxy.server_port}',workers=2,retry_failed=False,limit=0,timeout=300,seed=None);rc=h.cmd_paraphrase(a,HERE/'data')
 assert rc==0 and set(finished)==set(ids),(rc,len(finished))
 allpairs=rows(HERE/'data'/h.DONE);pairmap={r['id']:r for r in allpairs};failed_final=h.failed_ids(rows(HERE/'data'/h.FAILED),pairmap);assert len(pairmap)==len(allpairs) and set(pairmap)|failed_final=={u['id'] for u in units}
 assert len(pairmap)+len(failed_final)==220
 ratio=statistics.mean(h.words_of(r['plain'])/h.words_of(r['original']) for r in pairmap.values());share=len(failed_final)/220
 stats=io.StringIO()
 with contextlib.redirect_stdout(stats):stats_exit=h.cmd_stats(a,HERE/'data')
 (HERE/'CANONICAL-STATS.stdout.txt').write_text(stats.getvalue())
 check=subprocess.run([sys.executable,'-B',str(SOURCE/'pc/train_hegel.py'),'--check-data','--phase','restyle','--data',str(HERE/'data'),'--seq-restyle','1024'],capture_output=True)
 (HERE/'TRAINER-CHECK.stdout.txt').write_bytes(check.stdout);(HERE/'TRAINER-CHECK.stderr.txt').write_bytes(check.stderr)
 gate={'total_targets':220,'accounted':len(pairmap)+len(failed_final),'accepted':len(pairmap),'failed':len(failed_final),'accepted_train':sum(r['split']=='train' for r in pairmap.values()),'accepted_held':sum(r['split']=='held' for r in pairmap.values()),'failed_share':share,'mean_word_ratio':ratio,'canonical_10_percent_pass':share<h.GATE_FAILED and h.GATE_RATIO[0]<=ratio<=h.GATE_RATIO[1],'canonical_stats_exit':stats_exit,'human_strict_failed_share_maximum':0.15,'CPU_trainer_check_exit':check.returncode,'pass':share<0.15 and 0.8<=ratio<=1.2 and check.returncode==0,'scope':'Original220 corpus only; not a style score, trained adapter or adoption result'}
 save('DATA-GATE.json',gate)

except BaseException as e:error={'type':type(e).__name__,'message':str(e)};rc=1;traceback.print_exc()
finally:
 proxy.shutdown();thread.join(5);proxy.server_close();calls.close();provenance.close()
 try:after=verify()
 except BaseException as e:after=None;error=error or {'type':type(e).__name__,'message':str(e)};rc=1
 processing_end=time.monotonic();final={**run,'model_processing_finished_utc':utc(),'status':'DONE' if rc==0 else 'STOPPED','model_processing_exit':rc,'error':error,'completed':len(finished),'generation_calls':count,'normal_readiness_calls':health_count,'wall_seconds_through_processing':processing_end-START,'source_verified_after':after,'diagnostic_gate':gate}
 save('MODEL-END-BEFORE-EXPORT.json',final)
 export_error=None
 try:
  for name in ['http','data']:
   for f in sorted((HERE/name).rglob('*')):
    if f.is_file():dest=ROOT/f.relative_to(HERE);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(f.read_bytes());assert dest.read_bytes()==f.read_bytes()
  for name in ['http.jsonl','unit-results.jsonl','CANONICAL-STATS.stdout.txt','TRAINER-CHECK.stdout.txt','TRAINER-CHECK.stderr.txt']:
   if (HERE/name).exists():(ROOT/name).write_bytes((HERE/name).read_bytes())
 except BaseException as e:export_error={'type':type(e).__name__,'message':str(e)};rc=1;traceback.print_exc()
 final.update(finished_utc=utc(),process_exit=rc,export_error=export_error,wall_seconds=time.monotonic()-START,cumulative_GPU_work_charged_upper_bound_seconds=P['prior_GPU_work_charged_upper_bound_seconds']+time.monotonic()-START)
 save('RUN-end.json',final);save('RUN.json',final);print(json.dumps(final),flush=True)
sys.exit(rc)

