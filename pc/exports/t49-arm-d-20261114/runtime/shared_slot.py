"""One serial client for slot 1. Never controls the shared server or Hegel."""
import contextlib, datetime as dt, fcntl, hashlib, http.client, json, math, os, pathlib, re, select, signal, subprocess, sys, time
from zoneinfo import ZoneInfo
P=pathlib.Path
J=P('/home/ai/hegel-eval/codex-tasks-20261114/t39-d-111200')
E=P('/mnt/c/hegel/handover/codex-tasks-20261114/t39-d-111200')
S=J/'source'
GIT_REPO=P('/home/ai/hegel-eval/codex-tasks-20261114/t39-d-source-111200')
sys.path.insert(0,str(S))
from tools.recorded_llama import LatencyGuard, TransportError, json_bytes
from world.engine import until_of
from recovery_guard import call_measure, RULE_SHA
PLAN_PATH=J/'PLAN.json'
def h(b): return hashlib.sha256(b).hexdigest()
def read(p): return json.loads(p.read_bytes())
def utc(): return dt.datetime.now(dt.timezone.utc).isoformat()
def new(p,b):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
    fd=os.open(p.parent,os.O_DIRECTORY)
    try:os.fsync(fd)
    finally:os.close(fd)
def record(p,v):new(p,json_bytes(v))
def stat(p):
    s=P(p).stat();return dict(device=s.st_dev,inode=s.st_ino,bytes=s.st_size,mtime_ns=s.st_mtime_ns)
def run(cmd, wait=25): return subprocess.check_output(cmd,timeout=wait,stderr=subprocess.PIPE)
def git(*args):return run(['git','-C',str(GIT_REPO),*args])
class Defer(Exception):pass
class EndWindow(Exception):pass
class SlowStep(Exception):pass
def load_plan():
    b=PLAN_PATH.read_bytes()
    if h(b)!='41e1d798851ac2ea99e4ad561b17377ccf13ba80e0ab0691b2204046da4ce78e':raise ValueError('plan hash differs')
    d=json.loads(b)
    for label,info in d['days'].items():
        if h((J/'days'/(label+'.json')).read_bytes())!=info['sha256']:raise ValueError('day changed: '+label)
    return d
def until_due(day,plan):
    return (until_of(day)-dt.timedelta(minutes=plan['clock_shift_minutes']+plan['lead_minutes'])).timestamp()
def window_fits(now,allowance,cutoff,live_due):
    if now+allowance+5>=cutoff:raise EndWindow('no full request fits before clean stop')
    if now+allowance+10>=live_due:raise Defer('Hegel is due before the full request can drain')
def get_slots():
    c=http.client.HTTPConnection('127.0.0.1',8082,timeout=2)
    try:
        c.request('GET','/slots');r=c.getresponse();b=r.read()
        if r.status!=200:raise RuntimeError('slot inventory unavailable')
        slots=json.loads(b)
        if sorted((x['id'],x['n_ctx']) for x in slots)!=[(0,16384),(1,16384),(2,16384)]:raise RuntimeError('server slot layout changed')
        return slots
    finally:c.close()
def sampler_view(slots,slot=1):
    row=next(s for s in slots if s['id']==slot)
    return {k:row.get(k) for k in ('id','id_task','is_processing','n_ctx','params','n_prompt_tokens')}
def gpu_mib():
    data=run(['/usr/lib/wsl/lib/nvidia-smi','--query-gpu=memory.used','--format=csv,noheader,nounits'],5).decode().splitlines()
    if len(data)!=1:raise RuntimeError('unexpected GPU count')
    return int(data[0].strip())
