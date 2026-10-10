#!/usr/bin/env python3
"""Audit the existing HF/Unsloth adapter against WSL llama.cpp; never train.

Run from the repository with the system Python. The HF worker uses the pinned
training environment only after the owned llama-server process has exited.
All prompts are replayed from a previous diagnostic, not added to training data.
"""
import argparse
import contextlib
import hashlib
import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import time
import traceback
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace


def stamp():
    return datetime.now(timezone.utc).isoformat()


def save(root, name, value):
    path = Path(root) / name
    path.parent.mkdir(parents=True, exist_ok=True)
    content = value if isinstance(value, str) else json.dumps(value, indent=2, ensure_ascii=False) + "\n"
    temp = path.with_name(path.name + ".tmp")
    with temp.open("w", encoding="utf-8") as f:
        f.write(content)
        f.flush()
        os.fsync(f.fileno())
    temp.replace(path)


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def cases_from(manifest):
    cases = [{"id": "state-question", "max_tokens": 128, "messages": [{"role": "user", "content":
        "What is the relation of the state to civil society? Two sentences."}]}]
    for kind in ("essay", "letter"):
        found = [r for r in manifest["requests"] if r["condition"] == "chat-draft-adapter"
                 and r["plan"]["kind"] == kind and r["seed"] == 1]
        if len(found) != 1:
            raise ValueError(f"Expected exactly one frozen {kind} request; found {len(found)}")
        cases.append({"id": kind, "max_tokens": 256, "messages": found[0]["payload"]["messages"],
                      "source_label": found[0]["label"]})
    return cases


def first_difference(a, b):
    return next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)) if len(a) != len(b) else None)


def compare_prompts(hf, llama):
    checks = []
    for case_id, item in hf.items():
        other = llama[case_id]
        checks.append({"case": case_id, "text_equal": item["prompt"] == other["prompt"],
                       "tokens_equal": item["tokens"] == other["tokens"],
                       "hf_tokens": len(item["tokens"]), "llama_tokens": len(other["tokens"]),
                       "first_text_difference": first_difference(item["prompt"], other["prompt"]),
                       "first_token_difference": first_difference(item["tokens"], other["tokens"])})
    return checks


def api(port, route, payload=None, timeout=360):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(f"http://127.0.0.1:{port}" + route, data=data,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"{route}: HTTP {e.code}: {e.read().decode(errors='replace')}") from e


def stop_owned(proc):
    if proc is None or proc.poll() is not None:
        return
    proc.send_signal(signal.SIGINT)
    try:
        proc.wait(timeout=30)
    except subprocess.TimeoutExpired:
        proc.terminate()
        try:
            proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=15)


def assert_idle(port):
    with socket.socket() as s:
        s.bind(("127.0.0.1", port))
    for p in Path("/proc").iterdir():
        if not p.name.isdigit():
            continue
        try:
            argv = (p / "cmdline").read_bytes().decode(errors="replace").split("\0")
        except (OSError, ProcessLookupError):
            continue
        if argv and (Path(argv[0]).name == "llama-server" or
                     len(argv) > 1 and Path(argv[1]).name == "train_hegel.py"):
            raise RuntimeError(f"Another model process is active, PID {p.name}; will not interrupt it")
    info = subprocess.check_output(["nvidia-smi", "--query-gpu=memory.used,utilization.gpu", "--format=csv,noheader,nounits"], text=True)
    used, util = map(int, info.splitlines()[0].split(","))
    if used > 2048 or util > 10:
        raise RuntimeError(f"GPU not idle enough for exclusive diagnostic: {info.strip()}")
    return info.strip()


