#!/usr/bin/env python3
"""Build two blind prose packets; private identity keys must stay outside the repo.

No generation, judge calls, training or publishing. The original archive remains
unchanged. Decision entries contribute their thought and spoken words, with the
mechanical JSON action fields removed identically for every decision arm.
"""
import argparse
import copy
import csv
import gzip
import hashlib
import html
import json
from pathlib import Path
import random
import re
import secrets
import zipfile

ROOT=Path(__file__).resolve().parent.parent
GUIDE='''# Reading guide

Don't search the web or look anything up. Read every text independently.
Score every text from 1 to 5 on each dimension (1 = very weak, 5 = very strong).
Give a one-line reason for each of the four scores.

- Argument moves: does the text develop a claim the way he does (from the difficulty within a position, to what it presupposes and where it turns into its opposite), or does it assert, list, or lay a triad over the material?
- His commitments: are the positions his, as of 1831, including the prejudiced ones, neither softened into a present-day view nor exaggerated into a caricature?
- Response to the particular case: does the thought start from the specific situation and stay with it, or could the same paragraph stand under any title?
- Voice: does it read like him, not like a translator's pastiche or a modern essay?

Answer as a CSV, one row per text:
id,argument,commitments,particular,voice,reasons

Use the supplied random id exactly. In reasons, give four short reasons labelled
argument / commitments / particular / voice. Quote CSV fields containing commas
or line breaks. Judge only the supplied text; do not guess its source. Finish
and save your ratings before reading anyone else's judgments.
'''
HEADERS=['id','argument','commitments','particular','voice','reasons']
FAMOUS=('owl of minerva','what is rational is actual','what is actual is rational',
        'the real is the rational','the wounds of the spirit','the truth is the whole',
        'world-historical individual','world historical individual','slaughter-bench',
        'system of needs','master and slave','lordship and bondage',
        'beautiful soul','morning prayer','end of history',
        'a hand, which is cut off','daylight of consciousness')


def digest(value):
    return hashlib.sha256(value).hexdigest()


def grams(text,n=12):
    words=re.findall(r"[\w']+",text.casefold())
    return {tuple(words[i:i+n]) for i in range(len(words)-n+1)}


def display_text(text,title=''):
    """Remove bibliographic headings, never modernise or rewrite the prose."""
    text=text.strip()
    lines=text.splitlines()
    if lines and title and lines[0].lstrip('# ').strip()==title.strip():
        lines=lines[1:]
    text='\n'.join(lines).strip()
    text=re.sub(r'^\s*(?:§\s*\d+[. ]*|\d+\.\s+)(?=[A-Z(])','',text)
    text=re.sub(r'§\s*\d+[.]?\s*','',text)
    return text.strip()


def archived_texts(source_zip,label_key):
    key=json.loads(label_key.read_text())
    texts=[];private={}
    with zipfile.ZipFile(source_zip) as z:
        for name in ('masked-writing.json','masked-decisions.json'):
            matches=[p for p in z.namelist() if p.endswith('/'+name) or p==name]
            if len(matches)!=1:
                raise ValueError('Archive must contain exactly one '+name)
            groups=json.loads(z.read(matches[0]))
            for group in groups:
                for c in group['candidates']:
                    ident=c['id']
                    if ident not in key:
                        raise ValueError('No original identity for '+ident)
                    raw=c['text']
                    if key[ident].get('text_sha256')!=digest(raw.encode()):
                        raise ValueError('Original text fingerprint mismatch: '+ident)
                    if name=='masked-decisions.json':
                        decision=json.loads(raw)
                        parts=[decision['thought']]
                        if isinstance(decision.get('says'),str) and decision['says'].strip():
                            parts.append('“'+decision['says'].strip()+'”')
                        text='\n\n'.join(parts)
                    else:
                        text=raw
                    texts.append((ident,display_text(text,c.get('title',''))))
                    private[ident]=dict(key[ident],source_kind=name,original_id=ident,
                        original_text_sha256=digest(raw.encode()))
    return texts,private


def controls(index_file,excluded,count=10):
    index=json.load(gzip.open(index_file,'rt',encoding='utf-8'))
    banned=set()
    for text in excluded:
        banned.update(grams(text))
    pool=[]
    for work in index['works']:
        if work['lang']!='en':
            continue
        for i in range(work['start'],work['start']+work['n']):
            original=index['texts'][i]
            text=display_text(original)
            # Complete paragraphs, not famous test passages, footnotes or a
            # chapter heading. Provenance stays solely in the private key.
            if not 150<=len(text.split())<=300 or not re.search(r'[.!?][”"\']?$',text):
                continue
            if any(s in text.casefold() for s in FAMOUS) or grams(text)&banned:
                continue
            if re.search(r'https?://|\[(?:\d+|Footnote)|\b(?:TRANSLATOR|PREFACE|CONTENTS)\b',text):
                continue
            if re.search(r'\b(?:[a-z]{2,} [ij] [a-z]{2,}|\w*\d\w*)\b',text) or '§' in original[1:]:
                continue
            if re.match(r'^(?:[IVX]+\. |CHAPTER|SECTION|PART|[A-Z ]{20,}\n)',text):
                continue
            pool.append((work,i,text))
    rng=random.SystemRandom();rng.shuffle(pool)
    selected=[];by_work={};seen=set()
    for work,i,text in pool:
        if by_work.get(work['id'],0)>=2 or digest(text.encode()) in seen:
            continue
        selected.append((f'control-{len(selected)+1}',text,dict(arm='control',
            source_work=work['id'],source_ref=index['refs'][i],shelf_index=i,
            original_text_sha256=digest(index['texts'][i].encode()))))
        seen.add(digest(text.encode()));by_work[work['id']]=by_work.get(work['id'],0)+1
        if len(selected)==count:
            return selected
    raise ValueError(f'Only {len(selected)} eligible controls; need {count}')


