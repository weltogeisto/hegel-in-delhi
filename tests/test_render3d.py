"""Welt's 3D test (pc/qwen-trial): the twelve checks on made-up probe results, the page handling, the blind sheet,
and, where a Chromium is at hand, the real harness on the reference scene and on a broken page."""
import importlib.util
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TRIAL = Path(__file__).resolve().parent.parent / "pc" / "qwen-trial"
spec = importlib.util.spec_from_file_location("render3d", TRIAL / "render3d.py")
render3d = importlib.util.module_from_spec(spec)
spec.loader.exec_module(render3d)


def orrery(tilt=20, periods=(6, 10, 16), moon_period=3, moon_of="planet2", stars=400, cam_speed=0.05,
           ndc=(0.0, 0.0), still=False, drop=(), win=(1280, 633), aspect=None):
    """Probe results for an ideal scene, sampled at 1, 2 and 3 s, with one thing changed where asked."""
    samples = []
    for t in (1.0, 2.0, 3.0):
        tt = 0.0 if still else t
        pos = {"sun": [0.0, 0.0, 0.0]}
        for name, r, period in zip(("planet1", "planet2", "planet3"), (8, 13, 19), periods):
            a = tt / period * 2 * math.pi
            x, z = r * math.cos(a), r * math.sin(a)
            if name == "planet3":
                k = math.radians(tilt)
                pos[name] = [x, -z * math.sin(k), z * math.cos(k)]
            else:
                pos[name] = [x, 0.0, z]
        m = tt / moon_period * 2 * math.pi
        centre = pos[moon_of]
        pos["moon"] = [centre[0] + 2.4 * math.cos(m), centre[1], centre[2] + 2.4 * math.sin(m)]
        for name in drop:
            pos.pop(name)
        c = tt * cam_speed
        samples.append({
            "t": int(t * 1000), "win": list(win), "scene": True, "camera": True,
            "canvas": [0, 0, win[0], win[1], win[0], win[1]], "nonModal": 0.01,
            "changedVsFirst": None if t == 1.0 else (0 if still else 7000),
            "pos": pos, "lights": [[0.0, 0.0, 0.0]], "stars": stars, "sunGlows": True,
            "cam": [40 * math.cos(c), 25.0, 40 * math.sin(c)], "aspect": aspect or win[0] / win[1],
            "sunNdc": [ndc[0], ndc[1], 0.99]})
    return {"why": "samples", "frames": 90, "errors": [], "samples": samples}


def failed(land, port=None):
    res, _ = render3d.checks(land, port or orrery(win=(720, 1193)))
    return sorted(k for k, v in res.items() if not v)


class ChecksTest(unittest.TestCase):
    def test_the_ideal_scene_passes_all_twelve(self):
        res, info = render3d.checks(orrery(), orrery(win=(720, 1193)))
        self.assertEqual(sorted(res), sorted(render3d.CHECKS))
        self.assertEqual(len(res), 12)
        self.assertTrue(all(res.values()), info)
        self.assertAlmostEqual(info["tilt_deg"]["planet3"], 20, places=6)
        self.assertAlmostEqual(info["periods_s"]["planet2"], 10, places=6)

    def test_each_fault_costs_its_own_check(self):
        self.assertEqual(failed(orrery(tilt=0)), ["tilt"])
        self.assertEqual(failed(orrery(tilt=40)), ["tilt"])
        self.assertEqual(failed(orrery(periods=(16, 10, 6))), ["order"])
        self.assertEqual(failed(orrery(periods=(3, 3.3, 3.5))), ["periods"])
        self.assertEqual(failed(orrery(moon_of="sun")), ["moon"])
        self.assertEqual(failed(orrery(stars=150)), ["stars"])
        self.assertEqual(failed(orrery(ndc=(0.5, 0.0))), ["camera"])
        self.assertEqual(failed(orrery(cam_speed=0)), ["camera"])
        self.assertEqual(failed(orrery(), orrery(win=(720, 1193), aspect=16 / 9)), ["fills"])

    def test_an_error_or_a_missing_name_costs_loads_and_what_needs_it(self):
        land = orrery()
        land["errors"] = ["console: THREE.WebGLProgram: Shader Error"]
        self.assertEqual(failed(land), ["loads"])
        self.assertEqual(failed(orrery(drop=("moon",))), ["loads", "moon"])
        self.assertEqual(failed(orrery(drop=("planet3",))), ["loads", "orbits", "order", "periods", "tilt"])

    def test_a_still_scene_keeps_only_what_needs_no_motion(self):
        self.assertEqual(failed(orrery(still=True)),
                         ["animates", "camera", "moon", "orbits", "order", "periods", "tilt"])

    def test_nothing_measured_is_zero(self):
        res, _ = render3d.checks(None, None)
        self.assertFalse(any(res.values()))
        res, _ = render3d.checks({"errors": [], "samples": []}, {"errors": [], "samples": []})
        self.assertFalse(any(res.values()))


