"""Training 3 launcher, reusing Training 1's owned processes and restoration.

Build and review this code without loading a model. A reviewed, immutable intent
and an actual passed daytime rehearsal are required for a real training run.
The two serve checks prove conversion/routing only; T39 comparison stays pending.
"""
import argparse
import contextlib
import fcntl
import hashlib
import io
import json
import math
import os
from pathlib import Path
import signal
import statistics
import subprocess
import sys
import time
import traceback
import urllib.error
from zoneinfo import ZoneInfo
from datetime import datetime

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from pc import run_training1 as lifecycle
from pc import decision_dpo_data as preparation

VERSION = "training3-dpo-1"


def load(path, expected=None):
    path = Path(path).resolve()
    if expected and lifecycle.filehash(path) != expected:
        raise RuntimeError("intent changed")
    data = lifecycle.read(path)
    if data.get("version") != VERSION or path != Path(data["run_dir"]) / "INTENT.json":
        raise ValueError("Training 3 intent must remain at its original path")
    if Path(data["source_dir"]).resolve() != REPO or data["recipe"] != preparation.RECIPE:
        raise ValueError("source or DPO recipe differs")
    if data["trial_port"] == 8082 or not 1024 <= data["trial_port"] <= 65535:
        raise ValueError("adapter uses a separate loopback port")
    if not data["no_automatic_adoption"] or not data["no_restarts"]:
        raise ValueError("restart/adoption are not permitted")
    if data["dry_run"]:
        if (data["steps"], data["eval_steps"], data["selected_ids"]) != (3, 2, None):
            raise ValueError("rehearsal schedule differs")
    elif data["steps"] != preparation.step_count(len(data["selected_ids"])) or len(data["selected_ids"]) < 200:
        raise ValueError("real run is one epoch over its frozen roster")
    return data


def verify(data):
    if subprocess.check_output(["git", "-C", str(REPO), "rev-parse", "HEAD"], text=True).strip() != data["commit"]:
        raise RuntimeError("reviewed source commit changed")
    for name, expected in data["frozen_files"].items():
        lifecycle.verify_frozen_file(data, name, expected)


def validate_rehearsal(config):
    path = Path(config["passed_rehearsal"])
    verdict, end = lifecycle.read(path), lifecycle.read(path.parent / "RUN-END.json")
    previous = load(path.parent / "INTENT.json")
    if (not previous["dry_run"] or verdict.get("passed") is not True
            or end["status"] != "DPO_REHEARSAL_PASSED"
            or verdict["intent_sha256"] != lifecycle.filehash(path.parent / "INTENT.json")):
        raise ValueError("a genuinely completed, passed rehearsal is required")
    for key in ("base_model", "base_gguf", "candidates", "pairs", "pair_stats", "length_cap", "converter"):
        if config[key] != previous[key]:
            raise ValueError("rehearsal input differs: " + key)
    actual_commit = subprocess.check_output(["git", "-C", str(REPO), "rev-parse", "HEAD"], text=True).strip()
    if previous["commit"] != actual_commit:
        raise ValueError("source changed since the rehearsal; review and rehearse the new source")
    # Verify the preserved original, including actual conversion and restoration.
    for filename, key in (("training/training.json", "training_sha256"),
                          ("PHASE-C-END.json", "serve_sha256"),
                          ("DPO-C-TIMING.json", "c_timing_sha256"),
                          ("RESTORATION.json", "restoration_sha256")):
        if lifecycle.filehash(path.parent / filename) != verdict[key]:
            raise ValueError("rehearsal result changed: " + filename)
    return previous, verdict, lifecycle.read(path.parent / "TRAINING-ROSTER.json")



REHEARSED_FILES = ("candidates", "pairs", "pair_stats", "converter", "base_gguf")
REHEARSED_TREES = ("base_model", "converter_base")


def rehearsed_inputs(data):
    """The frozen hashes of what the rehearsal exercised: its data, model, tokenizer and converter."""
    files = {str(Path(data[k]).resolve()) for k in REHEARSED_FILES} | {str(Path(data["original"]["launcher"]).resolve())}
    trees = [Path(data[k]).resolve() for k in REHEARSED_TREES] + [Path(data["converter"]).resolve().parent]
    return {name: value for name, value in data["frozen_files"].items()
            if name in files or any(tree in Path(name).parents for tree in trees)}


