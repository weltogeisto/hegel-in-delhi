"""T8: replay the unchanged owl on three frozen days and ten declared seeds.

Use a frozen main snapshot, preserve its HTTPMind/OWL retries, and add only a
sampler seed and the reserved spare slot to each generation request.
"""
import argparse
import copy
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import time
import traceback
import urllib.error
import urllib.request

COMMAND_SHA = '1944b782a1c3557851d1c3639e04e43072e6c2a6e8eff6e96978f96d6e48d6b0'


def stamp():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    with path.open('x', encoding='utf-8') as h:
        json.dump(value, h, ensure_ascii=False, indent=2)
        h.write('\n')


def api(url, route, payload=None):
    req = urllib.request.Request(url+route, data=None if payload is None else json.dumps(payload).encode(),
                                 headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)


def server_check(url):
    assert sha(Path('/proc/384/cmdline')) == COMMAND_SHA
    assert api(url, '/health')['status'] == 'ok'
    assert api(url, '/lora-adapters') == []


class Transport:
    def __init__(self, url, seed, slot, directory, capture=False):
        self.url, self.seed, self.slot, self.directory, self.capture = url, seed, slot, directory, capture
        self.calls = []
        self.original = urllib.request.urlopen
        self.token_cache = {}

    def __enter__(self):
        urllib.request.urlopen = self.open
        return self

    def __exit__(self, *args):
        urllib.request.urlopen = self.original

    def metadata(self, route, payload):
        req = urllib.request.Request(self.url+route, data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json'})
        with self.original(req, timeout=30) as response:
            return json.load(response)

    def count(self, payload):
        key = json.dumps([payload['messages'], payload['chat_template_kwargs']], sort_keys=True)
        if key not in self.token_cache:
            prompt = self.metadata('/apply-template', {'messages': payload['messages'], 'chat_template_kwargs': payload['chat_template_kwargs']})['prompt']
            self.token_cache[key] = len(self.metadata('/tokenize', {'content': prompt, 'add_special': True, 'parse_special': True})['tokens'])
        return self.token_cache[key]

    def open(self, request, *args, **kwargs):
        url = getattr(request, 'full_url', str(request))
        if not url.endswith('/v1/chat/completions'):
            return self.original(request, *args, **kwargs)
        payload = json.loads(request.data)
        assert 'lora' not in payload and not payload['chat_template_kwargs']['enable_thinking']
        payload.update(seed=self.seed, id_slot=self.slot)
        count = self.count(payload)
        index = len(self.calls)+1
        base = self.directory/f'call-{index:02d}'
        save(base.with_suffix('.request.json'), payload)
        meta = {'started_utc': stamp(), 'seed': self.seed, 'slot': self.slot, 'measured_prompt_tokens': count, 'capture_only': self.capture}
        began = time.monotonic()
        try:
            if self.capture:
                answer = {'diary': 'Capture only; no model generation. ' * 8, 'revision_log': '', 'theses': [], 'depesche': 'Capture only.'}
                raw = json.dumps({'choices': [{'message': {'content': json.dumps(answer)}, 'finish_reason': 'stop'}]}).encode()
            else:
                req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=dict(request.header_items()))
                with self.original(req, *args, **kwargs) as response:
                    raw = response.read()
                with base.with_suffix('.response.json').open('xb') as h:
                    h.write(raw)
                decoded = json.loads(raw)
                meta['usage'] = decoded.get('usage')
                meta['finish_reason'] = decoded['choices'][0].get('finish_reason')
                meta['actual_prompt_tokens'] = decoded.get('usage', {}).get('prompt_tokens')
                assert meta['actual_prompt_tokens'] == count, 'Serving template/tokenizer count changed'
            if self.capture:
                with base.with_suffix('.response.json').open('xb') as h:
                    h.write(raw)
            return io.BytesIO(raw)
        except BaseException as exc:
            meta['error'] = type(exc).__name__+': '+str(exc)
            if isinstance(exc, urllib.error.HTTPError):
                with base.with_suffix('.http-error').open('xb') as h:
                    h.write(exc.read())
            raise
        finally:
            meta['seconds'] = time.monotonic()-began
            meta['finished_utc'] = stamp()
            self.calls.append(meta)
            save(base.with_suffix('.meta.json'), meta)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source', required=True, type=Path)
    ap.add_argument('--protocol', required=True, type=Path)
    ap.add_argument('--inputs', required=True, type=Path)
    ap.add_argument('--out', required=True, type=Path)
    ap.add_argument('--url', default='http://127.0.0.1:8082')
    ap.add_argument('--capture', action='store_true')
    args = ap.parse_args()
    sys.path.insert(0, str(args.source))
    from world import owl
    from world.config import Config
    from world.mind import HTTPMind
    from world.world import World
    assert Path(owl.__file__).resolve().is_relative_to(args.source.resolve())
    protocol = json.loads(args.protocol.read_text())
    assert protocol['code'] == '61accbdab85d78f14379d2d711205541d2b634c1'
    assert protocol['seeds'] == list(range(2026101380, 2026101390))
    args.out.mkdir()
    checks = {str(args.protocol): sha(args.protocol)}
    for item in protocol['days']:
        for suffix, expected in [('.json', item['sha256']), ('-known.txt', item['known_sha256']), ('-owl-record.txt', item['owl_record_sha256'])]:
            path = args.inputs/(item['id']+suffix)
            assert sha(path) == expected
            checks[str(path)] = expected
    for path in args.source.rglob('*'):
        if path.is_file() and '__pycache__' not in path.parts:
            checks[str(path)] = sha(path)
    checks[str(Path(__file__))] = sha(Path(__file__))
    save(args.out/'frozen-files.json', checks)
    cfg = Config({'HEGEL_ENV': os.devnull, 'HEGEL_REPO': str(args.source), 'HEGEL_STATE': str(args.out/'scratch-state'),
                  'HEGEL_BRANCH': 'shadow', 'HEGEL_PUSH': '0', 'HEGEL_FEEDS': '0', 'PC_MAC': '',
                  'HEGEL_CLOCK_SHIFT_MIN': '300', 'LEAD_MIN': '15', 'OWL_AT': '01:30', 'HEGEL_OWL_REASONING_TOKENS': '0',
                  'HEGEL_THESIS_REMINDERS': '1', 'HEGEL_VOICE_ADAPTER_SCALE': '', 'MIND_TIMEOUT': '300'})
    world = World()
    rows = []
    started = stamp()
    began = time.monotonic()
    seeds = protocol['seeds'][:1] if args.capture else protocol['seeds']
    try:
        for seed in seeds:
            for item in protocol['days']:
                for path, expected in checks.items():
                    assert sha(Path(path)) == expected, path
                server_check(args.url)
                jobid = f"{item['id']}-{seed}"
                directory = args.out/jobid
                directory.mkdir()
                day = json.loads((args.inputs/(item['id']+'.json')).read_bytes())
                assert sha(args.inputs/(item['id']+'.json')) == item['sha256']
                assert hashlib.sha256(owl.record(day).encode()).hexdigest() == item['owl_record_sha256']
                state = copy.deepcopy(day['state'])
                known = (args.inputs/(item['id']+'-known.txt')).read_text()
                mind = HTTPMind(args.url, timeout=300)
                mind.ready = True  # health was checked; never invokes a wake script
                job_start = time.monotonic()
                print('START', jobid, flush=True)
                with Transport(args.url, seed, 1, directory, capture=args.capture) as transport:
                    result = owl.write(cfg, day, state, mind, depesche_n=item['depesche_n'],
                                       problems=lambda text: world.problems(text, known), flag=world.flag, topic=world.topic)
                row = {'day': item['id'], 'seed': seed, 'label': item['label'], 'before': item['theses_before'],
                       'after': state['theses'], 'changes': result['theses'], 'result': result,
                       'seconds': time.monotonic()-job_start, 'calls': transport.calls}
                save(directory/'result.json', row)
                rows.append(row)
                server_check(args.url)
                print('END', jobid, len(result['theses']), 'changes', flush=True)
        for path, expected in checks.items():
            assert sha(Path(path)) == expected, path
        summary = []
        for item in protocol['days']:
            subset = [r for r in rows if r['day'] == item['id']]
            summary.append({'day': item['id'], 'label': item['label'], 'seeds': len(subset),
                            'any_thesis_moves': sum(bool(r['changes']) for r in subset),
                            'india_moves': sum(any(c['id']=='india' for c in r['changes']) for r in subset)})
        if not args.capture:
            assert len(rows) == 30 and all(x['seeds'] == 10 for x in summary)
        manifest = {str(p.relative_to(args.out)): sha(p) for p in sorted(args.out.rglob('*')) if p.is_file()}
        save(args.out/'complete.json', {'started_utc': started, 'finished_utc': stamp(), 'capture_only': args.capture,
                                       'seconds': time.monotonic()-began, 'summary': summary, 'jobs': rows, 'files_sha256': manifest})
        print(json.dumps(summary), flush=True)
    except BaseException as exc:
        save(args.out/'failure.json', {'started_utc': started, 'failed_utc': stamp(), 'error': repr(exc), 'traceback': traceback.format_exc(), 'completed_jobs': len(rows)})
        raise


if __name__ == '__main__':
    main()