class PageTest(unittest.TestCase):
    def test_the_first_html_fence_or_else_the_whole_answer(self):
        self.assertEqual(render3d.extract("Here:\n```html\n<p>a</p>\n```\n```html\n<p>b</p>\n```"), ("<p>a</p>\n", True))
        self.assertEqual(render3d.extract("<!doctype html><p>a</p>"), ("<!doctype html><p>a</p>", False))

    def test_the_probe_goes_first(self):
        self.assertTrue(render3d.inject("<html><HEAD><title>x</title>", "P").startswith("<html><HEAD>\n<script>\nP\n"))
        self.assertTrue(render3d.inject("<html lang=en><body>", "P").startswith("<html lang=en>\n<script>\nP\n"))
        self.assertTrue(render3d.inject("<canvas></canvas>", "P").startswith("<script>\nP\n"))

    def test_the_probe_result_is_the_last_one_in_the_page(self):
        dom = '<pre id="__probe3d">{"x": 1}</pre> ... <pre id="__probe3d" style="display: none;">{&quot;y&quot;: 2}</pre>'
        self.assertEqual(render3d.probe_of(dom), {"y": 2})
        self.assertIsNone(render3d.probe_of("<html></html>"))

    def test_the_pinned_three_is_beside_the_harness(self):
        import hashlib
        data = (TRIAL / "three.module.js").read_bytes()
        self.assertEqual(len(data), render3d.CASE["three"]["bytes"])
        self.assertEqual(hashlib.sha256(data).hexdigest(), render3d.CASE["three"]["sha256"])


class SheetTest(unittest.TestCase):
    def test_four_shuffled_labels_per_seed_and_the_key_apart(self):
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp)
        dirs = []
        for config in ("trial-qwen", "trial-nanbeige", "trial-arex", "trial-swift"):
            for seed in (101, 202):
                d = tmp / f"{config}-{seed}"
                d.mkdir()
                (d / "meta.json").write_text(json.dumps({"config": config, "seed": seed}))
                for ms in render3d.SHOTS:
                    (d / f"shot-{ms}.png").write_bytes(b"png")
                dirs.append(str(d))
        out = tmp / "sheet"
        subprocess.run([sys.executable, str(TRIAL / "render3d.py"), "sheet", "--out", str(out)] + dirs,
                       check=True, capture_output=True)
        key = json.loads((out / "key.json").read_text())
        self.assertEqual(sorted(key), [f"{s}-{l}" for s in (101, 202) for l in "ABCD"])
        for seed in (101, 202):
            self.assertEqual(sorted(key[f"{seed}-{l}"] for l in "ABCD"),
                             ["trial-arex", "trial-nanbeige", "trial-qwen", "trial-swift"])
        page = (out / "sheet.html").read_text()
        self.assertNotIn("trial-", page)                                              # blind
        self.assertIn("seed101-A-1000.png", page)


