"""The rehearsal over many days: `simulate --days`, `--set`, `--docs`, the stand-ins, the seed in HTTPMind's payload, and tools/fork_diff.py."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
import fork_diff  # noqa: E402

from world import __main__ as cli  # noqa: E402
from world.config import Config  # noqa: E402
from world.mind import HTTPMind, StubHome, StubMind, StubNo, StubWalker  # noqa: E402

START = "2026-10-03"
ENV = {k: v for k, v in os.environ.items() if not k.startswith("HEGEL_")} | {"HEGEL_ENV": "/nonexistent", "HEGEL_STATE": ""}


def simulate(out, *args, date=START):
    env = dict(ENV, HEGEL_STATE=str(Path(out) / "log"))      # keep the world.log of main() off the real state folder
    p = subprocess.run([sys.executable, "-m", "world", "simulate", "--date", date, "--out", str(out), *args], cwd=REPO, env=env,
                       capture_output=True, text=True)
    assert p.returncode == 0, p.stderr[-2000:]
    return p.stdout


def load(out, d):
    day = json.loads((Path(out) / "days" / f"{d}.json").read_text(encoding="utf-8"))
    for s in day["steps"]:
        s.get("mind", {}).pop("latency_s", None)            # wall time
    return day


class Folders(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        cls.runs = {}

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    @classmethod
    def run_once(cls, name, *args, **kw):
        if name not in cls.runs:
            cls.runs[name] = simulate(cls.tmp / name, *args, **kw)
        return cls.tmp / name


class Days(Folders):
    def test_one_day_is_what_a_longer_run_wrote_for_its_first_day(self):
        one, two = self.run_once("one", "--days", "1"), self.run_once("two", "--days", "2")
        self.assertEqual(load(one, START), load(two, START))

    def test_the_second_day_starts_from_what_the_first_left(self):
        two = self.run_once("two", "--days", "2")
        d1, d2 = load(two, START), load(two, "2026-10-04")
        self.assertEqual(d2["n"], d1["n"] + 1)
        self.assertEqual(d2["opening"]["cash"], d1["state"]["imprest"])
        self.assertTrue(d1["owl"] and d2["owl"])             # the owl after each day

    def test_output_has_one_line_per_day_and_the_seconds(self):
        out = self.run_once("two", "--days", "2").name and self.runs["two"].splitlines()
        self.assertEqual(sum(1 for x in out if x.startswith("day ")), 2)
        self.assertRegex(out[-1], r"^2 day\(s\) in [\d.]+s$")

    def test_set_turns_a_switch_on_in_the_rehearsals_world(self):
        sim = cli.rehearsal_config(Path("/tmp/x"), sets=cli.parse_sets(["HEGEL_CULTURE=1", "HEGEL_DECISION_DRAWS=4"], seed=7))
        self.assertTrue(sim.culture and cli.make_world(sim).culture)
        self.assertEqual((sim.decision_draws, sim.seed, sim.push, sim.pause_away), (4, 7, False, False))
        self.assertFalse(cli.make_world(cli.rehearsal_config(Path("/tmp/x"))).culture if not os.environ.get("HEGEL_CULTURE") else False)
        for bad in ("CULTURE=1", "HEGEL_PUSH=1", "HEGEL_STATE=/x", "HEGEL_PAUSE_AWAY=1", "nothing"):
            with self.assertRaises(SystemExit):
                cli.parse_sets([bad])

    def test_culture_changes_the_days(self):
        plain, culture = self.run_once("two", "--days", "2"), self.run_once("cult", "--days", "2", "--set", "HEGEL_CULTURE=1")
        self.assertIn("listings", json.dumps(load(culture, "2026-10-04")["steps"]))          # the day's listings reach his morning
        self.assertNotIn("listings", json.dumps(load(plain, "2026-10-04")["steps"]))
        self.assertNotEqual(load(plain, "2026-10-04")["steps"], load(culture, "2026-10-04")["steps"])


class Forks(Folders):
    def test_two_forks_of_the_same_morning_are_identical(self):
        base = self.run_once("base", "--days", "2")
        a = self.run_once("fa", "--days", "2", "--docs", str(base), date="2026-10-05")
        b = self.run_once("fb", "--days", "2", "--docs", str(base), date="2026-10-05")
        self.assertTrue(a and b)
        r = fork_diff.compare(self.tmp / "fa", self.tmp / "fb")
        self.assertTrue(r["identical"], r["first"])
        self.assertEqual(fork_diff.main([str(self.tmp / "fa"), str(self.tmp / "fb")]), 0)

    def test_a_fork_that_changes_nothing_continues_the_original(self):
        base = self.run_once("base3", "--days", "3")
        self.run_once("fork3", "--days", "1", "--docs", str(base), date="2026-10-05")
        self.assertEqual(load(base, "2026-10-05"), load(self.tmp / "fork3", "2026-10-05"))

    def test_stub_against_walker_differs_and_names_the_first_moment(self):
        base = self.run_once("base", "--days", "2")
        stub = self.run_once("fs", "--days", "1", "--docs", str(base), date="2026-10-05")
        walker = self.run_once("fw", "--days", "1", "--mind", "stub:walker", "--docs", str(base), date="2026-10-05")
        r = fork_diff.compare(stub, walker)
        self.assertFalse(r["identical"])
        self.assertEqual(r["first"]["date"], "2026-10-05")
        self.assertRegex(r["first"]["t"], r"^\d\d:\d\d$")
        self.assertEqual(fork_diff.main([str(stub), str(walker)]), 1)

    def test_the_stopwatch_is_not_compared(self):
        base = self.run_once("base", "--days", "2")
        copy = self.tmp / "slow"
        shutil.copytree(base, copy, dirs_exist_ok=True)
        for p in (copy / "days").glob("2026-10-0?.json"):
            day = json.loads(p.read_text(encoding="utf-8"))
            for s in day.get("steps", []):
                if "mind" in s:
                    s["mind"]["latency_s"] = 99.9
            p.write_text(json.dumps(day, ensure_ascii=False, indent=1), encoding="utf-8")
        self.assertTrue(fork_diff.compare(base, copy)["identical"])

    def test_a_state_only_difference_names_the_keys(self):
        base = self.run_once("base", "--days", "2")
        copy = self.tmp / "dirty"
        shutil.copytree(base, copy, dirs_exist_ok=True)
        p = copy / "days" / "2026-10-04.json"
        day = json.loads(p.read_text(encoding="utf-8"))
        day["state"]["imprest"] += 1
        p.write_text(json.dumps(day, ensure_ascii=False, indent=1), encoding="utf-8")
        r = fork_diff.compare(base, copy)
        self.assertEqual(r["first"], {"date": "2026-10-04", "state": ["imprest"]})

    def test_docs_brings_the_look_up_caches(self):
        base = self.tmp / "withcache"
        shutil.copytree(self.run_once("base", "--days", "2"), base, dirs_exist_ok=True)
        (base / "state" / "lookup").mkdir(parents=True)
        (base / "state" / "lookup" / "karl-marx.json").write_text("{}", encoding="utf-8")
        self.run_once("fc", "--days", "1", "--docs", str(base), date="2026-10-05")
        self.assertTrue((self.tmp / "fc" / "state" / "lookup" / "karl-marx.json").exists())
        with self.assertRaises(SystemExit):
            cli.rehearsal_setup(Config(), "2026-10-05", base.resolve(), docs=str(base))


def sit(**kw):
    s = dict(id="s1", day="Saturday 3 October", time="10:00", place="home", open_now=["home", "lodhi", "khan"], event="", imprest_left=500, present=[],
             on_mind=[], for_sale=[])
    s.update(kw)
    return s


class StandIns(unittest.TestCase):
    CHOICE = {"type": "object", "properties": {"answer": {"type": "string"}}}

    def test_no_declines_every_choice_and_yes_is_still_yes(self):
        self.assertEqual(json.loads(StubNo().chat([], self.CHOICE)), {"answer": "no"})
        self.assertEqual(json.loads(StubMind().chat([], self.CHOICE)), {"answer": "yes"})

    def test_home_stays_when_the_stub_would_stroll_and_goes_for_a_booking(self):
        for i in range(40):
            s = sit(id=f"x{i}")
            a = json.loads(StubHome().decide([], s))
            self.assertEqual(a["place"], "home", a)
            self.assertTrue(a["thought"].startswith("(rehearsal) "))
        booked = sit(on_mind=["Saturday 3 October 10:30: your talk at the IIC"], open_now=["home", "iic"])
        self.assertEqual(json.loads(StubHome().decide([], booked))["place"], "iic")

    def test_walker_goes_to_the_place_it_has_been_to_least(self):
        w, went = StubWalker(), []
        for i in range(6):
            a = json.loads(w.decide([], sit(id=f"w{i}", time="10:00")))
            self.assertEqual(a["action"], "walk")
            self.assertTrue(a["thought"].startswith("(rehearsal) "))
            went.append(a["place"])
        self.assertEqual(went, ["khan", "lodhi", "khan", "lodhi", "khan", "lodhi"])         # ties by name; each walk counts
        self.assertEqual(json.loads(StubWalker().decide([], sit(time="21:00")))["action"], "sleep")
        self.assertEqual(json.loads(StubWalker().decide([], sit(open_now=["home"])))["place"], "home")

    def test_make_mind_knows_the_stand_ins(self):
        cfg = Config({"HEGEL_ENV": "/nonexistent"})
        for name, cls in (("stub", StubMind), ("stub:no", StubNo), ("stub:home", StubHome), ("stub:walker", StubWalker)):
            self.assertIs(type(cli.make_mind(cfg, name)), cls)
        with self.assertRaises(SystemExit):
            cli.make_mind(cfg, "stub:flying")


class Seeds(unittest.TestCase):
    @staticmethod
    def reply(url):
        r = mock.MagicMock()
        r.__enter__.return_value = r
        r.read.return_value = json.dumps({"choices": [{"message": {"content": "ok"}}], "content": "ok"}).encode()
        return r

    def payloads(self, mind, calls):
        sent = []

        def fake(req, timeout=None):
            sent.append(json.loads(req.data.decode()))
            return self.reply(req)
        with mock.patch("urllib.request.urlopen", fake), mock.patch.object(HTTPMind, "ensure_awake", lambda self: None):
            for kind, kw in calls:
                getattr(mind, kind)(*(["hi"] if kind == "complete" else [[{"role": "user", "content": "hi"}]]), **kw)
        return sent

    CALLS = [("chat", {}), ("complete", {}), ("chat", {}), ("complete", {"seed": 5}), ("chat", {"seed": 6})]

    def test_without_a_base_seed_the_payload_is_what_it_was(self):
        sent = self.payloads(HTTPMind("http://x"), self.CALLS)
        self.assertEqual(["seed" in p for p in sent], [False, False, False, True, True])
        self.assertEqual([p.get("seed") for p in sent[3:]], [5, 6])

    def test_with_a_base_seed_every_call_without_its_own_sends_a_derived_one(self):
        a, b = self.payloads(HTTPMind("http://x", seed=1831), self.CALLS), self.payloads(HTTPMind("http://x", seed=1831), self.CALLS)
        self.assertEqual(a, b)
        seeds = [p["seed"] for p in a]
        self.assertEqual(seeds[3:], [5, 6])
        self.assertEqual(len(set(seeds[:3])), 3)
        self.assertTrue(all(isinstance(x, int) and 0 <= x < 2 ** 31 for x in seeds))
        self.assertNotEqual(seeds[:3], [p["seed"] for p in self.payloads(HTTPMind("http://x", seed=1832), self.CALLS)[:3]])

    def test_the_config_and_make_mind_carry_the_seed(self):
        cfg = Config({"HEGEL_ENV": "/nonexistent", "HEGEL_SEED": "42", "MIND_URL": "http://x"})
        self.assertEqual(cfg.seed, 42)
        self.assertEqual(cli.make_mind(cfg, None, wake=False).seed, 42)
        self.assertIsNone(Config({"HEGEL_ENV": "/nonexistent", "HEGEL_SEED": ""}).seed if "HEGEL_SEED" not in os.environ else None)


if __name__ == "__main__":
    unittest.main()
