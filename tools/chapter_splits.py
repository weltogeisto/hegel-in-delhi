"""Chapter-isolated Training 1 assignments over an immutable recipe4 corpus.

No target or generator ledger is rewritten. Top-level cleaned-source headings are
conservative chapter groups. A work with no such headings stays one whole group;
units crossing headings unite their groups, rather than dropping any target.
"""
import argparse
from bisect import bisect_right
from collections import Counter, defaultdict
import gzip
import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools import hegelizer as hg, hegelizer_round2 as data2
from tools.recorded_llama import json_bytes, write_new
from world import shelf

FORMAT = 'training1-chapter-splits-v2'

def sha(data):
    return hashlib.sha256(data).hexdigest()


def chapter_passages(work, cleaned, expected, style, mend=lambda text: text):
    """Recover chapter labels without changing a single indexed passage byte."""
    whole = shelf.split_passages(cleaned, style)
    heads = list(re.finditer(r'^# ([^\n]+)$', cleaned, re.M))
    cuts = sorted(set([0] + [m.start() for m in heads] + [len(cleaned)]))
    labels = {m.start(): m.group(1).strip() for m in heads}
    passages, chapters, names = [], [], {}
    current = '[unheaded work or preface]'
    for start, end in zip(cuts, cuts[1:]):
        current = labels.get(start, current)
        # Repeated source headings stay together even when discontinuous.
        chapter = work + ':' + sha(current.encode())[:20]
        names[chapter] = current
        rows = shelf.split_passages(cleaned[start:end], style)
        passages.extend(text for _, text in rows)
        chapters.extend([chapter] * len(rows))
    if passages != [text for _, text in whole]:
        raise ValueError('chapter boundaries changed indexed passage text: ' + work)
    # The historical shelf filtered damaged/later passages and mended OCR.
    # Reapply only its deterministic mender for provenance, then require every
    # already-indexed passage/ref byte-exact in source order. Do not rebuild the
    # index or repeat filtering, and keep every ambiguous chapter together.
    provenance = defaultdict(set)
    mended = []
    for (ref, raw), chapter in zip(whole, chapters):
        pair = (ref, mend(raw))
        mended.append(pair)
        provenance[pair].add(chapter)
    cursor, kept_chapters = 0, []
    for pair in expected:
        while cursor < len(mended) and mended[cursor] != pair:
            cursor += 1
        if cursor == len(mended):
            raise ValueError('indexed passage is not an exact ordered source match: ' + work)
        cursor += 1
        labels = sorted(provenance[pair])
        kept_chapters.append(labels[0] if len(labels) == 1 else tuple(labels))
    return [text for _, text in expected], kept_chapters, names


def memberships(full_units, passages, chapter_ids):
    """All exact source occurrences count: ambiguous repeats can only merge groups."""
    parts, starts, labels, pos = [], [], [], 1
    for text, chapter in zip(passages, chapter_ids):
        text = hg.apparatus(text)
        if not text:
            continue
        starts.append(pos)
        labels.append(chapter)
        parts.append(text)
        pos += len(text) + 1
    source = ' ' + ' '.join(parts) + ' '
    out = {}
    for unit in full_units:
        target = unit['original']
        if target != ' '.join(target.split()):
            raise ValueError('target whitespace differs from canonical corpus')
        needle, found, cursor = ' ' + target + ' ', set(), 0
        while True:
            begin = source.find(needle, cursor)
            if begin < 0:
                break
            first = bisect_right(starts, begin + 1) - 1
            last = bisect_right(starts, begin + len(needle) - 2) - 1
            for label in labels[first:last + 1]:
                found.update([label] if isinstance(label, str) else label)
            cursor = begin + 1
        if not found:
            raise ValueError('authentic target cannot be located: ' + unit['id'])
        out[unit['id']] = sorted(found)
    return out


def assign(units, membership, seed=1831, share=0.05):
    """Hash-selected whole connected chapter groups; never choose by model results."""
    if not 0 < share < 1 or type(seed) is not int:
        raise ValueError('invalid chapter split seed/share')
    by_id = {u['id']: u for u in units}
    if len(by_id) != len(units):
        raise ValueError('duplicate unit')
    full = {u['id']: u for u in units if u['kind'] == 'full'}
    if set(membership) != set(full) or any(not v for v in membership.values()):
        raise ValueError('every full unit needs chapter provenance')
    roots = {c: c for cs in membership.values() for c in cs}
    def root(c):
        while roots[c] != c:
            roots[c] = roots[roots[c]]
            c = roots[c]
        return c
    for cs in membership.values():
        group = min(root(c) for c in cs)
        for c in cs:
            roots[root(c)] = group
    groups = defaultdict(list)
    for chapter in sorted(roots):
        groups[root(chapter)].append(chapter)
    ordered = sorted(groups, key=lambda c: (sha((str(seed) + '|' + '|'.join(groups[c])).encode()), c))
    if len(ordered) < 2:
        raise ValueError('fewer than two independent chapter groups; no honest held-out split')
    # Keep the original 5% FULL-unit target as closely as indivisible chapters
    # permit. Only the frozen hash-order prefix length is chosen; no model
    # success/failure, style score or short-unit count enters the decision.
    weights = Counter(root(cs[0]) for cs in membership.values())
    target = max(1, round(share * len(full)))
    cumulative, choices = 0, []
    for count, group in enumerate(ordered[:-1], 1):
        cumulative += weights[group]
        choices.append((abs(cumulative - target), count))
    count = min(choices)[1]
    held = set(ordered[:count])
    assignments = {}
    for unit in units:
        parent = full.get(unit['parent_id'])
        if parent is None or parent['parent_id'] != parent['id'] or parent['work'] != unit['work']:
            raise ValueError('missing authentic full parent')
        if unit['kind'] not in ('full', 'short') or unit['kind'] == 'short' and unit['original'] not in parent['original']:
            raise ValueError('short unit must be an intact authentic parent span')
        group = root(membership[parent['id']][0])
        assignments[unit['id']] = {'parent_id': parent['id'], 'group': group,
                                   'split': 'held' if group in held else 'train'}
    return {'assignments': assignments, 'groups': dict(groups), 'held_groups': sorted(held),
            'group_count': len(groups), 'held_group_count': count,
            'held_full_target': target, 'held_full_selected': sum(weights[g] for g in held)}


