"""Preregister and seal T45 without generating or exposing confirmation outputs.

Legacy KPI 1's selector is unchanged. T45 uses only genuine archived mind thoughts
outside actual development cohorts, with balanced days and deterministic scene/person spread.
"""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import random
import re
import secrets
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.recorded_llama import json_bytes, write_new, freeze_plan
from tools import hegel_test_round2 as bench

RULE = {
    'format': 't45-rule-v2', 'count': 40, 'minimum_words': 40, 'seed': 1831,
    'development_exclusion': 'normalized hashes of every thought in the explicitly pinned prior voice cohorts; not unused thoughts merely archived on the same source day',
    'eligibility': 'source exactly mind; actual nonempty decision.thought; exclude later-than-Day1 cast names using legacy matcher',
    'freshness': 'exclude every declared development-cohort thought by normalized hash, plus duplicate candidate thoughts',
    'days': 'ascending day round-robin; exhausted days skip; no smaller cohort',
    'within_day': 'least-used scene, then least-used present-person tuple, then sha256(seed|day:step)',
    'scene': 'segment mode and at containing step.t; otherwise explicit unknown scene',
    'no_tuning': True, 'legacy_gate_unchanged': True,
}

def sha(data):
    return hashlib.sha256(data).hexdigest()

def text_hash(text):
    return sha(' '.join(text.casefold().split()).encode())

def preregister(out, shadow_commit, development_plans):
    if not re.fullmatch(r'[0-9a-f]{40}', shadow_commit):
        raise ValueError('pin the actual source commit before selection')
    if not development_plans:
        raise ValueError('pin the existing legacy voice cohort before selecting confirmation')
    hashes, plans = set(), []
    for path in development_plans:
        raw = Path(path).read_bytes()
        plan = json.loads(raw)
        bench.validate_plan(plan)
        if plan.get('purpose') == 't45-confirmation' or sha(json_bytes(plan['cohort'])) != plan['cohort_sha256']:
            raise ValueError('not an exact legacy development cohort')
        hashes.update(text_hash(row['plain']) for row in plan['cohort'])
        plans.append({'plan_sha256': sha(raw), 'cohort_sha256': plan['cohort_sha256'], 'count': len(plan['cohort'])})
    declared = json_bytes({'plans': plans, 'thought_sha256': sorted(hashes)})
    write_new(Path(out) / 'DECLARED-DEVELOPMENT.json', declared)
    receipt = {'rule': RULE, 'shadow_commit': shadow_commit, 'development_sha256': sha(declared),
               'utc': datetime.now(timezone.utc).isoformat(),
               'selector_sha256': sha(Path(__file__).read_bytes())}
    write_new(Path(out) / 'PREREGISTRATION.json', json_bytes(receipt))
    return receipt

def scene(day, step):
    time = step.get('t', '')
    for segment in day.get('segments', []):
        if segment.get('from', '') <= time < segment.get('to', ''):
            return (str(segment.get('mode', 'unknown')), str(segment.get('at', 'unknown')))
    return ('unknown', 'unknown')

