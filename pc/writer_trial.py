#!/usr/bin/env python3
"""Fixed histories, paired writers, and sealed blind review; no rollout or training.

prepare --out DIR freezes six saved runs listed in --sources JSON and the Karl
case in --cases JSON. run --out DIR --task T3|T4 uses spare slots on an existing
adapter-free server. It never starts/stops a server or writes to a saved run.
"""
import argparse
import copy
import csv
from datetime import date, datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import random
import re
import secrets
import subprocess
import sys
import time
import traceback
import urllib.request

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from world import contract, owl, records, shelf, works
from world.config import Config
from world.engine import Engine
from world.mind import HTTPMind
from world.memory import encountered_text
from world.world import World, at_dt
from pc.blind_review import GUIDE

SEEDS = [2026101201, 2026101202, 2026101203]
CEILING = 7263


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temp.replace(path)


def stamp():
    return datetime.now(timezone.utc).isoformat()


def api(url, path, payload=None):
    req = urllib.request.Request(url.rstrip('/') + path,
        data=None if payload is None else json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=600) as response:
        return json.load(response)


def config(out, variant='A', shelf_on=False):
    cfg = Config(dict(HEGEL_REPO=str(ROOT), HEGEL_ENV=os.devnull,
        HEGEL_SOUL_FILE='mind/soul-v2.md', HEGEL_STATE=str(out / 'scratch-state'),
        HEGEL_PUSH='0', HEGEL_FEEDS='0', HEGEL_SHELF=str(int(shelf_on)),
        HEGEL_WRITE_MODE='chat', HEGEL_OUTCOME_MEMORY=str(int(variant == 'B')),
        HEGEL_EVIDENCE_VIEW='compact' if variant == 'B' else 'full',
        HEGEL_CLAIM_CHECK='0', PC_MAC='', HEGEL_WRITE_REASONING_TOKENS='384',
        HEGEL_OWL_REASONING_TOKENS='384', HEGEL_VOICE_ADAPTER_SCALE='',
        HEGEL_WRITE_ADAPTER_SCALE='', HEGEL_DECISION_ADAPTER_SCALE=''))
    assert not cfg.push and not cfg.feeds and not cfg.claim_check and cfg.wake is None
    return cfg


def read_calls(run):
    path = run / 'http.jsonl'
    if not path.exists(): path = run / 'http-ledger.jsonl'
    if path.exists():
        with path.open(encoding='utf-8') as handle:
            rows = [json.loads(line) for line in handle]
        return [r.get('request') or r.get('original_payload') for r in rows
                if r.get('request') or r.get('original_payload')], [path]
    files = sorted((run / 'calls').glob('*.json'))
    return [json.loads(p.read_text())['request'] for p in files], files


def writing_calls(calls):
    out = {}
    for req in calls:
        schema = req.get('response_format', {}).get('json_schema', {}).get('schema') or req.get('json_schema') or {}
        if 'continues' not in schema.get('properties', {}): continue
        messages = req.get('messages') or []
        if len(messages) < 4: continue
        match = re.search(r', (\d\d:\d\d) Delhi time\.', messages[1]['content'])
        if match:
            out.setdefault(match[1], req)  # first request, never a selected successful retry
    return out


def trace_rows(run, day_date):
    path = run / f'{day_date}-steps.jsonl'
    if not path.exists(): path = run / 'step-ledger.jsonl'
    if not path.exists(): raise ValueError('Saved pre-step state is required: ' + str(run))
    with path.open(encoding='utf-8') as handle:
        rows = [json.loads(line) for line in handle]
    result = {}
    for row in rows:
        step = row.get('step') or row.get('result') or {}
        if row.get('date') == day_date and isinstance(step, dict) and step.get('t'):
            result[step['t']] = row
    return result, path


def prefix_day(day, when, before):
    """No future step, sitting, cash snapshot or final owl leaks into a writer."""
    result = copy.deepcopy(day)
    result.pop('records', None); result['owl'] = None; result['complete'] = False
    result['state'] = copy.deepcopy(before)
    result['entries'] = [e for e in result['entries'] if e.get('t', '24:00') < when]
    result['steps'] = [s for s in result['steps'] if s.get('t', '24:00') < when]
    result['segments'] = [s for s in result['segments'] if s.get('to', '24:00') <= when]
    result['observations'] = [e for e in result.get('observations', []) if e.get('t', '24:00') < when]
    if (result.get('plan') or {}).get('written', '24:00') > when: result['plan'] = None
    return result