def same_as_rehearsal(previous, data):
    """A real run accepts its rehearsal only for the same bytes, not merely the same paths."""
    if data["pair_provenance"] != previous["pair_provenance"]:
        raise ValueError("candidate or pair data changed since the rehearsal; rehearse again")
    then, now = rehearsed_inputs(previous), rehearsed_inputs(data)
    changed = sorted(name for name in then.keys() | now.keys() if then.get(name) != now.get(name))
    if changed:
        raise ValueError("rehearsal inputs changed at the same paths: " + ", ".join(changed[:5]))


def shadow_head(repo):
    argv = ["git", "-C", str(repo)]
    head = subprocess.check_output(argv + ["ls-remote", "--exit-code", "origin", "refs/heads/shadow"],
                                   text=True, timeout=30).split()[0]
    subprocess.run(argv + ["fetch", "--no-tags", "--no-write-fetch-head", "origin", head],
                   check=True, capture_output=True, timeout=30)
    return head


def natural_restoration(repo, baseline, restored_at):
    """Native append-only history evidence; never call or wake the live mind."""
    head = shadow_head(repo)
    argv = ["git", "-C", str(repo)]
    def git(*args):
        return subprocess.check_output(argv + list(args), timeout=30)
    subprocess.run(argv + ["merge-base", "--is-ancestor", baseline, head],
                   check=True, capture_output=True, timeout=30)
    previous = baseline
    import re
    for line in git("rev-list", "--parents", "--first-parent", "--reverse", baseline + ".." + head).decode().splitlines():
        parts = line.split()
        if len(parts) != 2 or parts[1] != previous:
            raise RuntimeError("shadow history skipped or changed a parent")
        commit, parent = parts
        previous = commit
        stamp = int(git("show", "-s", "--format=%ct", commit).decode())
        if stamp > time.time() + 1:
            raise RuntimeError("future-dated shadow commit")
        if stamp < lifecycle.epoch(restored_at):
            continue
        for name in git("diff", "--name-only", parent, commit, "--", "docs/days").decode().splitlines():
            if not re.fullmatch(r"docs/days/\d{4}-\d{2}-\d{2}\.json", name):
                continue
            raw = git("show", commit + ":" + name)
            child = json.loads(raw)
            old = subprocess.run(argv + ["show", parent + ":" + name], capture_output=True, timeout=30)
            prefix = json.loads(old.stdout)["steps"] if old.returncode == 0 else []
            if child["steps"][:len(prefix)] != prefix:
                raise RuntimeError("natural day prefix changed")
            for step in child["steps"][len(prefix):]:
                if step.get("decision") and step.get("mind", {}).get("source") == "mind":
                    return dict(head=head, commit=commit, parent=parent, commit_unix=stamp,
                                day=name, day_sha256=lifecycle.digest(raw), time=step["t"],
                                mind=step["mind"], no_forced_tick=True)
    raise RuntimeError("no natural mind decision since restoration; wait without forcing a tick")

