#!/usr/bin/env python3
"""Frozen paired education-persona trials, with declared control gates."""
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


def experiment(task='T4c', control_case=None):
    if task == 'T4c':
        return dict(cases=CASES, starts={case: 2026101220 for case in CASES},
            ordering_seed=2026101217,
            control_selection='Existing v2 fare reimbursement letter, unrelated to education or family.',
            pass_rule='Karl: B commitments >= A+0.5 and argument >= A. Fare: neither commitments nor argument lower.')
    if task == 'T4e':
        if control_case is not None:
            raise ValueError('T4e cases are fixed by the fresh-control specification')
        return dict(cases={'arch': 8, 'directions': 8, 'bowls': 8},
            starts={'arch': 2026101290, 'directions': 2026101300, 'bowls': 2026101310},
            ordering_seed=2026101241,
            control_selection="Existing v2 arch, child's map (directions), and bowls, unchanged essays; no Karl, fare or columns.",
            pass_rule='Across the 24 fresh control texts per arm, B commitments >= A-0.25 and B argument >= A-0.25. Report each case separately. The new margin applies only to T4e; T4c/T4d remain failed.')
    if task != 'T4d':
        raise ValueError('Unknown persona trial: '+task)
    if not control_case or control_case in ('karl', 'fare'):
        raise ValueError('T4d requires a distinct second non-teaching control')
    return dict(cases={'karl': 6, 'fare': 10, control_case: 10},
        starts={'karl': 2026101260, 'fare': 2026101270, control_case: 2026101280},
        ordering_seed=2026101231,
        control_selection='Fare letter and the explicitly selected existing v2 non-teaching control: '+control_case,
        pass_rule='Karl: B commitments >= A+0.5 and argument >= A. Across the 20 control texts per arm: neither commitments nor argument lower. No pooled Karl/control gate.')


def paired_jobs(task='T4c', control_case=None):
    spec = experiment(task, control_case)
    pairs = [(case, seed) for case, count in spec['cases'].items()
             for seed in range(spec['starts'][case], spec['starts'][case] + count)]
    rng = random.Random(spec['ordering_seed'])
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


def present_ids(world, names):
    """Keep frozen display names in the prompt; use existing cast IDs in context."""
    ids = []
    for name in names:
        matches = [cid for cid, person in world.cast.items()
                   if name in (cid, person.get('name'), person.get('short'))]
        if len(matches) != 1:
            raise ValueError('Present name must identify exactly one existing cast member: '+name)
        ids.append(matches[0])
    return ids


