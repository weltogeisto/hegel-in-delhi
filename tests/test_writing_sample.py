"""Tests for tools/writing_sample.py: a plan through the world's plain-text writing path, against a stand-in mind and a fake llama-server."""
import contextlib
import io
import json
import subprocess
import sys
import threading
import unittest
from datetime import date
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from test_deal import NOTE6, PROSE, SITTING, Talker, one_step  # noqa: E402  (this also keeps the tests off the Pi's env file)
from test_world import REPO  # noqa: E402

import writing_sample as ws  # noqa: E402
from world import works  # noqa: E402
from world.mind import MindAway, StubMind  # noqa: E402

LOOPS = {"repeat_penalty": 1.1, "repeat_last_n": 256, "dry_multiplier": 0.8}


def run(argv, mind=None):
    """(what main prints, what it says on stderr)."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        ws.main(argv, mind)
    return out.getvalue(), err.getvalue()


class Llama(BaseHTTPRequestHandler):
    """Answers /completion with `content` and keeps what it was sent."""
    bodies, content = [], ""

    def log_message(self, *a):
        pass

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Length", "2")
        self.end_headers()
        self.wfile.write(b"{}")

    def do_POST(self):
        Llama.bodies.append((self.path, json.loads(self.rfile.read(int(self.headers["Content-Length"])))))
        data = json.dumps({"content": Llama.content}).encode()
        self.send_response(200)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


class SampleTest(unittest.TestCase):
    def test_the_default_pair_is_the_essay_and_the_letter_with_their_primers_and_notes(self):
        out, err = run(["--date", "2026-10-06"], StubMind())
        self.assertEqual(out.count("-----"), 2)
        essay, letter = (x for x in out.split("-----\n") if x.strip())
        self.assertEqual(err, "")
        for block, head in ((essay, "Hegel, On the noise of the street. Written at Delhi, 6 October 2026."), (letter, "Hegel to Niethammer. Delhi, 6 October 2026.")):
            prompt, sitting = block.split("=== sitting ===\n")
            label, body = prompt.split(") ===\n", 1)
            self.assertTrue(label.startswith("=== prompt (primer: ") and not label.endswith("none"))
            self.assertTrue(any(body.startswith(h) for h in works.PRIMER_HEADS.values()))                  # a passage of his books first, as a document of its own
            self.assertIn("\n\n\n" + head + "\n[", body)
            self.assertIn("\n" + NOTE6 + "\n\n", body)
            self.assertTrue(sitting.startswith(("(rehearsal) ", "Dear Niethammer,\n\n(rehearsal) ")))          # the cleaned sitting: a new letter begins with its salutation
        self.assertTrue(letter.split("=== sitting ===\n")[0].endswith("Dear Niethammer,\n\n\n"))

    def test_it_makes_the_prompt_and_the_sitting_as_the_world_does(self):
        mind = Talker(says=None, action="write", sitting=SITTING, text=PROSE)
        box, e, day, step = one_step(mind, "ramesh", "home")
        try:
            prompt = next(a[0] for k, a in mind.asked if k == "complete")
            book, mine, w, why = ws.sample(Talker(text=PROSE), e.shelf, json.loads(SITTING), {}, date.fromisoformat(day["date"]))
            self.assertTrue(book)
            self.assertEqual((mine, why), (prompt, ""))
            self.assertEqual(w["text"], next(x["text"] for x in day["entries"] if x["k"] == "writing"))
        finally:
            box.close()

    def test_a_plan_that_continues_flows_on_from_the_sitting_before(self):
        plan = {"title": "On the verandah", "kind": "notes", "to": None, "continues": False, "about": "The morning."}
        out, _ = run(["--date", "2026-10-06", "--plan", json.dumps(plan), "--plan", json.dumps(dict(plan, continues=True, about="More of it."))], Talker(text=PROSE))
        first, second = (x for x in out.split("-----\n") if x.strip())
        self.assertTrue(first.split("=== sitting ===")[0].endswith(NOTE6 + "\n\n\n"))
        self.assertTrue(second.split("=== sitting ===")[0].endswith("[More of it.]\n" + NOTE6 + "\n\n" + PROSE + "\n"))      # the tail of the first, which is all of it

    def test_what_is_unusable_says_why(self):
        plan = json.dumps({"title": "On tea", "about": "the tea"})
        for text, why in ((MindAway("HTTP 503 from the mind"), "(unusable) the mind did not answer: HTTP 503 from the mind"), ("", "(unusable) the completion was empty"),
                          ("Too few words here.", "(unusable) fewer than 20 words were left of the completion ('Too few words here.')")):
            with self.subTest(why=why):
                out, _ = run(["--plan", plan], Talker(text=text))
                self.assertIn("=== sitting ===\n" + why + "\n-----\n", out)
        mind = Talker(text=PROSE)
        out, _ = run(["--plan", json.dumps({"title": "On tea"})], mind)
        self.assertIn("(unusable) the plan has no title or no about", out)
        self.assertEqual(mind.asked, [])

    def test_no_shelf_no_primer(self):
        with mock.patch.object(ws.shelf, "load", return_value=None):
            out, err = run(["--date", "2026-10-06"], StubMind())
        self.assertEqual(out.count("=== prompt (primer: none) ==="), 2)
        self.assertIn("no primer", err)
        self.assertTrue(out.split("=== prompt (primer: none) ===\n")[1].startswith("Hegel, On the noise of the street."))

    def test_the_arguments(self):
        for argv in ([], ["--url", "http://x", "--plan", "not json"], ["--url", "http://x", "--plan", "[1]"], ["--url", "http://x", "--date", "tomorrow"]):
            with self.subTest(argv=argv), contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as raised:
                ws.main(argv)
            self.assertEqual(raised.exception.code, 2)


class ScriptTest(unittest.TestCase):
    """The script as it is run on the PC: from the repo root, against llama-server."""

    def test_end_to_end_over_http(self):
        server = HTTPServer(("127.0.0.1", 0), Llama)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        Llama.bodies, Llama.content = [], "\n\n" + PROSE
        try:
            p = subprocess.run([sys.executable, "tools/writing_sample.py", "--url", f"http://127.0.0.1:{server.server_port}", "--date", "2026-10-06", "--seed", "5",
                                "--plan", json.dumps({"title": "On tea", "kind": "essay", "to": None, "continues": False, "about": "the tea at Khan Market"})],
                               cwd=REPO, capture_output=True, text=True, timeout=120)
        finally:
            server.shutdown()
            server.server_close()
        self.assertEqual(p.returncode, 0, p.stderr)
        (path, body), = Llama.bodies
        self.assertEqual(path, "/completion")
        self.assertEqual((body["n_predict"], body["seed"], {k: body[k] for k in LOOPS}), (works.TOKENS, 5, LOOPS))
        self.assertTrue(body["prompt"].endswith("Hegel, On tea. Written at Delhi, 6 October 2026.\n[the tea at Khan Market]\n" + NOTE6 + "\n\n"))
        self.assertTrue(any(body["prompt"].startswith(h) for h in works.PRIMER_HEADS.values()), body["prompt"][:100])
        self.assertEqual(p.stdout, f"=== prompt (primer: {p.stdout.split('primer: ')[1].split(') ===')[0]}) ===\n{body['prompt']}\n=== sitting ===\n{PROSE}\n-----\n")


if __name__ == "__main__":
    unittest.main()