def llama_stage(args, cases, env):
    command = [args.server, "-m", args.gguf, "--lora", args.adapter_gguf, "-ngl", "99", "-c", "16384",
               "--host", "127.0.0.1", "--port", str(args.port), "--alias", "hegel-parity"]
    save(args.out, "llama-command.json", command)
    proc = None
    prompts, results = {}, []
    with (args.out / "llama-server.log").open("w") as log:
        try:
            proc = subprocess.Popen(command, cwd=args.repo, env=env, stdout=log, stderr=subprocess.STDOUT)
            save(args.out, "owned-server.json", {"pid": proc.pid, "command": command})
            print(f"llama.cpp loading, PID {proc.pid}, isolated port {args.port}", flush=True)
            deadline = time.monotonic() + 300
            while time.monotonic() < deadline:
                if proc.poll() is not None:
                    raise RuntimeError(f"llama-server exited {proc.returncode}; see llama-server.log")
                try:
                    if api(args.port, "/health", timeout=3).get("status") == "ok":
                        break
                except (urllib.error.URLError, TimeoutError, OSError, RuntimeError):
                    pass
                time.sleep(2)
            else:
                raise RuntimeError("llama-server startup exceeded 300 seconds")
            adapters = api(args.port, "/lora-adapters")
            if len(adapters) != 1 or Path(adapters[0]["path"]).resolve() != Path(args.adapter_gguf).resolve() or adapters[0]["scale"] != 1:
                raise RuntimeError(f"Unexpected adapter inventory: {adapters!r}")
            save(args.out, "llama-health.json", {"health": api(args.port, "/health"), "adapters": adapters})
            save(args.out, "llama-props.json", api(args.port, "/props"))
            for case in cases:
                payload = {"messages": case["messages"], "chat_template_kwargs": {"enable_thinking": False}}
                prompt = api(args.port, "/apply-template", payload)["prompt"]
                tokens = api(args.port, "/tokenize", {"content": prompt, "add_special": False, "parse_special": True})["tokens"]
                prompts[case["id"]] = {"prompt": prompt, "tokens": tokens}
                save(args.out, "llama-prompts.json", prompts)
                for scale in (0, 1):
                    req = dict(payload, model="hegel-parity", max_tokens=case["max_tokens"], temperature=0,
                               seed=3407, repeat_penalty=1.0, dry_multiplier=0.0, cache_prompt=False,
                               lora=[{"id": 0, "scale": scale}], id_slot=0, logprobs=True, top_logprobs=5)
                    key = f"{case['id']}-lora{scale}"
                    save(args.out, f"requests/llama-{key}.json", req)
                    print(f"llama.cpp generating {key}", flush=True)
                    started = time.monotonic()
                    answer = api(args.port, "/v1/chat/completions", req)
                    save(args.out, f"responses/llama-{key}.json", answer)
                    slots = api(args.port, "/slots")
                    save(args.out, f"slots/{key}.json", slots)
                    slot = next(s for s in slots if s["id"] == 0)
                    if slot["params"].get("lora") != req["lora"]:
                        raise RuntimeError(f"Request-level LoRA scale was not confirmed for {key}")
                    choice = answer["choices"][0]
                    results.append({"case": case["id"], "adapter_scale": scale, "backend": "llama.cpp",
                                    "content": choice["message"].get("content") or "", "message": choice["message"],
                                    "finish_reason": choice["finish_reason"], "seconds": time.monotonic() - started,
                                    "usage": answer.get("usage"), "logprobs": choice.get("logprobs")})
                    save(args.out, "llama-results.json", results)
                    print(f"llama.cpp completed {key}: {choice['finish_reason']}", flush=True)
        finally:
            stop_owned(proc)
            save(args.out, "llama-stopped.json", {"stopped_at": stamp(), "returncode": proc.returncode if proc else None})
    return prompts, results