class TrialMind(HTTPMind):
    """One deterministic stream per frozen job. Retain every engine retry."""
    def __init__(self, url, seed, slot, directory, capture=False):
        super().__init__(url, timeout=600, writing_reasoning_tokens=384)
        self.seed, self.slot, self.directory, self.capture = seed, slot, directory, capture
        self.calls = []; self.count_cache = {}

    def prompt_tokens(self, value, thinking=False):
        key = json.dumps([value, thinking], ensure_ascii=False, sort_keys=True)
        if key not in self.count_cache:
            self.count_cache[key] = super().prompt_tokens(value, thinking)
        return self.count_cache[key]

    def chat(self, messages, schema=None, max_tokens=700, temperature=None, *, adapter_scale=None, reasoning_budget=0):
        assert adapter_scale is None, 'No adapter selection in this experiment'
        count = self.prompt_tokens(messages, thinking=bool(reasoning_budget))
        if count > CEILING: raise ValueError(f'Whole prompt {count} exceeds frozen ceiling {CEILING}')
        payload = dict(model='qwen', messages=messages, max_tokens=max_tokens,
            temperature=self.temperature if temperature is None else temperature,
            chat_template_kwargs=dict(enable_thinking=bool(reasoning_budget)),
            seed=(self.seed + len(self.calls) * 10007) % (2**31 - 1),
            id_slot=self.slot, lora=[], cache_prompt=False)
        if reasoning_budget: payload['reasoning_budget_tokens'] = reasoning_budget
        if schema: payload['response_format'] = dict(type='json_schema', json_schema=dict(name='answer', schema=schema))
        if self.capture:
            self.calls.append(dict(request=copy.deepcopy(payload), measured_prompt_tokens=count))
            if 'diary' in (schema or {}).get('properties', {}):
                return json.dumps(dict(diary='Capture only. ' * 15, revision_log='', theses=[], depesche='Capture only.'))
            return json.dumps(dict(title='Capture', kind='notes', to=None, continues=False, text='Capture only; no real generation.'))
        started = time.monotonic()
        row = dict(request=payload, measured_prompt_tokens=count, started=stamp())
        try:
            answer = api(self.url, '/v1/chat/completions', payload); row['response'] = answer
            actual = answer.get('usage', {}).get('prompt_tokens')
            row['actual_prompt_tokens'] = actual
            if not isinstance(actual, int) or actual > CEILING:
                raise ValueError(f'Unexpected actual prompt count: measured {count}, usage {actual}')
            if actual != count:
                raise ValueError(f'Tokenizer/template mismatch: preflight {count}, usage {actual}')
            if api(self.url, '/lora-adapters') != []: raise ValueError('Unexpected server adapter')
            choice = answer['choices'][0]; row['finish_reason'] = choice['finish_reason']
            return (choice['message'].get('content') or '').strip()
        except BaseException as exc:
            row['error'] = repr(exc); raise
        finally:
            row['wall_seconds'] = time.monotonic() - started; self.calls.append(row)
            dump(self.directory / f'call-{len(self.calls):02}.json', row)


def run_writing(engine, job, source):
    day = source['day']; when = job['time']; row = source['traces'][when]
    before = row['before']; partial = prefix_day(day, when, before)
    req = source['writing_calls'][when]
    original = req['messages']
    # Freeze the original situation and accepted decision, but give both arms
    # the same current persona, manuscript memory and writing implementation.
    messages = [dict(role='system', content=engine.soul), copy.deepcopy(original[1])]
    raw = original[2]['content']
    accepted = contract.extract_json(raw)
    if not isinstance(accepted, dict) or accepted.get('action') != 'write':
        raise ValueError('Captured assistant was not the accepted writing decision')
    step = next(s for s in day['steps'] if s['t'] == when)
    sit = row.get('situation') or dict(time=when, place=before['place'], weather=str(day['weather']),
                                     aqi='unknown', present=step.get('present', []))
    ctx = dict(t=at_dt(date.fromisoformat(day['date']), int(when[:2])*60 + int(when[3:])),
        known_text='\n'.join([engine.memory.known_before(day['date']), encountered_text(partial), original[1]['content']]),
        manuscripts=engine.memory.manuscripts(partial, before_time=when))
    evidence = records.current(partial, sit, dict(public=[], observations=step.get('observations', [])))
    if engine.cfg.outcome_memory: ctx['records'] = evidence
    output = engine.write_chat(messages, raw, ctx, copy.deepcopy(before))
    return output, evidence


