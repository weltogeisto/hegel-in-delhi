"""Grade the screening's coding answers (C1-C3) off the PC, in a disposable Linux container.

    python3 codegrade.py --key answer-key.json --answers ANSWERS_DIR --out grades.json

ANSWERS_DIR holds one folder per configuration with C1.txt, C2.txt and C3.txt: each the model's answer with its
reasoning removed. The answer key (Hermes's benchmark-v1) supplies the arguments; only the arguments go into the
sandbox, and the results are compared with the expected values outside it.

Each answer runs alone:
  - a new network namespace with no interfaces up (no route anywhere) and a new user namespace;
  - a new PID namespace whose first process is killed when unshare ends (--kill-child), and unshare dies with this
    supervisor (PR_SET_PDEATHSIG): when the supervisor times out, finishes or crashes, every process of the answer
    is gone, which the tests check;
  - a new mount namespace with empty tmpfs over /home, /root, /tmp, /mnt, /var/tmp and /run, the answer and its
    trusted runner bound read-only into /mnt/w, an empty environment, a 10 s wall clock, CPU, file-size and memory
    limits, and at most 256 KiB of output.
Standard library only. Linux with unprivileged user namespaces; refuses to run without them.
"""
import argparse
import ctypes
import json
import math
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

WALL_S = 10
OUT_MAX = 256 * 1024
NODE = shutil.which("node")

PY_RUNNER = r'''
import copy, json, sys
src = open("/mnt/w/solution.txt", encoding="utf-8").read()
tests = json.load(open("/mnt/w/args.json"))
name = sys.argv[1]
out = {"defined": False, "tests": []}
ns = {"__name__": "solution"}
try:
    exec(compile(src, "solution.py", "exec"), ns)
    f = ns.get(name)
    out["defined"] = callable(f)
except BaseException as e:
    out["load_error"] = type(e).__name__ + ": " + str(e)[:300]
    f = None
for args in tests:
    row = {}
    if f is not None:
        before = json.dumps(args, sort_keys=True)
        call = copy.deepcopy(args)
        try:
            r = f(*call)
            row["result"] = json.loads(json.dumps(r))
        except BaseException as e:
            row["exception"] = type(e).__name__
            row["message"] = str(e)[:200]
        row["inputs_unchanged"] = json.dumps(call, sort_keys=True) == before
    out["tests"].append(row)
sys.stdout.write("\n@@RESULT@@" + json.dumps(out))
'''

JS_RUNNER = r'''
const fs = require("fs"), vm = require("vm");
const src = fs.readFileSync("/mnt/w/solution.txt", "utf8");
const tests = JSON.parse(fs.readFileSync("/mnt/w/args.json", "utf8"));
const name = process.argv[2];
const out = {defined: false, tests: []};
const ctx = {module: {exports: {}}, exports: {}};
ctx.globalThis = ctx;
vm.createContext(ctx);
let f = null;
try {
  vm.runInContext(src + "\n;globalThis.__f = (typeof " + name + " !== 'undefined') ? " + name +
                  " : (module.exports && module.exports." + name + ") || module.exports;", ctx, {timeout: 5000});
  f = typeof ctx.__f === "function" ? ctx.__f : null;
  out.defined = f !== null;
} catch (e) { out.load_error = String(e && e.name) + ": " + String(e && e.message).slice(0, 300); }
for (const args of tests) {
  const row = {};
  if (f) {
    const before = JSON.stringify(args);
    const call = JSON.parse(before);
    try {
      const r = f(...call);
      row.result = r === undefined ? null : JSON.parse(JSON.stringify(r));
      row.new_object = r !== null && typeof r === "object" && !call.some(a => a === r);
    } catch (e) { row.exception = (e && e.name) || String(e); row.message = String(e && e.message).slice(0, 200); }
    row.inputs_unchanged = JSON.stringify(call) === before;
  }
  out.tests.push(row);
}
process.stdout.write("\n@@RESULT@@" + JSON.stringify(out));
'''

SETUP = r'''
set -e
for d in /home /root /mnt /var/tmp /run; do [ -d "$d" ] && mount -t tmpfs -o size=16m tmpfs "$d"; done
mkdir -p /mnt/w
mount --bind "$WORK" /mnt/w
mount -o remount,bind,ro /mnt/w 2>/dev/null || true
mount -t tmpfs -o size=16m tmpfs /tmp
cd /mnt/w
ulimit -t 10
ulimit -f 10240
[ "$KIND" = python ] && ulimit -v 1048576
exec env -i PATH=/usr/local/bin:/usr/bin:/bin:"$NODEDIR" HOME=/tmp "$@"
'''


def extract(answer):
    """The first fenced block if there is one (any language tag), else the whole answer."""
    m = re.search(r"```[A-Za-z0-9_+-]*[ \t]*\r?\n(.*?)```", answer, re.S)
    return (m.group(1), True) if m else (answer, False)


def _die_with_parent():
    ctypes.CDLL("libc.so.6", use_errno=True).prctl(1, signal.SIGKILL)       # PR_SET_PDEATHSIG
    os.setsid()


