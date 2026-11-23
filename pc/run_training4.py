"""Training 4 launcher: his letters, trained at night, behind Training 1's owned processes and restoration.

    python3 -m pc.run_training4 --write-intent NEW_JOB --restore-by ISO_TIME --rehearsal < machine-config.json
    python3 -m pc.run_training4 --write-intent NEW_JOB --restore-by ISO_TIME             < machine-config.json
    python3 -m pc.run_training4 --intent NEW_JOB/INTENT.json --intent-sha256 HASH --detach

It reuses pc/run_training1.py for everything that guards the live server: the Pi pause, the original-server startup lock, admission in a
child with no ML import, owned child processes, the deadline arithmetic, conversion and restoration. The trainer is pc/train_letters.py.
The runbook is pc/TRAINING-4-RUN.md; the reasons are in pc/TRAINING-4.md and DECISIONS.md 65.

A rehearsal runs three optimizer steps, one evaluation, a checkpoint save, conversion to GGUF, one served completion at adapter scale 1 and one
at scale 0 (plain /completion, the scale set per request), and restores the original server. A real run needs a complete passed rehearsal
with the same bytes in every input. It trains at night: the restore deadline may be the next morning, at 08:15 Berlin at the latest, and
must leave the usual reserve before the power cutoff. There is one controller and no automatic restart; every failure restores.
Every saved checkpoint stays. Converting more of them is a later step, not this launcher's.
"""
import argparse
import fcntl
import json
import math
import os
from datetime import datetime
from pathlib import Path
import signal
import statistics
import subprocess
import sys
import time
import urllib.error
from zoneinfo import ZoneInfo

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from pc import run_training1 as lifecycle  # noqa: E402
from pc import train_letters  # noqa: E402

VERSION = "training4-letters-1"
RECIPE = dict(rank=16, alpha=32, lr=1e-4, epochs=3, batch=1, accum=8, seq=1536, patience=3, goldfish=True, goldfish_k=4,
              goldfish_context=13, seed=3407, text_only=True, loss_target_gib=0.125)
REAL_EVAL_STEPS, REAL_SAVE_STEPS = 50, 50
REHEARSAL_STEPS, REHEARSAL_EVAL_STEPS = 3, 2
MINIMUM_REAL_STEPS = 100                  # two evaluations: a shorter window is not worth the night (unless the whole schedule is shorter)
BERLIN = ZoneInfo("Europe/Berlin")
NIGHT_END, DAY_END = (8, 15, 0), (20, 0, 0)
POWER_MARGIN = 900                        # the existing cutoff must come this long after the restore deadline
REHEARSED_FILES = ("train", "heldout", "converter", "base_gguf")
REHEARSED_TREES = ("base_model", "converter_base")
PASSED, FAILED_REHEARSAL, TRAINED = "LETTERS_REHEARSAL_PASSED", "LETTERS_REHEARSAL_FAILED", "LETTERS_TRAINED_SMOKE_VERIFIED_EVALUATION_PENDING"


# ── the window ──────────────────────────────────────────────────────
def check_window(deadline, now):
    """Raise unless `deadline` (epoch seconds) is an allowed restore time for a job started at `now`, by Berlin's clock.

    By day (the rehearsal): the same date, started between 09:00 and 20:00, restored by 20:00, as Training 3 requires.
    By night (the real run): started from 20:00 on, restored by 08:15 the next morning; or started after midnight, restored by 08:15 the same morning."""
    end, start = datetime.fromtimestamp(deadline, BERLIN), datetime.fromtimestamp(now, BERLIN)
    clock, days = (end.hour, end.minute, end.second), (end.date() - start.date()).days
    if deadline <= now:
        raise ValueError("the restore deadline is in the past")
    by_day = days == 0 and 9 <= start.hour < 20 and clock <= DAY_END
    by_night = clock <= NIGHT_END and ((start.hour >= 20 and days == 1) or (start.hour < 8 and days == 0))
    if not (by_day or by_night):
        raise ValueError("a same-day window ending by 20:00 Berlin, or a night window ending by 08:15 Berlin, is required")