class Window:
    def __init__(self,label,plan,cutoff,anchor,limit):
        self.plan=plan;self.label=label;self.cutoff=cutoff;self.anchor=anchor;self.limit=limit
        self.dir=J/'windows'/label;self.dir.mkdir(exist_ok=True,parents=True)
        self.head=anchor;self.obs=None;self.checked=0;self.cached_slots=None
        self.recovery_passes=[];self.recovery_ready=False
        self.date=(dt.datetime.now(dt.timezone.utc)+dt.timedelta(minutes=plan['clock_shift_minutes']+330)).date().isoformat()
        self.log=self.dir/'events.jsonl';self.identity_fd=None
    def event(self,name,**vals):
        with self.log.open('ab') as f:f.write(json_bytes(dict(event=name,utc=utc(),**vals)));f.flush();os.fsync(f.fileno())
    def bind(self):
        d=self.plan
        if P('/proc/sys/kernel/random/boot_id').read_text().strip()!=d['linux_boot']:raise RuntimeError('Linux boot changed')
        lines=run(['ss','-H','-ltnp','sport = :8082']).decode().splitlines()
        if len(lines)!=1:raise RuntimeError('plain 8082 listener absent or ambiguous')
        matches=re.findall(r'pid=(\d+)',lines[0])
        if len(matches)!=1:raise RuntimeError('ambiguous listener process')
        self.pid=int(matches[0]);self.proc=P('/proc')/str(self.pid);self.identity_fd=os.pidfd_open(self.pid)
        self.poll=select.poll();self.poll.register(self.identity_fd,select.POLLIN)
        if self.pid!=d['expected_pid'] or (self.proc/'stat').read_text().rsplit(')',1)[1].split()[19]!=d['expected_start_ticks']:raise RuntimeError('original server identity changed')
        argv=(self.proc/'cmdline').read_bytes().rstrip(b'\0').split(b'\0')
        if argv!=[os.fsencode(x) for x in d['expected_argv']] or self.proc.joinpath('exe').resolve()!=P(d['expected_argv'][0]).resolve():raise RuntimeError('listener is not the saved plain Qwen')
        if stat(d['weight_path'])!=d['weight_stat'] or 'libggml-cuda.so' not in (self.proc/'maps').read_text():raise RuntimeError('weight or CUDA backend differs')
        self.event('server_identity',pid=self.pid,start_ticks=(self.proc/'stat').read_text().rsplit(')',1)[1].split()[19],boot=P('/proc/sys/kernel/random/boot_id').read_text().strip(),argv_sha256=h((self.proc/'cmdline').read_bytes()),exe=d['expected_argv'][0],model_sha256=d['weight_sha256'],adapters='none in verified argv',cutoff=self.cutoff)
    def observe(self):
        head=git('ls-remote','--exit-code','origin','refs/heads/shadow').decode().split()[0]
        if head==self.head:return
        git('fetch','--no-tags','--no-write-fetch-head','origin',head);git('merge-base','--is-ancestor',self.head,head)
        name='docs/days/'+self.date+'.json'
        for row in git('rev-list','--parents','--first-parent','--reverse',self.head+'..'+head).decode().splitlines():
            hashes=row.split()
            if len(hashes)!=2:raise RuntimeError('nonlinear shadow history')
            c,p=hashes
            if p!=self.head:raise RuntimeError('shadow history skipped a parent')
            self.head=c
            names=git('diff','--name-only',p,c,'--',name).decode().splitlines()
            if name not in names:continue
            bb=git('show',c+':'+name);day=json.loads(bb)
            prev=subprocess.run(['git','-C',str(GIT_REPO),'show',p+':'+name],capture_output=True,timeout=10)
            old=json.loads(prev.stdout)['steps'] if prev.returncode==0 else []
            if day['steps'][:len(old)]!=old:raise RuntimeError('natural day prefix changed')
            appended=[x for x in day['steps'][len(old):] if x.get('decision') is not None]
            if not appended:continue
            stamp=int(git('show','-s','--format=%ct',c).decode())
            if stamp>time.time()+1:raise RuntimeError('future shadow commit')
            for st in appended:
                self.obs=None
                metric=call_measure(st.get('mind') or {})
                if metric is None:
                    self.recovery_passes=[]
                    self.event('natural_step_without_call',sha=c,world_time=st['t'])
                    continue
                observed=dict(observed_unix=stamp,limit_s=self.limit,commit=c,parent=p,world_time=st['t'],next_due_unix=until_due(day,self.plan),day_sha256=h(bb),**metric)
                self.event('natural_step_measured',**observed)
                if metric['latency_s']>self.limit:
                    self.recovery_passes=[]
                    self.event('slow_natural_step',sha=c,limit_s=self.limit,stop_number_today=self.plan['prior_stops_today']+1,**metric)
                    raise SlowStep('natural per-call latency exceeded 13.2 seconds; no automatic restart')
                self.recovery_passes=(self.recovery_passes+[observed])[-2:]
                self.obs=observed
            if self.obs:
                path=self.dir/('observation-'+c+'.json')
                if not path.exists():record(path,self.obs)
    def admit(self,seconds):
        verify_power(self.plan)
        if time.time()+seconds+5>=self.cutoff:raise EndWindow('request will not fit')
        if self.poll.poll(0):raise RuntimeError('original serving process exited')
        self.observe()
        if not self.obs:raise Defer('awaiting a new natural decision')
        if len(self.recovery_passes)<(2 if self.plan['prior_stops_today'] else 1):raise Defer('waiting for required consecutive passing natural steps')
        row=self.obs
        try:LatencyGuard(self.dir/('observation-'+row['commit']+'.json'),limit=self.limit)()
        except TransportError as e:raise Defer(str(e)) from e
        window_fits(time.time(),seconds,self.cutoff,row['next_due_unix'])
        s=get_slots()
        if any(x['is_processing'] for x in s):raise Defer('world or another client has an active request')
        if run(['ss','-H','-tn','state','established','sport = :8082']).strip():raise Defer('an established 8082 connection is active')
        if not self.recovery_ready:
            record(self.dir/'RECOVERY-READY.json',dict(utc=utc(),rule_sha256=RULE_SHA,consecutive_natural_steps=self.recovery_passes,limit_s=self.limit,total_step_latency_retained=True,prior_stop_count_today=self.plan['prior_stops_today']))
            self.event('recovery_ready',rule_sha256=RULE_SHA,consecutive_natural_steps=self.recovery_passes)
            self.recovery_ready=True
        return row,s
    def await_admission(self,seconds):
        last=None
        while True:
            try:return self.admit(seconds)
            except Defer as e:
                if str(e)!=last:self.event('defer',reason=str(e));last=str(e)
                remain=self.cutoff-time.time()-seconds-5
                if remain<=0:raise EndWindow('clean stop before next request')
                time.sleep(min(20,remain))