def sandboxed(cmd, kind, work, wall=WALL_S):
    """Run cmd inside the namespaces. Returns (stdout, stderr, how), how in ok / timeout / output_cap / exit:N."""
    env = {"PATH": "/usr/local/bin:/usr/bin:/bin", "WORK": str(work), "KIND": kind,
           "NODEDIR": str(Path(NODE).parent) if NODE else ""}
    full = ["unshare", "--user", "--map-root-user", "--net", "--pid", "--fork", "--kill-child", "--mount-proc",
            "--mount", "sh", "-c", SETUP, "setup"] + cmd
    p = subprocess.Popen(full, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env,
                         preexec_fn=_die_with_parent)
    bufs, over = {"out": b"", "err": b""}, threading.Event()

    def pump(stream, key):
        while True:
            chunk = stream.read(8192)
            if not chunk:
                return
            if len(bufs[key]) + len(chunk) > OUT_MAX:
                over.set()
                p.kill()
                return
            bufs[key] += chunk

    pumps = [threading.Thread(target=pump, args=(p.stdout, "out"), daemon=True),
             threading.Thread(target=pump, args=(p.stderr, "err"), daemon=True)]
    for t in pumps:
        t.start()
    try:
        code = p.wait(timeout=wall)
        how = "ok" if code == 0 else f"exit:{code}"
    except subprocess.TimeoutExpired:
        p.kill()
        p.wait()
        how = "timeout"
    for t in pumps:
        t.join(timeout=2)
    p.stdout.close()
    p.stderr.close()
    if over.is_set():
        how = "output_cap"
    return bufs["out"].decode("utf-8", "replace"), bufs["err"].decode("utf-8", "replace"), how


def same(got, want, tol):
    if isinstance(want, bool) or want is None:
        return got == want and type(got) is type(want)
    if isinstance(want, (int, float)):
        return isinstance(got, (int, float)) and not isinstance(got, bool) and math.isfinite(got) and abs(got - want) <= tol
    if isinstance(want, list):
        return isinstance(got, list) and len(got) == len(want) and all(same(g, w, tol) for g, w in zip(got, want))
    if isinstance(want, dict):
        return isinstance(got, dict) and set(got) == set(want) and all(same(got[k], want[k], tol) for k in want)
    return got == want


def grade(case, key, answer):
    src, fenced = extract(answer)
    kind = "python" if key["kind"] == "python_function" else "javascript"
    work = Path(tempfile.mkdtemp(prefix="codegrade-"))
    try:
        (work / "solution.txt").write_text(src, encoding="utf-8")
        (work / "args.json").write_text(json.dumps([t["args"] for t in key["tests"]]), encoding="utf-8")
        if kind == "python":
            (work / "runner.py").write_text(PY_RUNNER, encoding="utf-8")
            cmd = ["python3", "-I", "-S", "/mnt/w/runner.py", key["function"]]
        else:
            if not NODE:
                return {"case": case, "passed": False, "note": "no node here"}
            (work / "runner.js").write_text(JS_RUNNER, encoding="utf-8")
            cmd = ["node", "--max-old-space-size=256", "/mnt/w/runner.js", key["function"]]
        out, err, how = sandboxed(cmd, kind, work)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    res = None
    if "@@RESULT@@" in out:
        try:
            res = json.loads(out.rsplit("@@RESULT@@", 1)[1])
        except ValueError:
            res = None
    row = {"case": case, "fenced": fenced, "run": how, "tests": [], "passed": False}
    if res is None:
        row["note"] = (err or out)[-500:]
        return row
    row["defined"] = res.get("defined")
    if res.get("load_error"):
        row["load_error"] = res["load_error"]
    tol = key.get("tolerance", 0)
    props = key.get("properties") or []
    for t, r in zip(key["tests"], res["tests"]):
        if "expected_exception" in t:
            ok = r.get("exception") == t["expected_exception"]
        else:
            ok = "result" in r and same(r["result"], t["expected"], tol)
        if "input_deep_equal_before_after" in props:
            ok = ok and r.get("inputs_unchanged") is True
        if "new_result_object" in props and "expected_exception" not in t:
            ok = ok and r.get("new_object") is True
        row["tests"].append({"ok": ok, **{k: r[k] for k in ("result", "exception", "inputs_unchanged") if k in r}})
    row["passed_tests"] = sum(t["ok"] for t in row["tests"])
    row["passed"] = bool(res.get("defined")) and len(row["tests"]) == len(key["tests"]) and all(t["ok"] for t in row["tests"])
    return row


def usable():
    out, err, how = sandboxed(["sh", "-c", "echo ok"], "python", Path(tempfile.gettempdir()))
    return how == "ok" and out.strip() == "ok"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--key", required=True)
    ap.add_argument("--answers", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    if not usable():
        sys.exit("no unprivileged user, network, PID and mount namespaces here; refusing to run answers")
    keys = json.loads(Path(a.key).read_text(encoding="utf-8"))["cases"]
    grades = {}
    for conf in sorted(p for p in Path(a.answers).iterdir() if p.is_dir()):
        grades[conf.name] = []
        for case in ("C1", "C2", "C3"):
            f = conf / f"{case}.txt"
            if not f.exists():
                grades[conf.name].append({"case": case, "passed": False, "note": "no answer"})
                continue
            grades[conf.name].append(grade(case, keys[case], f.read_text(encoding="utf-8", errors="replace")))
    Path(a.out).write_text(json.dumps(grades, indent=2), encoding="utf-8")
    print(json.dumps({c: [f"{g['case']}:{'pass' if g['passed'] else 'fail'}" for g in gs] for c, gs in grades.items()}))


if __name__ == "__main__":
    main()
