"""T49 arm D: original T39 replay, owner selector, isolated shared-slot client."""
import copy,datetime as dt,fcntl,json,os,pathlib,shlex,subprocess,sys,time,traceback
from collections import defaultdict
P=pathlib.Path
J=P('/home/ai/hegel-eval/codex-tasks-20261114/t39-d-111200')
E=P('/mnt/c/hegel/handover/codex-tasks-20261114/t39-d-111200')
O=P('/mnt/c/hegel/handover/codex-tasks-20261113/ordered-work-131600')
LABEL='t39-d-20261114-111200'
sys.path.insert(0,str(J/'source'));sys.path.insert(0,str(J/'runtime'))
import shared_slot as slot
import legacy_replay as legacy
from world import contract,prefer,report
from world.mind import MindAway
from tools.decision_pairs import shown
LOCK=P('/home/ai/hegel-eval/codex-tasks-20261106/t39-20261106/serial.lock')
FREEZE='6cd8e3dc076d1a4e18d8f997828bf1bf793edb68cb51ae92d983fb20d68e58a3'
def verify_inputs():
 b=(J/'INPUT-FREEZE.json').read_bytes()
 if slot.h(b)!=FREEZE:raise RuntimeError('input seal changed')
 f=json.loads(b)
 for rel,want in f['source'].items():
  if slot.h((J/'source'/rel).read_bytes())!=want:raise RuntimeError('source changed: '+rel)
 for rel,want in f['inputs'].items():
  if slot.h((J/rel).read_bytes())!=want:raise RuntimeError('input changed: '+rel)
 for filename,k in [('PLAN.json','plan_sha256'),('STUDY-PROTOCOL.json','protocol_sha256'),('DRAW-SEEDS.json','seeds_sha256'),('ORIGINAL-STUDY-PROTOCOL.json','original_protocol_sha256'),('runtime/legacy_replay.py','legacy_replay_sha256')]:
  if slot.h((J/filename).read_bytes())!=f[k]:raise RuntimeError('frozen file changed: '+filename)
 for filename,want in slot.read(J/'RUNTIME-SEAL.json').items():
  if slot.h((J/'runtime'/filename).read_bytes())!=want:raise RuntimeError('runtime changed: '+filename)
 p=slot.load_plan()
 m=(O/'M1-v2-TERMINAL-CHECK.json').read_bytes();v=json.loads(m);c=v['reconciliation']
 if slot.h(m)!=p['m1_completion_sha256'] or v['end']['status']!='ALL_SCREEN_REPLIES_RECORDED' or not v['controller_exit_confirmed'] or c['records']!=144 or c['complete_chains']!=144 or c['unknown'] or c['errors'] or c['completed_unrecorded']:
  raise RuntimeError('M1 completion prerequisite failed')
 return p