def check_power(power, deadline):
    """The authorised power cutoff must come at least 15 minutes after the restore deadline; no power change is ever made here."""
    if lifecycle.epoch(power["deadlineUtc"]) < deadline + POWER_MARGIN:
        raise ValueError("existing power cutoff lacks restoration margin; no power change")


def fit_steps(estimate, upper, interval, available):
    """The most optimizer steps (at most `upper`) whose measured projection fits `available` seconds; 0 if none."""
    for steps in range(upper, 0, -1):
        if lifecycle.projection(estimate["step_seconds"], estimate["evaluation_seconds"], steps, interval) <= available:
            return steps
    return 0


# ── the intent ──────────────────────────────────────────────────────
def training_argv(data):
    """The trainer's whole command line, from the intent alone."""
    r = RECIPE
    argv = ["--base", data["base_model"], "--train", data["train"], "--heldout", data["heldout"],
            "--out", str(lifecycle.intent_paths(data)["training"]), "--rank", str(r["rank"]), "--alpha", str(r["alpha"]),
            "--lr", str(r["lr"]), "--epochs", str(r["epochs"]), "--batch", str(r["batch"]), "--accum", str(r["accum"]),
            "--seq", str(r["seq"]), "--save-steps", str(data["save_steps"]), "--eval-steps", str(data["eval_steps"]),
            "--patience", str(r["patience"]), "--goldfish", "--goldfish-k", str(r["goldfish_k"]),
            "--goldfish-context", str(r["goldfish_context"]), "--seed", str(r["seed"]), "--max-steps", str(data["steps"]),
            "--text-only", "--loss-target-gib", str(r["loss_target_gib"])]
    return argv


def load(path, expected=None):
    path = Path(path).resolve()
    if expected and lifecycle.filehash(path) != expected:
        raise RuntimeError("intent changed")
    data = lifecycle.read(path)
    if data.get("version") != VERSION or path != Path(data["run_dir"]) / "INTENT.json":
        raise ValueError("Training 4 intent must remain at its original path")
    if Path(data["source_dir"]).resolve() != REPO or data["recipe"] != RECIPE:
        raise ValueError("source or recipe differs")
    if data["trial_port"] == 8082 or not 1024 <= data["trial_port"] <= 65535:
        raise ValueError("adapter uses a separate loopback port")
    if not data["no_automatic_adoption"] or not data["no_restarts"]:
        raise ValueError("restart/adoption are not permitted")
    if data["adapter_subdir"] != "final" or data["training_argv"] != training_argv(data):
        raise ValueError("worker and intent arguments disagree")
    if data["dry_run"]:
        if (data["steps"], data["eval_steps"], data["save_steps"]) != (REHEARSAL_STEPS, REHEARSAL_EVAL_STEPS, 2):
            raise ValueError("rehearsal schedule differs")
    elif (data["eval_steps"], data["save_steps"]) != (REAL_EVAL_STEPS, REAL_SAVE_STEPS) or not min(MINIMUM_REAL_STEPS, data["upper_steps"]) <= data["steps"] <= data["upper_steps"]:
        raise ValueError("real run schedule differs from the recipe or the measured window")
    return data


def verify(data):
    if subprocess.check_output(["git", "-C", str(REPO), "rev-parse", "HEAD"], text=True).strip() != data["commit"]:
        raise RuntimeError("reviewed source commit changed")
    for name, expected in data["frozen_files"].items():
        lifecycle.verify_frozen_file(data, name, expected)


