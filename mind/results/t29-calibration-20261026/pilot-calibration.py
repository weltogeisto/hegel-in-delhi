import fcntl, hashlib, json, os, pathlib, shlex, signal, subprocess, sys, time, urllib.request
from datetime import datetime, timezone

JOB=pathlib.Path(__file__).resolve().parent
PLAN=json.loads((JOB/'PLAN.json').read_text());MIRROR=pathlib.Path(PLAN['mirror'])
def now():return datetime.now(timezone.utc).isoformat()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,d):
    p=JOB/name
    with p.open('x',encoding='utf8') as f:f.write(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
    (MIRROR/name).write_bytes(p.read_bytes())
def export():
    for p in JOB.rglob('*'):
        if p.is_file():
            q=MIRROR/p.relative_to(JOB);q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(p.read_bytes())
def servers():
    found=[]
    for p in pathlib.Path('/proc').iterdir():
        if not p.name.isdigit():continue
        try:
            if (p/'comm').read_text().strip()!='llama-server':continue
            raw=(p/'cmdline').read_bytes()
            if b'--port\x008082\x00' not in raw:continue
            assert hashlib.sha256(raw).hexdigest()==PLAN['server']['argv_nul_sha256'],'8082 command changed'
            assert os.readlink(p/'cwd')==PLAN['server']['cwd'],'8082 cwd changed'
            assert ('LD_LIBRARY_PATH='+PLAN['server']['LD_LIBRARY_PATH']).encode() in (p/'environ').read_bytes().split(b'\0')
            found.append(int(p.name))
        except (FileNotFoundError,ProcessLookupError):continue
    assert len(found)<=1,'Multiple 8082 servers';return found
def query(path):
    with urllib.request.urlopen('http://127.0.0.1:8082'+path,timeout=5) as r:return r.status,json.loads(r.read())
def pi(action):
    code=(JOB/'pi-training-guard.py').read_text()
    command=shlex.join(['python3','-u','-c',code,action,PLAN['pi_guard_receipt']])
    r=subprocess.run([*PLAN['pi_ssh'],command],capture_output=True,text=True,timeout=55)
    tag=datetime.now(timezone.utc).strftime('%H%M%S%f')
    save(f'PI-{action}-{tag}.json',{'utc':now(),'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr})
    if r.returncode==2:return json.loads(r.stdout.strip().splitlines()[-1])
    if r.returncode:raise RuntimeError('Pi '+action+' failed; receipt retained')
    result=json.loads(r.stdout.strip().splitlines()[-1]);return result
def stop_own_training():
    p=JOB/'TRAINING-PROCESS.json'
    if not p.exists():return
    pid=json.loads(p.read_text())['pid'];proc=pathlib.Path('/proc')/str(pid)
    if not proc.exists():return
    raw=(proc/'cmdline').read_bytes()
    assert str(pathlib.Path(PLAN['source'])/'pc/train_hegel.py').encode() in raw and PLAN['output'].encode() in raw,'Do not terminate a reused/foreign PID'
    os.killpg(pid,signal.SIGTERM)
    end=time.monotonic()+30
    while proc.exists() and time.monotonic()<end:time.sleep(1)
    if proc.exists():os.killpg(pid,signal.SIGKILL)
def restore():
    with (JOB/'cleanup.lock').open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        if (JOB/'RESTORED.json').exists():return
        attempts=list(JOB.glob('RESTORE-ATTEMPT-*.json'))
        assert len(attempts)<2,'Two restoration attempts recorded; inspect receipts without another automatic retry'
        save(f'RESTORE-ATTEMPT-{len(attempts)+1}.json',{'utc':now()})
        stop_own_training()
        result={'utc':now(),'plain_restore_action':'PRESERVED_EXISTING','timer_restore':None}
        if (JOB/'PI-PAUSE-INTENT.json').exists() and not (JOB/'PI-DEFERRED.json').exists():
            if not servers():
                listener=subprocess.check_output(['ss','-ltnp','sport = :8082'],text=True);assert 'LISTEN' not in listener
                session='hegel-pilot-plain-restored-20261026-142600'
                command='exec '+shlex.join(['env','LD_LIBRARY_PATH='+PLAN['server']['LD_LIBRARY_PATH'],*PLAN['server']['argv']])+' >>'+shlex.quote(str(JOB/'plain-restoration.log'))+' 2>&1'
                subprocess.run(['tmux','new-session','-d','-s',session,'-c',PLAN['server']['cwd'],command],check=True,timeout=15)
                result.update(plain_restore_action='STARTED_EXACT_SAVED_ARGV_ONCE',session=session)
            deadline=time.monotonic()+210
            while time.monotonic()<deadline:
                try:
                    pids=servers();health=query('/health')
                    if len(pids)==1 and health[0]==200 and health[1].get('status')=='ok':break
                except (OSError,ValueError,urllib.error.URLError):pass
                time.sleep(3)
            else:raise RuntimeError('Exact plain server restoration did not become ready; no duplicate launch')
            pid=servers()[0];assert 'libggml-cuda.so' in (pathlib.Path('/proc')/str(pid)/'maps').read_text()
            slots=query('/slots');assert slots[0]==200 and len(slots[1])==3 and all(s['n_ctx']==16384 for s in slots[1])
            result.update(plain_pid=pid,argv_nul_sha256=PLAN['server']['argv_nul_sha256'],CUDA_backend_loaded=True,health=health,slots=slots[1])
            result['timer_restore']=pi('restore')
            assert result['timer_restore']['status'] in ['PRIOR_TIMER_STATE_RESTORED','NO_PAUSE_INTENT_NO_ACTION'],'Timer restoration deferred; preserve the active natural call'
        result['status']='EXACT_PLAIN_AND_PRIOR_TIMER_RESTORED';save('RESTORED.json',result)
def watchdog(parent,lockfd):
    limit=time.monotonic()+PLAN['maximum_compute_window_seconds']
    while pathlib.Path('/proc',str(parent)).exists() and not (JOB/'RESTORED.json').exists() and time.monotonic()<limit:time.sleep(2)
    if not (JOB/'RESTORED.json').exists():
        for attempt in range(1,3):
            if len(list(JOB.glob('RESTORE-ATTEMPT-*.json')))>=2:break
            try:restore();break
            except Exception as e:save(f'WATCHDOG-RESTORE-ERROR-{attempt}.json',{'utc':now(),'error':repr(e)});time.sleep(3)
    export();os.close(lockfd)
def main():
    start=time.monotonic();started=now();code=1;watch=None;lock=None;child=None
    try:
        assert not (JOB/'RUN-start.json').exists() and not pathlib.Path(PLAN['output']).exists()
        manifest=json.loads(pathlib.Path(PLAN['source_manifest']).read_text())
        assert len(manifest)==492 and all(sha(pathlib.Path(PLAN['source'])/p)==m['sha256'] for p,m in manifest.items())
        assert sha(JOB/'data/hegelizer.jsonl')==PLAN['data_sha256']
        lock=open(PLAN['server']['startup_lock'],'r+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert servers()==[PLAN['server']['pid']]
        save('RUN-start.json',{'status':'CALIBRATION_CONTROLLER_STARTED','utc':started,'controller_pid':os.getpid(),'source_files_verified':492,'model_training_started':False})
        watch=subprocess.Popen([sys.executable,__file__,'watchdog',str(os.getpid()),str(lock.fileno())],pass_fds=(lock.fileno(),),start_new_session=True,stdout=open(JOB/'watchdog.stdout.log','x'),stderr=open(JOB/'watchdog.stderr.log','x'))
        save('WATCHDOG.json',{'pid':watch.pid,'maximum_compute_window_seconds':PLAN['maximum_compute_window_seconds'],'restoration_reserve_seconds':600})
        save('PI-PAUSE-INTENT.json',{'utc':now(),'remote_receipt':PLAN['pi_guard_receipt']})
        pause=pi('pause')
        if pause['status'].startswith('DEFERRED_'):
            save('PI-DEFERRED.json',pause);code=2;raise RuntimeError('Active natural tick preserved; no server or timer change')
        assert pause['status']=='PAUSED_PROSPECTIVELY_FOR_AUTHORIZED_CALIBRATION'
        slots=query('/slots');assert slots[0]==200 and len(slots[1])==3 and all(not s.get('is_processing',True) for s in slots[1]),'Active inference call preserved; defer calibration'
        assert servers()==[PLAN['server']['pid']]
        save('SAVED-SERVER.json',{'utc':now(),**PLAN['server'],'slots_before':slots[1]})
        os.kill(PLAN['server']['pid'],signal.SIGINT)
        deadline=time.monotonic()+45
        while servers() and time.monotonic()<deadline:time.sleep(1)
        assert not servers(),'Plain server did not exit gracefully; no forced termination'
        save('PLAIN-SERVER-RELEASED.json',{'utc':now(),'signal':'SIGINT','pid':PLAN['server']['pid']})
        gpu=subprocess.run(['/usr/lib/wsl/lib/nvidia-smi','--query-compute-apps=pid,process_name,used_gpu_memory','--format=csv,noheader'],capture_output=True,text=True,timeout=15)
        assert gpu.returncode==0 and not gpu.stdout.strip(),'Other GPU workload present; restore and defer'
        assert not pathlib.Path(PLAN['output']).exists(),'Calibration output exists; preserve it'
        child=subprocess.Popen(PLAN['argv'],cwd=PLAN['source'],stdout=open(JOB/'trainer.stdout.log','x'),stderr=open(JOB/'trainer.stderr.log','x'),start_new_session=True,env={**os.environ,'PYTHONUNBUFFERED':'1','HF_HUB_OFFLINE':'1','TRANSFORMERS_OFFLINE':'1'})
        save('TRAINING-PROCESS.json',{'utc':now(),'pid':child.pid,'argv':PLAN['argv'],'kind':'FIVE_STEP_CALIBRATION_ONLY','full_training_started':False})
        export()
        remaining=PLAN['maximum_compute_window_seconds']-(time.monotonic()-start)-30
        try:code=child.wait(timeout=max(1,remaining))
        except subprocess.TimeoutExpired:stop_own_training();code=124
        save('CALIBRATION-MODEL-END.json',{'utc':now(),'exit':code,'wall_since_controller_start_seconds':time.monotonic()-start,'output':PLAN['output']})
    except BaseException as e:
        save('CONTROLLER-ERROR.json',{'utc':now(),'error':repr(e)})
    finally:
        try:restore()
        except BaseException as e:save('FINALLY-RESTORE-ERROR.json',{'utc':now(),'error':repr(e)});code=1
        if child is not None:
            try:child.wait(timeout=5)
            except subprocess.TimeoutExpired:pass
        if watch is not None and (JOB/'RESTORED.json').exists():
            try:watch.wait(timeout=10)
            except subprocess.TimeoutExpired:pass
        if lock is not None:lock.close()
        elapsed=time.monotonic()-start
        save('CONTROLLER-end.json',{'status':'EXITED','started_utc':started,'finished_utc':now(),'process_exit':code,'wall_seconds':elapsed,'restored':(JOB/'RESTORED.json').exists(),'prior_charged_upper_bound_seconds':PLAN['prior_charged_GPU_work_upper_bound_seconds'],'cumulative_charged_upper_bound_seconds':PLAN['prior_charged_GPU_work_upper_bound_seconds']+elapsed,'remaining_GPU_work_seconds_minimum':7200-PLAN['prior_charged_GPU_work_upper_bound_seconds']-elapsed,'calibration_only':True,'full_training_started':False})
        export()
    return code

if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='watchdog':watchdog(int(sys.argv[2]),int(sys.argv[3]));sys.exit(0)
    sys.exit(main())