def fresh_tasks(template_file):
    template=json.loads(template_file.read_text())
    case=template['cases'][0]
    template['cases']=[]
    for kind in ('essay','letter'):
        for i in range(1,9):
            row=copy.deepcopy(case)
            row.update(id=f'{kind}-{i:02}',kind=kind)
            template['cases'].append(row)
    template['status']='16 blank situations for Welt to author; no model-authored cases'
    template['author']=''
    return template


def build(source_zip,label_key,index_file,exclude_file,template_file,out,private_key):
    out=out.resolve();private_key=private_key.resolve()
    if private_key.is_relative_to(ROOT.resolve()) or private_key.is_relative_to(out):
        raise ValueError('Private key must be outside both the repository and rater output')
    if private_key.exists() or out.exists():
        raise ValueError('Refusing to replace an existing packet or private key')
    source,original_key=archived_texts(source_zip,label_key)
    excluded=[t for _,t in source]+[exclude_file.read_text()]
    chosen=controls(index_file,excluded)
    all_texts=source+[(ident,text) for ident,text,_ in chosen]
    original_key.update({ident:metadata for ident,_,metadata in chosen})
    key={};packet=[]
    for original,text in all_texts:
        ident=secrets.token_hex(6).upper()
        while ident in key:
            ident=secrets.token_hex(6).upper()
        key[ident]=dict(original_key[original],display_sha256=digest(text.encode()))
        packet.append(dict(id=ident,text=text))
    out.mkdir(parents=True)
    orders={};rng=random.SystemRandom()
    for order in ('a','b'):
        rows=list(packet);rng.shuffle(rows)
        if order=='b' and [r['id'] for r in rows]==orders['a']:
            rows.reverse()
        orders[order]=[r['id'] for r in rows]
        directory=out/f'packet-{order}';directory.mkdir()
        (directory/'guide.md').write_text(GUIDE,encoding='utf-8')
        (directory/'texts.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        articles='\n'.join('<article><h2>'+r['id']+'</h2><div>'+html.escape(r['text'])+'</div></article>' for r in rows)
        page='<!doctype html><meta charset="utf-8"><title>Reading packet</title><style>body{max-width:54em;margin:2em auto;font:18px/1.6 Georgia}article{break-after:page;margin:3em 0;border-bottom:1px solid #aaa}article div{white-space:pre-wrap}h2{font:1em monospace}</style>'+articles
        (directory/'texts.html').write_text(page,encoding='utf-8')
        with (directory/'ratings.csv').open('w',newline='',encoding='utf-8') as f:
            writer=csv.writer(f);writer.writerow(HEADERS)
            writer.writerows([r['id'],'','','','',''] for r in rows)
        with zipfile.ZipFile(out/f'packet-{order}.zip','w',zipfile.ZIP_DEFLATED) as z:
            for path in directory.iterdir():
                z.write(path,path.name)
    (out/'fresh-situations-for-Welt.json').write_text(json.dumps(fresh_tasks(template_file),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    private_key.parent.mkdir(parents=True,exist_ok=True)
    with private_key.open('x',encoding='utf-8') as f:
        json.dump(dict(welt_only=True,source_zip_sha256=digest(source_zip.read_bytes()),
            keys=key,orders=orders,policy='Never send this file to a rater or include in a repository or bundle.'),f,ensure_ascii=False,indent=2)
        f.write('\n')
    manifest={p.relative_to(out).as_posix():digest(p.read_bytes()) for p in out.rglob('*') if p.is_file()}
    (out/'manifest.json').write_text(json.dumps(dict(n=len(packet),files=manifest,contains_source_key=False),indent=2)+'\n')
    return dict(texts=len(packet),writing_texts=len([x for x in source if x[0].startswith('W')]),
                decision_texts=len([x for x in source if x[0].startswith('D')]),controls=len(chosen),
                packet_ids_match=set(orders['a'])==set(orders['b']),key_outside_repo=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for flag in ('source-zip','label-key','shelf-index','exclude-texts','template','out','private-key'):
        p.add_argument('--'+flag,type=Path,required=True)
    a=p.parse_args()
    print(json.dumps(build(a.source_zip,a.label_key,a.shelf_index,a.exclude_texts,a.template,a.out,a.private_key)))
