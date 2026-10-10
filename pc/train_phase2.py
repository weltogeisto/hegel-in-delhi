#!/usr/bin/env python3
"""Bounded, separately saved phase-2 feasibility experiments. Never resumes an optimizer."""
import argparse
import hashlib
import json
import math
import shutil
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from pc.train_hegel import encode_chat, split_chat, load_model, versions, vram


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def dump(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def read_selected(data):
    data = Path(data)
    meta = json.loads((data / 'selection.json').read_text())
    if sha(data / 'accepted.jsonl') != meta['accepted_sha256']:
        raise ValueError('Selected data hash changed')
    parent = Path(meta['parent'])
    for name, expected in meta['parent_frozen_hashes'].items():
        if sha(parent / name) != expected:
            raise ValueError('Frozen parent changed: ' + name)
    rows = [json.loads(x) for x in (data / 'accepted.jsonl').read_text().splitlines() if x.strip()]
    provenance = {}
    for name in ['source-candidates.jsonl', 'qwen-candidates.jsonl']:
        for line in (parent/name).read_text().splitlines():
            item = json.loads(line)
            provenance[item['id']] = item
    if not rows or len({x['id'] for x in rows}) != len(rows):
        raise ValueError('Empty selection or duplicate IDs')
    seen = set()
    for x in rows:
        if x.get('review') != 'accepted':
            raise ValueError('Unreviewed row: ' + x['id'])
        m = x['messages']
        roles = [v['role'] for v in m]
        body = roles[1:] if roles[0] == 'system' else roles
        if body != ['user', 'assistant'] * (len(body) // 2) or not body:
            raise ValueError('Invalid turn sequence: ' + x['id'])
        if any(not isinstance(v.get('content'), str) or not v['content'].strip() for v in m):
            raise ValueError('Empty content: ' + x['id'])
        target = hashlib.sha256(m[-1]['content'].encode()).hexdigest()
        if target != x['target_sha256'] or target in seen:
            raise ValueError('Changed or duplicate target: ' + x['id'])
        original = provenance.get(x.get('parent_id', x['id']))
        if original is None:
            raise ValueError('Missing parent provenance: ' + x['id'])
        if x['category'] in {'authentic-writing', 'authentic-answer'}:
            source = original.get('source', {})
            text = source.get('text')
            if original.get('category') not in {'primary', 'letter-source'} or source.get('author') != 'Hegel' or not text:
                raise ValueError('Invalid authentic source: ' + x['id'])
            if hashlib.sha256(text.encode()).hexdigest() != source.get('sha256'):
                raise ValueError('Authentic source hash mismatch: ' + x['id'])
            if x['category'] == 'authentic-answer':
                if m[-1]['content'] != text:
                    raise ValueError('Authentic answer prose changed: ' + x['id'])
            else:
                wrapper = json.loads(m[-1]['content'])
                genre = 'letter' if original['category'] == 'letter-source' else 'essay'
                if (set(wrapper) != {'title','kind','to','continues','text'} or wrapper['text'] != text
                        or wrapper['kind'] != genre or wrapper['to'] != source.get('to') or wrapper['continues'] is not False):
                    raise ValueError('Authentic writing prose or wrapper changed: ' + x['id'])
        elif x['category'] == 'source-writing':
            wrapper = json.loads(m[-1]['content'])
            if wrapper['text'] != original['messages'][-1]['content'] or wrapper['kind'] != 'chapter' or not wrapper['continues']:
                raise ValueError('Primary prose changed in writing wrapper: ' + x['id'])
        elif m != original['messages']:
            raise ValueError('Original messages changed: ' + x['id'])
        seen.add(target)
    return rows, meta


def encode_selected(tok, rows, max_seq):
    encoded, audit = [], []
    for x in rows:
        prompt, completion = split_chat(tok, x['messages'])
        row = encode_chat(tok, x['messages'], max_seq)
        if row is None:
            raise ValueError('Overlength; no skipping or truncation: ' + x['id'])
        full = tok(prompt + completion, add_special_tokens=False)['input_ids']
        if full != row['input_ids']:
            raise ValueError('Token boundary differs from full rendering: ' + x['id'])
        p = len(tok(prompt, add_special_tokens=False)['input_ids'])
        if not p or p >= len(full) or row['labels'][:p] != [-100] * p or row['labels'][p:] != full[p:]:
            raise ValueError('Final-assistant mask failure: ' + x['id'])
        encoded.append(row)
        audit.append(dict(id=x['id'], category=x['category'], prompt_tokens=p,
                          target_tokens=len(full)-p, total_tokens=len(full), target_sha256=x['target_sha256']))
    counts = Counter(x['category'] for x in audit)
    targets = Counter()
    for x in audit:
        targets[x['category']] += x['target_tokens']
    report = dict(rows=len(rows), categories=dict(counts), target_tokens=dict(targets),
                  target_token_shares={k: round(v/sum(targets.values()), 5) for k, v in targets.items()},
                  total_target_tokens=sum(targets.values()), max_total_tokens=max(x['total_tokens'] for x in audit),
                  planned_updates=math.ceil(len(rows)/16), masked_final_assistant_only=True,
                  skipped=0, truncated=0, audit=audit)
    return encoded, report


def preflight(a):
    from transformers import AutoTokenizer
    rows, meta = read_selected(a.data)
    tok = AutoTokenizer.from_pretrained(a.base, local_files_only=True)
    _, report = encode_selected(tok, rows, a.max_seq)
    report.update(accepted_sha256=meta['accepted_sha256'], tokenizer_base=a.base,
                  template_sha256=hashlib.sha256(str(tok.chat_template).encode()).hexdigest())
    dump(Path(a.data)/'preflight.json', report)
    # A small complete rendered packet makes masking independently inspectable.
    packet = []
    for category in sorted(report['categories']):
        for x in [x for x in rows if x['category'] == category][:2]:
            p, c = split_chat(tok, x['messages'])
            packet.append(dict(id=x['id'], masked_prompt=p, supervised_completion=c))
    dump(Path(a.data)/'rendered-mask-samples.json', packet)
    print(json.dumps({k:v for k,v in report.items() if k != 'audit'}, indent=2), flush=True)
    print('preflight ok: every selected row fits; only final assistant tokens supervised', flush=True)


def train(a):
    started = time.monotonic()
    rows, meta = read_selected(a.data)
    if meta.get('training', {}).get('epochs', 1) != a.epochs:
        raise ValueError('Epoch count differs from selected experiment')
    proof = json.loads((Path(a.data)/'preflight.json').read_text())
    if proof['accepted_sha256'] != meta['accepted_sha256'] or proof['tokenizer_base'] != a.base:
        raise ValueError('Missing or stale token preflight')
    out = Path(a.out).resolve()
    protected = (REPO/'pc/out/hegel-lora').resolve()
    if out == protected or protected in out.parents or out.exists():
        raise ValueError('Output must be new and separate from the original adapter')
    # Refuse competing GPU work, using the established server/process/GPU guard.
    from pc.check_backend_parity import assert_idle
    assert_idle(18089)
    warm = Path(a.warmstart).resolve()
    cfg = json.loads((warm/'adapter_config.json').read_text())
    if cfg['r'] != 16 or cfg['lora_alpha'] != 32:
        raise ValueError('Warmstart rank/alpha differs from planned pilot')
    final_gguf = REPO/'pc/out/hegel-lora.gguf'
    originals = {str(p): sha(p) for p in [warm/'adapter_model.safetensors', warm/'adapter_config.json', final_gguf,
                                        protected/'adapter_model.safetensors']}
    out.mkdir(parents=True)
    copied = out/'warmstart'
    copied.mkdir()
    for name in ['adapter_model.safetensors', 'adapter_config.json', 'README.md']:
        if (warm/name).exists():
            shutil.copyfile(warm/name, copied/name)
    if sha(copied/'adapter_model.safetensors') != originals[str(warm/'adapter_model.safetensors')]:
        raise ValueError('Warmstart copy mismatch')
    dump(out/'inputs.json', dict(data=str(Path(a.data).resolve()), data_sha256=meta['accepted_sha256'],
        original_hashes=originals, script_sha256=sha(__file__), trainer_sha256=sha(REPO/'pc/train_hegel.py'),
        runtime_diff=subprocess.check_output(['git','diff'],cwd=REPO,text=True),
        versions=versions(), settings=vars(a), fresh_optimizer=True, resume_from_checkpoint=False))
    args = SimpleNamespace(base=a.base, seq_corpus=a.max_seq, seq_format=a.max_seq, bf16=False,
        text_only=True, loss_target_gib=.125, rank=16, alpha=32, seed=1831)
    print('Loading separate corpus-only warmstart; fresh optimizer; original final adapter preserved', flush=True)
    model, tokenizer = load_model(args, adapter=copied)
    tok = getattr(tokenizer,'tokenizer',tokenizer)
    encoded, report = encode_selected(tok, rows, a.max_seq)
    if report['audit'] != proof['audit']:
        raise ValueError('Training tokenizer differs from CPU preflight')
    from peft import get_peft_model_state_dict
    from safetensors.torch import load_file
    import torch
    source = load_file(str(copied/'adapter_model.safetensors'))
    loaded = get_peft_model_state_dict(model)
    if set(source) != set(loaded) or any(not torch.equal(v,loaded[k].detach().cpu().to(v.dtype)) for k,v in source.items()):
        raise ValueError('Warmstart tensors not loaded exactly')
    trainable = [(k,p.numel()) for k,p in model.named_parameters() if p.requires_grad]
    if not trainable or any('lora_' not in k for k,_ in trainable):
        raise ValueError('Trainable parameters are not exclusively LoRA')
    dump(out/'load-audit.json', dict(exact_tensor_matches=len(source), trainable_tensors=len(trainable),
        trainable_parameters=sum(n for _,n in trainable), only_lora_trainable=True, token_audit=report))
    del loaded, source
    import gc
    gc.collect(); torch.cuda.empty_cache()
    if time.monotonic()-started >= a.minutes*60:
        raise RuntimeError('Time budget exhausted during preflight/loading; no updates started')
    from datasets import Dataset
    from transformers import Trainer, TrainingArguments, TrainerCallback, DataCollatorForSeq2Seq
    deadline = started+a.minutes*60
    class Budget(TrainerCallback):
        def on_step_end(self,args,state,control,**kw):
            if time.monotonic() >= deadline:
                control.should_save=True
                control.should_training_stop=True
                print('Time budget reached: checkpoint and stop at optimizer boundary',flush=True)
        def on_log(self,args,state,control,logs=None,**kw):
            if logs and 'loss' in logs:
                if not math.isfinite(logs['loss']):
                    raise RuntimeError('Nonfinite training loss; stop pilot')
                entry=dict(step=state.global_step, elapsed_minutes=round((time.monotonic()-started)/60,2),**logs)
                print('PILOT '+json.dumps(entry)+'; '+vram(),flush=True)
                # Append exact trainer metrics; no loss-as-quality verdict.
                with (out/'metrics.jsonl').open('a') as f: f.write(json.dumps(entry)+'\n')
    targs=TrainingArguments(output_dir=str(out/'checkpoints'), per_device_train_batch_size=1,
        gradient_accumulation_steps=16, learning_rate=5e-5, num_train_epochs=a.epochs,
        lr_scheduler_type='cosine', warmup_steps=1, weight_decay=0., max_grad_norm=1.,
        optim='adamw_8bit',bf16=True,logging_steps=1,save_strategy='steps',save_steps=1,
        save_total_limit=3,report_to='none',seed=1831,remove_unused_columns=False,disable_tqdm=True)
    trainer=Trainer(model=model,args=targs,train_dataset=Dataset.from_list(encoded),processing_class=tok,
        data_collator=DataCollatorForSeq2Seq(tokenizer=tok,padding=True,label_pad_token_id=-100),callbacks=[Budget()])
    if trainer.optimizer is not None:
        raise ValueError('Optimizer unexpectedly pre-existing')
    print(f'TRAINING START: {len(rows)} rows, {report["planned_updates"] * a.epochs} optimizer updates, {a.epochs} epochs, 90-minute cooperative deadline including load',flush=True)
    torch.cuda.reset_peak_memory_stats()
    result=trainer.train(resume_from_checkpoint=None)
    model.save_pretrained(str(out/'adapter'))
    tok.save_pretrained(str(out/'adapter'))
    before = load_file(str(copied/'adapter_model.safetensors'))
    after = load_file(str(out/'adapter/adapter_model.safetensors'))
    if set(before) != set(after) or any(not torch.isfinite(v).all() for v in after.values()):
        raise ValueError('Saved adapter tensor coverage or finiteness failed')
    changed_tensors = sum(not torch.equal(v,after[k].to(v.dtype)) for k,v in before.items())
    if trainer.state.global_step and not changed_tensors:
        raise ValueError('No adapter tensor changed despite optimizer updates')
    changed = [p for p,h in originals.items() if sha(p)!=h]
    if changed: raise ValueError('Protected inputs changed: '+str(changed))
    dump(out/'complete.json',dict(status='pilot complete; evaluation required before adoption',
        optimizer_updates=trainer.state.global_step,planned_updates=report['planned_updates'] * a.epochs,
        stopped_at_deadline=trainer.state.global_step<report['planned_updates'] * a.epochs,
        minutes_including_load=round((time.monotonic()-started)/60,2),metrics=result.metrics,
        original_hashes_verified=True,changed_adapter_tensors=changed_tensors,
        adapter=str(out/'adapter'),holdout_run=False))
    print('done: pilot adapter saved separately; original adapters unchanged; evaluation pending',flush=True)


def main():
    p=argparse.ArgumentParser(); p.add_argument('--data',required=True);p.add_argument('--base',default='/home/ai/models/qwen-base')
    p.add_argument('--preflight',action='store_true');p.add_argument('--max-seq',type=int,default=4096)
    p.add_argument('--warmstart',default=str(REPO/'pc/out/hegel-lora/work/phase1-adapter'))
    p.add_argument('--out');p.add_argument('--minutes',type=int,default=90)
    p.add_argument('--epochs',type=int,choices=[1,3],default=1)
    a=p.parse_args()
    if a.minutes!=90 or a.max_seq!=4096: p.error('This reviewed pilot fixes 90 minutes and 4096 tokens')
    if a.preflight: preflight(a)
    elif not a.out: p.error('--out required for training')
    else: train(a)


if __name__=='__main__': main()
