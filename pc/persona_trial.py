#!/usr/bin/env python3
"""T4c: one frozen education-persona paragraph, with a non-education control."""
import argparse
import copy
from datetime import date
import json
from pathlib import Path
import random
import subprocess
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from pc import writer_trial as trial
from world import contract, shelf
from world.engine import Engine
from world.world import World, at_dt

SOULS = {'A': 'mind/soul.md', 'B': 'mind/soul-bildung.md'}
CASES = {'karl': 10, 'fare': 5}


def paired_jobs():
    pairs = [(case, seed) for case, count in CASES.items()
             for seed in range(2026101220, 2026101220 + count)]
    rng = random.Random(2026101217)
    rng.shuffle(pairs)
    jobs = []
    for case, seed in pairs:
        variants = ['A', 'B']; rng.shuffle(variants)
        jobs.extend(dict(id=f'{case}-{seed}-{v}', case=case, seed=seed, variant=v)
                    for v in variants)
    return jobs


def configuration(out, variant):
    cfg = trial.config(out, 'A', shelf_on=False, soul_file=SOULS[variant])
    cfg.shelf_whole = False
    assert not cfg.outcome_memory and not cfg.claim_check and not cfg.push
    return cfg


def write_case(engine, job, out):
    case = json.loads((out / 'cases.json').read_text())[job['case']]
    d = date.fromisoformat(case['date'])
    st = copy.deepcopy(engine.days.load(date(2026, 10, 2))['state'])
    st.update(place=case['place'], until=case['date']+'T'+case['time'], works=[], theses=[])
    if 'cash_inr' in case: st['imprest'] = case['cash_inr']
    events = '\n'.join(x['text'] for x in case['events'])
    event = events + '\nUnknown: ' + '; '.join(case['unknowns']) + '.'
    event += (f"\nThis sitting is a private, unsent letter to {case['to']}, "
              '120–200 words, below 2800 characters. Do not invent a recent event or identify the unknown people.')
    sit = dict(id=case['date']+'T'+case['time'], day=d.strftime('%A %-d %B'),
        time=case['time'], place=case['place'], weather='unknown', aqi='unknown',
        imprest_left=st['imprest'], cash_label='Cash', outfit=st['wearing'],
        present=case.get('present', []), open_now=[case['place']], closes={},
        speakers=[], for_sale=[], on_mind=[], earlier=[], event=events)
    ctx = dict(t=at_dt(d, int(case['time'][:2])*60+int(case['time'][3:])),
               present=case.get('present', []), recent=[], known_text=event)
    engine.shelf = shelf.load(out/'shelf.json.gz', out/'shelf-terms.json')
    offered = engine.offer(dict(steps=[]), sit, ctx, st)
    sit['shelf'] = offered; sit['event'] = event
    ctx['known_text'] += '\n' + '\n'.join(x['text'] for x in offered)
    raw = json.dumps(dict(thought=f"I shall write privately to {case['to']} about the events recorded here.",
        action='write', place=case['place'], minutes=45, says=None, buys=[], revision=None))
    messages = [dict(role='system', content=engine.soul),
                dict(role='user', content=contract.render(sit))]
    return engine.write_chat(messages, raw, ctx, st), dict(case=case, shelf=offered)


def require_t3_finished(base, packet):
    """No new GPU generation until T3 is complete and packaged under its freeze."""
    for p in [base/'T3-v3-job.exit', base/'writer-trial-v3/T3/run.exit']:
        if not p.exists() or p.read_text().strip() != '0':
            raise ValueError('T3 must finish successfully before T4c generation: '+str(p))
    complete = json.loads((base/'writer-trial-v3/T3/complete.json').read_text())
    cleanup = json.loads((base/'writer-trial-v3/T3/cleanup.json').read_text())
    if complete['jobs'] != 138 or not complete['frozen_inputs_verified']:
        raise ValueError('T3 completion or source verification is missing')
    if not all(cleanup[k] for k in ('frozen_inputs_unchanged', 'shared_server_untouched', 'original_days_unchanged')):
        raise ValueError('T3 cleanup verification failed')
    manifest = packet/'manifest.json'
    if not manifest.exists(): raise ValueError('Package T3 before starting T4c')
    sealed = json.loads(manifest.read_text())
    if sealed['task'] != 'T3' or sealed['texts'] != 210:
        raise ValueError('Unexpected T3 packet manifest')