def validate_rehearsal(config):
    """(rehearsal intent, its verdict) if the rehearsal named in `config` ran to the end and passed, with its records unchanged."""
    path = Path(config["passed_rehearsal"])
    verdict, end = lifecycle.read(path), lifecycle.read(path.parent / "RUN-END.json")
    previous = load(path.parent / "INTENT.json")
    if (not previous["dry_run"] or verdict.get("passed") is not True or end["status"] != PASSED
            or verdict["intent_sha256"] != lifecycle.filehash(path.parent / "INTENT.json")):
        raise ValueError("a genuinely completed, passed rehearsal is required")
    for key in ("base_model", "base_gguf", "train", "heldout", "converter", "converter_base"):
        if config[key] != previous[key]:
            raise ValueError("rehearsal input differs: " + key)
    if subprocess.check_output(["git", "-C", str(REPO), "rev-parse", "HEAD"], text=True).strip() != previous["commit"]:
        raise ValueError("source changed since the rehearsal; review and rehearse the new source")
    for filename, key in (("training/RESULT.json", "training_sha256"), ("PHASE-C-END.json", "serve_sha256"),
                          ("LETTERS-C-TIMING.json", "c_timing_sha256"), ("RESTORATION.json", "restoration_sha256")):
        if lifecycle.filehash(path.parent / filename) != verdict[key]:
            raise ValueError("rehearsal result changed: " + filename)
    return previous, verdict


def rehearsed_inputs(data):
    """The frozen hashes of what the rehearsal exercised: its data, model, tokenizer and converter, and the server launcher."""
    files = {str(Path(data[k]).resolve()) for k in REHEARSED_FILES} | {str(Path(data["original"]["launcher"]).resolve())}
    trees = [Path(data[k]).resolve() for k in REHEARSED_TREES] + [Path(data["converter"]).resolve().parent]
    return {name: value for name, value in data["frozen_files"].items()
            if name in files or any(tree in Path(name).parents for tree in trees)}


def same_as_rehearsal(previous, data):
    """A real run accepts its rehearsal only for the same bytes, not merely the same paths."""
    then, now = rehearsed_inputs(previous), rehearsed_inputs(data)
    changed = sorted(name for name in then.keys() | now.keys() if then.get(name) != now.get(name))
    if changed:
        raise ValueError("rehearsal inputs changed at the same paths: " + ", ".join(changed[:5]))


