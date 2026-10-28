"""Welt's 3D test: render a model's answer in a headless browser and grade it by scene3d.json's twelve checks.

    python3 render3d.py run --answer ANSWER.txt --three three.module.js --browser PATH --out DIR [--no-sandbox]
    python3 render3d.py sheet --out SHEET_DIR ATTEMPT_DIR [ATTEMPT_DIR ...]

run    Takes the answer as the model gave it (reasoning already removed), extracts the page (scene3d.json's rule),
       puts probe3d.js first in it, and serves the page and three.module.js, nothing else, on 127.0.0.1. Then a
       Chromium-family browser (Edge, Chrome, Chromium) runs it headless with a fresh profile and every other
       request blocked. Two probe runs, at 1280x720 and 720x1280, and two screenshots, at 1 s and 3 s. Writes
       page.html, probe-*.json, shot-*.png and checks.json into DIR and prints the checks as one JSON line.
       If the browser is a Windows .exe called from WSL, paths are converted with wslpath; WSL must run in
       mirrored networking mode for the browser to reach the loopback server.
sheet  One contact sheet per seed for Welt: the four configurations under labels A to D, shuffled at random,
       screenshots only. Each ATTEMPT_DIR needs meta.json {"config": ..., "seed": ...}. The key goes into
       key.json beside sheet.html; Welt opens it after looking.

Before grading any model, run the reference scene once on the PC (`selftest.html` in this folder) with the same
browser: it must score 12 of 12, or the harness is not working there. Standard library only.
"""
import argparse
import functools
import hashlib
import html
import http.server
import json
import math
import random
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.parse
from pathlib import Path

HERE = Path(__file__).resolve().parent
CASE = json.loads((HERE / "scene3d.json").read_text(encoding="utf-8"))
SIZES = [tuple(s) for s in CASE["render"]["sizes"]]
SHOTS = CASE["render"]["screenshots_ms"]
HOLD = CASE["render"]["probe_load_held_ms"]
GIF = bytes.fromhex("47494638396101000100800000000000ffffff21f90401000000002c00000000010001000002024401003b")
CHECKS = list(CASE["checks"])
PLANETS = ["planet1", "planet2", "planet3"]


# ---- the page ----------------------------------------------------------------------------------------------------

def extract(answer):
    """scene3d.json: the first ```html fenced block if there is one, else the whole answer."""
    m = re.search(r"```html[ \t]*\r?\n(.*?)```", answer, re.S | re.I)
    return (m.group(1), True) if m else (answer, False)


def inject(page, probe):
    tag = "<script>\n" + probe + "\n</script>\n"
    for pat in (r"<head\b[^>]*>", r"<html\b[^>]*>"):
        m = re.search(pat, page, re.I)
        if m:
            return page[:m.end()] + "\n" + tag + page[m.end():]
    return tag + page


class Quiet(http.server.SimpleHTTPRequestHandler):
    """Serves the page and three.js; /__wait?ms=N answers with a 1x1 image after N ms, holding the load event."""

    def log_message(self, *args):
        pass

    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        if url.path != "/__wait":
            return super().do_GET()
        ms = min(10000, int((urllib.parse.parse_qs(url.query).get("ms") or ["0"])[0]))
        time.sleep(ms / 1000)
        self.send_response(200)
        self.send_header("Content-Type", "image/gif")
        self.send_header("Content-Length", str(len(GIF)))
        self.end_headers()
        self.wfile.write(GIF)


def serve(folder):
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=str(folder)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def winpath(p, browser):
    if str(browser).lower().endswith(".exe") and shutil.which("wslpath"):
        return subprocess.run(["wslpath", "-w", str(p)], capture_output=True, text=True, check=True).stdout.strip()
    return str(p)


