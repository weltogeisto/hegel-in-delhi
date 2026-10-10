#!/usr/bin/env python3
"""Prepare frozen, auditable v2 candidate requests; generate with local Qwen only.

This does NOT accept examples or train a model. Every generated answer must be
reviewed against its source before selection. Existing mind/train is read-only.
All assistant targets are either exact source text, existing human dataset rows,
or unedited local Qwen output. Prompt templates are code, not target prose.
"""
import argparse
import collections
import gzip
import hashlib
import json
import random
import re
import sys
import time
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools'))
from world import contract, works


def digest(value):
    raw = value if isinstance(value, bytes) else value.encode()
    return hashlib.sha256(raw).hexdigest()


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def rows(path):
    return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]


def jsonl(path, values):
    with path.open('x') as f:
        for value in values:
            f.write(json.dumps(value, ensure_ascii=False) + '\n')


def source_pool():
    import corpus
    from train_data import held_out
    # Reuse the corpus cleaner and old benchmark exclusion, without fetching.
    kept, removed = held_out(corpus.kept_works())
    meta = {w['id']: w for w in corpus.WORKS}
    pool = []
    for w in kept:
        if w['lang'] != 'en' or w['author'] != 'Hegel':
            continue
        m = meta[w['id']]
        for i, (ref, text) in enumerate(w['passages']):
            if not 100 <= len(text.split()) <= 230 or not re.search(r'[.!?][”\"]?$', text):
                continue
            pool.append(dict(work=w['id'], ref=ref, index=i, text=text, sha256=digest(text),
                             title=m['title'], translator=m['who'], edition=m['year'], language='en',
                             author='Hegel', source_file=f"mind/shelf/{w['id']}.txt.gz"))
    return pool, removed


def situation_pool():
    """Only current observed context from prior engine/Qwen rehearsals.

    Exclude all remembered thoughts, theses, plans and old retrieved excerpts.
    Exclude NPC prose here as its accuracy against the ledger needs a separate
    audit. No synthetic stand-in or hand-written benchmark scene is used.
    """
    out, seen = [], set()
    for row in rows(ROOT / 'mind/train/decisions.jsonl'):
        text = row['messages'][1]['content']
        if 'What happens: ' not in text:
            continue
        header = text.split('\n\n')[0]
        event = text.split('What happens: ', 1)[1].split('\n\n')[0].strip()
        if re.search(r'says:|remarks:|replies:|“|”|\(stub\)|\(rehearsal\)', event, re.I):
            continue
        place = re.search(r'You are at: ([a-z]+)\.', header).group(1)
        # Same observation at different dates/times is one family. Reserve all
        # variants of a held-out family, not just a randomly selected row.
        family = re.sub(r'\d+', '#', event.lower())
        key = (place, family)
        if key in seen:
            continue
        seen.add(key)
        out.append(dict(id=row['meta']['key'], date=row['meta']['day'], place=place,
                        event=event, family=digest(family), header=header,
                        provenance=dict(file='mind/train/decisions.jsonl', key=row['meta']['key'],
                                        original_row_sha256=digest(json.dumps(row, sort_keys=True, ensure_ascii=False)))))
    return out


BOUNDARY = ('The simulation date is {date}. The current observations below are the entire factual record for this exercise. '
            'Earlier visits, conversations and letters are unknown unless explicitly recorded. '
            'A plan is not an event; a written letter has not been sent. '
            'Do not invent facts to make the writing vivid.\n\n')


def scene_messages(soul, scene, kind, variant=0):
    user = BOUNDARY.format(date=scene['date']) + scene['header'] + '\n\nWhat happens: ' + scene['event']
    if kind == 'decision':
        user += '\n\n' + contract.ASK
        schema, budget = contract.SCHEMA, 650
    else:
        genres = [('essay', None), ('letter', 'Niethammer'), ('notes', None), ('letter', 'Marie')]
        genre, recipient = genres[variant % len(genres)]
        user += '\n\n' + works.ask({}, date.fromisoformat(scene['date']))
        user += (f' For this sitting choose kind {genre}' + (f', addressed to {recipient}' if recipient else '')
                 + '. Keep it between 160 and 240 words. Choose the subject from the observation supplied. '
                   'No person other than those listed is present; a letter may address someone absent. '
                   'Develop the particular subject; ordinary matters need not become a theory of the state.')
        schema, budget = contract.WRITE_SCHEMA, 1100
    return [dict(role='system', content=soul), dict(role='user', content=user)], schema, budget