def create(config, root, restore_by, rehearsal):
    root = Path(root).resolve()
    if root.exists():
        raise FileExistsError("new job required; preserve prior evidence")
    deadline = lifecycle.epoch(restore_by)
    local = datetime.fromtimestamp(deadline, ZoneInfo("Europe/Berlin"))
    today = datetime.now(ZoneInfo("Europe/Berlin"))
    if local.date() != today.date() or not (9 <= today.hour < 20) or (local.hour, local.minute, local.second) > (20, 0, 0):
        raise ValueError("a same-day window ending no later than 20:00 Berlin is required")
    if deadline <= time.time() + lifecycle.RESTORE_RESERVE:
        raise ValueError("no remaining compute window")
    if subprocess.check_output(["git", "-C", str(REPO), "status", "--porcelain"]):
        raise RuntimeError("reviewed source checkout must be clean")
    pairs, provenance = preparation.validated_pairs(config["candidates"], config["pairs"], config["pair_stats"])
    data = dict(config, version=VERSION, source_dir=str(REPO), run_dir=str(root), dry_run=bool(rehearsal),
                recipe=preparation.RECIPE, restore_by=restore_by, phase_b_cap_s=25200,
                no_restarts=True, no_automatic_adoption=True, written_utc=lifecycle.utc(),
                selected_ids=None, pair_provenance=provenance)
    previous = None
    if not Path(data["shadow_repo"]).is_absolute():
        raise ValueError("native shadow repository path required")
    if rehearsal:
        data.update(steps=3, eval_steps=2, shadow_anchor=shadow_head(data["shadow_repo"]))
        if not all(math.isfinite(data["estimate"][k]) and data["estimate"][k] > 0
                   for k in ("step_seconds", "evaluation_seconds", "phase_c_seconds")):
            raise ValueError("bounded rehearsal estimates required")
    else:
        previous, verdict, roster = validate_rehearsal(config)
        if data["pair_provenance"] != previous["pair_provenance"]:
            raise ValueError("candidate or pair data changed since the rehearsal; rehearse again")
        restored = lifecycle.read(Path(data["passed_rehearsal"]).parent/"RESTORATION.json")
        data["natural_recovery"] = natural_restoration(data["shadow_repo"], previous["shadow_anchor"], restored["utc"])
        data["shadow_anchor"] = data["natural_recovery"]["head"]
        data["estimate"] = verdict["estimate"]
        availability = min(deadline-time.time()-lifecycle.RESTORE_RESERVE, 25200) - verdict["loaded_seconds"]
        selected, receipt = preparation.choose_roster(
            [dict(id=ident) for ident in roster["ids"]], availability, verdict["measured"])
        data["selected_ids"] = [r["id"] for r in selected]
        data["selection"] = receipt
        data["steps"] = preparation.step_count(len(selected))
        data["eval_steps"] = data["steps"]
        data["reference_estimate"] = verdict["reference_seconds_per_pair"] * len(selected) * 1.15
        data["loaded_estimate"] = verdict["loaded_seconds"] * 1.15
    data["commit"] = subprocess.check_output(["git", "-C", str(REPO), "rev-parse", "HEAD"], text=True).strip()
    paths = [REPO / n for n in subprocess.check_output(["git","-C",str(REPO),"ls-files","-z"]).decode().split("\0") if n]
    paths += [Path(data[k]) for k in ("candidates","pairs","pair_stats","converter","base_gguf","power_receipt")]
    paths += [Path(data["original"]["launcher"])]
    for key in ("base_model", "converter_base"):
        paths += [p for p in Path(data[key]).rglob("*") if p.is_file()]
    paths += [p for p in Path(data["converter"]).parent.rglob("*.py") if ".git" not in p.parts]
    if previous:
        path = Path(data["passed_rehearsal"])
        paths += [path, path.parent/"INTENT.json", path.parent/"RUN-END.json",
                  path.parent/"TRAINING-ROSTER.json", path.parent/"RESTORATION.json",
                  path.parent/"training/training.json", path.parent/"PHASE-C-END.json",path.parent/"DPO-C-TIMING.json"]
    if any(root == p.resolve() or root in p.resolve().parents for p in paths):
        raise ValueError("output overlaps an input")
    for base in (REPO, Path(data["base_model"]), Path(data["converter_base"])):
        if root == base.resolve() or base.resolve() in root.parents:
            raise ValueError("job output is inside a source/model input directory")
    lifecycle.freeze_inputs(data, paths, previous)
    if previous:
        same_as_rehearsal(previous, data)
    data["power"] = lifecycle.read(data["power_state"])
    receipt = lifecycle.read(data["power_receipt"])
    if (data["power"].get("pendingUtc") or receipt.get("status") != "VERIFIED"
            or receipt["state"]["lastRequestId"] != data["power"]["lastRequestId"]):
        raise ValueError("normal power deadline is unverified or shutdown is pending")
    if lifecycle.epoch(data["power"]["deadlineUtc"]) < deadline + 900:
        raise ValueError("existing power cutoff lacks restoration margin; no power change")
    data["linux_boot"] = Path("/proc/sys/kernel/random/boot_id").read_text().strip()
    root.mkdir()
    lifecycle.write_new(root/"INTENT.json",data)
    load(root/"INTENT.json")
    return root/"INTENT.json"


