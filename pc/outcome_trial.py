#!/usr/bin/env python3
"""One isolated accelerated trajectory against an already running test server.

Run before/after in separate processes with --code pointing to frozen snapshots.
The caller owns the GPU server. This runner owns only a local recording proxy.
No publication, feeds, external lookup, live state, adapter or training writes.
"""
import argparse
import copy
from datetime import date,timedelta
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import json
import os
from pathlib import Path
import random
import sys
import threading
import time
import urllib.error
import urllib.request


def main(a):
    sys.path.insert(0,str(a.code.resolve()))
    os.environ['HEGEL_ENV']=os.devnull
    from world.config import Config
    from world.engine import Engine,until_of
    from world.world import World
    from world.mind import HTTPMind
    random.seed(a.seed)
    out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
    (out/'docs/days').mkdir(parents=True)
    for name in ('2026-10-02.json','index.json'):
        (out/'docs/days'/name).write_bytes((a.code/'docs/days'/name).read_bytes())
    ledger=(out/'http.jsonl').open('x',encoding='utf-8')
    lock=threading.Lock();counter=0;role_counts={};calls=[]

    class Proxy(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_GET(self):self.forward(None)
        def do_POST(self):self.forward(json.loads(self.rfile.read(int(self.headers['Content-Length']))))
        def forward(self,payload):
            nonlocal counter
            started=time.monotonic();forwarded=copy.deepcopy(payload)
            role='metadata'
            if payload is not None:
                if self.path=='/completion':role='vote' if payload.get('n_predict')==1 else 'completion'
                elif self.path=='/v1/chat/completions':
                    name=payload.get('response_format',{}).get('json_schema',{}).get('name')
                    role='claim-extraction' if name=='claims' else 'generation'
                else:role=self.path
                if role in ('generation','completion'):
                    # Claim checks never consume the generation seed sequence.
                    role_counts[role]=role_counts.get(role,0)+1
                    forwarded['seed']=(a.seed+10007*role_counts[role])%(2**31-1)
                if role in ('generation','completion','vote','claim-extraction'):
                    forwarded.update(id_slot=a.slot,cache_prompt=True,lora=[])
            request=urllib.request.Request(a.url.rstrip('/')+self.path,
                data=json.dumps(forwarded).encode() if forwarded is not None else None,
                headers={'Content-Type':'application/json'})
            error=None
            try:
                with urllib.request.urlopen(request,timeout=600) as response:
                    data=response.read();code=response.status
            except urllib.error.HTTPError as exc:
                data=exc.read();code=exc.code;error=str(exc)
            except Exception as exc:
                code=502;error=str(exc);data=json.dumps(dict(error=error)).encode()
            try:parsed=json.loads(data)
            except ValueError:parsed=dict(raw=data.decode('utf-8',errors='replace'))
            with lock:
                counter+=1
                row=dict(index=counter,role=role,path=self.path,request=payload,forwarded=forwarded,
                    status=code,response=parsed,error=error,wall_seconds=time.monotonic()-started)
                ledger.write(json.dumps(row,ensure_ascii=False)+'\n');ledger.flush();calls.append(row)
            self.send_response(code);self.end_headers();self.wfile.write(data)

    proxy=ThreadingHTTPServer(('127.0.0.1',0),Proxy)
    thread=threading.Thread(target=proxy.serve_forever,daemon=True);thread.start()
    overrides={'HEGEL_REPO':str(a.code.resolve()),'HEGEL_SOUL_FILE':'mind/soul-v2.md',
        'HEGEL_PUSH':'0','HEGEL_FEEDS':'0','HEGEL_SHELF':'0','HEGEL_WRITE_MODE':'chat',
        'HEGEL_STATE':str(out/'state'),'HEGEL_OUTCOME_MEMORY':str(int(a.condition=='after')),
        'HEGEL_CLAIM_CHECK':str(int(a.condition=='after')),
        'HEGEL_CLAIM_CALIBRATION':str(a.calibration.resolve()),
        'PC_MAC':'',
        'HEGEL_VOICE_ADAPTER_SCALE':'','HEGEL_WRITE_ADAPTER_SCALE':'','HEGEL_DECISION_ADAPTER_SCALE':'',
        'HEGEL_WRITE_REASONING_TOKENS':'384','HEGEL_DECISION_REASONING_TOKENS':'384',
        'HEGEL_OWL_REASONING_TOKENS':'384'}
    cfg=Config(overrides);cfg.docs=out/'docs'
    assert not cfg.push and not cfg.feeds and not cfg.shelf and cfg.wake is None
    mind=HTTPMind(f'http://127.0.0.1:{proxy.server_port}',timeout=600,
        writing_reasoning_tokens=384,decision_reasoning_tokens=384)
    engine=Engine(cfg,World(),mind,git=None)
    engine.lookup=lambda *args:dict(note='External lookup disabled in this isolated rehearsal.')
    (out/'configuration.json').write_text(json.dumps(dict(condition=a.condition,seed=a.seed,
        code=str(a.code.resolve()),config=overrides,slot=a.slot,days=a.days,
        model='WSL Qwen3.8-27B UD-Q4_K_M, adapter-free in both conditions',
        isolation='scratch docs/state; no publishing, wake, feeds, external lookup or training'),indent=2)+'\n')
    capture={};check_log=[]
    real_situation=engine.world.situation;real_check=engine.world.check
    def situation(*args,**kwargs):
        sit,ctx=real_situation(*args,**kwargs);capture.update(sit=sit,ctx=ctx)
        return sit,ctx
    def check(*args,**kwargs):
        result=real_check(*args,**kwargs)
        check_log.append(dict(proposal=copy.deepcopy(args[0]),errors=result[0],warnings=result[1]))
        return result
    engine.world.situation=situation;engine.world.check=check
    summaries=[];previous=engine.days.load(date(2026,10,2));failure=None
    try:
        for offset in range(a.days):
            d=date(2026,10,3)+timedelta(days=offset)
            day=engine.new_day(previous,d);engine.days.save(day)
            started=time.monotonic();steps=0
            with (out/f'{d}-steps.jsonl').open('x',encoding='utf-8') as log:
                while until_of(day).date()==d:
                    if steps>=240:raise RuntimeError(f'{d} exceeded 240 steps without completing')
                    before=copy.deepcopy(day['state']);check_log.clear()
                    step=engine.step(day,until_of(day));engine.days.save(day);steps+=1
                    if engine.days.load(d)!=day:raise RuntimeError('Persisted day reload mismatch')
                    row=dict(date=str(d),before=before,after=day['state'],step=step,
                        situation=capture.get('sit'),checks=check_log)
                    log.write(json.dumps(row,ensure_ascii=False,default=str)+'\n');log.flush()
                    print(f'{a.condition} seed={a.seed} {d} step={steps} {step["t"]} {step.get("decision",{}).get("action")}',flush=True)
                    if (step.get('mind') or {}).get('source') in ('away','quiet'):
                        raise RuntimeError('Rehearsal stopped on an unavailable or repeatedly refused decision; inspect raw HTTP and step logs')
                day['complete']=True;engine.days.save(day)
                engine.run_owl(day,until_of(day)+timedelta(minutes=90))
                engine.days.save(day)
            summary=dict(date=str(d),steps=steps,complete=True,owl=bool(day.get('owl')),
                depesche=bool((day.get('owl') or {}).get('depesche')),wall_seconds=time.monotonic()-started,
                writing_sittings=sum(e.get('k')=='writing' for e in day['entries']))
            summaries.append(summary);previous=day
            print(json.dumps(summary),flush=True)
    except Exception as exc:
        failure=dict(type=type(exc).__name__,message=str(exc));raise
    finally:
        proxy.shutdown();thread.join(timeout=3);proxy.server_close();ledger.close()
        (out/'completion.json').write_text(json.dumps(dict(condition=a.condition,seed=a.seed,
            completed_days=summaries,requested_days=a.days,finished=len(summaries)==a.days,
            failure=failure,http_calls=counter,publication=False,training=False),indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--url',required=True);p.add_argument('--condition',choices=['before','after'],required=True)
    p.add_argument('--code',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--calibration',type=Path,required=True);p.add_argument('--seed',type=int,required=True)
    p.add_argument('--days',type=int,choices=[1,2],required=True);p.add_argument('--slot',type=int,default=0)
    main(p.parse_args())