def extract_dry(payload,answer,before,after):
    direct=(answer.get('__verbose') or {}).get('generation_settings',{}) or answer.get('generation_settings',{})
    p=after.get('params') or {}
    linked=(after['id_task'] is not None and after['id_task']!=before['id_task'] and p.get('seed')==payload['seed'] and p.get('n_predict')==payload['max_tokens'])
    settings=direct or (p if linked else {})
    ok=all(settings.get(k)==payload[k] for k in ('dry_multiplier','dry_base','dry_allowed_length','dry_penalty_last_n'))
    return dict(verified=ok,source='chat response' if direct else 'slot 1 completed task' if linked else 'unavailable',settings=settings)
def send(w,key,payload,seconds):
    base=J/'requests'/key
    request=json_bytes(payload);done=base/'done.json';begin=base/'begin.json'
    if done.exists():
        result=read(done);reply=(base/'response.bin').read_bytes()
        if (not begin.exists() or h(request)!=result['request_sha256'] or (base/'request.json').read_bytes()!=request or h(reply)!=result['response_sha256'] or result['status']!=200):raise RuntimeError('saved reply failed reconciliation')
        return json.loads(reply),result
    if base.exists():raise RuntimeError('partial request evidence; do not resend '+key)
    if payload.get('id_slot')!=1 or payload.get('model')!='qwen' or payload.get('stream') is not False:raise ValueError('unauthorized request routing')
    row,slots=w.await_admission(seconds)
    mem=gpu_mib()
    # Recheck after the snapshot and immediately before sending. The world timeline must cover the whole allowance.
    row,slots=w.await_admission(seconds)
    proof=dict(utc=utc(),observation=row,slot=sampler_view(slots),allowance_s=seconds,gpu_mib=mem)
    body_hash=h(request)
    new(base/'request.json',request);record(begin,dict(request_sha256=body_hash,**proof))
    absolute=time.monotonic()+seconds
    def expired(sig,frame):raise TimeoutError('absolute request deadline')
    original=signal.signal(signal.SIGALRM,expired)
    httpc=http.client.HTTPConnection('127.0.0.1',8082,timeout=seconds)
    try:
        window_fits(time.time(),seconds,w.cutoff,row['next_due_unix'])
        if w.poll.poll(0) or time.time()-row['observed_unix']>300:raise RuntimeError('admission expired before transmission')
        signal.setitimer(signal.ITIMER_REAL,max(.001,absolute-time.monotonic()))
        w.event('sent',key=key);httpc.request('POST','/v1/chat/completions',body=request,headers={'Content-Type':'application/json','Connection':'close'})
        resp=httpc.getresponse();raw=resp.read();status=resp.status
        new(base/'response.bin',raw)
    except BaseException as exc:
        partial=getattr(exc,'partial',b'')
        if partial:new(base/'partial.bin',partial)
        record(base/'unknown.json',dict(utc=utc(),reason=repr(exc),no_resend=True));raise
    finally:
        signal.setitimer(signal.ITIMER_REAL,0);signal.signal(signal.SIGALRM,original);httpc.close()
    elapsed=seconds-(absolute-time.monotonic())
    info=dict(utc=utc(),seconds=elapsed,status=status,request_sha256=body_hash,response_sha256=h(raw))
    record(done,info)
    if status!=200:raise RuntimeError('recorded HTTP '+str(status))
    answer=json.loads(raw);out=sampler_view(get_slots());record(base/'settings.json',dict(before=proof['slot'],after=out,gpu_mib_after=gpu_mib(),timings=answer.get('timings'),usage=answer.get('usage')))
    return answer,info