def prepare(args):
    if args.out.exists(): raise ValueError('Create-once output already exists')
    cases = json.loads(args.cases.read_text())['writing_cases']
    selected = {c['id']: c for c in cases if c['id'] in CASES}
    if set(selected) != set(CASES): raise ValueError('Both frozen v2 cases are required')
    if any(c['kind'] != 'letter' for c in selected.values()): raise ValueError('Both cases must be letters')
    args.out.mkdir(parents=True)
    trial.dump(args.out/'cases.json', selected)
    trial.dump(args.out/'T4c-jobs.json', paired_jobs())
    for rel, name in [('mind/shelf/index.json.gz', 'shelf.json.gz'),
                      ('world/data/shelf_terms.json', 'shelf-terms.json')]:
        (args.out/name).write_bytes((ROOT/rel).read_bytes())
    old = (ROOT/SOULS['A']).read_text(); new = (ROOT/SOULS['B']).read_text()
    paragraph = next(line for line in new.splitlines() if line.startswith('- On education '))
    if new.replace(paragraph+'\n', '', 1) != old:
        raise ValueError('Persona variant must differ by the single education paragraph only')
    preflight = []; offers = {}
    for case in CASES:
        for variant in SOULS:
            mind = trial.TrialMind(args.url, 1, 2, args.out, capture=True)
            engine = Engine(configuration(args.out, variant), World(), mind)
            _, evidence = write_case(engine, dict(case=case, variant=variant), args.out)
            prompt = '\n'.join(m['content'] for m in mind.calls[-1]['request']['messages'])
            shown = paragraph in prompt
            if shown != (variant == 'B'): raise ValueError('Wrong persona reached the actual writer prompt')
            count = mind.calls[-1]['measured_prompt_tokens']
            if count > trial.CEILING: raise ValueError('Whole prompt exceeds the frozen ceiling')
            offers[case, variant] = evidence['shelf']
            preflight.append(dict(case=case, variant=variant, tokens=count, education_paragraph_shown=shown))
        if offers[case, 'A'] != offers[case, 'B']:
            raise ValueError('Paired shelf offers differ with the persona')
    trial.dump(args.out/'preflight.json', preflight)
    files = list(ROOT.glob('world/*.py')) + list(ROOT.glob('world/data/*.json'))
    files += [Path(__file__), ROOT/'pc/writer_trial.py', ROOT/'pc/blind_review.py',
              ROOT/'docs/days/2026-10-02.json', args.cases] + [ROOT/p for p in SOULS.values()]
    files += [p for p in args.out.iterdir() if p.is_file()]
    trial.dump(args.out/'protocol.json', dict(task='T4c', at=trial.stamp(), jobs=30,
        candidate=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        ceiling=trial.CEILING, training=False, rollout=False, claim_check=False,
        cases=dict(karl=10, fare=5), seeds='2026101220–29 Karl; 2026101220–24 fare',
        comparison='Only the persona differs: soul.md versus soul-bildung.md. Excerpts and event-only query in both.',
        control_selection='The existing v2 fare letter concerns reimbursement, not teaching, children or family; same genre as Karl.',
        pass_rule='Karl: B commitments >= A+0.5 and argument >= A. Fare: neither commitments nor argument lower.',
        generation_held_until='T3 complete, integrity verified and 210-text blind packet produced.',
        protected_sha256={str(p.resolve()):trial.sha(p) for p in sorted(set(files))}))
    print(json.dumps(dict(task='T4c',jobs=30,preflight=preflight,generation_started=False)),flush=True)