def select(days, cast, development_hashes):
    by_n = {}
    for day in days:
        n = day.get('n')
        if type(n) is not int or n < 1 or n in by_n:
            raise ValueError('invalid or duplicated raw day')
        by_n[n] = day
    if 1 not in by_n:
        raise ValueError('Day1 is required for name exclusions')
    if not development_hashes or any(not re.fullmatch(r'[0-9a-f]{64}', h) for h in development_hashes):
        raise ValueError('actual prior voice-cohort hashes are required')
    patterns = [re.compile(r'(?<!\w)' + re.escape(n) + r'(?!\w)', re.I)
                for n in bench.later_names(by_n[1], cast)]
    seen = set(development_hashes)
    candidates, excluded = defaultdict(list), Counter()
    for n, day in sorted(by_n.items()):
        if n == 1:
            continue
        for index, step in enumerate(day.get('steps', [])):
            thought = (step.get('decision') or {}).get('thought')
            if step.get('mind', {}).get('source') != 'mind' or not isinstance(thought, str):
                excluded['not_actual_mind'] += 1
                continue
            if len(thought.split()) < RULE['minimum_words']:
                excluded['under40words'] += 1
                continue
            if any(p.search(thought) for p in patterns):
                excluded['later_name'] += 1
                continue
            checksum = text_hash(thought)
            if checksum in seen:
                excluded['development_or_duplicate'] += 1
                continue
            seen.add(checksum)
            identity = str(n) + ':' + str(index)
            present = step.get('present') or []
            if not isinstance(present, list) or any(not isinstance(p, str) for p in present):
                raise ValueError('unrecognized present-person provenance')
            candidates[n].append({'id': identity, 'day': n, 'step': index, 'plain': thought,
                                  'scene': scene(day, step), 'people': tuple(sorted(set(present)))})
    selected, used_scenes, used_people = [], Counter(), Counter()
    while any(candidates.values()) and len(selected) < RULE['count']:
        for day in sorted(candidates):
            if not candidates[day] or len(selected) == RULE['count']:
                continue
            row = min(candidates[day], key=lambda r: (
                used_scenes[r['scene']], used_people[r['people']],
                sha((str(RULE['seed']) + '|' + r['id']).encode())))
            candidates[day].remove(row)
            selected.append(row)
            used_scenes[row['scene']] += 1
            used_people[row['people']] += 1
    if len(selected) != RULE['count']:
        raise ValueError('fewer than40 fresh eligible thoughts; keep preregistration, do not relax or shrink')
    return selected, {'excluded': dict(excluded), 'by_day': dict(Counter(r['day'] for r in selected)),
                       'scene_count': len(used_scenes), 'people_group_count': len(used_people), 'rule': RULE}

def seal(out, days_dir, cast_path, cases_path, soul_path, shelf_path):
    out = Path(out)
    prereg_bytes = (out / 'PREREGISTRATION.json').read_bytes()
    prereg = json.loads(prereg_bytes)
    if prereg['rule'] != RULE or prereg['selector_sha256'] != sha(Path(__file__).read_bytes()):
        raise ValueError('preregistered selector changed; preserve and resolve explicitly')
    if (out / 'private').exists() or (out / 'SEAL.json').exists():
        raise FileExistsError('confirmation already selected or partially frozen; no reselection')
    inputs, days = {}, []
    for path in sorted(Path(days_dir).glob('*.json')):
        value = json.loads(path.read_bytes())
        if isinstance(value, dict) and type(value.get('n')) is int:
            name = 'day-' + str(value['n']) + '.json'
            if name in inputs:
                raise ValueError('duplicate raw day file')
            inputs[name] = path.read_bytes()
            days.append(value)
    declared = (out / 'DECLARED-DEVELOPMENT.json').read_bytes()
    if sha(declared) != prereg['development_sha256']:
        raise ValueError('preregistered development exclusions changed')
    inputs['development.json'] = declared
    cast_bytes = Path(cast_path).read_bytes()
    cohort, selection = select(days, json.loads(cast_bytes), json.loads(declared)['thought_sha256'])
    cases_bytes, soul_bytes, shelf_bytes = (Path(p).read_bytes() for p in (cases_path, soul_path, shelf_path))
    cases = json.loads(cases_bytes)['situations']
    if len(cases) != 20 or len({c['id'] for c in cases}) != 20:
        raise ValueError('canonical twenty contract cases required')
    nonce, order, key = secrets.token_hex(16), list(range(40)), {}
    random.Random(RULE['seed']).shuffle(order)
    assigned = {'welt': [], 'claude': []}
    for position, index in enumerate(order):
        row = cohort[index]
        opaque = sha((nonce + '|' + row['id']).encode())[:20]
        judge = 'welt' if position < 20 else 'claude'
        key[opaque] = {'source_id': row['id'], 'judge': judge,
                      'adapter': 'AB'[hashlib.sha256((nonce + '|order|' + row['id']).encode()).digest()[0] % 2]}
        assigned[judge].append(opaque)
    inputs.update({'cast.json': cast_bytes, 'situations.json': cases_bytes, 'soul.md': soul_bytes})
    plan = {'purpose': 't45-confirmation', 'cohort': cohort, 'selection': selection, 'seed': RULE['seed'],
            'shadow_commit': prereg['shadow_commit'], 'preregistration_sha256': sha(prereg_bytes),
            'key': key, 'assigned': assigned, 'key_commitment': sha(json_bytes(key)),
            'cohort_sha256': sha(json_bytes(cohort)), 'cases': cases, 'soul': soul_bytes.decode(),
            'shelf_path': str(Path(shelf_path).resolve()),
            'source_sha256': {**{name: sha(data) for name, data in inputs.items()}, 'shelf': sha(shelf_bytes)},
            'meaning_review_ids': [r['id'] for r in cohort[:10]],
            'bar': {'adapter_preferences': 28, 'per_judge': 12, 'Delta': 0.38, 'meaning': 36,
                    'copied12': 1, 'valid': 20, 'leaking': 0, 'max_restyle_seconds': 8}}
    bench.validate_plan(plan)
    private = out / 'private'
    private.mkdir(mode=0o700)
    for name, data in inputs.items():
        path = private / 'inputs' / name
        write_new(path, data)
        path.chmod(0o600)
    raw = json_bytes(plan)
    write_new(private / 'plan.json', raw)
    (private / 'plan.json').chmod(0o600)
    receipt = {'format': 't45-seal-v1', 'preregistration_sha256': sha(prereg_bytes),
               'plan_sha256': sha(raw), 'cohort_sha256': plan['cohort_sha256'],
               'key_commitment': plan['key_commitment'], 'count': 40,
               'by_day': selection['by_day'], 'scene_count': selection['scene_count'],
               'people_group_count': selection['people_group_count'], 'shadow_commit': prereg['shadow_commit']}
    write_new(out / 'SEAL.json', json_bytes(receipt))
    return receipt

