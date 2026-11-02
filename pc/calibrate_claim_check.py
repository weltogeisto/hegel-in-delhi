#!/usr/bin/env python3
"""Score frozen agent-labelled rehearsal sentences; fit one scalar, no weights.

Uses an already running, adapter-free server. Keep raw votes and held-out errors.
Neither synthetic probes nor held-out labels choose temperature or threshold.
"""
import argparse
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from world.claim_check import (PROTOCOL, SupportVerifier, calibrated,
                              calibration_metrics, fit_temperature)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def confusion(rows, temperature, threshold):
    counts = dict(supported_kept=0, supported_omitted=0,
                  unsupported_accepted=0, unsupported_rejected=0)
    errors = []
    for r in rows:
        accept = calibrated(r['log_odds'], temperature) >= threshold
        key = ('supported_kept' if accept else 'supported_omitted') if r['label'] else (
            'unsupported_accepted' if accept else 'unsupported_rejected')
        counts[key] += 1
        if accept != bool(r['label']):
            errors.append(dict(id=r['id'], label=r['label'],
                               probability=calibrated(r['log_odds'], temperature)))
    unsupported = counts['unsupported_accepted'] + counts['unsupported_rejected']
    supported = counts['supported_kept'] + counts['supported_omitted']
    return dict(counts, unsupported_recall=counts['unsupported_rejected']/unsupported if unsupported else None,
                supported_retention=counts['supported_kept']/supported if supported else None, errors=errors)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', required=True)
    parser.add_argument('--data', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    frozen = json.loads((args.data/'freeze.json').read_text())
    for name, expected in frozen['files'].items():
        if digest(args.data/name) != expected:
            raise RuntimeError('Frozen calibration input changed: '+name)
    rows = json.loads((args.data/'candidates.json').read_text())
    protocol = json.loads((args.data/'protocol.json').read_text())
    labels = json.loads((args.data/'labels.json').read_text())
    by_id = {r['id']:r for r in labels['rows']}
    if len(rows) != 150 or set(by_id) != {r['id'] for r in rows}:
        raise RuntimeError('Expected exactly 150 aligned frozen labels')
    groups = {split:{r['group'] for r in rows if r['split']==split} for split in ('calibration','heldout')}
    if groups['calibration'] & groups['heldout']:
        raise RuntimeError('A complete-source group crossed the held-out split')
    with urllib.request.urlopen(args.url.rstrip('/')+'/lora-adapters',timeout=10) as response:
        if json.load(response) != []:
            raise RuntimeError('Calibration requires the adapter-free server')
    args.out.mkdir(parents=True,exist_ok=True)
    if list(args.out.iterdir()):
        raise RuntimeError('Refusing to overwrite saved calibration predictions')
    verifier = SupportVerifier(args.url)
    scored = []
    for i,r in enumerate(rows,1):
        label = by_id[r['id']]
        if hashlib.sha256(r['sentence'].encode()).hexdigest() != label['sentence_sha256']:
            raise RuntimeError('Label sentence mismatch: '+r['id'])
        evidence = (args.data/r['evidence_file']).read_text()
        if hashlib.sha256(evidence.encode()).hexdigest() != r['evidence_sha256']:
            raise RuntimeError('Evidence mismatch: '+r['id'])
        with (args.out/(r['id']+'-exchanges.jsonl')).open('x') as raw_log:
            def audit(exchange):
                raw_log.write(json.dumps(exchange,ensure_ascii=False)+'\n');raw_log.flush()
            verifier.audit=audit
            result = verifier.score(r['sentence'],evidence)
        raw = dict(id=r['id'],split=r['split'],group=r['group'],
                   label=label['label'],label_rationale=label['rationale'],
                   concrete_assertion=label['concrete_assertion'],
                   evidence_sha256=r['evidence_sha256'],**result)
        (args.out/(r['id']+'.json')).write_text(json.dumps(raw,ensure_ascii=False,indent=2)+'\n')
        scored.append(raw)
        print(f"{i}/150 {r['id']} saved",flush=True)
    train = [r for r in scored if r['split']=='calibration']
    held = [r for r in scored if r['split']=='heldout']
    temperature = fit_temperature([r['log_odds'] for r in train],[r['label'] for r in train])
    threshold = protocol['threshold_predeclared']
    report = dict(protocol=PROTOCOL,n=150,label_author=labels['author'],
                  temperature=temperature,temperature_at_bound=temperature<=.050001 or temperature>=19.9999,
                  threshold=threshold,threshold_chosen_before_predictions=True,
                  fit_partition='calibration only',weights_trained=False,
                  inputs_sha256=frozen['files'],partitions={})
    for name,part in [('calibration',train),('heldout',held)]:
        z=[r['log_odds'] for r in part];y=[r['label'] for r in part]
        report['partitions'][name]=dict(uncalibrated=calibration_metrics(z,y),
            calibrated=calibration_metrics(z,y,temperature),
            decisions=confusion(part,temperature,threshold),
            supported=sum(y),unsupported=len(y)-sum(y))
        factual=[r for r in part if r['concrete_assertion']]
        if factual:
            report['partitions'][name]['concrete_assertions_only']=dict(
                calibrated=calibration_metrics([r['log_odds'] for r in factual],
                    [r['label'] for r in factual],temperature),
                decisions=confusion(factual,temperature,threshold),
                supported=sum(r['label'] for r in factual),
                unsupported=sum(1-r['label'] for r in factual))
    report['limitations']=protocol['limitations']+[
        'Labels are manual assessments by Codex, not independent human judgments.',
        'Legacy missing evidence makes plausible facts unsupported; this measures record support, not truth.',
        'Positive labels include many non-factual philosophical sentences; inspect the concrete-assertion subset separately.',
        'This calibration is not the fresh three-seed before/after fidelity test and does not enable a runtime guard.']
    (args.out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(temperature=temperature,heldout=report['partitions']['heldout']),ensure_ascii=False),flush=True)


if __name__=='__main__':
    main()