def browse(browser, url, size, mode, no_sandbox=False, timeout=120):
    """One headless run in real time; mode is ["--dump-dom"] or ["--screenshot=PATH"]. The browser acts at the load
    event, which the probe holds open for the url's ?wait= milliseconds. Returns (returncode, stdout, stderr)."""
    profile = Path(tempfile.mkdtemp(prefix="scene3d-profile-"))
    try:
        cmd = [str(browser), "--headless", f"--user-data-dir={winpath(profile, browser)}", "--no-first-run",
               "--no-default-browser-check", "--disable-extensions", "--disable-background-networking",
               "--disable-sync", "--disable-component-update", "--mute-audio", "--hide-scrollbars",
               "--force-device-scale-factor=1", "--proxy-server=http://127.0.0.1:9",
               "--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE 127.0.0.1",
               "--use-angle=swiftshader", "--enable-unsafe-swiftshader",
               f"--window-size={size[0]},{size[1]}"]
        if no_sandbox:
            cmd.append("--no-sandbox")
        r = subprocess.run(cmd + mode + [url], capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout, r.stderr
    except subprocess.TimeoutExpired:
        return None, "", "timeout"
    finally:
        shutil.rmtree(profile, ignore_errors=True)


def probe_of(dom):
    found = re.findall(r'<pre id="__probe3d"[^>]*>(.*?)</pre>', dom or "", re.S)
    if not found:
        return None
    try:
        return json.loads(html.unescape(found[-1]))
    except ValueError:
        return None


# ---- the twelve checks -------------------------------------------------------------------------------------------

def sub(a, b): return [a[0] - b[0], a[1] - b[1], a[2] - b[2]]
def dot(a, b): return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
def cross(a, b): return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]
def norm(a): return math.sqrt(dot(a, a))


def unit(a):
    n = norm(a)
    return [x / n for x in a] if n > 1e-12 else None


def angle(a, b):
    ua, ub = unit(a), unit(b)
    if ua is None or ub is None:
        return None
    return math.degrees(math.acos(max(-1.0, min(1.0, dot(ua, ub)))))


def plane_normal(vs):
    """The orbit plane's normal from three radius vectors."""
    n = [x + y for x, y in zip(cross(vs[0], vs[1]), cross(vs[1], vs[2]))]
    return unit(n)


def acute(a, b):
    """Angle between two planes' normals, 0 to 90 degrees."""
    return math.degrees(math.acos(min(1.0, abs(dot(a, b)))))