def create(config, root, restore_by, rehearsal, now=None):
    """Write the one immutable INTENT.json of a new job. CPU only; nothing is started."""
    root = Path(root).resolve()
    if root.exists():
        raise FileExistsError("new job required; preserve prior evidence")
    now = time.time() if now is None else now
    deadline = lifecycle.epoch(restore_by)
    check_window(deadline, now)
    if deadline <= now + lifecycle.RESTORE_RESERVE:
        raise ValueError("no remaining compute window")
    if subprocess.check_output(["git", "-C", str(REPO), "status", "--porcelain"]):
        raise RuntimeError("reviewed source checkout must be clean")
    train, heldout = train_letters.validate(config["train"], config["heldout"])
    upper = train_letters.total_steps(len(train), RECIPE["batch"], RECIPE["accum"], RECIPE["epochs"])
    data = dict(config, version=VERSION, source_dir=str(REPO), run_dir=str(root), dry_run=bool(rehearsal), recipe=RECIPE,
                restore_by=restore_by, phase_b_cap_s=25200, no_restarts=True, no_automatic_adoption=True,
                written_utc=lifecycle.utc(), adapter_subdir="final", upper_steps=upper, train_rows=len(train), heldout_rows=len(heldout))
    previous = None
    if rehearsal:
        data.update(steps=REHEARSAL_STEPS, eval_steps=REHEARSAL_EVAL_STEPS, save_steps=2)
        if not all(math.isfinite(data["estimate"][k]) and data["estimate"][k] > 0 for k in ("step_seconds", "evaluation_seconds", "phase_c_seconds")):
            raise ValueError("bounded rehearsal estimates required")
    else:
        previous, verdict = validate_rehearsal(config)
        data["estimate"] = verdict["estimate"]
        data.update(eval_steps=REAL_EVAL_STEPS, save_steps=REAL_SAVE_STEPS)
        available = min(deadline - now - lifecycle.RESTORE_RESERVE, data["phase_b_cap_s"]) - data["estimate"]["phase_c_seconds"]
        data["steps"] = fit_steps(data["estimate"], upper, REAL_EVAL_STEPS, available)
        if data["steps"] < min(MINIMUM_REAL_STEPS, upper):
            raise ValueError(f"the window fits only {data['steps']} steps; at least {min(MINIMUM_REAL_STEPS, upper)} are needed")
    data["commit"] = subprocess.check_output(["git", "-C", str(REPO), "rev-parse", "HEAD"], text=True).strip()
    paths = [REPO / n for n in subprocess.check_output(["git", "-C", str(REPO), "ls-files", "-z"]).decode().split("\0") if n]
    paths += [Path(data[k]) for k in ("train", "heldout", "converter", "base_gguf", "power_receipt")] + [Path(data["original"]["launcher"])]
    for key in REHEARSED_TREES:
        paths += [p for p in Path(data[key]).rglob("*") if p.is_file()]
    paths += [p for p in Path(data["converter"]).parent.rglob("*.py") if ".git" not in p.parts]
    if previous:
        folder = Path(data["passed_rehearsal"]).parent
        paths += [folder / name for name in ("REHEARSAL.json", "INTENT.json", "RUN-END.json", "RESTORATION.json", "PHASE-C-END.json",
                                             "LETTERS-C-TIMING.json", "training/RESULT.json")]
    if any(root == p.resolve() or root in p.resolve().parents for p in paths):
        raise ValueError("output overlaps an input")
    for base in (REPO, Path(data["base_model"]), Path(data["converter_base"])):
        if root == base.resolve() or base.resolve() in root.parents:
            raise ValueError("job output is inside a source/model input directory")
    data["training_argv"] = training_argv(dict(data, run_dir=str(root)))
    lifecycle.freeze_inputs(data, paths, previous)
    if previous:
        same_as_rehearsal(previous, data)
    data["power"] = lifecycle.read(data["power_state"])
    receipt = lifecycle.read(data["power_receipt"])
    if (data["power"].get("pendingUtc") or receipt.get("status") != "VERIFIED"
            or receipt["state"]["lastRequestId"] != data["power"]["lastRequestId"]):
        raise ValueError("normal power deadline is unverified or shutdown is pending")
    check_power(data["power"], deadline)
    data["linux_boot"] = Path("/proc/sys/kernel/random/boot_id").read_text().strip()
    root.mkdir()
    lifecycle.write_new(root / "INTENT.json", data)
    load(root / "INTENT.json")
    return root / "INTENT.json"


# ── the trainer, timed ──────────────────────────────────────────────
class TimedBackend:
    """Wraps the trainer's backend and writes Training 1's timing.jsonl events (step_begin, step, evaluate_*, checkpoint) that its guards and
    the rehearsal verdict read. Before every step it checks the deadline. Everything else is passed through."""
    def __init__(self, inner, timing, check, sync=lambda: None, peaks=lambda: {}):
        self.inner, self.timing, self.check, self.sync, self.peaks = inner, Path(timing), check, sync, peaks
        self.began = {}

    def __getattr__(self, name):
        return getattr(self.inner, name)

    def emit(self, kind, **fields):
        with self.timing.open("ab") as stream:
            stream.write((json.dumps(dict(event=kind, utc=lifecycle.utc(), unix=time.time(), **fields)) + "\n").encode())
            stream.flush()
            os.fsync(stream.fileno())

    def event(self, kind, **fields):
        if kind == "step_begin":
            self.check()
            self.sync()
            self.began["step"] = time.monotonic()
        elif kind == "step":
            self.sync()
            fields.update(seconds=time.monotonic() - self.began["step"], **self.peaks())
        elif kind in ("evaluate_begin", "checkpoint_begin"):
            self.began[kind.split("_")[0]] = time.monotonic()
        elif kind in ("evaluate_end", "checkpoint"):
            fields["seconds"] = time.monotonic() - self.began[kind.split("_")[0]]
        if kind != "checkpoint_begin":
            self.emit(kind, **fields)