def load_sources(spec):
    result = {}
    for item in spec:
        run = Path(item['run']); day = json.loads((run / 'docs/days' / (item['date'] + '.json')).read_text())
        if not day.get('complete'): raise ValueError('Saved day must be complete: ' + str(run))
        calls, call_files = read_calls(run); traces, trace_file = trace_rows(run, item['date'])
        writers = writing_calls(calls)
        times = [s['t'] for s in day['steps'] if (s.get('decision') or {}).get('action') == 'write']
        if any(t not in writers or t not in traces for t in times):
            raise ValueError('Missing first writing request or pre-step state for ' + str(run) + ': ' + str(times))
        result[item['id']] = dict(spec=item, run=run, day=day, writing_calls=writers,
                                  traces=traces, files=call_files + [trace_file, run / 'docs/days' / (item['date']+'.json')], times=times)
    return result


def paired_jobs(sources):
    """Shuffle situations, then run each seeded A/B pair adjacently."""
    pairs = [dict(day=ident, kind=kind, time=when, seed=seed)
             for ident, source in sources.items() for seed in SEEDS
             for kind, when in [('owl', '24:00')] + [('writing', t) for t in source['times']]]
    rng = random.Random(2026101209)
    rng.shuffle(pairs)
    jobs = []
    for pair in pairs:
        variants = ['A', 'B']; rng.shuffle(variants)
        for variant in variants:
            jobs.append(dict(pair, variant=variant,
                id=f'{pair["day"]}-{pair["kind"]}-{pair["time"].replace(":", "")}-{pair["seed"]}-{variant}'))
    return jobs


