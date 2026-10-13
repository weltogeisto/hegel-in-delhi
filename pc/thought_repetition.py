"""Count four-word reuse from an earlier thought in each saved day (T9).

Stdlib only. This audits saved output and changes no world or prose.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import unicodedata

# Frozen English function-word list, included in the report for reproducibility.
STOPWORDS = frozenset("""a about above after again against all am an and any are aren't as at be because been before being below between both but by can can't cannot could couldn't did didn't do does doesn't doing don't down during each few for from further had hadn't has hasn't have haven't having he he'd he'll he's her here here's hers herself him himself his how how's i i'd i'll i'm i've if in into is isn't it it's its itself just me more most must mustn't my myself no nor not of off on once only or other ought our ours ourselves out over own same she she'd she'll she's should shouldn't so some such than that that's the their theirs them themselves then there there's these they they'd they'll they're they've this those through to too under until up very was wasn't we we'd we'll we're we've were weren't what what's when when's where where's which while who who's whom why why's will with won't would wouldn't you you'd you'll you're you've your yours yourself yourselves""".split())
WORD = re.compile(r"[^\W\d_]+(?:'[^\W\d_]+)*|\d+(?:[,.]\d+)*", re.UNICODE)


def grams(text):
    text = unicodedata.normalize('NFKC', text).casefold().replace('\u2019', "'").replace('\u2018', "'")
    words = WORD.findall(text)
    out = set()
    for i in range(len(words) - 3):
        g = tuple(words[i:i+4])
        # Numerals are boundaries, not removed words that could create a phrase.
        if any(w[0].isdigit() for w in g) or all(w in STOPWORDS for w in g):
            continue
        out.add(' '.join(g))
    return out


def audit(day, label, source_sha256):
    thoughts = [e for e in day['entries'] if e['k'] == 'diary']
    decisions = [s for s in day.get('steps', []) if 'decision' in s]
    assert [(e['t'], e['text']) for e in thoughts] == [(s['t'], s['decision']['thought']) for s in decisions]
    earlier = defaultdict(list)
    marked = []
    for index, e in enumerate(thoughts, 1):
        g = grams(e['text'])
        matches = [{'phrase': p, 'earlier_thoughts': list(earlier[p])} for p in sorted(g) if earlier[p]]
        marked.append({'thought': index, 't': e['t'], 'text': e['text'], 'reuses_earlier_phrase': bool(matches), 'matches': matches})
        for p in g:
            earlier[p].append({'thought': index, 't': e['t']})
    repeated = [{'phrase': p, 'thoughts': len(v), 'reuses_after_first': len(v)-1, 'occurrences': v}
                for p, v in earlier.items() if len(v)>1]
    repeated.sort(key=lambda x: (-x['reuses_after_first'], x['phrase']))
    n = sum(x['reuses_earlier_phrase'] for x in marked)
    return {'label': label, 'date': day['date'], 'n': day['n'], 'source_sha256': source_sha256,
            'thoughts': len(marked), 'marked_thoughts': n, 'share': n/len(marked) if marked else None,
            'top_ten': repeated[:10], 'all_repeated_phrases': repeated, 'marked': marked}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--manifest', required=True, type=Path)
    ap.add_argument('--inputs', required=True, type=Path)
    ap.add_argument('--out', required=True, type=Path)
    args = ap.parse_args()
    manifest = json.loads(args.manifest.read_text())
    result = {'method': {'unit': 'diary entry, independently equal to the validated decision thought',
                         'normalization': 'Unicode NFKC, casefold, curly apostrophes to ASCII; punctuation ignored; numerals are boundaries',
                         'phrase': 'four contiguous words with at least one word outside the fixed stopword set',
                         'mark': 'at least one eligible phrase occurs in an earlier thought that day; within-thought repetition alone does not mark it',
                         'ranking': 'number of distinct later thoughts reusing a phrase after its first thought; ties alphabetic',
                         'stopwords': sorted(STOPWORDS),
                         'limit': 'Literal phrase reuse, not semantic repetition or a judgment that a thought is bad.'}, 'days': []}
    for item in manifest['days']:
        raw = (args.inputs/(item['id']+'.json')).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == item['sha256']
        result['days'].append(dict(id=item['id'], **audit(json.loads(raw), item['label'], item['sha256'])))
    with args.out.open('x', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
        f.write('\n')
    print(json.dumps([{'id': d['id'], 'marked': d['marked_thoughts'], 'thoughts': d['thoughts'], 'share': d['share'], 'top_ten': [{'phrase': p['phrase'], 'thoughts': p['thoughts']} for p in d['top_ten']]} for d in result['days']], ensure_ascii=False))


if __name__ == '__main__':
    main()
