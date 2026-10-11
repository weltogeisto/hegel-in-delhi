#!/usr/bin/env python3
"""Atomic-claim development calibration. Never relabel or overwrite the old run.

The old split has been inspected: it is a reused development split, not new
independent validation. Fit temperature and select the decision threshold using
only non-uncertain calibration rows. Fresh trajectories are evaluated separately.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from world.claim_check import (ClaimExtractor,SupportVerifier,EXTRACTION_PROTOCOL,
    PROTOCOL,api,fit_temperature,calibrated,calibration_metrics)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(data,sources):
    frozen=json.loads((data/'freeze.json').read_text())
    for name,expected in frozen['files'].items():
        if sha(data/name)!=expected:
            raise RuntimeError('Frozen calibration input changed: '+name)
    candidates=json.loads((data/'candidates.json').read_text())
    labels={r['id']:r for r in json.loads((data/'labels.json').read_text())['rows']}
    if len(candidates)!=150 or len(labels)!=150 or set(labels)!={r['id'] for r in candidates}:
        raise RuntimeError('Expected exactly 150 aligned frozen labels')
    groups={split:{r['group'] for r in candidates if r['split']==split} for split in ('calibration','heldout')}
    if groups['calibration'] & groups['heldout']:
        raise RuntimeError('A complete-source group crossed the old development split')
    contexts={}
    for row in candidates:
        label=labels[row['id']]
        if hashlib.sha256(row['sentence'].encode()).hexdigest()!=label['sentence_sha256']:
            raise RuntimeError('Label sentence mismatch: '+row['id'])
        if sha(data/row['evidence_file'])!=row['evidence_sha256']:
            raise RuntimeError('Evidence mismatch: '+row['id'])
        source=json.loads((sources/row['run']/'docs/days'/(row['date']+'.json')).read_text())
        for part in row['pointer']:
            source=source[part]
        if hashlib.sha256(source.encode()).hexdigest()!=row['source_text_sha256']:
            raise RuntimeError('Original literary context mismatch: '+row['id'])
        contexts[row['id']]=source
    return candidates,labels,contexts,frozen


def choose_threshold(rows,temperature):
    # Predeclared retention safeguard prevents the degenerate delete-everything
    # solution. Among eligible rules maximise balanced accuracy, then recall.
    candidates=[i/100 for i in range(5,96)]
    def quality(threshold):
        pos=[r for r in rows if r['label']==1];neg=[r for r in rows if r['label']==0]
        keep=sum(not r['claims'] or calibrated(r['log_odds'],temperature)>=threshold for r in pos)/len(pos)
        reject=sum(bool(r['claims']) and calibrated(r['log_odds'],temperature)<threshold for r in neg)/len(neg)
        factual=[r for r in pos if r['concrete_assertion']]
        factual_keep=sum(not r['claims'] or calibrated(r['log_odds'],temperature)>=threshold for r in factual)/len(factual) if factual else keep
        return keep,reject,factual_keep
    eligible=[t for t in candidates if quality(t)[0]>=.8 and quality(t)[2]>=.8]
    if not eligible:
        raise RuntimeError('No calibration rule retains at least 80% of supported prose')
    return max(eligible,key=lambda t:(sum(quality(t)[:2])/2,quality(t)[1],t))


def summarize(rows,temperature,threshold):
    counts=dict(supported_kept=0,supported_omitted=0,unsupported_accepted=0,unsupported_rejected=0)
    probabilities=[];errors=[]
    for r in rows:
        p=calibrated(r['log_odds'],temperature) if r['claims'] else 1.
        accepted=p>=threshold
        counts[('supported_kept' if accepted else 'supported_omitted') if r['label'] else
               ('unsupported_accepted' if accepted else 'unsupported_rejected')]+=1
        probabilities.append((p,r['label']))
        if accepted!=bool(r['label']):errors.append(dict(id=r['id'],sentence=r['sentence'],probability=p,label=r['label']))
    if not rows:
        return dict(n=0,**counts,errors=[],ece=None,brier=None)
    groups=[[] for _ in range(10)]
    for p,y in probabilities:groups[min(9,int(p*10))].append((p,y))
    return dict(n=len(rows),**counts,errors=errors,
        ece=sum(abs(sum(p for p,y in g)-sum(y for p,y in g)) for g in groups)/len(rows),
        brier=sum((p-y)**2 for p,y in probabilities)/len(rows))


def run(url,data,out,audit_file,sources,heartbeat=None):
    candidates,labels,contexts,frozen=validate(data,sources)
    if api(url,'/lora-adapters',None)!=[]:
        raise RuntimeError('Calibration requires the adapter-free server')
    out.mkdir(parents=True,exist_ok=False)
    uncertain=json.loads(audit_file.read_text())['uncertain']
    extractor=ClaimExtractor(url);verifier=SupportVerifier(url);scored=[]
    for n,row in enumerate(candidates,1):
        if heartbeat:
            heartbeat()
        with (out/(row['id']+'-raw.jsonl')).open('x') as audit:
            def log(value):audit.write(json.dumps(value,ensure_ascii=False)+'\n');audit.flush()
            extractor.audit=log;verifier.audit=log
            extracted=extractor.extract(row['sentence'],context=contexts[row['id']])
            claims=[claim for s in extracted for claim in s['claims']]
            evidence=(data/row['evidence_file']).read_text()
            votes=[verifier.score(claim,evidence) for claim in claims]
        result=dict(id=row['id'],split=row['split'],group=row['group'],sentence=row['sentence'],
            label=labels[row['id']]['label'],rationale=labels[row['id']]['rationale'],
            uncertain=row['id'] in uncertain,uncertainty_reason=uncertain.get(row['id']),
            concrete_assertion=labels[row['id']]['concrete_assertion'],claims=claims,
            evidence_sha256=row['evidence_sha256'],context_sha256=row['source_text_sha256'],
            log_odds=min((v['log_odds'] for v in votes),default=None),votes=votes)
        (out/(row['id']+'.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
        scored.append(result);print(f"{n}/150 {row['id']}: {len(claims)} factual claims",flush=True)
    fitting=[r for r in scored if r['split']=='calibration' and not r['uncertain'] and r['claims']]
    temperature=fit_temperature([r['log_odds'] for r in fitting],[r['label'] for r in fitting])
    train=[r for r in scored if r['split']=='calibration' and not r['uncertain']]
    threshold=choose_threshold(train,temperature)
    settings=dict(extraction_protocol=EXTRACTION_PROTOCOL,probability_protocol=PROTOCOL,
        temperature=temperature,threshold=threshold,fit_partition='non-uncertain calibration only',
        threshold_rule='max balanced accuracy subject to >=80% supported retention overall AND on concrete premises; calibration partition only',
        model='Qwen3.8-27B UD-Q4_K_M, adapter disabled',weights_trained=False)
    report=dict(settings=settings,n=150,uncertain=uncertain,label_author='Codex manual assessment',
        inputs_sha256=frozen['files'],uncertainty_audit_sha256=sha(audit_file),
        validation_status='Old split inspected previously; reused development data, not independent confirmation',
        partitions={})
    report['uncertain_results']=summarize([r for r in scored if r['uncertain']],temperature,threshold)
    for split in ('calibration','heldout'):
        subset=[r for r in scored if r['split']==split and not r['uncertain']]
        facts=[r for r in subset if r['claims']]
        report['partitions'][split]=dict(pipeline=summarize(subset,temperature,threshold),
            uncalibrated_claim_vote=calibration_metrics([r['log_odds'] for r in facts],[r['label'] for r in facts]) if facts else None,
            calibrated_claim_vote=calibration_metrics([r['log_odds'] for r in facts],[r['label'] for r in facts],temperature) if facts else None,
            concrete_sentences=summarize([r for r in subset if r['concrete_assertion']],temperature,threshold))
    (out/'settings.json').write_text(json.dumps(settings,indent=2)+'\n')
    (out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--url',required=True)
    for name in ('data','out','audit','sources'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();run(a.url,a.data,a.out,a.audit,a.sources)