def source_request(soul, source, variant=0):
    tasks = [
        'Develop one distinction that does work in this passage. Explain why it is needed and what goes wrong if its sides are conflated.',
        'State the strongest objection to the particular inference in this passage, then give the reply the passage supports. Leave unresolved what it does not settle.',
        'Follow one transition in the argument: give its starting claim, the difficulty it produces, and what changes in addressing that difficulty.',
    ]
    prompt = (f"Source: {source['title']}, {source['ref']} ({source['translator']}, {source['edition']}).\n"
              + source['text'] + '\n\n' + tasks[variant % len(tasks)]
              + ' Write 130–200 words as an argumentative note in your own voice. Stay with this passage; '
                'no new historical claims, invented quotations or claims about recent events. Return prose, not JSON.')
    return [dict(role='system', content=soul), dict(role='user', content=prompt)]


def prepare(a):
    if a.out.exists():
        raise SystemExit(f'Refusing to overwrite {a.out}')
    soul = a.soul.read_text()
    rng = random.Random(a.seed)
    sources, removed = source_pool()
    scenes = situation_pool()
    rng.shuffle(sources)
    rng.shuffle(scenes)
    reserved = {'dev': {'haldane-2'}, 'holdout': {'wallace-mind', 'haldane-1'}}
    reserved_places = {'dev': {'lodhi'}, 'holdout': {'iic', 'safdarjung', 'gandhi'}}
    evaluation, eval_scene_families = [], set()
    for split, ns, nw in [('dev', 4, 4), ('holdout', 8, 8)]:
        ss = [s for s in sources if s['work'] in reserved[split]][:ns]
        sc = [s for s in scenes if s['place'] in reserved_places[split]][:nw]
        if len(ss) != ns or len(sc) != nw:
            raise SystemExit(f'Insufficient {split} source families: {len(ss)}, {len(sc)}')
        for n, source in enumerate(ss):
            evaluation.append(dict(id=f'{split}-argument-{n:02}', split=split, kind='argument',
                                   family=source['work'], source=source, messages=source_request(soul, source, n),
                                   schema=None, max_tokens=650, seeds=[1831, 1832]))
        for n, scene in enumerate(sc):
            eval_scene_families.add(scene['family'])
            for kind in ['writing', 'decision']:
                messages, schema, budget = scene_messages(soul, scene, kind, n)
                evaluation.append(dict(id=f'{split}-{kind}-{n:02}', split=split, kind=kind, family=scene['family'],
                                       scene=scene, messages=messages, schema=schema, max_tokens=budget, seeds=[1831, 1832]))
    training_sources = [s for s in sources if s['work'] not in set.union(*reserved.values())]
    # Round-robin books prevents one large work dominating the frozen requests.
    grouped = collections.defaultdict(list)
    for s in training_sources:
        grouped[s['work']].append(s)
    balanced = []
    while any(grouped.values()):
        for w in sorted(grouped):
            if grouped[w]:
                balanced.append(grouped[w].pop())
    training_scenes = [s for s in scenes if s['place'] in {'home', 'khan', 'estates'}
                       and s['family'] not in eval_scene_families]
    if len(training_scenes) < 24 or len(balanced) < 144:
        raise SystemExit(f'Insufficient clean training pool: {len(training_scenes)} scenes, {len(balanced)} sources')
    requests, anchors = [], []
    for n, source in enumerate(balanced[:96]):
        # Explicit source continuation; split at a sentence boundary, not a word.
        boundaries = list(re.finditer(r'(?<=[.!?])\s+(?=[A-Z])', source['text']))
        if not boundaries:
            continue
        cut = min(boundaries, key=lambda m: abs(m.start() - len(source['text']) * .3)).end()
        prefix, target = source['text'][:cut], source['text'][cut:]
        if len(target.split()) < 50:
            continue
        messages = [dict(role='user', content=f"Continue this exact passage from {source['title']}, {source['ref']}. "
                         'Return only its continuation, without commentary.\n\n' + prefix), dict(role='assistant', content=target)]
        anchors.append(dict(id=f'primary-{n:03}', category='primary', source=source, messages=messages,
                            target_origin='verbatim cleaned primary source', target_sha256=digest(target), review='pending'))
    for n, source in enumerate(balanced[96:144]):
        requests.append(dict(id=f'argument-{n:03}', category='argument', family=source['work'], source=source,
                             messages=source_request(soul, source, n), schema=None, max_tokens=650, seed=a.seed + n))
    for n, scene in enumerate(training_scenes[:48]):
        for variant in range(2):
            for kind in ['writing', 'decision']:
                messages, schema, budget = scene_messages(soul, scene, kind, n + variant)
                requests.append(dict(id=f'{kind}-{n:03}-{variant}', category=kind, family=scene['family'], scene=scene,
                                     messages=messages, schema=schema, max_tokens=budget, seed=a.seed + 100 + n * 2 + variant))
    general = rows(ROOT / 'mind/train/general.jsonl')
    rng.shuffle(general)
    human = []
    for row in general:
        subset = row.get('meta', {}).get('subset', '').lower()
        if not any(s in subset for s in ('oasst1', 'aya')):
            continue
        target = row['messages'][-1]['content']
        if not 60 <= len(target.split()) <= 250:
            continue
        human.append(dict(id=f'general-{len(human):03}', category='general', messages=row['messages'],
                          source=row['meta'], target_origin='existing human-source dataset',
                          target_sha256=digest(target), review='pending'))
        if len(human) == 96:
            break
    a.out.mkdir(parents=True)
    (a.out / 'soul.txt').write_text(soul)
    jsonl(a.out / 'requests.jsonl', requests)
    jsonl(a.out / 'evaluation.jsonl', evaluation)
    jsonl(a.out / 'source-candidates.jsonl', anchors + human)
    original_files = [ROOT / 'mind/train' / f'{n}.jsonl' for n in ['corpus', 'decisions', 'writings', 'plans', 'voices', 'general']]
    code_files = [ROOT / x for x in ['world/memory.py', 'world/engine.py', 'world/contract.py', 'world/works.py',
                                    'world/config.py', 'tools/phase2_data.py', 'mind/soul-v2.md']]
    hashes = {str(p.relative_to(ROOT)): digest(p.read_bytes()) for p in original_files + code_files}
    manifest = dict(seed=a.seed, created=time.strftime('%Y-%m-%dT%H:%M:%S%z'), review='pending; no examples accepted',
                    source_candidates=len(anchors), human_candidates=len(human), qwen_requests=len(requests),
                    eval_counts=dict(collections.Counter(x['split'] for x in evaluation)), original_and_runtime_hashes=hashes,
                    reserved_works={k: sorted(v) for k, v in reserved.items()}, reserved_places={k: sorted(v) for k, v in reserved_places.items()},
                    benchmark_passages_excluded=removed, clean_training_scene_families=len(training_scenes),
                    limitations=['Holdout is new to v2 selection, not claimed unseen by the base or original training.',
                                 'Scene separation uses location and exact normalised event families; semantic neighbours require review.',
                                 'Source split is whole English works; no German source enters v2.',
                                 'Primary sources were mechanically cleaned by the existing corpus tool; each candidate still needs review.',
                                 'General subsets are described by their publishers as human-written; volunteer contamination remains possible.'],
                    gates=dict(pilot_rows=[200,400], epochs=1, max_minutes=90, lr=5e-5, rank=16, alpha=32,
                               target_token_mix=dict(primary_and_argument=.35,writing=.30,decision=.20,general=.15),
                               review='Every selected row must have an evidence-based review; generated outputs are never auto-accepted.',
                               final_evaluation='Blinded argument/voice improvement across topics, no grounding regression, no invalid executed action.'))
    dump(a.out / 'manifest.json', manifest)
    frozen = {p.name: digest(p.read_bytes()) for p in a.out.iterdir() if p.is_file()}
    dump(a.out / 'frozen-hashes.json', frozen)
    print(json.dumps({k: manifest[k] for k in ('qwen_requests','source_candidates','human_candidates','eval_counts','clean_training_scene_families')}, indent=2))


