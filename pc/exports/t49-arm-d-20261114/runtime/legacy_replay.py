"""Fixed-day decision generation. Model calls go only through the original shared-slot guard."""
import copy, datetime as dt, fcntl, hashlib, json, os, pathlib, re, sys, time
from collections import defaultdict
from zoneinfo import ZoneInfo
from shared_slot import J, E, S, read, h, record, utc, load_plan, send, day_window, EndWindow, SlowStep
from world import contract, engine, memory, report, world
MANIFEST_SHA='1c7105a26f8604b62bac9d84d0861f4f9fb769ad2db48b573e6277e8281dfd3a'
W=world.World()
def checked_file(path,digest):
    data=path.read_bytes()
    if h(data)!=digest:raise ValueError('frozen bytes differ: '+str(path))
    return data
def data_for(ref):return checked_file(J/'fixtures/objects'/ref,ref)
def read_obj(ref):return json.loads(data_for(ref))
def compact(text,limit=140):
    return text if len(text)<=limit else text[:limit-1].rsplit(' ',1)[0]+'…'
def earlier_lines(day,i,finished):
    lines=[];quoted=[]
    for k in range(max(0,i-6),i):
        row=finished[k]
        text=row['thought']
        if not text:continue
        st=day['steps'][k];answer=st['decision']
        first=compact(re.split(r'(?<=[.!?])\s',text.strip())[0])
        activity=[seg['now'] for seg in day['segments'] if seg.get('now') and st['t']<=seg['from']<st['end'] and seg['to']<=st['end']]
        done=compact(' '.join(dict.fromkeys(activity)))
        line=f"{st['t']} recorded step: {answer['action']} ({answer['place']})"
        if done:line+='; executed activity: '+done
        line+='; you thought: “'+first+'”'
        warnings=st['mind'].get('warnings') or []
        if warnings:line+=' Engine note: '+compact('; '.join(warnings[:2]))+'.'
        lines.append(line);quoted.append(first)
    while len(lines)>1 and sum(len(x)+3 for x in lines)>world.RECENT_CHARS:lines.pop(0);quoted.pop(0)
    return lines,quoted
def render_case(case,arm,day,history):
    i=case['index'];assert len(history)==i
    base=data_for(case['template']).decode()
    by_time={r['time']:r for r in history}
    visible=list(case['visible_prior'])
    for token,d in case['recall_refs'].items():
        assert base.count(token)==1 and d['time']<case['time']
        text=by_time[d['time']]['thought']
        if text:
            shown=memory.fit(d['prefix'].removeprefix('- '),text,quote=True)
            base=base.replace(token,'- '+shown)
            visible.append(shown.split('you thought: “',1)[1][:-1])
        else:base=base.replace(token+'\n','')
    assert '{{T39_' not in base
    sections=base.split('\n\n')
    sections=[s for s in sections if s.strip()!='You remember:']
    if arm=='B':
        again=report.echoes([r['thought'] for r in history if r['thought']])
        if again:
            index=next(k for k,x in enumerate(sections) if x.startswith('On your mind:'))
            sections[index]+='\n- '+engine.ECHO_LINE.format(phrases=', '.join('“'+x+'”' for x in again))
            visible.extend(again)
    earlier,quoted=earlier_lines(day,i,history)
    if earlier:
        insert=next(k for k,x in enumerate(sections) if x.startswith(('From your shelf:','What happens:')))
        sections.insert(insert,'Earlier today:\n'+''.join('- '+line+'\n' for line in earlier).rstrip('\n'))
    visible.extend(quoted)
    prompt='\n\n'.join(sections)
    assert all(v in prompt for v in visible)
    return prompt,visible
def payload(messages,sit,arm,seed):
    result=dict(model='qwen',messages=messages,max_tokens=700,temperature=0.7,chat_template_kwargs={'enable_thinking':False},response_format={'type':'json_schema','json_schema':{'name':'answer','schema':contract.decision_schema(sit)}},stream=False,id_slot=1,seed=seed)
    if arm=='C':result.update(dry_multiplier=0.8,dry_base=1.75,dry_allowed_length=3,dry_penalty_last_n=4096)
    return result
