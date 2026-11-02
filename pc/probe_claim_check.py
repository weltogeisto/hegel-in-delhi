#!/usr/bin/env python3
"""Protocol smoke check against an already running, adapter-free WSL server.

Diagnostic examples below are not the calibration set or a performance test.
Retain raw probabilities, requests and responses; enable no runtime guard.
"""
import argparse
import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from world.claim_check import SupportVerifier, PROTOCOL

CASES = [
    ("executed-meal", "I ate at home at thirteen hundred hours.", 1),
    ("offered-breakfast", "I ate breakfast at seven.", 0),
    ("reported-speech", "Ramesh told me that the river was the Ganges.", 1),
    ("speech-as-fact", "The river beside the bungalow is the Ganges.", 0),
    ("draft-as-sent", "I sent Marie a letter today.", 0),
    ("closing-cash", "At the day's close I had four hundred rupees.", 1),
    ("wrong-cash", "At the day's close I had one hundred rupees.", 0),
    ("philosophical-claim", "Freedom requires recognition.", 1),
]
EVIDENCE = """Date: 2026-10-03. Complete day.
[event e1] 13:00-13:30 at home: executed eat. No menu recorded.
[event e2] 07:00 at home: breakfast was laid out; consumption not recorded here.
[statement s1] 08:00 at home: Ramesh said to Hegel: "The river beside the bungalow is the Ganges." Unverified.
[work w1] 15:00 at home: draft letter "To Marie", addressed to Marie; not sent.
[event e3] 24:00: cash at day close: INR 400.
Statements prove words said, not the truth of their content. A draft is not sent.
Offers and purchases do not establish eating. Missing records prove no absence."""


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args=parser.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    with urllib.request.urlopen(args.url.rstrip("/")+"/lora-adapters",timeout=10) as response:
        if json.load(response) != []:
            raise RuntimeError("Protocol probe requires an adapter-free server")
    verifier=SupportVerifier(args.url)
    rows=[]
    for ident,sentence,expected in CASES:
        path=args.out/(ident+".json")
        if path.exists():
            raise RuntimeError("Refusing to overwrite a saved probe: "+str(path))
        with (args.out/(ident+'-exchanges.jsonl')).open('x') as raw:
            def audit(exchange):
                raw.write(json.dumps(exchange,ensure_ascii=False)+'\n');raw.flush()
            verifier.audit=audit
            try:
                row=dict(id=ident,expected_smoke_vote=expected,**verifier.score(sentence,EVIDENCE))
            except Exception as error:
                path.write_text(json.dumps(dict(id=ident,error=str(error),exchanges=verifier.exchanges),
                    ensure_ascii=False,indent=2)+'\n')
                raise
        path.write_text(json.dumps(row,ensure_ascii=False,indent=2)+"\n")
        rows.append(dict(id=ident,expected=expected,p_supported=row["probability"]))
        print(ident+": p(Yes)="+str(row["probability"]),flush=True)
    result=dict(protocol=PROTOCOL,rows=rows,calibrated=False,calibration_examples=0,
                diagnostic_only=True,runtime_enabled=False,training_performed=False)
    (args.out/"summary.json").write_text(json.dumps(result,indent=2)+"\n")
    print("Probability protocol probe complete; calibration and fidelity evaluation still pending.")


if __name__ == "__main__":
    main()