def prepare(args):
    if args.task == 'T4b':
        return prepare_whole_shelf(args)
    if args.out.exists(): raise ValueError('Create-once output directory already exists')
    sources_spec = json.loads(args.sources.read_text()); sources = load_sources(sources_spec)
    if len(sources) != 6: raise ValueError('Exactly six saved days are required')
    args.out.mkdir(parents=True)
    jobs = paired_jobs(sources)
    dump(args.out / 'sources.json', sources_spec); dump(args.out / 'T3-jobs.json', jobs)
    cases = json.loads(args.cases.read_text()); cases = cases.get('writing_cases', cases) if isinstance(cases, dict) else cases
    karl = next(c for c in cases if c['id'] == 'karl'); dump(args.out / 'karl.json', karl)
    for rel, filename in [('mind/shelf/index.json.gz', 'old-shelf.json.gz'), ('world/data/shelf_terms.json', 'old-terms.json')]:
        raw = subprocess.check_output(['git', 'show', 'c03a431:' + rel], cwd=ROOT)
        (args.out / filename).write_bytes(raw)
    (args.out / 'new-shelf.json.gz').write_bytes((ROOT / 'mind/shelf/index.json.gz').read_bytes())
    (args.out / 'new-terms.json').write_bytes((ROOT / 'world/data/shelf_terms.json').read_bytes())
    shelf_jobs = [dict(id=f'karl-{s}-{v}', seed=s, variant=v) for s in range(2026101220,2026101230) for v in ('OLD','NEW')]
    random.Random(2026101210).shuffle(shelf_jobs); dump(args.out / 'T4-jobs.json', shelf_jobs)
    preflight = []
    for ident, source in sources.items():
        for variant in ('A', 'B'):
            cfg=config(args.out,variant);cfg.docs=source['run']/'docs'
            mind=TrialMind(args.url,1,1,args.out,capture=True);engine=Engine(cfg,World(),mind)
            for when in source['times']:
                run_writing(engine,dict(time=when),source)
                preflight.append(dict(day=ident,variant=variant,kind='writing',time=when,
                    tokens=mind.calls[-1]['measured_prompt_tokens']))
            d=copy.deepcopy(source['day']);state=copy.deepcopy(d['state'])
            owl.write(cfg,d,state,mind,depesche_n=1)
            preflight.append(dict(day=ident,variant=variant,kind='owl',tokens=mind.calls[-1]['measured_prompt_tokens']))
    dump(args.out/'preflight.json',preflight)
    files = list(ROOT.glob('world/*.py')) + list(ROOT.glob('world/data/*.json')) + [Path(__file__), ROOT/'mind/soul-v2.md', ROOT/'mind/owl.md']
    files += [p for source in sources.values() for p in source['files']]
    files += [p for p in args.out.iterdir() if p.is_file()] + [args.sources, args.cases]
    dump(args.out / 'protocol.json', dict(at=stamp(), sources=sources_spec, seeds=SEEDS, T3_jobs=len(jobs), T4_jobs=20,
        main=subprocess.check_output(['git','rev-parse','origin/main'],cwd=ROOT,text=True).strip(),
        candidate=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        ceiling=CEILING, outcome_checker=False, rollout=False, training=False,
        ordering='T3: seeded-random pair order, adjacent A/B with seeded-random order within every pair; T4: frozen shuffled schedule. Sequential task workers, slots 1 and 2; slot 0 reserved for world.',
        comparison='Same fixed situation/accepted decision and current persona in A and B. A uses legacy owl/input; B uses compact typed evidence. No new decisions or feedback between sittings.',
        limits=['Known development histories, not fresh independent worlds.', 'Old baselines have less granular observed-event records; ambiguous claims must be flagged, not silently called false.',
                'A and B see the same original situation/decision; earlier fictional claims may remain there and in manuscript memory, explicitly labelled interpretation.',
                'Shared GPU concurrency is logged; compare summed per-job wall times, with cached prompts disabled in both variants.'],
        pass_rule='B: fewer statement promotions per 100 sentences, no more contradictions per 100 sentences, owl argument (diary/revision log, v2 rubric) not lower, wall time <= 1.2*A. Report failed/empty outputs separately; no default enablement before blind scoring.',
        protected_sha256={str(p.resolve()):sha(p) for p in sorted(set(files))}))
    print(json.dumps(dict(prepared=True, T3_jobs=len(jobs), T4_jobs=20, sources=sources_spec)), flush=True)


def verify(out):
    protocol = json.loads((out / 'protocol.json').read_text())
    for path, expected in protocol['protected_sha256'].items():
        if sha(path) != expected: raise ValueError('Frozen input changed: ' + path)
    return protocol


def shelf_writing(engine, job, out, *, events_only=False, version=None):
    case = json.loads((out / 'karl.json').read_text()); d = date.fromisoformat(case['date'])
    st = copy.deepcopy(engine.days.load(date(2026,10,2))['state'])
    st.update(place=case['place'], until=case['date']+'T'+case['time'], works=[], theses=[])
    events = '\n'.join(x['text'] for x in case['events'])
    event = events
    event += '\nUnknown: ' + '; '.join(case['unknowns']) + '.'
    event += '\nThis sitting is a private, unsent letter to Karl, 120–200 words, below 2800 characters. Do not invent a recent event or identify the unknown people.'
    sit = dict(id=case['date']+'T'+case['time'], day=d.strftime('%A %-d %B'), time=case['time'],
        place=case['place'], weather='unknown', aqi='unknown', imprest_left=st['imprest'], cash_label='Cash',
        outfit=st['wearing'], present=[], open_now=['home'], closes={}, speakers=[], for_sale=[], on_mind=[], earlier=[], event=event)
    ctx = dict(t=at_dt(d,int(case['time'][:2])*60+int(case['time'][3:])), present=[], recent=[], known_text=event)
    version = version or job['variant'].lower()
    engine.shelf = shelf.load(out / (version + '-shelf.json.gz'), out / (version + '-terms.json'))
    if events_only: sit['event'] = events
    offered = engine.offer(dict(steps=[]), sit, ctx, st); sit['shelf'] = offered
    sit['event'] = event
    ctx['known_text'] += '\n' + '\n'.join(x['text'] for x in offered)
    raw = json.dumps(dict(thought='I shall write privately to Karl about the boy and the correction I saw, whose correctness I could not judge.',
        action='write', place='home', minutes=45, says=None, buys=[], revision=None))
    messages = [dict(role='system',content=engine.soul),dict(role='user',content=contract.render(sit))]
    result = engine.write_chat(messages,raw,ctx,st)
    return result, dict(case=case, shelf=offered)