class Backend(lifecycle.Backend):
    def __init__(self, path):
        # Training 1's load_intent enforces its own fixed 517-step recipe. Never
        # forge that intent or mutate its globals to run a different experiment.
        self.path = Path(path).resolve()
        self.hash = lifecycle.filehash(self.path)
        self.data = load(self.path, self.hash)
        self.root = Path(self.data["run_dir"])
        self.paths = lifecycle.intent_paths(self.data)
        self.children, self.startlock, self.paused = [], None, False
        self.last_sample, self.server = 0, None

    def check_time(self, end=None, reserve=0):
        load(self.path, self.hash)
        cutoff = lifecycle.deadline(self.data)
        if time.time() + reserve >= min(cutoff, end or cutoff):
            raise TimeoutError("compute deadline; preserve restoration reserve")
        return cutoff

    def worker(self, name, end):
        python = "/usr/bin/python3" if name == "admission" else self.data["python"]
        child = lifecycle.OwnedChild(self, name, [python, "-B", str(Path(__file__).resolve()),
                    "--intent", str(self.path), "--intent-sha256", self.hash, "--worker", name])
        child.wait(end, training=name == "train")
        return child

    def admission(self):
        self.worker("admission", self.check_time())

    def phase_b(self):
        estimate = self.data["estimate"]
        projected = lifecycle.projection(estimate["step_seconds"], estimate["evaluation_seconds"],
                                         self.data["steps"], self.data["eval_steps"])
        projected += self.data.get("reference_estimate", 1800) + self.data.get("loaded_estimate", 300)
        end = min(self.check_time(), time.time() + self.data["phase_b_cap_s"])
        if time.time() + projected > end:
            raise RuntimeError("measured training projection cannot fit")
        lifecycle.write_new(self.root/"B-BUDGET.json",dict(utc=lifecycle.utc(),phase_b_end=end,
                                                        projected_seconds=projected))
        self.worker("train", end)
        report = lifecycle.read(self.paths["training"]/"training.json")
        if report["steps"] != self.data["steps"]:
            raise RuntimeError("training ended before its frozen schedule")
        lifecycle.write_new(self.root/"PHASE-B-END.json",
                            dict(steps=report["steps"],utc=lifecycle.utc(),
                                 report_sha256=lifecycle.filehash(self.paths["training"]/"training.json")))
        if self.data["dry_run"]:
            self.sample_memory(force=True)

    def phase_c(self):
        began = time.monotonic()
        super().phase_c()
        lifecycle.write_new(self.root/"DPO-C-TIMING.json",dict(utc=lifecycle.utc(),seconds=time.monotonic()-began))

    def sheets(self):
        # The later T39 comparison needs its frozen manifest/better arm/blind
        # audit. This smoke check never creates or releases human score sheets.
        return None