def write_case(engine, job, out):
    case = json.loads((out / 'cases.json').read_text())[job['case']]
    d = date.fromisoformat(case['date'])
    st = copy.deepcopy(engine.days.load(date(2026, 10, 2))['state'])
    st.update(place=case['place'], until=case['date']+'T'+case['time'], works=[], theses=[])
    if 'cash_inr' in case: st['imprest'] = case['cash_inr']
    events = '\n'.join(x['text'] for x in case['events'])
    event = events + '\nUnknown: ' + '; '.join(case['unknowns']) + '.'
    if case['kind'] == 'letter':
        writing = f"a private, unsent letter to {case['to']}"
        thought = f"I shall write privately to {case['to']} about the events recorded here."
    elif case['kind'] == 'essay':
        writing = 'an essay on the events recorded here'
        thought = 'I shall write an essay about the events recorded here.'
    else:
        raise ValueError('Unsupported writing kind: '+case['kind'])
    event += (f"\nThis sitting is {writing}, "
              '120–200 words, below 2800 characters. Do not invent a recent event or identify the unknown people.')
    sit = dict(id=case['date']+'T'+case['time'], day=d.strftime('%A %-d %B'),
        time=case['time'], place=case['place'], weather='unknown', aqi='unknown',
        imprest_left=st['imprest'], cash_label='Cash', outfit=st['wearing'],
        present=case.get('present', []), open_now=[case['place']], closes={},
        speakers=[], for_sale=[], on_mind=[], earlier=[], event=events)
    present = case.get('present', [])
    if present:
        present = present_ids(engine.world, present)
    ctx = dict(t=at_dt(d, int(case['time'][:2])*60+int(case['time'][3:])),
               present=present, recent=[], known_text=event)
    engine.shelf = shelf.load(out/'shelf.json.gz', out/'shelf-terms.json')
    offered = engine.offer(dict(steps=[]), sit, ctx, st)
    sit['shelf'] = offered; sit['event'] = event
    ctx['known_text'] += '\n' + '\n'.join(x['text'] for x in offered)
    raw = json.dumps(dict(thought=thought,
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
    task = getattr(args, 'task', 'T4c')
    control_case = getattr(args, 'control_case', None)
    spec = experiment(task, control_case)
    cases = json.loads(args.cases.read_text())['writing_cases']
    selected = {c['id']: c for c in cases if c['id'] in spec['cases']}
    if set(selected) != set(spec['cases']): raise ValueError('Every declared frozen v2 case is required')
    if any(selected[name]['kind'] != 'letter' for name in ('karl', 'fare') if name in selected):
        raise ValueError('Karl and fare must remain letters')
    if task == 'T4e' and any(c['kind'] != 'essay' for c in selected.values()):
        raise ValueError('T4e fresh controls must remain the original essays')
    if any(c['kind'] not in ('letter', 'essay') for c in selected.values()):
        raise ValueError('Every case must be a letter or essay')
    args.out.mkdir(parents=True)
    trial.dump(args.out/'cases.json', selected)
    jobs = paired_jobs(task, control_case)
    trial.dump(args.out/(task+'-jobs.json'), jobs)
    for rel, name in [('mind/shelf/index.json.gz', 'shelf.json.gz'),
                      ('world/data/shelf_terms.json', 'shelf-terms.json')]:
        (args.out/name).write_bytes((ROOT/rel).read_bytes())
    old = (ROOT/SOULS['A']).read_text(); new = (ROOT/SOULS['B']).read_text()
    paragraph = next(line for line in new.splitlines() if line.startswith('- On education '))
    if new.replace(paragraph+'\n', '', 1) != old:
        raise ValueError('Persona variant must differ by the single education paragraph only')
    preflight = []; offers = {}
    for case in spec['cases']:
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
    if task == 'T4e':
        files.append(ROOT/'pc/PERSONA-FRESH-CONTROLS-TRIAL-20261012.md')
    files += [p for p in args.out.iterdir() if p.is_file()]
    trial.dump(args.out/'protocol.json', dict(task=task, at=trial.stamp(), jobs=len(jobs),
        candidate=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        ceiling=trial.CEILING, training=False, rollout=False, claim_check=False,
        cases=spec['cases'], second_control=control_case,
        seeds={case:list(range(spec['starts'][case], spec['starts'][case]+count))
               for case,count in spec['cases'].items()}, ordering_seed=spec['ordering_seed'],
        comparison='Only the persona differs: soul.md versus soul-bildung.md. Excerpts and event-only query in both.',
        control_selection=spec['control_selection'], pass_rule=spec['pass_rule'],
        generation_held_until='T3 complete, integrity verified and 210-text blind packet produced.',
        protected_sha256={str(p.resolve()):trial.sha(p) for p in sorted(set(files))}))
    print(json.dumps(dict(task=task,jobs=len(jobs),preflight=preflight,generation_started=False)),flush=True)


def run(args):
    require_t3_finished(args.t3_root, args.t3_packet)
    protocol = trial.verify(args.out)
    task = getattr(args, 'task', 'T4c')
    if protocol['task'] != task: raise ValueError('Requested task differs from the frozen protocol')
    jobs = json.loads((args.out/(task+'-jobs.json')).read_text())
    if jobs != paired_jobs(task, protocol.get('second_control')):
        raise ValueError('Schedule differs from the predeclared paired experiment')
    if trial.api(args.url,'/health').get('status') != 'ok' or trial.api(args.url,'/lora-adapters') != []:
        raise ValueError('A healthy adapter-free shared server is required')
    if trial.api(args.url,'/props')['total_slots'] < 3: raise ValueError('Three shared slots required')
    output=args.out/task
    if output.exists(): raise ValueError('Create-once run already exists')
    output.mkdir(); started=time.monotonic(); failure=None; rows=[]
    try:
        for i,job in enumerate(jobs,1):
            trial.verify(args.out);directory=output/job['id'];directory.mkdir();began=time.monotonic()
            mind=trial.TrialMind(args.url,job['seed'],2,directory)
            engine=Engine(configuration(args.out,job['variant']),World(),mind,git=None)
            assert engine.claim_guard is None
            print('START',task,i,len(jobs),job['id'],flush=True)
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
            print('DONE',task,i,len(jobs),'calls',len(mind.calls),flush=True)
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
    p.add_argument('--task',choices=['T4c','T4d','T4e'],default='T4c')
    p.add_argument('--control-case',help='Explicit second non-teaching v2 control for T4d')
    p.add_argument('--t3-root',type=Path,default=Path('/mnt/c/hegel/handover/codex-tasks-20261012'))
    p.add_argument('--t3-packet',type=Path,default=Path('/home/ai/hegel-in-delhi/mind/results/fixed-day-writers-20261012'))
    a=p.parse_args()
    if a.action=='prepare':prepare(a)
    elif a.action=='run':sys.exit(run(a))
    else:trial.packet(a)