def compute_one(case,day,soul,history,seed,window,transport=None):
 transport=transport or slot.send
 result=dict(case=case['id'],time=case['time'],arm='D',seed=seed,thought=None,attempts=[],repetition_refusals=0,echo_grams=[],warnings=[],schema_fallbacks=0,source='fixed decision replay')
 if case['historical_source']=='bedtime' and day['steps'][case['index']]['mind']['attempts']==0:
  result.update(source='recorded deterministic bedtime, no decision request',draws=None,no_fresh_draw=None);return result
 text,visible=legacy.render_case(case,'A',day,history)
 messages=[dict(role='system',content=soul),dict(role='user',content=text)]
 sit,state,ctx=legacy.validator(case,day,history)
 selector_shown=prefer.shown_thoughts(legacy.earlier_lines(day,case['index'],history)[0])
 if selector_shown!=[r[3] for r in shown(messages)]:raise RuntimeError('selector shown-thought view differs from prompt')
 result.update(prompt_sha256=slot.h(text.encode()),visible_earlier_thoughts=visible,selector_shown=selector_shown)
 seeds=slot.read(J/'DRAW-SEEDS.json')[case['id']+'|'+str(seed)]
 def inspect(raw):
  return legacy.W.check(contract.extract_json(raw),copy.deepcopy(sit),copy.deepcopy(ctx),copy.deepcopy(state))
 def ask(key,used_seed,msg):
  p=legacy.payload(msg,sit,'A',used_seed);ans,receipt=transport(window,key,p,90)
  measures=legacy.check_sampler(key,p,ans)
  raw=(ans['choices'][0]['message'].get('content') or '').strip()
  errors,warnings,rep=inspect(raw)
  result['repetition_refusals']+=int(any('this repeats what you thought at' in e for e in errors))
  result['attempts'].append(dict(key=key,receipt=receipt,measures=measures,errors=errors,warnings=warnings,finish_reason=ans['choices'][0].get('finish_reason')))
  return raw
 count=0
 def draw():
  nonlocal count
  count+=1
  return ask(f"study-D/{case['id']}/{seed}/draw/{count}",seeds[count-1],messages)
 def check(raw):
  errors,_,rep=inspect(raw);return errors,None if errors else rep[0].get('thought')
 # Guard and transport exceptions must propagate. Engine.draw catches ONLY MindAway.
 raw,note=prefer.choose(draw,check,selector_shown,4,away=MindAway)
 result.update(draws=note,no_fresh_draw=(note['refused']+note['echo']==note['n']))
 result['selected_initial_request']=result['attempts'][note['picked']]['key']
 for turn in range(1,4):
  if turn>1:raw=ask(f"study-D/{case['id']}/{seed}/refusal/{turn}",seed,messages)
  errors,warnings,rep=inspect(raw)
  if not errors:
   accepted,_=rep;result.update(decision=accepted,thought=accepted.get('thought'),warnings=warnings)
   old=set().union(*(report.grams(q) for q in visible))
   result['echo_grams']=sorted(report.grams(accepted.get('thought') or '') & old)
   break
  messages=messages+[dict(role='assistant',content=raw),dict(role='user',content='The world refuses this step: '+'; '.join(errors)+'. Decide again. Answer with the JSON object only.')]
 if not result['thought']:result['source']='quiet after recorded contract refusals'
 return result
def schedule():
 manifest=slot.read(J/'fixtures/MANIFEST.json');groups=defaultdict(list)
 for c in manifest['case_rows']:groups[c['label']].append(c)
 days={k:slot.read(J/'days'/(k+'.json')) for k in groups}
 return manifest,groups,days