def build_manifest(units_path, index_path, shelf_dir, seed=1831, share=0.05):
    from tools.corpus import WORKS, GARBLE, mend
    units_path, index_path, shelf_dir = Path(units_path), Path(index_path), Path(shelf_dir)
    units = data2.strict_rows(units_path)
    index_bytes = index_path.read_bytes()
    index = json.loads(gzip.decompress(index_bytes))
    specs = {w['id']: w for w in WORKS}
    full_by_work = defaultdict(list)
    for unit in units:
        if unit['kind'] == 'full':
            full_by_work[unit['work']].append(unit)
    member, names, sources, unheaded = {}, {}, {}, []
    cleaned_sources, good_words = {}, Counter()
    for spec in WORKS:
        if spec['lang'] != 'en' or not spec['shelf']:
            continue
        data = (shelf_dir / (spec['id'] + '.txt.gz')).read_bytes()
        sources[spec['id']] = sha(data)
        cleaned_sources[spec['id']] = gzip.decompress(data).decode('utf-8')
        for _, passage in shelf.split_passages(cleaned_sources[spec['id']], spec['ref']):
            good_words.update(re.findall(r'[a-z]{3,}', shelf.fold(GARBLE.sub(' ', passage))))
    indexed_works = {w['id']: w for w in index['works']}
    for work, full in sorted(full_by_work.items()):
        w, spec = indexed_works[work], specs[work]
        if w['lang'] != 'en':
            raise ValueError('non-English training work')
        cleaned = cleaned_sources[work]
        if not re.search(r'^# ', cleaned, re.M):
            unheaded.append(work)
        start, end = w['start'], w['start'] + w['n']
        expected = list(zip(index['refs'][start:end], index['texts'][start:end]))
        passages, chapters, titles = chapter_passages(work, cleaned, expected, spec['ref'], lambda text: mend(text, good_words)[0])
        # Reconstruct only the original segmentation, without rerunning filters,
        # dropping units, generating text or changing any frozen target/result.
        made, _ = hg.work_units([(ref, hg.apparatus(text)) for ref, text in expected])
        for unit in full:
            prefix, ordinal = unit['id'].rsplit(':', 1)
            if prefix != work or made[int(ordinal)] != (unit['ref'], unit['original']):
                raise ValueError('unit identity differs from frozen source segmentation')
        member.update(memberships(full, passages, chapters))
        names.update(titles)
    assigned = assign(units, member, seed, share)
    return {'format': FORMAT, 'seed': seed, 'held_full_share_target': share,
            'units_sha256': sha(units_path.read_bytes()), 'index_sha256': sha(index_bytes),
            'index_path': str(index_path.resolve()), 'shelf_dir': str(shelf_dir.resolve()),
            'source_sha256': sources, 'chapter_names': names, 'membership': member,
            'whole_work_fallback': unheaded,
            'rule': 'top-level source headings; unheaded work kept whole; merge all crossed/ambiguous chapters; hash-order prefix nearest5%full-unit count',
            **assigned}


def load_manifest(path, units_path):
    path = Path(path)
    raw = path.read_bytes()
    manifest = json.loads(raw)
    if manifest.get('format') != FORMAT:
        raise ValueError('unknown chapter split format')
    expected = build_manifest(units_path, manifest['index_path'], manifest['shelf_dir'],
                              manifest['seed'], manifest['held_full_share_target'])
    if manifest != expected:
        raise ValueError('chapter manifest, source or frozen units changed')
    return manifest, sha(raw)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--units', type=Path, required=True)
    p.add_argument('--index', type=Path, default=shelf.INDEX)
    p.add_argument('--shelf-dir', type=Path, default=shelf.INDEX.parent)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--seed', type=int, default=1831)
    a = p.parse_args(argv)
    manifest = build_manifest(a.units, a.index, a.shelf_dir, a.seed)
    raw = json_bytes(manifest)
    write_new(a.out, raw)
    print(json.dumps({'sha256': sha(raw), 'units': len(manifest['assignments']),
                      'groups': manifest['group_count'], 'held_groups': manifest['held_group_count'],
                      'whole_work_fallback': manifest['whole_work_fallback']}))

if __name__ == '__main__':
    main()