def checks(land, port):
    """land and port are the probe results at 1280x720 and 720x1280. Returns ({check: bool}, measures).
    Each check needs only its own objects: a misnamed moon costs "loads" and "moon", not the planets' checks."""
    res = {c: False for c in CHECKS}
    info = {}
    ss = (land or {}).get("samples") or []
    errs = list((land or {}).get("errors") or []) + list((port or {}).get("errors") or [])
    info["errors"] = errs[:10]
    info["frames"] = (land or {}).get("frames")
    ok3 = len(ss) == 3 and all(s.get("scene") and s.get("camera") for s in ss)

    def have(*names):
        return ok3 and all(n in (s.get("pos") or {}) for s in ss for n in names)

    res["loads"] = have("sun", *PLANETS, "moon") and not errs
    info["nonModal_1s"] = ss[0].get("nonModal") if ss else None
    res["renders"] = bool(ss) and (ss[0].get("nonModal") or 0) >= 0.001
    info["changed_px_3s"] = ss[2].get("changedVsFirst") if len(ss) == 3 else None
    if len(ss) == 3:
        moved = any(norm(sub(ss[2]["pos"][p], ss[0]["pos"][p])) > 1e-6
                    for p in PLANETS if all(p in (s.get("pos") or {}) for s in ss))
        res["animates"] = moved and (ss[2].get("changedVsFirst") or 0) >= 50
    if not have("sun"):
        return res, fills(res, info, land, port)
    sun = [s["pos"]["sun"] for s in ss]
    dt = [(ss[i + 1]["t"] - ss[i]["t"]) / 1000 for i in range(2)]
    there = [p for p in PLANETS if have(p)]
    vec = {p: [sub(s["pos"][p], sun[i]) for i, s in enumerate(ss)] for p in there}
    r = {p: [norm(v) for v in vec[p]] for p in there}
    mean_r = {p: sum(r[p]) / 3 for p in there}
    omega, normal = {}, {}
    for p in there:
        a = [angle(vec[p][i], vec[p][i + 1]) for i in range(2)]
        omega[p] = None if None in a else (a[0] / dt[0] + a[1] / dt[1]) / 2
        normal[p] = plane_normal(vec[p])
    info["omega_deg_s"] = omega
    if len(there) == 3:
        steady = all(min(r[p]) > 0 and max(r[p]) / min(r[p]) <= 1.05 for p in PLANETS)
        turned = all((angle(vec[p][0], vec[p][2]) or 0) >= 5 for p in PLANETS)
        res["orbits"] = steady and turned and mean_r["planet1"] < mean_r["planet2"] < mean_r["planet3"]
        if None not in omega.values():
            res["order"] = omega["planet1"] > omega["planet2"] > omega["planet3"]
            periods = {p: (360 / omega[p] if omega[p] > 0 else math.inf) for p in PLANETS}
            info["periods_s"] = periods
            res["periods"] = all(3.6 <= periods[p] <= 22 for p in PLANETS)
    inner = None
    if normal.get("planet1") and normal.get("planet2"):
        n1, n2 = normal["planet1"], normal["planet2"]
        n2 = n2 if dot(n1, n2) >= 0 else [-x for x in n2]
        inner = unit([a + b for a, b in zip(n1, n2)])
        tilt = {"planet1_planet2": acute(n1, n2)}
        if normal.get("planet3"):
            tilt["planet3"] = acute(normal["planet3"], inner)
            res["tilt"] = tilt["planet1_planet2"] <= 5 and 15 <= tilt["planet3"] <= 25
        info["tilt_deg"] = tilt
    if have("planet2", "moon"):
        mv = [sub(s["pos"]["moon"], s["pos"]["planet2"]) for s in ss]
        md = [norm(v) for v in mv]
        turns = [angle(mv[i], mv[i + 1]) for i in range(2)]
        info["moon_turns_deg"] = turns
        res["moon"] = (min(md) > 0 and max(md) / min(md) <= 1.05 and sum(md) / 3 < 0.5 * mean_r["planet2"]
                       and None not in turns and min(turns) >= 30)
    if "planet1" in mean_r:
        lit = all(any(norm(sub(l, sun[i])) <= 0.05 * mean_r["planet1"] for l in s.get("lights") or [])
                  for i, s in enumerate(ss))
        res["light"] = lit and all(s.get("sunGlows") for s in ss)
    info["stars"] = ss[0].get("stars")
    res["stars"] = (ss[0].get("stars") or 0) >= 200
    if inner is not None and all(s.get("cam") and s.get("sunNdc") for s in ss):
        rel = [sub(s["cam"], sun[i]) for i, s in enumerate(ss)]
        flat = [sub(v, [dot(v, inner) * x for x in inner]) for v in rel]
        circled = angle(flat[0], flat[2])
        elev = [math.degrees(math.asin(min(1.0, abs(dot(unit(v), inner))))) if unit(v) else None for v in rel]
        centred = all(abs(s["sunNdc"][0]) <= 0.3 and abs(s["sunNdc"][1]) <= 0.3 and -1 <= s["sunNdc"][2] <= 1
                      for s in ss)
        info["camera"] = {"circled_deg": circled, "elevation_deg": elev, "sun_ndc": [s["sunNdc"] for s in ss]}
        res["camera"] = (circled is not None and circled >= 1 and centred
                         and None not in elev and all(10 <= e <= 80 for e in elev))
    return res, fills(res, info, land, port)


def fills(res, info, land, port):
    ok = []
    for probe in (land, port):
        last = ((probe or {}).get("samples") or [None])[-1]
        if not last or not last.get("canvas") or not last.get("aspect"):
            ok.append(False)
            continue
        w, h = last["win"]
        cw, ch = last["canvas"][2], last["canvas"][3]
        ok.append(abs(cw - w) <= 2 and abs(ch - h) <= 2 and abs(last["aspect"] - w / h) / (w / h) <= 0.02)
    res["fills"] = all(ok)
    info["fills"] = ok
    return info


# ---- run and sheet -----------------------------------------------------------------------------------------------