def train_worker(data, path, expected):
    """In the ML process, after admission: the reviewed trainer with the intent's arguments and the timing wrapper."""
    load(path, expected)
    root = Path(data["run_dir"])
    admission = lifecycle.read(root / "admission" / "ADMISSION.json")
    if not admission["allowed"] or not admission["before_ml_import"]:
        raise RuntimeError("no successful pre-Python admission")
    if time.time() - lifecycle.epoch(admission["utc"]) > 120:
        raise RuntimeError("admission is stale")
    os.environ["UNSLOTH_CE_LOSS_TARGET_GB"] = str(RECIPE["loss_target_gib"])
    import unsloth  # noqa: F401  (patches Transformers before the trainer imports it)
    args = train_letters.parser().parse_args(training_argv(data))
    inner = train_letters.TorchBackend()

    def check():
        load(path, expected)
        if time.time() + 120 >= lifecycle.deadline(data):
            raise TimeoutError("trainer deadline")

    def peaks():
        cuda = inner.torch.cuda
        return dict(peak_reserved=cuda.max_memory_reserved(), peak_allocated=cuda.max_memory_allocated())

    timed = TimedBackend(inner, root / "timing.jsonl", check, lambda: inner.torch.cuda.synchronize(), peaks)
    train_letters.train(args, timed)


# ── the serve checks ────────────────────────────────────────────────
def serve_checks(data, intent, expected):
    """One plain /completion at adapter scale 1 and one at scale 0, on the first held-out prompt. An unknown reply stops everything: no resend."""
    root = Path(data["run_dir"])
    server = lifecycle.read(root / "ADAPTER-READY.json")["identity"]
    prompt = train_letters.validate(data["train"], data["heldout"])[1][0]["prompt"]
    window, cases = root / "http-windows.jsonl", []

    def log(kind, rid, **values):
        with window.open("ab") as stream:
            stream.write((json.dumps(dict(event=kind, request=rid, unix=time.time(), **values)) + "\n").encode())
            stream.flush()
            os.fsync(stream.fileno())

    for number, scale in enumerate((1, 0), 1):
        rid = str(number)
        load(intent, expected)
        if time.time() + lifecycle.HTTP_TIMEOUT >= lifecycle.deadline(data) or not lifecycle.same_process(server):
            raise RuntimeError("owned adapter identity or remaining time differs")
        payload = json.dumps(dict(prompt=prompt, n_predict=120, temperature=0, seed=1831, cache_prompt=False, stream=False,
                                  id_slot=1, lora=[dict(id=0, scale=scale)])).encode()
        log("http_begin", rid, deadline=time.time() + lifecycle.HTTP_TIMEOUT, payload_sha256=lifecycle.digest(payload))
        try:
            status, raw = lifecycle.http(data["trial_port"], "/completion", payload, lifecycle.HTTP_TIMEOUT)
        except BaseException as exc:
            lifecycle.write_new(root / "unknown" / (rid + ".partial.bin"), getattr(exc, "partial", b""), True)
            lifecycle.write_new(root / "unknown" / (rid + ".json"), dict(error=repr(exc), no_resend=True))
            raise RuntimeError("unknown response; no resend") from exc
        log("http_end", rid, status=status, response_sha256=lifecycle.digest(raw))
        if status != 200:
            raise urllib.error.HTTPError("/completion", status, "HTTP error", {}, None)
        lifecycle.write_new(root / "serve" / ("scale-" + str(scale) + ".json"), raw, True)
        text = json.loads(raw).get("content")
        if not isinstance(text, str) or not text.strip():
            raise RuntimeError("scale " + str(scale) + " returned no text")
        cases.append(dict(scale=scale, text=text))
    lifecycle.write_new(root / "PHASE-C-END.json", dict(status="TWO_COMPLETION_SERVE_CHECKS", cases=cases, prompt=prompt, utc=lifecycle.utc(),
                                                       texts_differ=cases[0]["text"] != cases[1]["text"],
                                                       quality_test_pending=True, automatic_adoption=False))