def serve_checks(data, intent, expected):
    from tools.recorded_llama import RecordedClient, TransportError
    from world import contract
    root = Path(data["run_dir"])
    server = lifecycle.read(root/"ADAPTER-READY.json")["identity"]
    pairs, _ = preparation.validated_pairs(data["candidates"],data["pairs"],data["pair_stats"])
    first_id = lifecycle.read(root/"TRAINING-ROSTER.json")["ids"][0]
    sample = next(r for r in pairs if r["id"] == first_id)
    candidates = preparation.read_rows(Path(data["candidates"]).read_bytes())
    candidate = next(r for r in candidates if r["id"] == first_id)
    # Rehearsal output is a decision from the actual training corpus, never a
    # human-authored substitute and never a held T39 decision.
    schema = candidate["decision_schema"]
    number = 0
    class Response:
        def __init__(self, raw, status): self.raw,self.status=raw,status
        def read(self): return self.raw
        def __enter__(self): return self
        def __exit__(self,*a): return False

    def opener(request, timeout):
        nonlocal number
        load(intent,expected)
        if (time.time()+lifecycle.HTTP_TIMEOUT >= lifecycle.deadline(data)
                or not lifecycle.same_process(server)):
            raise RuntimeError("owned adapter identity or remaining time differs")
        number += 1
        rid = str(number)
        def log(kind, **values):
            with (root/"http-windows.jsonl").open("ab") as f:
                f.write((json.dumps(dict(event=kind,request=rid,unix=time.time(),**values))+"\n").encode())
                f.flush();os.fsync(f.fileno())
        log("http_begin",deadline=time.time()+lifecycle.HTTP_TIMEOUT,
            payload_sha256=lifecycle.digest(request.data))
        try:
            status,raw = lifecycle.http(data["trial_port"],"/v1/chat/completions",request.data,lifecycle.HTTP_TIMEOUT)
        except BaseException as exc:
            lifecycle.write_new(root/"unknown"/(rid+".partial.bin"),getattr(exc,"partial",b""),True)
            lifecycle.write_new(root/"unknown"/(rid+".json"),dict(error=repr(exc),no_resend=True))
            raise TransportError("unknown response; no resend") from exc
        log("http_end",status=status,response_sha256=lifecycle.digest(raw))
        if status!=200:
            raise urllib.error.HTTPError(request.full_url,status,"HTTP error",{},io.BytesIO(raw))
        return Response(raw,status)

    cases=[]
    for scale in (1,0):
        client=RecordedClient("http://127.0.0.1:"+str(data["trial_port"]),
            root/"benchmark"/("scale-"+str(scale)),timeout=lifecycle.HTTP_TIMEOUT,
            slot=1,lora=[dict(id=0,scale=scale)],model=data["model_alias"],opener=opener)
        payload=dict(model=data["model_alias"], stream=False, messages=sample["prompt"],max_tokens=700,temperature=.7,seed=1831,
                     chat_template_kwargs={"enable_thinking":False},
                     response_format={"type":"json_schema","json_schema":dict(name="answer",schema=schema)})
        response=client.post("decision",payload)
        raw=response["choices"][0]["message"].get("content") or ""
        answer=contract.extract_json(raw)
        errors,_=contract.check_shape(answer)
        if errors:
            raise RuntimeError("scale "+str(scale)+" did not produce a valid decision shape")
        cases.append(dict(scale=scale,pair=sample["id"],answer=answer))
    lifecycle.write_new(root/"PHASE-C-END.json",dict(status="TWO_DECISION_SERVE_CHECKS",cases=cases,
                        utc=lifecycle.utc(),quality_test_pending=True,automatic_adoption=False))


def verdict(data, result):
    root=Path(data["run_dir"])
    log=lifecycle.rows(root/"timing.jsonl")
    steps=[x for x in log if x["event"]=="step"]
    evaluations=[x for x in log if x["event"]=="evaluate_end"]
    before=[x["seconds"] for x in steps if x["step"]<=2]
    after=[x["seconds"] for x in steps if x["step"]>2]
    if len(steps)!=3 or len(before)!=2 or len(after)!=1 or not evaluations:
        raise RuntimeError("incomplete rehearsal timing")
    training=lifecycle.read(root/"training/training.json")
    serve=lifecycle.read(root/"PHASE-C-END.json")
    ratio=max(after)/statistics.median(before)
    gates=dict(post_eval_speed=ratio<=1.5,
        within_card=max(x["peak_reserved"] for x in steps)<lifecycle.CARD_BYTES,
        two_scales=serve["status"]=="TWO_DECISION_SERVE_CHECKS" and [c["scale"] for c in serve["cases"]]==[1,0],
        restored=result["restoration"]["status"]=="ORIGINAL_QWEN_AND_TIMER_RESTORED",
        route=result["restoration"].get("pi_probe",{}).get("status")=="PI_HEALTH_AND_ONE_TOKEN_VERIFIED")
    step=statistics.median(x["seconds"] for x in steps)
    refs=training["reference_seconds"]/training["pairs"]
    evaluation=max(x["seconds"] for x in evaluations)
    actual_c=lifecycle.read(root/"DPO-C-TIMING.json")["seconds"]
    if not math.isfinite(actual_c) or actual_c <= 0:raise RuntimeError("missing measured conversion/serve time")
    measured=dict(seconds_per_pair=step/8+refs,evaluation_seconds=evaluation,
                  conversion_and_test_seconds=actual_c*1.15)
    return dict(passed=all(gates.values()),gates=gates,utc=lifecycle.utc(),
        intent_sha256=lifecycle.filehash(root/"INTENT.json"),
        training_sha256=lifecycle.filehash(root/"training/training.json"),
        serve_sha256=lifecycle.filehash(root/"PHASE-C-END.json"),
        c_timing_sha256=lifecycle.filehash(root/"DPO-C-TIMING.json"),
        restoration_sha256=lifecycle.filehash(root/"RESTORATION.json"),
        post_eval_ratio=ratio,reference_seconds_per_pair=refs,loaded_seconds=training["loaded_seconds"],
        measured=measured,estimate=dict(step_seconds=step,evaluation_seconds=evaluation,
              phase_c_seconds=actual_c*1.15,rehearsal_c_seconds=actual_c*1.15))