def whole_shelf_jobs():
    rng = random.Random(2026101211)
    seeds = list(range(2026101220, 2026101230)); rng.shuffle(seeds)
    jobs = []
    for seed in seeds:
        variants = ['A', 'B']; rng.shuffle(variants)
        jobs.extend(dict(id=f'karl-{seed}-{variant}', seed=seed, variant=variant) for variant in variants)
    return jobs


def prepare_whole_shelf(args):
    """Freeze the paired whole-passage experiment without touching T3's checkout."""
    if args.out.exists(): raise ValueError('Create-once output directory already exists')
    args.out.mkdir(parents=True)
    cases = json.loads(args.cases.read_text())
    cases = cases.get('writing_cases', cases) if isinstance(cases, dict) else cases
    dump(args.out/'karl.json', next(c for c in cases if c['id']=='karl'))
    for rel, name in [('mind/shelf/index.json.gz','new-shelf.json.gz'), ('world/data/shelf_terms.json','new-terms.json')]:
        (args.out/name).write_bytes((ROOT/rel).read_bytes())
    jobs = whole_shelf_jobs(); dump(args.out/'T4b-jobs.json', jobs)
    preflight = []; offered_ids = []
    for variant in ['A','B']:
        cfg = config(args.out, 'A'); cfg.shelf_whole = variant=='B'
        mind = TrialMind(args.url, 1, 2, args.out, capture=True)
        engine = Engine(cfg, World(), mind)
        _, evidence = shelf_writing(engine, dict(variant=variant), args.out, events_only=True, version='new')
        shown = '\n'.join(p['text'] for p in evidence['shelf'])
        if variant=='B' and 'Gehorsams gegen die Lehrer' not in shown:
            raise ValueError('Whole-passage prompt does not contain the required obedience sentence')
        offered_ids.append([p['id'] for p in evidence['shelf']])
        preflight.append(dict(variant=variant,tokens=mind.calls[-1]['measured_prompt_tokens'],
                              required_sentence_shown='Gehorsams gegen die Lehrer' in shown))
    if offered_ids[0] != offered_ids[1]: raise ValueError('Passage selection differs between paired conditions')
    dump(args.out/'preflight.json', preflight)
    files = list(ROOT.glob('world/*.py')) + list(ROOT.glob('world/data/*.json'))
    files += [Path(__file__), ROOT/'mind/soul-v2.md', ROOT/'mind/owl.md', ROOT/'docs/days/2026-10-02.json', args.cases]
    files += [p for p in args.out.iterdir() if p.is_file()]
    dump(args.out/'protocol.json', dict(task='T4b',at=stamp(),jobs=len(jobs),
        main=subprocess.check_output(['git','rev-parse','origin/main'],cwd=ROOT,text=True).strip(),
        candidate=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        ceiling=CEILING,training=False,rollout=False,outcome_checker=False,
        ordering='Adjacent A/B pairs; fixed shuffled seed order and randomized within-pair order.',
        comparison='A: NEW shelf excerpts; B: identical NEW shelf passages whole. Query only observed events. Unknowns and writing instructions stay in both writer prompts.',
        pass_rule='B commitments >= A+0.5 and B argument >= A, scored blind with v2 guide.',
        protected_sha256={str(p.resolve()):sha(p) for p in sorted(set(files))}))
    print(json.dumps(dict(task='T4b',jobs=len(jobs),preflight=preflight)),flush=True)