def hf_stage(args):
    # Same loader and saved training arguments as the completed run. No optimiser.
    sys.path.insert(0, str(args.repo))
    from pc.train_hegel import load_model, versions
    train_meta = json.loads((Path(args.adapter_dir) / "training.json").read_text())
    settings = SimpleNamespace(**train_meta["args"])
    settings.base = args.base
    model, tokenizer = load_model(settings, adapter=args.adapter_dir)
    from unsloth import FastModel
    import torch
    from transformers import AutoTokenizer
    from peft import get_peft_model_state_dict
    from safetensors.torch import load_file
    FastModel.for_inference(model)
    from gguf import GGUFReader
    metadata = {}
    for label, path in (("base", args.gguf), ("adapter", args.adapter_gguf)):
        reader = GGUFReader(path)
        selected = {name: field.contents() for name, field in reader.fields.items()
                    if name.startswith(("general.", "adapter.")) or
                    name in ("tokenizer.ggml.bos_token_id", "tokenizer.ggml.eos_token_id", "tokenizer.ggml.add_bos_token")}
        metadata[label] = {"fields": selected, "tensor_count": len(reader.tensors)}
        del reader
    save(args.out, "gguf-metadata.json", metadata)
    source = load_file(str(Path(args.adapter_dir) / "adapter_model.safetensors"))
    loaded = get_peft_model_state_dict(model)
    tensor_checks = {k: k in loaded and torch.equal(v, loaded[k].detach().cpu().to(v.dtype)) for k, v in source.items()}
    save(args.out, "adapter-tensor-check.json", {"source_tensors": len(source), "loaded_tensors": len(loaded), "checks": tensor_checks})
    if set(source) != set(loaded) or not all(tensor_checks.values()):
        raise RuntimeError("HF adapter tensor coverage or values differ from the saved adapter; see adapter-tensor-check.json")
    del source, loaded
    cases = json.loads((args.out / "cases.json").read_text())
    base_tok = AutoTokenizer.from_pretrained(args.base, local_files_only=True)
    saved_tok = AutoTokenizer.from_pretrained(args.adapter_dir, local_files_only=True)
    prompts, tokenizer_checks = {}, []
    for case in cases:
        kw = dict(tokenize=False, add_generation_prompt=True, enable_thinking=False)
        prompt = tokenizer.apply_chat_template(case["messages"], **kw)
        tokens = tokenizer(prompt, add_special_tokens=False)["input_ids"]
        prompts[case["id"]] = {"prompt": prompt, "tokens": tokens}
        for name, tok in (("base", base_tok), ("saved_adapter", saved_tok)):
            other = tok.apply_chat_template(case["messages"], **kw)
            tokenizer_checks.append({"case": case["id"], "tokenizer": name, "text_equal": prompt == other,
                                     "tokens_equal": tokens == tok(other, add_special_tokens=False)["input_ids"]})
    save(args.out, "hf-prompts.json", prompts)
    checks = compare_prompts(prompts, json.loads((args.out / "llama-prompts.json").read_text()))
    save(args.out, "prompt-parity.json", {"backend_checks": checks, "tokenizer_checks": tokenizer_checks})
    save(args.out, "hf-config.json", {"versions": versions(), "model_type": model.config.model_type,
        "generation_config": model.generation_config.to_dict(), "special_tokens": tokenizer.special_tokens_map,
        "eos_token_id": tokenizer.eos_token_id, "bos_token_id": tokenizer.bos_token_id,
        "pad_token_id": tokenizer.pad_token_id, "settings": vars(settings),
        "adapter_config": model.peft_config["default"].to_dict()})
    if not all(x["tokens_equal"] for x in checks + tokenizer_checks):
        raise RuntimeError("Rendered prompt tokens differ between training, saved tokenizer or llama.cpp; see prompt-parity.json. No automatic workaround.")
    print("Exact prompt token parity passed for all three cases; adapter tensors match.", flush=True)
    results, probe_scores = [], {}
    for case in cases:
        inputs = tokenizer(prompts[case["id"]]["prompt"], add_special_tokens=False, return_tensors="pt").to("cuda")
        if inputs["input_ids"].shape[1] + case["max_tokens"] > settings.seq_format:
            raise RuntimeError(f"Diagnostic exceeds training context for {case['id']}")
        for scale in (0, 1):
            key = f"{case['id']}-lora{scale}"
            print(f"HF generating {key}", flush=True)
            torch.manual_seed(3407)
            started = time.monotonic()
            context = model.disable_adapter() if scale == 0 else contextlib.nullcontext()
            with torch.inference_mode(), context:
                if case["id"] == "state-question":
                    probe = model.generate(**inputs, max_new_tokens=1, do_sample=False, use_cache=True,
                                           return_dict_in_generate=True, output_scores=True)
                    probe_scores[scale] = probe.scores[0][0].detach().float().cpu()
                    del probe
                output = model.generate(**inputs, max_new_tokens=case["max_tokens"], do_sample=False,
                                        repetition_penalty=1.0, use_cache=True, return_dict_in_generate=True, output_scores=False)
            tokens = output.sequences[0, inputs["input_ids"].shape[1]:].detach().cpu().tolist()
            result = {"case": case["id"], "adapter_scale": scale, "backend": "Unsloth HF",
                      "content": tokenizer.decode(tokens, skip_special_tokens=True),
                      "raw_decoded": tokenizer.decode(tokens, skip_special_tokens=False), "tokens": tokens,
                      "finish_reason": "length" if len(tokens) == case["max_tokens"] else "eos",
                      "seconds": time.monotonic() - started}
            results.append(result)
            save(args.out, f"responses/hf-{key}.json", result)
            save(args.out, "hf-results.json", results)
            print(f"HF completed {key}: {result['finish_reason']}, {len(tokens)} tokens", flush=True)
            del output
        del inputs
    finite = torch.isfinite(probe_scores[0]) & torch.isfinite(probe_scores[1])
    delta = (probe_scores[1][finite] - probe_scores[0][finite]).abs()
    effect = {"finite_logits_compared": int(finite.sum()), "max_abs_first_token_logit_change": float(delta.max()),
              "mean_abs_first_token_logit_change": float(delta.mean())}
    save(args.out, "hf-adapter-effect.json", effect)
    if effect["max_abs_first_token_logit_change"] == 0:
        raise RuntimeError("Adapter toggle made no measurable first-token logit change")
    print("HF backend check complete; adapter toggle changes logits.", flush=True)


