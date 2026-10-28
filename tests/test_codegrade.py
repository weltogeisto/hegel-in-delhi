"""The coding answers' grader (pc/qwen-trial/codegrade.py): right answers pass, wrong ones fail, and a hostile answer
finds no network, no secrets, no way to outlive its sandbox, and no way to flood the grader. A made-up key keeps the
benchmark's private answer key out of the repository. Skipped where unprivileged namespaces are not available."""
import importlib.util
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

TRIAL = Path(__file__).resolve().parent.parent / "pc" / "qwen-trial"
spec = importlib.util.spec_from_file_location("codegrade", TRIAL / "codegrade.py")
codegrade = importlib.util.module_from_spec(spec)
spec.loader.exec_module(codegrade)

PY_KEY = {"kind": "python_function", "function": "add",
          "tests": [{"args": [1, 2], "expected": 3}, {"args": [[1], [2]], "expected": [1, 2]}],
          "properties": ["input_deep_equal_before_after"]}
JS_KEY = {"kind": "javascript_function", "function": "half",
          "tests": [{"args": [{"v": 3}], "expected": {"v": 1.5}}, {"args": [{"v": -1}], "expected_exception": "RangeError"}],
          "tolerance": 1e-9, "properties": ["input_deep_equal_before_after", "new_result_object"]}


def available():
    try:
        return shutil.which("unshare") is not None and codegrade.usable()
    except Exception:
        return False


def leftovers(tag):
    r = subprocess.run(["pgrep", "-f", tag], capture_output=True, text=True)
    return [l for l in r.stdout.split() if l.strip()]


@unittest.skipUnless(available(), "no unprivileged user, network, PID and mount namespaces here")
class CodegradeTest(unittest.TestCase):
    def test_right_answers_pass_and_wrong_ones_fail(self):
        self.assertTrue(codegrade.grade("P", PY_KEY, "```python\ndef add(a, b):\n    return a + b\n```")["passed"])
        g = codegrade.grade("P", PY_KEY, "def add(a, b):\n    a += b\n    return a")                # mutates the list
        self.assertFalse(g["passed"])
        self.assertEqual(g["passed_tests"], 1)
        if codegrade.NODE:
            good = ("function half(o) { if (o.v < 0) throw new RangeError('neg'); return {v: o.v / 2}; }")
            self.assertTrue(codegrade.grade("J", JS_KEY, good)["passed"])
            same = "function half(o) { if (o.v < 0) throw new RangeError('neg'); o.v /= 2; return o; }"
            self.assertFalse(codegrade.grade("J", JS_KEY, same)["passed"])                       # not a new object

    def test_a_snooping_answer_sees_no_network_no_secrets_no_files(self):
        os.environ["CODEGRADE_TEST_SECRET"] = "s3cret"
        self.addCleanup(os.environ.pop, "CODEGRADE_TEST_SECRET", None)
        src = ("import os, socket, glob, json\n"
               "seen = {'env': sorted(os.environ), 'files': glob.glob('/root/*') + glob.glob('/home/*') + glob.glob('/tmp/*'),"
               " 'mnt': os.listdir('/mnt')}\n"
               "try:\n    socket.create_connection(('1.1.1.1', 53), timeout=2); seen['net'] = 'open'\n"
               "except OSError as e:\n    seen['net'] = e.errno\n"
               "def add(a, b):\n    return seen\n")
        g = codegrade.grade("P", {**PY_KEY, "tests": [{"args": [0, 0], "expected": 0}]}, src)
        seen = g["tests"][0]["result"]
        self.assertNotIn("CODEGRADE_TEST_SECRET", seen["env"])
        self.assertLessEqual(set(seen["env"]), {"PATH", "HOME", "LC_CTYPE"})
        self.assertEqual(seen["files"], [])
        self.assertEqual(seen["mnt"], ["w"])
        self.assertNotEqual(seen["net"], "open")

    def test_no_process_outlives_a_timeout(self):
        src = ("import os, subprocess, time\n"
               "subprocess.Popen(['sleep', '311'], start_new_session=True)\n"
               "if os.fork() == 0:\n    os.setsid()\n    if os.fork() == 0:\n        os.execvp('sleep', ['sleep', '312'])\n    os._exit(0)\n"
               "while True:\n    pass\n")
        t = time.time()
        g = codegrade.grade("P", PY_KEY, src)
        self.assertLess(time.time() - t, codegrade.WALL_S + 5)
        self.assertEqual(g["run"], "timeout")
        time.sleep(1)
        self.assertEqual(leftovers("^sleep 31[12]"), [])

    def test_no_process_outlives_a_crashed_supervisor(self):
        work = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, work, True)
        script = work / "sup.py"
        script.write_text(
            "import importlib.util, sys\nfrom pathlib import Path\n"
            f"spec = importlib.util.spec_from_file_location('c', {str(TRIAL / 'codegrade.py')!r})\n"
            "c = importlib.util.module_from_spec(spec); spec.loader.exec_module(c)\n"
            "w = Path(sys.argv[1]); (w / 'runner.py').write_text(c.PY_RUNNER); (w / 'args.json').write_text('[]')\n"
            "(w / 'solution.txt').write_text(\"import subprocess, time\\nsubprocess.Popen(['sleep', '313'], start_new_session=True)\\ntime.sleep(120)\\n\")\n"
            "c.sandboxed(['python3', '-I', '-S', '/mnt/w/runner.py', 'x'], 'python', w, wall=60)\n")
        sup = subprocess.Popen([sys.executable, "-I", str(script), str(work)])
        for _ in range(50):
            if leftovers("^sleep 313"):
                break
            time.sleep(0.2)
        self.assertTrue(leftovers("^sleep 313"))                                              # it was running
        sup.send_signal(signal.SIGKILL)
        sup.wait()
        time.sleep(1.5)
        self.assertEqual(leftovers("^sleep 313"), [])

    def test_a_flood_of_output_is_cut_off(self):
        g = codegrade.grade("P", PY_KEY, "import sys\nwhile True:\n    sys.stdout.write('x' * 65536)\n")
        self.assertEqual(g["run"], "output_cap")
        self.assertFalse(g["passed"])


if __name__ == "__main__":
    unittest.main()