def run(args):
    protocol = verify(args.out)
    if api(args.url, '/health').get('status') != 'ok' or api(args.url, '/lora-adapters') != []:
        raise ValueError('A healthy adapter-free shared server is required')
    props=api(args.url,'/props')
    if props['total_slots'] < 3: raise ValueError('Three shared slots are required')
    output=args.out/args.task
    if output.exists(): raise ValueError('Create-once run output already exists')
    output.mkdir(); started=time.monotonic(); failure=None; results=[]
    jobs=json.loads((args.out/(args.task+'-jobs.json')).read_text())
    sources=load_sources(protocol['sources']) if args.task=='T3' else {}
    try:
        for i,job in enumerate(jobs,1):
            verify(args.out); directory=output/job['id']; directory.mkdir(); began=time.monotonic()
            mind=TrialMind(args.url,job['seed'],1 if args.task=='T3' else 2,directory)
            cfg=config(args.out,job['variant'] if args.task=='T3' else 'A',shelf_on=False)
            if args.task=='T4b': cfg.shelf_whole=job['variant']=='B'
            if args.task=='T3': cfg.docs=sources[job['day']]['run']/'docs'
            engine=Engine(cfg,World(),mind,git=None)
            assert engine.claim_guard is None
            print('START',args.task,i,len(jobs),job['id'],flush=True)
            if args.task=='T4b':
                result,evidence=shelf_writing(engine,job,args.out,events_only=True,version='new')
                if job['variant']=='B' and not any('Gehorsams gegen die Lehrer' in p['text'] for p in evidence['shelf']):
                    raise ValueError('Required whole-passage sentence absent from the actual prompt')
            elif args.task=='T4':
                result,evidence=shelf_writing(engine,job,args.out)
            elif job['kind']=='owl':
                day=copy.deepcopy(sources[job['day']]['day']); state=copy.deepcopy(day['state'])
                depesche_n=(day.get('owl') or {}).get('depesche',{}).get('n',1)
                result=owl.write(cfg,day,state,mind,depesche_n=depesche_n)
                evidence=records.project(day)
            else:
                result,evidence=run_writing(engine,job,sources[job['day']])
            row=dict(job=job,result=result,evidence=evidence,wall_seconds=time.monotonic()-began,
                calls=len(mind.calls),prompt_tokens=[c['actual_prompt_tokens'] for c in mind.calls],
                finish_reasons=[c.get('finish_reason') for c in mind.calls])
            dump(directory/'result.json',row); results.append(row)
            dump(output/'status.json',dict(at=stamp(),done=i,total=len(jobs),last=job['id'],wall_seconds=time.monotonic()-started))
            print('DONE',args.task,i,len(jobs),'calls',len(mind.calls),flush=True)
        verify(args.out)
        dump(output/'complete.json',dict(at=stamp(),jobs=len(results),wall_seconds=time.monotonic()-started,
            variant_wall_seconds={v:sum(r['wall_seconds'] for r in results if r['job']['variant']==v) for v in sorted({r['job']['variant'] for r in results})},
            job_wall_seconds=[dict(r['job'], wall_seconds=r['wall_seconds'], calls=r['calls']) for r in results],
            frozen_inputs_verified=True,shared_server_left_running=True,blind_review_pending=True))
    except BaseException as exc:
        failure=dict(at=stamp(),error=repr(exc),traceback=traceback.format_exc()); dump(output/'failure.json',failure)
        traceback.print_exc()
    finally:
        intact=True
        try: verify(args.out)
        except Exception as exc: intact=False;dump(output/'integrity-failure.json',dict(error=repr(exc)))
        dump(output/'cleanup.json',dict(frozen_inputs_unchanged=intact,shared_server_untouched=True,
            original_days_unchanged=intact,training=False,rollout=False))
        (output/'run.exit').write_text('0\n' if not failure and intact else '1\n')
    return int(bool(failure) or not intact)