def run(args):
    require_t3_finished(args.t3_root, args.t3_packet)
    trial.verify(args.out)
    if trial.api(args.url,'/health').get('status') != 'ok' or trial.api(args.url,'/lora-adapters') != []:
        raise ValueError('A healthy adapter-free shared server is required')
    if trial.api(args.url,'/props')['total_slots'] < 3: raise ValueError('Three shared slots required')
    output=args.out/'T4c'
    if output.exists(): raise ValueError('Create-once run already exists')
    output.mkdir(); started=time.monotonic(); failure=None; rows=[]
    jobs=json.loads((args.out/'T4c-jobs.json').read_text())
    try:
        for i,job in enumerate(jobs,1):
            trial.verify(args.out);directory=output/job['id'];directory.mkdir();began=time.monotonic()
            mind=trial.TrialMind(args.url,job['seed'],2,directory)
            engine=Engine(configuration(args.out,job['variant']),World(),mind,git=None)
            assert engine.claim_guard is None
            print('START T4c',i,len(jobs),job['id'],flush=True)
            result,evidence=write_case(engine,job,args.out)
            paragraph=next(line for line in (ROOT/SOULS['B']).read_text().splitlines() if line.startswith('- On education '))
            for call in mind.calls:
                prompt='\n'.join(m['content'] for m in call['request']['messages'])
                if (paragraph in prompt) != (job['variant']=='B'):
                    raise ValueError('Wrong persona in actual generation or retry')
            row=dict(job=job,result=result,evidence=evidence,wall_seconds=time.monotonic()-began,
                calls=len(mind.calls),prompt_tokens=[c['actual_prompt_tokens'] for c in mind.calls],
                finish_reasons=[c.get('finish_reason') for c in mind.calls])
            trial.dump(directory/'result.json',row);rows.append(row)
            trial.dump(output/'status.json',dict(at=trial.stamp(),done=i,total=len(jobs),last=job['id'],wall_seconds=time.monotonic()-started))
            print('DONE T4c',i,len(jobs),'calls',len(mind.calls),flush=True)
        trial.verify(args.out)
        trial.dump(output/'complete.json',dict(at=trial.stamp(),jobs=len(rows),wall_seconds=time.monotonic()-started,
            variant_wall_seconds={v:sum(r['wall_seconds'] for r in rows if r['job']['variant']==v) for v in SOULS},
            job_wall_seconds=[dict(r['job'],wall_seconds=r['wall_seconds'],calls=r['calls']) for r in rows],
            frozen_inputs_verified=True,shared_server_left_running=True,blind_review_pending=True))
    except BaseException as exc:
        failure=dict(at=trial.stamp(),error=repr(exc),traceback=traceback.format_exc())
        trial.dump(output/'failure.json',failure);traceback.print_exc()
    finally:
        intact=True
        try:trial.verify(args.out)
        except Exception as exc:intact=False;trial.dump(output/'integrity-failure.json',dict(error=repr(exc)))
        trial.dump(output/'cleanup.json',dict(frozen_inputs_unchanged=intact,shared_server_untouched=True,
            original_days_unchanged=intact,training=False,rollout=False))
        (output/'run.exit').write_text('0\n' if not failure and intact else '1\n')
    return int(bool(failure) or not intact)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=['prepare','run','packet']);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--cases',type=Path);p.add_argument('--url',default='http://127.0.0.1:8082')
    p.add_argument('--review');p.add_argument('--private-key',type=Path)
    p.add_argument('--t3-root',type=Path,default=Path('/mnt/c/hegel/handover/codex-tasks-20261012'))
    p.add_argument('--t3-packet',type=Path,default=Path('/home/ai/hegel-in-delhi/mind/results/fixed-day-writers-20261012'))
    a=p.parse_args();a.task='T4c'
    if a.action=='prepare':prepare(a)
    elif a.action=='run':sys.exit(run(a))
    else:trial.packet(a)
