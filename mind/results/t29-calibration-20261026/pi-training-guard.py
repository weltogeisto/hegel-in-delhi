import fcntl, hashlib, json, os, pathlib, subprocess, sys
from datetime import datetime, timezone

def now(): return datetime.now(timezone.utc).isoformat()
def run(argv):
    p=subprocess.run(argv,capture_output=True,text=True,timeout=25)
    if p.returncode: raise RuntimeError(str({'argv':argv,'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}))
    return p.stdout
def props(unit,names):
    return dict(l.split('=',1) for l in run(['systemctl','--user','show',unit,*sum((['-p',n] for n in names),[])]).splitlines() if '=' in l)
def timer(): return props('hegel-world.timer',['ActiveState','SubState','UnitFileState','NextElapseUSecRealtime'])
def service(): return props('hegel-world.service',['ActiveState','SubState','ExecMainStartTimestampMonotonic','Result'])
def seal(paths):
    return {str(p):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(paths)}
def save(p,d):
    with p.open('x',encoding='utf8') as f:f.write(json.dumps(d,ensure_ascii=False,indent=2)+'\n')

action,folder=sys.argv[1:];root=pathlib.Path(folder)
assert root==pathlib.Path('/home/faqts/hegel-eval/lora-calibration-20261026-142600')
os.chdir('/home/faqts/hegel-in-delhi');sys.path.insert(0,os.getcwd())
from world.config import Config
cfg=Config();result={'utc':now(),'action':action,'receipt_root':str(root),'mutated':False}
try:
    assert cfg.branch=='shadow' and cfg.clock_shift_min==300 and cfg.lead==15 and cfg.owl_at=='01:30'
    with (cfg.state/'tick.lock').open('r+') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:
            result['status']='DEFERRED_ACTIVE_NATURAL_TICK';print(json.dumps(result));sys.exit(2)
        if action=='pause':
            before_service=service();before_timer=timer()
            if before_service['ActiveState']!='inactive':
                result.update(status='DEFERRED_ACTIVE_NATURAL_SERVICE',service=before_service,timer=before_timer);print(json.dumps(result));sys.exit(2)
            assert not root.exists()
            assert run(['git','status','--porcelain=v1'])==''
            paths=set(pathlib.Path('docs/days').glob('*.json'))|set(cfg.state.glob('*.json'))
            before=seal(paths);head=run(['git','rev-parse','HEAD']).strip()
            root.mkdir(parents=True);(root/'raw').mkdir()
            for i,p in enumerate(sorted(paths)):(root/'raw'/f'{i:04d}.json').write_bytes(p.read_bytes())
            result.update(status='PAUSE_INTENT',service_before=before_service,timer_before=before_timer,head_before=head,raw_before=before,config={'branch':cfg.branch,'shift':cfg.clock_shift_min,'lead':cfg.lead,'owl_at':cfg.owl_at,'state':str(cfg.state)})
            save(root/'PAUSE-INTENT.json',result)
            run(['systemctl','--user','stop','hegel-world.timer']);result['mutated']=True
            after_service=service();after_timer=timer()
            assert after_timer['ActiveState']=='inactive' and after_timer['UnitFileState']==before_timer['UnitFileState']
            assert after_service['ActiveState']=='inactive' and after_service['ExecMainStartTimestampMonotonic']==before_service['ExecMainStartTimestampMonotonic']
            assert seal(paths)==before and run(['git','rev-parse','HEAD']).strip()==head and run(['git','status','--porcelain=v1'])==''
            result.update(status='PAUSED_PROSPECTIVELY_FOR_AUTHORIZED_CALIBRATION',timer_after=after_timer,service_after=after_service,raw_after_exact=True)
            save(root/'PAUSED.json',result)
        elif action=='restore':
            if not (root/'PAUSE-INTENT.json').exists():result['status']='NO_PAUSE_INTENT_NO_ACTION'
            elif (root/'RESTORED.json').exists():result=json.loads((root/'RESTORED.json').read_text());result['idempotent_readback']=True
            else:
                old=json.loads((root/'PAUSE-INTENT.json').read_text())['timer_before'];current=timer()
                assert current['UnitFileState']==old['UnitFileState'],'Enabled state changed independently; preserve it for review'
                if old['ActiveState']=='active':run(['systemctl','--user','start','hegel-world.timer']);result['mutated']=True
                elif old['ActiveState']=='inactive':assert current['ActiveState']=='inactive'
                else:raise RuntimeError('Prior timer state is neither active nor inactive')
                after=timer();assert after['ActiveState']==old['ActiveState'] and after['UnitFileState']==old['UnitFileState']
                result.update(status='PRIOR_TIMER_STATE_RESTORED',timer_before=current,timer_after=after,original_timer=old)
                save(root/'RESTORED.json',result)
        else:raise ValueError(action)
except Exception as e:
    result.update(status='FAILED_PRESERVE_RECEIPTS',error=type(e).__name__+': '+str(e));print(json.dumps(result));sys.exit(1)
print(json.dumps(result,ensure_ascii=False),flush=True)