def detach(data,path,expected):
    root=Path(data["run_dir"])
    if (root/"RUN-BEGIN.json").exists() or (root/"DETACHED-LAUNCH.json").exists():
        raise RuntimeError("already launched; reconcile instead of restarting")
    argv=["/usr/bin/python3","-B",str(Path(__file__).resolve()),"--intent",str(path),"--intent-sha256",expected]
    lifecycle.write_new(root/"DETACHED-LAUNCH.json",dict(utc=lifecycle.utc(),argv=argv,intent_sha256=expected))
    with (root/"launcher.log").open("xb") as log:
        child=subprocess.Popen(argv,cwd=data["source_dir"],stdin=subprocess.DEVNULL,
                               stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    lifecycle.write_new(root/"DETACHED-PROCESS.json",dict(identity=lifecycle.identity(child.pid),new_session=True,
                                                        stdin_null=True,no_parent_death_signal=True))
    return 0


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--write-intent",type=Path);p.add_argument("--restore-by")
    p.add_argument("--rehearsal",action="store_true");p.add_argument("--detach",action="store_true")
    p.add_argument("--intent",type=Path);p.add_argument("--intent-sha256")
    p.add_argument("--worker",choices=("admission","train","verify-conversion","benchmark"))
    a=p.parse_args(argv)
    if a.write_intent:
        if not a.restore_by or a.intent or a.worker or a.detach:p.error("new intent needs restore-by and JSON config on stdin")
        path=create(json.load(sys.stdin),a.write_intent,a.restore_by,a.rehearsal)
        print(json.dumps(dict(intent=str(path),sha256=lifecycle.filehash(path))));return 0
    if not a.intent or not a.intent_sha256:p.error("pinned intent required")
    data=load(a.intent,a.intent_sha256)
    if a.worker:
        if a.worker=="admission":lifecycle.gpu_admission(Path(data["run_dir"])/"admission")
        elif a.worker=="verify-conversion":lifecycle.verify_conversion(data)
        elif a.worker=="benchmark":serve_checks(data,a.intent,a.intent_sha256)
        else:
            from pc.decision_dpo_worker import train
            root=Path(data["run_dir"])
            end=lifecycle.read(root/"B-BUDGET.json")["phase_b_end"]
            def check_time():
                load(a.intent,a.intent_sha256)
                if time.time()+120>=min(end,lifecycle.deadline(data)):raise TimeoutError("training deadline")
            train(data,lambda: load(a.intent,a.intent_sha256),check_time)
        return 0
    verify(data)
    if a.detach:return detach(data,a.intent,a.intent_sha256)
    root=Path(data["run_dir"])
    with (root/"run.lock").open("a+") as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        lifecycle.write_new(root/"RUN-BEGIN.json",dict(utc=lifecycle.utc(),pid=os.getpid(),intent_sha256=a.intent_sha256))
        def interrupted(sig,frame):raise RuntimeError("interrupted; restore and never restart")
        for sig in (signal.SIGINT,signal.SIGTERM,signal.SIGHUP):signal.signal(sig,interrupted)
        result=lifecycle.run_pipeline(Backend(a.intent))
        if result["status"]=="B_AND_C_COMPLETE":
            if data["dry_run"]:
                try:
                    report=verdict(data,result)
                    lifecycle.write_new(root/"REHEARSAL.json",report)
                    result["status"]="DPO_REHEARSAL_PASSED" if report["passed"] else "DPO_REHEARSAL_FAILED"
                except BaseException as exc:result.update(status="DPO_REHEARSAL_FAILED",error=repr(exc))
            else:result["status"]="DPO_TRAINED_SMOKE_VERIFIED_T39_TEST_PENDING"
        result["finished_utc"]=lifecycle.utc()
        lifecycle.write_new(root/"RUN-END.json",result)
        print(json.dumps(dict(status=result["status"],run_dir=str(root),error=result.get("error"))))
        return 0 if result["status"] in ("DPO_REHEARSAL_PASSED","DPO_TRAINED_SMOKE_VERIFIED_T39_TEST_PENDING") else 1


if __name__=="__main__":
    raise SystemExit(main())