def run(args):
    if args.out.exists():
        raise RuntimeError(f"Output directory already exists: {args.out}; choose a new run directory")
    assert_idle(args.port)
    args.out.mkdir(parents=True)
    status = {"status": "running", "started_at": stamp(), "training_started": False}
    save(args.out, "status.json", status)
    originals = [Path(args.adapter_dir) / "adapter_model.safetensors", Path(args.adapter_dir) / "adapter_config.json", Path(args.adapter_gguf)]
    hashes = {str(p): digest(p) for p in originals}
    try:
        cases = cases_from(json.loads(Path(args.manifest).read_text()))
        save(args.out, "cases.json", cases)
        save(args.out, "manifest.json", {"created_at": stamp(), "args": {k: str(v) if isinstance(v, Path) else v for k, v in vars(args).items()},
            "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=args.repo, text=True).strip(),
            "original_hashes": hashes, "script_sha256": digest(__file__),
            "sampling": "greedy, repetition penalty 1, thinking disabled; prose equality across quantizers is not required"})
        env = dict(os.environ)
        env["LD_LIBRARY_PATH"] = Path(args.ldpath).read_text().strip()
        save(args.out, "llama-version.txt", subprocess.check_output([args.server, "--version"], env=env, text=True, stderr=subprocess.STDOUT))
        config_files = [Path(args.base) / "config.json", Path(args.base) / "tokenizer_config.json",
                        Path(args.base) / "generation_config.json", Path(args.base) / ".cache/huggingface/download/config.json.metadata"]
        save(args.out, "base-configuration.json", {str(p): {"sha256": digest(p), "content": p.read_text()} for p in config_files if p.exists()})
        llama_stage(args, cases, env)
        print("Owned llama-server stopped. Starting the pinned training backend; no training will occur.", flush=True)
        cmd = [args.hf_python, "-u", str(Path(__file__).resolve()), *sys.argv[1:], "--hf-worker"]
        save(args.out, "hf-command.json", cmd)
        proc = None
        try:
            with (args.out / "hf.log").open("w") as log:
                proc = subprocess.Popen(cmd, cwd=args.repo, stdout=log, stderr=subprocess.STDOUT,
                    env=dict(os.environ, HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", TOKENIZERS_PARALLELISM="false"))
                save(args.out, "owned-hf.json", {"pid": proc.pid, "command": cmd})
                rc = proc.wait(timeout=args.hf_timeout)
            if rc:
                raise RuntimeError(f"HF worker exited {rc}:\n" + "\n".join((args.out / "hf.log").read_text().splitlines()[-30:]))
        finally:
            stop_owned(proc)
        lines = ["Backend parity comparison", "Greedy generation; outputs are not expected to match across different quantization backends.",
                 "Token parity and adapter effect must be reviewed alongside content. No quality verdict is automated."]
        for file in ("llama-results.json", "hf-results.json"):
            for item in json.loads((args.out / file).read_text()):
                lines += [f"\n--- {item['backend']} / {item['case']} / LoRA {item['adapter_scale']} / {item['finish_reason']} ---", item["content"]]
        save(args.out, "comparison.txt", "\n".join(lines) + "\n")
        status.update(status="complete", exit_code=0, requires_content_review=True)
    except BaseException as exc:
        save(args.out, "error.txt", traceback.format_exc())
        status.update(status="failed", exit_code=1, error=str(exc))
        raise
    finally:
        after = {str(p): digest(p) for p in originals}
        status.update(finished_at=stamp(), original_adapters_unchanged=hashes == after)
        if hashes != after:
            status.update(status="failed", exit_code=1, error="Original adapter hash changed")
        save(args.out, "status.json", status)
        save(args.out, "checksums.json", {str(p.relative_to(args.out)): digest(p) for p in args.out.rglob("*")
             if p.is_file() and p.name not in ("checksums.json", "run.log")})
        if args.mirror:
            args.mirror.mkdir(parents=True, exist_ok=True)
            for p in args.out.rglob("*"):
                if p.is_file() and p.name != "run.log":
                    dest = args.mirror / p.relative_to(args.out)
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(p, dest)
        print(f"Backend parity {status['status']}; exit {status.get('exit_code')}; originals unchanged: {hashes == after}", flush=True)
    return status["exit_code"]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("repo", "out"):
        p.add_argument("--" + name, type=Path, required=True)
    for name in ("manifest", "base", "adapter-dir", "adapter-gguf", "gguf", "server", "ldpath", "hf-python"):
        p.add_argument("--" + name, required=True)
    p.add_argument("--mirror", type=Path)
    p.add_argument("--port", type=int, default=18082)
    p.add_argument("--hf-timeout", type=int, default=1200)
    p.add_argument("--hf-worker", action="store_true", help=argparse.SUPPRESS)
    args = p.parse_args()
    if args.hf_worker:
        hf_stage(args)
        return 0
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