def verify_seal(path):
    path = Path(path)
    raw = path.read_bytes()
    receipt = json.loads(raw)
    root = path.parent
    if receipt.get('format') != 't45-seal-v1' or receipt.get('count') != 40:
        raise ValueError('not a complete T45 seal')
    prereg = (root / 'PREREGISTRATION.json').read_bytes()
    plan_bytes = (root / 'private/plan.json').read_bytes()
    if sha(prereg) != receipt['preregistration_sha256'] or sha(plan_bytes) != receipt['plan_sha256']:
        raise ValueError('sealed confirmation changed')
    plan = bench.load_plan(root)
    if plan.get('purpose') != 't45-confirmation' or plan['cohort_sha256'] != receipt['cohort_sha256'] or plan['key_commitment'] != receipt['key_commitment']:
        raise ValueError('confirmation cohort/key changed')
    if (plan['preregistration_sha256'] != sha(prereg) or json.loads(prereg)['rule'] != RULE or
            json.loads(prereg)['selector_sha256'] != sha(Path(__file__).read_bytes())):
        raise ValueError('confirmation selection rule changed')
    days = []
    for name, checksum in plan['source_sha256'].items():
        data = Path(plan['shelf_path']).read_bytes() if name == 'shelf' else (root / 'private/inputs' / name).read_bytes()
        if sha(data) != checksum:
            raise ValueError('confirmation source changed: ' + name)
        if name.startswith('day-'):
            days.append(json.loads(data))
    declared = (root / 'private/inputs/development.json').read_bytes()
    if sha(declared) != json.loads(prereg)['development_sha256']:
        raise ValueError('development exclusion commitment changed')
    cohort, selection = select(days, json.loads((root / 'private/inputs/cast.json').read_bytes()), json.loads(declared)['thought_sha256'])
    if json_bytes(cohort) != json_bytes(plan['cohort']) or json_bytes(selection) != json_bytes(plan['selection']):
        raise ValueError('confirmation no longer matches preregistered selection')
    return receipt, sha(raw)