def verdict(data, result):
    """The rehearsal's gates, from the timing log, the trainer's RESULT.json, the serve record and the restoration."""
    root = Path(data["run_dir"])
    log = lifecycle.rows(root / "timing.jsonl")
    steps = [x for x in log if x["event"] == "step"]
    evaluations = [x for x in log if x["event"] == "evaluate_end"]
    before = [x["seconds"] for x in steps if x["step"] <= 2]
    after = [x["seconds"] for x in steps if x["step"] > 2]
    if len(steps) != 3 or len(before) != 2 or len(after) != 1 or not evaluations:
        raise RuntimeError("incomplete rehearsal timing")
    training = lifecycle.read(root / "training/RESULT.json")
    serve = lifecycle.read(root / "PHASE-C-END.json")
    ratio = max(after) / statistics.median(before)
    gates = dict(post_eval_speed=ratio <= 1.5,
                 within_card=max(x["peak_reserved"] for x in steps) < lifecycle.CARD_BYTES,
                 trained_three_steps=training["steps_run"] == REHEARSAL_STEPS and training["best_step"] is not None,
                 checkpoint_saved=any(x["event"] == "checkpoint" for x in log) and (root / "training/checkpoint-2").is_dir(),
                 final_adapter=(root / "training/final/adapter_model.safetensors").is_file(),
                 two_scales=serve["status"] == "TWO_COMPLETION_SERVE_CHECKS" and [c["scale"] for c in serve["cases"]] == [1, 0],
                 restored=result["restoration"]["status"] == "ORIGINAL_QWEN_AND_TIMER_RESTORED",
                 route=result["restoration"].get("pi_probe", {}).get("status") == "PI_HEALTH_AND_ONE_TOKEN_VERIFIED")
    actual_c = lifecycle.read(root / "LETTERS-C-TIMING.json")["seconds"]
    if not math.isfinite(actual_c) or actual_c <= 0:
        raise RuntimeError("missing measured conversion/serve time")
    estimate = dict(step_seconds=statistics.median(x["seconds"] for x in steps), evaluation_seconds=max(x["seconds"] for x in evaluations),
                    phase_c_seconds=actual_c * 1.15, rehearsal_c_seconds=actual_c * 1.15)
    return dict(passed=all(gates.values()), gates=gates, utc=lifecycle.utc(), post_eval_ratio=ratio,
                intent_sha256=lifecycle.filehash(root / "INTENT.json"),
                training_sha256=lifecycle.filehash(root / "training/RESULT.json"),
                serve_sha256=lifecycle.filehash(root / "PHASE-C-END.json"),
                c_timing_sha256=lifecycle.filehash(root / "LETTERS-C-TIMING.json"),
                restoration_sha256=lifecycle.filehash(root / "RESTORATION.json"),
                texts_differ=serve.get("texts_differ"), estimate=estimate)


# ── the owning controller ───────────────────────────────────────────
class Backend(lifecycle.Backend):
    def __init__(self, path):
        # Training 1's load_intent enforces its own fixed recipe: never forge that intent or change its globals.
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
        projected = lifecycle.projection(estimate["step_seconds"], estimate["evaluation_seconds"], self.data["steps"], self.data["eval_steps"])
        end = min(self.check_time(), time.time() + self.data["phase_b_cap_s"])
        if time.time() + projected > end:
            raise RuntimeError("measured training projection cannot fit")
        lifecycle.write_new(self.root / "B-BUDGET.json", dict(utc=lifecycle.utc(), phase_b_end=end, projected_seconds=projected,
                                                             steps=self.data["steps"]))
        self.worker("train", end)
        report = lifecycle.read(self.paths["training"] / "RESULT.json")
        exact = self.data["dry_run"]
        if (report["steps_run"] != self.data["steps"] if exact else not 1 <= report["steps_run"] <= self.data["steps"]):
            raise RuntimeError("training ended outside its frozen schedule")
        if not (lifecycle.adapter_dir(self.data) / "adapter_model.safetensors").is_file():
            raise RuntimeError("the final adapter is missing")
        lifecycle.write_new(self.root / "PHASE-B-END.json", dict(steps=report["steps_run"], stopped=report["stopped"], utc=lifecycle.utc(),
                                                                report_sha256=lifecycle.filehash(self.paths["training"] / "RESULT.json")))
        if self.data["dry_run"]:
            self.sample_memory(force=True)

    def phase_c(self):
        began = time.monotonic()
        super().phase_c()
        lifecycle.write_new(self.root / "LETTERS-C-TIMING.json", dict(utc=lifecycle.utc(), seconds=time.monotonic() - began))

    def sheets(self):
        return None                                 # nothing is judged here: the instrument measures the checkpoints later