def validator(case,day,history):
    sit=read_obj(case['fixed_sit']);state=read_obj(case['validation_state'])
    recent=case['recent_before']+[(r['time'],r['thought']) for r in history if r['thought']]
    ctx=dict(t=engine.at_dt(dt.date.fromisoformat(case['date']),engine.hm(case['time'])),present=case['present'],public=case['public'],recent=recent[-12:],known_text=data_for(case['known_before']).decode()+'\n'+data_for(case['known_current']).decode())
    return sit,state,ctx
def check_sampler(key,p,ans):
    raw=read(J/'requests'/key/'settings.json');last=raw['after'];a=last['params'];old=raw['before']
    if last['id']!=1 or old['id_task']==last['id_task'] or a.get('seed')!=p['seed'] or a.get('n_predict')!=p['max_tokens']:raise ValueError('effective sampler could not be attributed to '+key)
    import struct
    expected=struct.unpack('<f',struct.pack('<f',p.get('dry_multiplier',0.0)))[0]
    if a['dry_multiplier']!=expected or 'dry' not in a['samplers'] and expected or not abs(a['temperature']-p['temperature'])<1e-6:raise ValueError('effective sampler mismatch at '+key)
    if expected and any(a[k]!=p[k] for k in ('dry_allowed_length','dry_base','dry_penalty_last_n')):raise ValueError('effective DRY parameters differ')
    return dict(usage=ans.get('usage'),timings=ans.get('timings'),peak_sampled_gpu_mib=max(read(J/'requests'/key/'begin.json')['gpu_mib'],raw['gpu_mib_after']),sampler_file_sha256=h((J/'requests'/key/'settings.json').read_bytes()))
def compute_one(case,day,soul,history,arm,seed,window):
    run_id=f"{case['id']}/{seed}/{arm}"
    result=dict(case=case['id'],time=case['time'],arm=arm,seed=seed,thought=None,attempts=[],repetition_refusals=0,echo_grams=[],warnings=[],schema_fallbacks=0,source='fixed decision replay')
    # Replay every historically offered decision, even when today's bedtime rule is earlier.
    if case['historical_source']=='bedtime' and day['steps'][case['index']]['mind']['attempts']==0:
        result['source']='recorded deterministic bedtime, no decision request';return result
    text,visible=render_case(case,arm,day,history)
    messages=[{'role':'system','content':soul},{'role':'user','content':text}]
    sit,state,ctx=validator(case,day,history)
    result.update(prompt_sha256=h(text.encode()),visible_earlier_thoughts=visible)
    for attempt in range(1,4):
        key='study/'+run_id+'/'+str(attempt);p=payload(messages,sit,arm,seed)
        ans,info=send(window,key,p,90)
        measures=check_sampler(key,p,ans)
        raw=(ans['choices'][0]['message'].get('content') or '').strip()
        decision=contract.extract_json(raw)
        errors,warnings,rep=W.check(decision,sit,ctx,state)
        result['repetition_refusals']+=int(any('this repeats what you thought at' in err for err in errors))
        result['attempts'].append(dict(key=key,receipt=info,measures=measures,errors=errors,warnings=warnings,finish_reason=ans['choices'][0].get('finish_reason')))
        if not errors:
            accepted,_=rep
            result.update(decision=accepted,thought=accepted.get('thought'),warnings=warnings)
            old=set().union(*(report.grams(q) for q in visible))
            result['echo_grams']=sorted(report.grams(accepted.get('thought') or '') & old)
            break
        messages=messages+[{'role':'assistant','content':raw},{'role':'user','content':'The world refuses this step: '+'; '.join(errors)+'. Decide again. Answer with the JSON object only.'}]
    if not result['thought']:result['source']='quiet after recorded contract refusals'
    return result
def reconcile_requests():
    base=J/'requests'
    if not base.is_dir():raise ValueError('initial probe evidence missing')
    begins={p.parent for p in base.rglob('begin.json')}
    for suffix in ('unknown.json','partial.bin'):
        if any(base.rglob(suffix)):raise RuntimeError('unresolved '+suffix+'; no transmission')
    for suffix in ('request.json','response.bin','done.json','settings.json'):
        if {p.parent for p in base.rglob(suffix)}!=begins:raise RuntimeError('request membership differs for '+suffix)
    for folder in begins:
        b=read(folder/'begin.json');d=read(folder/'done.json')
        if d['status']!=200 or h((folder/'request.json').read_bytes())!=d['request_sha256'] or b['request_sha256']!=d['request_sha256'] or h((folder/'response.bin').read_bytes())!=d['response_sha256']:raise RuntimeError('receipt changed at '+str(folder))
    return len(begins)