class GateTest(unittest.TestCase):
    """The browser's only way out serves the page and three.js on the made-up origin, and refuses everything else."""

    def ask(self, raw):
        import socket
        srv = render3d.serve("<p>page</p>", b"three")
        self.addCleanup(srv.server_close)
        self.addCleanup(srv.shutdown)
        with socket.create_connection(srv.server_address) as c:
            c.sendall(raw.encode())
            got = b""
            while chunk := c.recv(4096):
                got += chunk
        return got.decode(errors="replace"), srv.refused

    def test_the_page_and_three_on_the_origin(self):
        got, refused = self.ask(f"GET http://{render3d.ORIGIN}/index.html HTTP/1.0\r\n\r\n")
        self.assertIn(" 200 ", got.splitlines()[0])
        self.assertTrue(got.endswith("<p>page</p>"))
        got, _ = self.ask(f"GET http://{render3d.ORIGIN}/three.module.js HTTP/1.0\r\n\r\n")
        self.assertIn("text/javascript", got)
        self.assertEqual(refused, [])

    def test_everything_else_is_refused_and_noted(self):
        for raw in ("GET http://127.0.0.1:8090/completion HTTP/1.0\r\n\r\n",
                    "CONNECT 127.0.0.1:8090 HTTP/1.0\r\n\r\n",
                    f"POST http://{render3d.ORIGIN}/index.html HTTP/1.0\r\nContent-Length: 0\r\n\r\n",
                    f"GET http://{render3d.ORIGIN}/../../secret HTTP/1.0\r\n\r\n",
                    "GET https://example.com/ HTTP/1.0\r\n\r\n"):
            got, refused = self.ask(raw)
            self.assertIn(" 403 ", got.splitlines()[0], raw)
            self.assertEqual(len(refused), 1, raw)


def chromium():
    for c in (os.environ.get("SCENE3D_BROWSER"), "/opt/pw-browsers/chromium-1194/chrome-linux/chrome",
              shutil.which("chromium"), shutil.which("google-chrome")):
        if c and Path(c).exists():
            return c
    return None


@unittest.skipUnless(chromium(), "no Chromium here; set SCENE3D_BROWSER to run the harness for real")
class HarnessTest(unittest.TestCase):
    def grade(self, answer):
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp)
        (tmp / "answer.txt").write_text(answer)
        cmd = [sys.executable, str(TRIAL / "render3d.py"), "run", "--answer", str(tmp / "answer.txt"),
               "--three", str(TRIAL / "three.module.js"), "--browser", chromium(), "--out", str(tmp / "out")]
        if hasattr(os, "geteuid") and os.geteuid() == 0:
            cmd.append("--no-sandbox")
        subprocess.run(cmd, check=True, capture_output=True, timeout=300)
        return json.loads((tmp / "out" / "checks.json").read_text()), tmp / "out"

    def test_the_reference_scene_scores_twelve_and_a_broken_page_nothing(self):
        page = (TRIAL / "selftest.html").read_text()
        got, out = self.grade(page)
        self.assertEqual(got["score"], 12, got)
        self.assertTrue((out / "shot-1000.png").stat().st_size > 1000)
        got, _ = self.grade("```html\n" + page.replace("new THREE.Clock();", "new THREE.Clock(;") + "\n```")
        self.assertEqual(got["score"], 0, got)
        self.assertTrue(got["fenced"])
        self.assertTrue(any("SyntaxError" in e for e in got["info"]["errors"]))

    def test_a_page_reaches_nothing_but_the_gate(self):
        cmd = [sys.executable, str(TRIAL / "render3d.py"), "leaktest", "--browser", chromium()]
        if hasattr(os, "geteuid") and os.geteuid() == 0:
            cmd.append("--no-sandbox")
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        got = json.loads(r.stdout)
        self.assertEqual(r.returncode, 0, got)
        self.assertTrue(got["page_ran"] and got["isolated"], got)
        self.assertEqual(got["webrtc"]["candidates"], 0, got)
        self.assertGreaterEqual(got["page_open_ms"], 5000, got)


if __name__ == "__main__":
    unittest.main()