def packet(args):
    verify(args.out); output=args.out/args.task
    if (output/'run.exit').read_text().strip() != '0': raise ValueError('Cannot package an incomplete run')
    target=ROOT/'mind/results'/args.review
    key_path=args.private_key.resolve()
    if key_path.is_relative_to(ROOT) or key_path.is_relative_to(target): raise ValueError('Key must stay outside Git and rater packet')
    if key_path.exists() or target.exists(): raise ValueError('Create-once packet/key already exists')
    target.mkdir(parents=True); texts=[]; key={}
    from world.claim_check import sentence_spans
    for path in sorted(output.glob('*/result.json')):
        row=json.loads(path.read_text()); result=row['result']
        fields=('diary','revision_log','depesche') if row['job'].get('kind')=='owl' else ('text',)
        for field in fields:
            raw=(result or {}).get(field)
            text=raw.get('text','') if isinstance(raw,dict) else raw or ''
            ident=secrets.token_hex(6).upper()
            spans=list(sentence_spans(text))
            evidence=row['evidence']
            if args.task=='T3':
                proof=dict(evidence,records=[{k:v for k,v in r.items() if not (r['kind']=='work' and k=='text')} for r in evidence['records']])
            else:
                proof=dict(case=evidence['case'])  # shelf condition is private until scoring
            texts.append(dict(id=ident,kind=field, text=text, records=proof,
                              sentences=[dict(n=i+1,text=text[a:b]) for i,(a,b) in enumerate(spans)]))
            key[ident]=dict(row['job'],field=field,text_sha256=hashlib.sha256(text.encode()).hexdigest(),
                sentences=len(spans),empty=not bool(text.strip()),source=str(path))
    random.SystemRandom().shuffle(texts)
    guide=GUIDE if args.task in ('T4','T4b') else '''# Fixed-day factual audit

Read only these texts and their supplied typed records. Do not search. Do not infer a variant or consult a key.
Count contradictions with the records separately from unverified statements asserted as fact. A claim clearly
attributed to its speaker is not a promotion. Plans are intentions; drafts are not sent letters. Earlier source
prose and a plausible quotation prove no event. Missing evidence is not a contradiction: flag uncertain cases.
For each numbered sentence with a problem, record one row: id,sentence,contradiction,promotion,uncertain,record_ids,reason.
Use 0/1 flags; a sentence can receive both kinds of error. Count each kind at most once per sentence.
Return a second CSV with one row per text: id,sentences,contradictions,promotions,uncertain.
Return a third CSV for every diary and revision log: id,argument,reason. Score argument from 1 to 5:
does the text develop a claim from the difficulty within a position, to what it presupposes and where it
turns into its opposite, or does it assert, list, or lay a triad over the material? Give a one-line reason.
For an empty revision log use 1 and the reason "empty; no argument"; absence must not raise the mean.
Judge the supplied prose, not the position or eloquence of a quoted speaker in its records.
Use the supplied sentence count, including all zero-error texts. Score every text and commit both CSVs and
the argument CSV and their SHA256 hashes before requesting the key. Empty or unusable outputs remain in the packet and are reported.
'''
    (target/'guide.md').write_text(guide,encoding='utf-8'); dump(target/'texts.json',texts)
    rendered=[]
    for row in texts:
        rendered.append('## '+row['id']+'\n\n'+row['text']+'\n\n### Records for this text\n\n```json\n'+json.dumps(row['records'],ensure_ascii=False)+'\n```\n')
    (target/'packet.md').write_text('\n'.join(rendered),encoding='utf-8')
    key_path.parent.mkdir(parents=True,exist_ok=True);dump(key_path,dict(task=args.task,keys=key))
    dump(target/'manifest.json',dict(task=args.task,texts=len(texts),sentences=sum(len(r['sentences']) for r in texts),
        files={p.name:sha(p) for p in target.iterdir() if p.is_file()},key_not_in_packet=True,scores_before_key=True))
    print(json.dumps(dict(packet=str(target),texts=len(texts),private_key=str(key_path))),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('action',choices=['prepare','run','packet'])
    p.add_argument('--out',type=Path,required=True); p.add_argument('--sources',type=Path);p.add_argument('--cases',type=Path)
    p.add_argument('--url',default='http://127.0.0.1:8082');p.add_argument('--task',choices=['T3','T4','T4b'])
    p.add_argument('--review');p.add_argument('--private-key',type=Path)
    a=p.parse_args()
    if a.action=='prepare':prepare(a)
    elif a.action=='run':sys.exit(run(a))
    else:packet(a)