def reconcile(replay=False):
 errors=[];unknown=[];complete={};rows={};mapped=set()
 qroot=J/'requests';seed_table=slot.read(J/'DRAW-SEEDS.json')
 for base in sorted({p.parent for p in qroot.rglob('*') if p.is_file()}):
  key=base.relative_to(qroot).as_posix()
  try:
   parts=key.split('/');assert len(parts)==6 and parts[0]=='study-D'
   caseid='/'.join(parts[1:3]);paired=int(parts[3]);kind=parts[4];ordinal=int(parts[5])
   values=seed_table[caseid+'|'+str(paired)]
   expected=values[ordinal-1] if kind=='draw' and 1<=ordinal<=4 else paired if kind=='refusal' and ordinal in (2,3) else None
   assert expected is not None
   if (base/'unknown.json').exists() or not (base/'done.json').exists():unknown.append(key);continue
   q=(base/'request.json').read_bytes();r=(base/'response.bin').read_bytes();b=slot.read(base/'begin.json');d=slot.read(base/'done.json');p=json.loads(q)
   assert slot.h(q)==b['request_sha256']==d['request_sha256'] and slot.h(r)==d['response_sha256'] and d['status']==200
   assert p['seed']==expected and p['model']=='qwen' and p['id_slot']==1 and p['temperature']==.7 and p['max_tokens']==700 and p['stream'] is False and 'dry_multiplier' not in p and 'lora' not in str(p.keys()).lower()
   answer=json.loads(r);legacy.check_sampler(key,p,answer)
   complete[key]=(d,answer)
  except Exception as exc:errors.append(key+': '+repr(exc))
 manifest,groups,days=schedule();soul=legacy.data_for(manifest['soul']).decode()
 expected_paths=[]
 for label,cases in groups.items():
  for case in cases:
   for seed in (1831,2718,3141):expected_paths.append((legacy.row_location(case,seed,'D'),case,seed))
 present={p for p in (J/'rows').rglob('*.json')}
 prefix=0
 while prefix<len(expected_paths) and expected_paths[prefix][0] in present:prefix+=1
 if present!={p for p,_,_ in expected_paths[:prefix]}:errors.append('row set is not exact deterministic prefix')
 hist=defaultdict(list)
 for path,case,seed in expected_paths[:prefix]:
  try:
   row=slot.read(path);assert slot.h(path.read_bytes())==path.with_suffix('.sha256').read_text().strip()
   assert (row['case'],row['seed'],row['arm'])==(case['id'],seed,'D')
   for a in row['attempts']:
    key=a['key'];assert key in complete and key not in mapped and a['receipt']==complete[key][0]
    assert slot.h((qroot/key/'settings.json').read_bytes())==a['measures']['sampler_file_sha256'];mapped.add(key)
   if replay:
    def saved(w,k,p,s):
     assert k in complete and (qroot/k/'request.json').read_bytes()==slot.json_bytes(p)
     return complete[k][1],complete[k][0]
    actual=compute_one(case,days[case['label']],soul,hist[case['label'],seed],seed,None,saved)
    assert actual==row,'offline saved-result replay differs'
   hist[case['label'],seed].append(row);rows[path.relative_to(J).as_posix()]=slot.h(path.read_bytes())
  except Exception as exc:errors.append(str(path)+': '+repr(exc))
 partial=sorted(set(complete)-mapped)
 next_case=expected_paths[prefix] if prefix<len(expected_paths) else None
 if partial:
  allowed_prefix=None if next_case is None else f"study-D/{next_case[1]['id']}/{next_case[2]}/"
  if not allowed_prefix or any(not k.startswith(allowed_prefix) for k in partial):errors.append('completed unledgered replies are not the single next scheduled case')
 return dict(rows=len(rows),actual_decisions=sum(1 for p in present if slot.read(p)['attempts']),complete_chains=len(complete),
  unknown=unknown,errors=errors,completed_unledgered=partial,row_sha256=rows,exact_prefix=prefix,
  next_case=None if next_case is None else dict(case=next_case[1]['id'],seed=next_case[2],arm='D'))

def verify_prior_shift():
 plan=slot.load_plan()
 raw=(E/'PRIOR-CLOSURE.json').read_bytes();files=(J/'PRIOR-RESULTS.json').read_bytes()
 if slot.h(raw)!=plan['prior_closure_sha256'] or slot.h(files)!=plan['prior_results_sha256']:raise RuntimeError('prior shift evidence changed')
 v=json.loads(raw)
 if v['status']!='CLEAN_WINDOW_STOP' or not v['controller_exit_confirmed'] or not v['tmux_absent'] or v['unknown'] or v['receipt_errors'] or v['completed_unledgered']:raise RuntimeError('prior shift not clean')
 if (v['completed_decisions'],v['complete_chains'])!=(294,383):raise RuntimeError('prior prefix differs')
 for rel,want in json.loads(files).items():
  if slot.h((J/rel).read_bytes())!=want:raise RuntimeError('saved output changed: '+rel)

def preflight():
 p=verify_inputs();verify_prior_shift();slot.verify_power(p)
 if dt.datetime.now(dt.timezone.utc).date().isoformat()!=p['date']:raise slot.EndWindow('operating date ended')
 c=reconcile(replay=True)
 if c['unknown'] or c['errors']:raise RuntimeError('unresolved prior evidence')
 return c
