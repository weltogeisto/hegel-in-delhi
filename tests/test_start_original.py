"""pc/run_training1.start_original: the live server is put back by its Windows starter when the intent names one."""
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from pc import run_training1 as lifecycle

SLOTS = json.dumps([{"id": i, "n_ctx": 16384, "is_processing": False} for i in range(3)]).encode()
STARTER = ["/mnt/c/Windows/System32/schtasks.exe", "/Run", "/TN", "Hegel Qwen 8082 GPU"]


class StartOriginalTest(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.root = Path(self.td.name)
        self.ran = []

    def tearDown(self):
        self.td.cleanup()

    def run_with(self, code=0, out=b""):
        def run(argv, **kw):
            self.ran.append(argv)
            return SimpleNamespace(returncode=code, stdout=out, stderr=b"")
        return run

    def test_without_a_starter_the_launcher_script_reports_as_before(self):
        report = json.dumps({"outcome": "GPU_READY", "slots": json.loads(SLOTS)}).encode()
        ready = lifecycle.start_original({"launcher": "/x/start.py", "cwd": "/"}, self.root, run=self.run_with(out=report))
        self.assertEqual(self.ran, [["/usr/bin/python3", "-B", "/x/start.py"]])
        self.assertEqual((ready["outcome"], len(ready["slots"])), ("GPU_READY", 3))
        self.assertEqual((self.root / "RESTORE.stdout").read_bytes(), report)

    def test_the_starter_is_run_and_the_server_is_asked_itself(self):
        answers = iter([OSError("refused"), (503, b"{}"), (200, b'{"status": "ok"}'), (200, SLOTS)])
        asked, naps = [], []

        def get(port, path="/health"):
            asked.append((port, path))
            a = next(answers)
            if isinstance(a, Exception):
                raise a
            return a
        ready = lifecycle.start_original({"launcher": "/x/start.py", "cwd": "/", "starter_argv": STARTER}, self.root,
                                         run=self.run_with(), get=get, pause=naps.append)
        self.assertEqual(self.ran, [STARTER])                                  # the script is not run from this session
        self.assertEqual(asked, [(8082, "/health")] * 3 + [(8082, "/slots")])
        self.assertEqual(len(naps), 2)
        self.assertEqual(ready, {"outcome": "GPU_READY", "via": "starter_argv", "slots": [{"id": i, "n_ctx": 16384} for i in range(3)]})

    def test_a_starter_that_fails_or_a_server_that_never_answers_is_an_error(self):
        old = {"launcher": "/x/start.py", "cwd": "/", "starter_argv": STARTER}
        with self.assertRaises(RuntimeError):
            lifecycle.start_original(old, self.root / "a", run=self.run_with(code=1), get=lambda *a: (200, b'{"status": "ok"}'))

        def down(port, path="/health"):
            raise OSError("refused")
        with self.assertRaises(RuntimeError):
            lifecycle.start_original(old, self.root / "b", run=self.run_with(), get=down, wait=0, pause=lambda s: None)


if __name__ == "__main__":
    unittest.main()