def api(url, route, data=None, timeout=180):
    req = urllib.request.Request(url.rstrip('/') + route, data=json.dumps(data).encode() if data is not None else None,
                                 headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.load(response)


def verify_frozen(out):
    expected = json.loads((out / 'frozen-hashes.json').read_text())
    for name, sha in expected.items():
        if digest((out / name).read_bytes()) != sha:
            raise SystemExit(f'Frozen input changed: {name}')
    manifest = json.loads((out / 'manifest.json').read_text())
    for name, sha in manifest['original_and_runtime_hashes'].items():
        if digest((ROOT / name).read_bytes()) != sha:
            raise SystemExit(f'Original data or frozen runtime changed: {name}')


def screen(item, response):
    reasons = []
    choice = response['choices'][0]
    text = choice['message'].get('content') or ''
    if choice.get('finish_reason') != 'stop':
        reasons.append('not completed: ' + str(choice.get('finish_reason')))
    if not text.strip():
        reasons.append('empty content')
    if item['category'] == 'writing' and works.clean(contract.extract_json(text)) is None:
        reasons.append('writing schema/length rejected')
    if item['category'] == 'decision':
        errors, _ = contract.check_shape(contract.extract_json(text))
        reasons += errors
    return reasons


def generate(a):
    verify_frozen(a.out)
    if api(a.url, '/health').get('status') != 'ok':
        raise SystemExit('Server not healthy')
    adapters = api(a.url, '/lora-adapters')
    if adapters != []:
        raise SystemExit(f'Candidate generation requires unadapted Qwen; adapters={adapters}')
    models = api(a.url, '/v1/models')
    dump(a.out / 'generator-server.json', dict(models=models, adapters=adapters, url=a.url,
                                             temperature=.65, thinking=False, status='candidate generation only'))
    requests = rows(a.out / 'requests.jsonl')
    path = a.out / 'qwen-candidates.jsonl'
    done = {x['id'] for x in rows(path)} if path.exists() else set()
    if not done <= {x['id'] for x in requests}:
        raise SystemExit('Unknown IDs in existing candidates')
    with path.open('a') as f:
        for n, item in enumerate(requests, 1):
            if item['id'] in done:
                continue
            payload = dict(messages=item['messages'], max_tokens=item['max_tokens'], temperature=.65,
                           seed=item['seed'], chat_template_kwargs={'enable_thinking': False}, stream=False)
            if item['schema'] is not None:
                payload['response_format'] = {'type':'json_object', 'schema':item['schema']}
            start = time.monotonic()
            response = api(a.url, '/v1/chat/completions', payload, timeout=300)
            text = response['choices'][0]['message'].get('content') or ''
            record = dict(id=item['id'], category=item['category'], request=item, response=response,
                          messages=item['messages']+[dict(role='assistant',content=text)],
                          target_origin='local unadapted Qwen3.8-27B', target_sha256=digest(text),
                          screening=screen(item,response), review='pending', elapsed_s=round(time.monotonic()-start,2))
            f.write(json.dumps(record,ensure_ascii=False)+'\n');f.flush()
            print(f"candidate {n}/{len(requests)} {item['id']} {record['elapsed_s']}s screening={record['screening']} REVIEW PENDING",flush=True)
    verify_frozen(a.out)
    dump(a.out / 'generation-complete.json', dict(candidates=len(requests), status='complete; review required before training'))
    print('done: candidates saved; none automatically accepted or trained',flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=['prepare','generate'])
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--soul',type=Path,default=ROOT/'mind/soul-v2.md')
    p.add_argument('--seed',type=int,default=183107)
    p.add_argument('--url',default='http://127.0.0.1:18082')
    a=p.parse_args()
    (prepare if a.command=='prepare' else generate)(a)


if __name__=='__main__':main()