def run():
 directory=J/'sessions'/LABEL;lock=LOCK.open('a+b');fcntl.flock(lock,fcntl.LOCK_EX)
 slot.record(directory/'START.json',dict(utc=slot.utc(),pid=os.getpid(),boot=P('/proc/sys/kernel/random/boot_id').read_text().strip(),
  start_ticks=P('/proc/self/stat').read_text().rsplit(')',1)[1].split()[19],runtime_sha256=slot.h(P(__file__).read_bytes())))
 status='FAILED';error=None;window=None
 try:
  old=preflight();slot.record(directory/'PREFLIGHT.json',dict(utc=slot.utc(),existing=old))
  window=slot.day_window(slot.load_plan(),LABEL);manifest,groups,days=schedule();soul=legacy.data_for(manifest['soul']).decode()
  new_rows=0
  for label,cases in groups.items():
   histories={seed:[] for seed in (1831,2718,3141)}
   for i,case in enumerate(cases):
    for seed in (1831,2718,3141):
     history=histories[seed];dest=legacy.row_location(case,seed,'D');assert len(history)==i
     if time.time()+5>=window.cutoff:raise slot.EndWindow('clean stop before window end')
     if dest.exists():row=slot.read(dest)
     else:
      row=compute_one(case,days[label],soul,history,seed,window);slot.record(dest,row)
      slot.new(dest.with_suffix('.sha256'),(slot.h(dest.read_bytes())+'\n').encode());new_rows+=1
      if new_rows==1:window.event('first_verified_new_row',case=case['id'],arm='D',seed=seed,actual_requests=len(row['attempts']))
     history.append(row)
  status='ALL_DECISIONS_RECORDED'
 except slot.EndWindow as exc:status='CLEAN_WINDOW_STOP';error=str(exc)
 except slot.SlowStep as exc:status='LATENCY_STOP';error=str(exc)
 except BaseException as exc:error=repr(exc);traceback.print_exc()
 finally:
  final=reconcile(replay=True)
  if final['unknown'] or final['errors']:status='BLOCKED_UNRECONCILED'
  if status=='ALL_DECISIONS_RECORDED' and (final['rows']!=471 or final['actual_decisions']!=468 or final['completed_unledgered']):status='BLOCKED_INCOMPLETE'
  if window is not None and window.identity_fd is not None:os.close(window.identity_fd)
  slot.record(directory/'END.json',dict(utc=slot.utc(),status=status,error=error,reconciliation=final,server_or_timer_changed=False,no_automatic_restart=True))
  lock.close()
 print(json.dumps(dict(status=status,rows=final['rows'],chains=final['complete_chains'],error=error)),flush=True)
def launch():
 c=preflight();d=J/'sessions'/LABEL
 if d.exists():raise RuntimeError('existing intent: reconcile, never relaunch')
 lock=LOCK.open('a+b');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 d.mkdir(parents=True)
 command='exec '+shlex.join(['/usr/bin/python3','-B',str(P(__file__).resolve()),'run'])+' >'+shlex.quote(str(d/'stdout.log'))+' 2>'+shlex.quote(str(d/'stderr.log'))
 argv=['tmux','new-session','-d','-s',LABEL,'-c',str(J),command]
 slot.record(d/'INTENT.json',dict(utc=slot.utc(),argv=argv,source_freeze=FREEZE,existing=c,runtime_sha256=slot.h(P(__file__).read_bytes())))
 r=subprocess.run(argv,capture_output=True,timeout=15)
 slot.record(d/'LAUNCH.json',dict(utc=slot.utc(),returncode=r.returncode,stdout=r.stdout.decode(),stderr=r.stderr.decode()))
 lock.close();r.check_returncode();print(LABEL+' detached',flush=True)
if __name__=='__main__':
 if sys.argv[1:]==['launch']:launch()
 elif sys.argv[1:]==['run']:run()
 else:raise SystemExit('launch or run required')