def run(args):
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    three = Path(args.three).read_bytes()
    if hashlib.sha256(three).hexdigest() != CASE["three"]["sha256"]:
        sys.exit("three.module.js is not the pinned file (scene3d.json); refusing to run")
    answer = Path(args.answer).read_text(encoding="utf-8", errors="replace")
    page, fenced = extract(answer)
    (out / "page.html").write_text(page, encoding="utf-8")
    result = {"fenced": fenced, "score": 0, "checks": {c: False for c in CHECKS}}
    if "<" not in page or not page.strip():
        result["note"] = "no page in the answer"
    else:
        site = Path(tempfile.mkdtemp(prefix="scene3d-site-"))
        try:
            (site / "index.html").write_text(inject(page, (HERE / "probe3d.js").read_text(encoding="utf-8")),
                                             encoding="utf-8")
            (site / CASE["three"]["served_as"]).write_bytes(three)
            srv = serve(site)
            url = f"http://127.0.0.1:{srv.server_address[1]}/index.html?wait="
            try:
                probes = []
                for size in SIZES:
                    code, dom, err = browse(args.browser, url + str(HOLD), size, ["--dump-dom"], args.no_sandbox)
                    p = probe_of(dom)
                    probes.append(p)
                    name = f"probe-{size[0]}x{size[1]}.json"
                    (out / name).write_text(json.dumps(p if p is not None else {"missing": True, "returncode": code,
                                                                                  "stderr": err[-2000:]}), encoding="utf-8")
                for ms in SHOTS:
                    shot = (out / f"shot-{ms}.png").resolve()
                    browse(args.browser, url + str(ms), CASE["render"]["screenshot_size"],
                           [f"--screenshot={winpath(shot, args.browser)}"], args.no_sandbox)
            finally:
                srv.shutdown()
                srv.server_close()
        finally:
            shutil.rmtree(site, ignore_errors=True)
        res, info = checks(probes[0], probes[1])
        result.update(checks=res, score=sum(res.values()), info=info)
    (out / "checks.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"score": result["score"], "of": len(CHECKS), "checks": result["checks"]}))


def sheet(args):
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    rng = random.SystemRandom()
    by_seed = {}
    for d in map(Path, args.attempts):
        meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
        by_seed.setdefault(meta["seed"], []).append((meta["config"], d))
    key, rows = {}, []
    for seed in sorted(by_seed):
        group = by_seed[seed][:]
        rng.shuffle(group)
        cells = []
        for label, (config, d) in zip("ABCDEFGH", group):
            key[f"{seed}-{label}"] = config
            imgs = []
            for ms in SHOTS:
                src = d / f"shot-{ms}.png"
                name = f"seed{seed}-{label}-{ms}.png"
                if src.exists():
                    shutil.copyfile(src, out / name)
                    imgs.append(f'<img src="{name}" alt="{label} at {ms / 1000:g} s">')
                else:
                    imgs.append(f"<p>no screenshot at {ms / 1000:g} s</p>")
            cells.append(f"<td><h3>{label}</h3>{''.join(imgs)}</td>")
        rows.append(f"<h2>Seed {seed}</h2><table><tr>{''.join(cells)}</tr></table>")
    page = ("<!doctype html><meta charset='utf-8'><title>3D test, blind</title><style>body{font:15px sans-serif;"
            "background:#111;color:#eee;margin:16px}td{vertical-align:top;padding:6px}img{width:320px;display:block;"
            "margin-bottom:6px}</style><h1>Welt's 3D test: four models, labels shuffled per seed</h1>"
            "<p>Screenshots at 1 s and 3 s. The key is in key.json; look first.</p>" + "".join(rows))
    (out / "sheet.html").write_text(page, encoding="utf-8")
    (out / "key.json").write_text(json.dumps(key, indent=2), encoding="utf-8")
    print(json.dumps({"sheet": str(out / "sheet.html"), "seeds": sorted(by_seed)}))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    s = p.add_subparsers(dest="cmd", required=True)
    r = s.add_parser("run")
    r.add_argument("--answer", required=True)
    r.add_argument("--three", required=True)
    r.add_argument("--browser", required=True)
    r.add_argument("--out", required=True)
    r.add_argument("--no-sandbox", action="store_true", help="only where the browser must run as root")
    h = s.add_parser("sheet")
    h.add_argument("--out", required=True)
    h.add_argument("attempts", nargs="+")
    args = p.parse_args()
    run(args) if args.cmd == "run" else sheet(args)


if __name__ == "__main__":
    main()