def detach(data, path, expected):
    root = Path(data["run_dir"])
    if (root / "RUN-BEGIN.json").exists() or (root / "DETACHED-LAUNCH.json").exists():
        raise RuntimeError("already launched; reconcile instead of restarting")
    argv = ["/usr/bin/python3", "-B", str(Path(__file__).resolve()), "--intent", str(path), "--intent-sha256", expected]
    lifecycle.write_new(root / "DETACHED-LAUNCH.json", dict(utc=lifecycle.utc(), argv=argv, intent_sha256=expected))
    with (root / "launcher.log").open("xb") as log:
        child = subprocess.Popen(argv, cwd=data["source_dir"], stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    lifecycle.write_new(root / "DETACHED-PROCESS.json", dict(identity=lifecycle.identity(child.pid), new_session=True, stdin_null=True,
                                                            no_parent_death_signal=True))
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--write-intent", type=Path)
    p.add_argument("--restore-by")
    p.add_argument("--rehearsal", action="store_true")
    p.add_argument("--detach", action="store_true")
    p.add_argument("--intent", type=Path)
    p.add_argument("--intent-sha256")
    p.add_argument("--worker", choices=("admission", "train", "verify-conversion", "benchmark"))
    a = p.parse_args(argv)
    if a.write_intent:
        if not a.restore_by or a.intent or a.worker or a.detach:
            p.error("a new intent needs --restore-by and the JSON configuration on stdin")
        path = create(json.load(sys.stdin), a.write_intent, a.restore_by, a.rehearsal)
        print(json.dumps(dict(intent=str(path), sha256=lifecycle.filehash(path))))
        return 0
    if not a.intent or not a.intent_sha256:
        p.error("the pinned intent is required")
    data = load(a.intent, a.intent_sha256)
    if a.worker:
        if a.worker == "admission":
            lifecycle.gpu_admission(Path(data["run_dir"]) / "admission")
        elif a.worker == "verify-conversion":
            lifecycle.verify_conversion(data)
        elif a.worker == "benchmark":
            serve_checks(data, a.intent, a.intent_sha256)
        else:
            train_worker(data, a.intent, a.intent_sha256)
        return 0
    verify(data)
    if a.detach:
        return detach(data, a.intent, a.intent_sha256)
    root = Path(data["run_dir"])
    with (root / "run.lock").open("a+") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        lifecycle.write_new(root / "RUN-BEGIN.json", dict(utc=lifecycle.utc(), pid=os.getpid(), intent_sha256=a.intent_sha256))

        def interrupted(sig, frame):
            raise RuntimeError("interrupted; restore and never restart")
        for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
            signal.signal(sig, interrupted)
        result = lifecycle.run_pipeline(Backend(a.intent))
        if result["status"] == "B_AND_C_COMPLETE":
            if data["dry_run"]:
                try:
                    report = verdict(data, result)
                    lifecycle.write_new(root / "REHEARSAL.json", report)
                    result["status"] = PASSED if report["passed"] else FAILED_REHEARSAL
                except BaseException as exc:
                    result.update(status=FAILED_REHEARSAL, error=repr(exc))
            else:
                result["status"] = TRAINED
        result["finished_utc"] = lifecycle.utc()
        lifecycle.write_new(root / "RUN-END.json", result)
        print(json.dumps(dict(status=result["status"], run_dir=str(root), error=result.get("error"))))
        return 0 if result["status"] in (PASSED, TRAINED) else 1


if __name__ == "__main__":
    raise SystemExit(main())