def verify_power(plan):
    current=read(P('/mnt/c/ProgramData/PCPowerGuard/state.json'))
    if current.get('pendingUtc'):raise EndWindow('shutdown pending')
    if current.get('boot')!=plan['power'].get('boot'):raise EndWindow('Windows boot changed')
    deadline=dt.datetime.fromisoformat(current['deadlineUtc'].replace('Z','+00:00')).timestamp()-900
    if time.time()+95>=min(deadline,dt.datetime.fromisoformat(plan['cutoff_utc']).timestamp()):raise EndWindow('clean stop before power or authorized cutoff')
    return deadline
def day_window(plan,label,anchor=None):
    local=dt.datetime.now(ZoneInfo('Europe/Berlin'));day=local.date().isoformat()
    if day!=plan['date']:raise EndWindow('no authorization for this operating date')
    pi_bytes=(E/('PI-WINDOW-'+day+'.json')).read_bytes()
    if h(pi_bytes)!=plan['pi_window_sha256']:raise RuntimeError('Pi window proof changed')
    pi=json.loads(pi_bytes)
    if pi['shift']!=1170 or pi['lead']!=15 or pi['timer']['ActiveState']!='active' or pi['timer']['UnitFileState']!='enabled':raise RuntimeError('approved natural world window not established')
    proof=(E/'MODEL-TMUX-REVALIDATED.json').read_bytes()
    if h(proof)!=plan['model_proof_sha256'] or json.loads(proof)['linux_boot']!=P('/proc/sys/kernel/random/boot_id').read_text().strip():raise RuntimeError('model proof changed or rebooted')
    if os.readlink('/proc/self/ns/mnt')!=plan['mount_namespace']:raise RuntimeError('model proof belongs to another mount namespace')
    cutoff=min(dt.datetime.fromisoformat(plan['cutoff_utc']).timestamp(),verify_power(plan))
    w=Window(label,plan,cutoff,anchor or plan['anchor'],plan['limit_s']);w.bind();return w