def row_location(case,seed,arm):return J/'rows'/case['label']/str(seed)/arm/(str(case['index']).zfill(3)+'.json')
def run_day(label):
    plan=load_plan();assert read(J/'DRY-RECONCILIATION.json')['verified']
    manifest=json.loads(checked_file(J/'fixtures/MANIFEST.json',MANIFEST_SHA));soul=data_for(manifest['soul']).decode()
    protocol=read(J/'STUDY-PROTOCOL.json')
    assert protocol['case_sha256']==MANIFEST_SHA and h((J/'private/blind-order.json').read_bytes())==protocol['blind_order_sha256']
    assert len(manifest['case_rows'])==157
    count=reconcile_requests()
    groups=defaultdict(list)
    for row in manifest['case_rows']:groups[row['label']].append(row)
    days={key:read(J/'days'/(key+'.json')) for key in groups}
    window=day_window(plan,label)
    start=utc();rows_done=0;new_rows=0
    window.event('study_window_opened',reconciled_requests=count)
    counts=defaultdict(int)
    try:
        for day_index,(day_key,cases) in enumerate(groups.items()):
            histories={(seed,arm):[] for seed in plan['seeds'] for arm in protocol['arms']}
            for i,case in enumerate(cases):
                for si,seed in enumerate(plan['seeds']):
                    arms=protocol['arms'];offset=(i+si+day_index)%len(arms)
                    for arm in arms[offset:]+arms[:offset]:
                        history=histories[seed,arm];dest=row_location(case,seed,arm)
                        if time.time()+5>=window.cutoff:raise EndWindow('clean stop before window end')
                        if dest.exists():
                            row=read(dest)
                            if (row['case'],row['seed'],row['arm'])!=(case['id'],seed,arm):raise RuntimeError('existing row identity differs')
                            for a in row['attempts']:
                                folder=J/'requests'/a['key']
                                if read(folder/'done.json')!=a['receipt'] or h((folder/'settings.json').read_bytes())!=a['measures']['sampler_file_sha256']:raise RuntimeError('existing row receipt differs')
                            if h(dest.read_bytes())!=dest.with_suffix('.sha256').read_text().strip():raise RuntimeError('existing result digest differs; preserve')
                        else:
                            row=compute_one(case,days[day_key],soul,history,arm,seed,window)
                            record(dest,row)
                            from shared_slot import new
                            new(dest.with_suffix('.sha256'),(h(dest.read_bytes())+'\n').encode())
                            new_rows+=1
                            if new_rows==1:window.event('first_verified_new_row',case=case['id'],arm=arm,seed=seed,actual_requests=len(row['attempts']))
                        assert len(history)==i;history.append(row);rows_done+=1;counts[arm]+=1
        status='ALL_DECISIONS_RECORDED'
    except EndWindow as exc:status='CLEAN_WINDOW_STOP';window.event('window_cutoff',reason=str(exc))
    except SlowStep as exc:status='LATENCY_STOP';window.event('latency_guard_stop',reason=str(exc))
    finally:
        window.event('study_window_ended',status=locals().get('status','ERROR'),rows_traversed=rows_done,new_rows=new_rows)
    return dict(status=status,since_utc=start,end_utc=utc(),rows_traversed=rows_done,new_rows=new_rows,counts_by_arm=dict(counts),normal_stop_utc=dt.datetime.fromtimestamp(window.cutoff,dt.timezone.utc).isoformat())
if __name__=='__main__':
    label=sys.argv[1];lock=(pathlib.Path('/home/ai/hegel-eval/codex-tasks-20261106/t39-20261106/serial.lock')).open('a+b')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    folder=J/'sessions'/label
    record(folder/'START.json',dict(utc=utc(),pid=os.getpid(),label=label))
    try:result=run_day(label)
    except BaseException as exc:
        record(folder/'END.json',dict(utc=utc(),status='BLOCKED',reason=repr(exc)));raise
    else:record(folder/'END.json',result);print(json.dumps(result),flush=True)