def lock_profile(out, adapter_path, profile, lora_id, scale, legacy_out, control, adapter):
    """Freeze a single post-tuning artifact/profile before any confirmation requests."""
    out, adapter_path = Path(out), Path(adapter_path)
    receipt, seal_hash = verify_seal(out / 'SEAL.json')
    plan = bench.load_plan(legacy_out)
    if plan.get('purpose') == 't45-confirmation':
        raise ValueError('confirmation cannot be its own development result')
    for result, arm in ((control, 'control'), (adapter, 'adapter')):
        bench.validate_result(plan, result, arm)
    if type(lora_id) is not int or lora_id < 0 or not 0 < scale <= 1 or not re.fullmatch(r'[A-Za-z0-9_-]+', profile):
        raise ValueError('invalid fixed confirmation profile')
    if adapter_path.stat().st_size == 0:
        raise ValueError('empty adapter')
    release = {'seal_sha256': seal_hash, 'adapter_path': str(adapter_path.resolve()),
               'adapter_sha256': sha(adapter_path.read_bytes()), 'profile': profile,
               'lora_id': lora_id, 'scale': scale, 'legacy_cohort_sha256': plan['cohort_sha256'],
               'legacy_control_sha256': sha(json_bytes(control)), 'legacy_adapter_sha256': sha(json_bytes(adapter)),
               'policy': 'single fixed profile; never select or tune using confirmation results'}
    write_new(out / 'private/CONFIRMATION-RELEASE.json', json_bytes(release))
    return release

def verify_release(out, arm, profile, client):
    out = Path(out)
    _, seal_hash = verify_seal(out / 'SEAL.json')
    release = json.loads((out / 'private/CONFIRMATION-RELEASE.json').read_bytes())
    if release['seal_sha256'] != seal_hash or release['profile'] != profile:
        raise ValueError('confirmation profile differs from the one frozen after tuning')
    if sha(Path(release['adapter_path']).read_bytes()) != release['adapter_sha256']:
        raise ValueError('fixed confirmation adapter changed')
    if arm == 'adapter' and client.lora != [{'id': release['lora_id'], 'scale': release['scale']}]:
        raise ValueError('confirmation scale or adapter differs from frozen profile')
    return sha(json_bytes(release))

def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    actions = p.add_mutually_exclusive_group(required=True)
    actions.add_argument('--preregister', action='store_true')
    actions.add_argument('--seal', action='store_true')
    actions.add_argument('--verify', action='store_true')
    actions.add_argument('--lock-profile', action='store_true', help='freeze one artifact/profile after development, before confirmation')
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--shadow-commit')
    p.add_argument('--development-plan', type=Path, action='append', help='actual frozen prior voice plan; repeat for each development cohort')
    p.add_argument('--days-dir', type=Path)
    p.add_argument('--source-root', type=Path, default=Path(__file__).resolve().parents[1])
    p.add_argument('--adapter', type=Path)
    p.add_argument('--profile')
    p.add_argument('--lora-id', type=int)
    p.add_argument('--scale', type=float)
    p.add_argument('--legacy-out', type=Path)
    p.add_argument('--control-result', type=Path)
    p.add_argument('--adapter-result', type=Path)
    a = p.parse_args(argv)
    if a.preregister:
        print(json.dumps(preregister(a.out, a.shadow_commit, a.development_plan)))
    elif a.seal:
        if a.days_dir is None:
            p.error('--seal requires frozen --days-dir')
        root = a.source_root
        print(json.dumps(seal(a.out, a.days_dir, root / 'world/data/cast.json', root / 'mind/situations.json',
                              root / 'mind/soul.md', root / 'mind/shelf/index.json.gz')))
    elif a.lock_profile:
        if any(x is None for x in (a.adapter, a.profile, a.lora_id, a.scale, a.legacy_out, a.control_result, a.adapter_result)):
            p.error('--lock-profile needs adapter, profile, lora-id, scale, legacy-out and both complete legacy results')
        release = lock_profile(a.out, a.adapter, a.profile, a.lora_id, a.scale, a.legacy_out,
                               json.loads(a.control_result.read_bytes()), json.loads(a.adapter_result.read_bytes()))
        print(json.dumps({'locked': True, 'release_sha256': sha(json_bytes(release))}))
    else:
        receipt, checksum = verify_seal(a.out / 'SEAL.json')
        print(json.dumps({'verified': True, 'seal_sha256': checksum, **receipt}))

if __name__ == '__main__':
    main()
