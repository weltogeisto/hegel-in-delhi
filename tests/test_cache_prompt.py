"""HEGEL_CACHE_PROMPT: HTTPMind's `cache_prompt` field, the Config switch, simulate --seed turning the cache off, and the wants screen's requests."""
import json
import os
import sys
import unittest
from argparse import Namespace
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from tools import wants_screen as ws  # noqa: E402
from world import __main__ as cli  # noqa: E402
from world.config import Config  # noqa: E402
from world.mind import HTTPMind  # noqa: E402

FROZEN = REPO / "pc/exports/m1-screen-20261107"
CALLS = [("chat", {}), ("chat", {"seed": 6}), ("complete", {}), ("complete", {"seed": 5})]


def sent_by(mind):
    sent = []

    def fake(req, timeout=None):
        sent.append(json.loads(req.data.decode()))
        r = mock.MagicMock()
        r.__enter__.return_value = r
        r.read.return_value = json.dumps({"choices": [{"message": {"content": "ok"}}], "content": "ok"}).encode()
        return r
    with mock.patch("urllib.request.urlopen", fake), mock.patch.object(HTTPMind, "ensure_awake", lambda self: None):
        for kind, kw in CALLS:
            getattr(mind, kind)(*(["hi"] if kind == "complete" else [[{"role": "user", "content": "hi"}]]), **kw)
    return sent


def conf(**v):
    return Config({"HEGEL_ENV": "/nonexistent", "HEGEL_CACHE_PROMPT": "", **v})


class Payloads(unittest.TestCase):
    def test_default_adds_no_key(self):
        sent = sent_by(HTTPMind("http://x"))
        self.assertTrue(all("cache_prompt" not in p for p in sent[:2]))        # chat: nothing is said
        self.assertEqual([p["cache_prompt"] for p in sent[2:]], [False, False])   # complete() has always sent False itself, and still does

    def test_false_and_true_are_in_every_payload(self):
        for value in (False, True):
            sent = sent_by(HTTPMind("http://x", cache_prompt=value))
            self.assertEqual([p["cache_prompt"] for p in sent], [value] * 4)

    def test_nothing_else_changes(self):
        for value in (False, True):
            a, b = sent_by(HTTPMind("http://x", seed=3)), sent_by(HTTPMind("http://x", seed=3, cache_prompt=value))
            self.assertEqual([{k: v for k, v in p.items() if k != "cache_prompt"} for p in b], [{k: v for k, v in p.items() if k != "cache_prompt"} for p in a])

    def test_a_bad_value_is_refused(self):
        with self.assertRaises(ValueError):
            HTTPMind("http://x", cache_prompt="no")


class Settings(unittest.TestCase):
    def test_parsing(self):
        for text, want in (("", None), ("  ", None), ("0", False), ("no", False), ("False", False), ("1", True), ("yes", True), ("TRUE", True)):
            self.assertIs(conf(HEGEL_CACHE_PROMPT=text).cache_prompt, want, text)
        for bad in ("2", "maybe", "off"):
            with self.assertRaises(ValueError):
                conf(HEGEL_CACHE_PROMPT=bad)

    def test_make_mind_passes_it(self):
        for text, want in (("", None), ("0", False), ("1", True)):
            cfg = conf(HEGEL_CACHE_PROMPT=text, MIND_URL="http://x")
            self.assertIs(cli.make_mind(cfg, None, wake=False).cache_prompt, want)


class Simulate(unittest.TestCase):
    """cmd_simulate cannot be run against a fake HTTP mind cheaply (it needs a day folder and a whole engine), so this tests seeded_sets, the function
    that builds the rehearsal's settings and its notice, and the Config that rehearsal_config makes of them."""
    NOTICE = "seed 7: the prompt cache is off for this rehearsal, so that the same seed is the same day (HEGEL_CACHE_PROMPT=1 to keep it on)"

    def sets(self, seed=7, mind="http://x", set=None, **env):
        return cli.seeded_sets(conf(**env), Namespace(seed=seed, mind=mind, set=set))

    def test_a_seed_turns_the_cache_off_and_says_so(self):
        sets, notice = self.sets()
        self.assertEqual(notice, self.NOTICE)
        self.assertIs(cli.rehearsal_config(Path("/tmp/x"), sets=sets).cache_prompt, False)
        self.assertEqual(sets["HEGEL_SEED"], "7")

    def test_explicit_settings_win(self):
        for one, want in (("1", True), ("0", False)):
            sets, notice = self.sets(set=[f"HEGEL_CACHE_PROMPT={one}"])
            self.assertIsNone(notice)
            self.assertIs(cli.rehearsal_config(Path("/tmp/x"), sets=sets).cache_prompt, want)
        sets, notice = self.sets(HEGEL_CACHE_PROMPT="1")          # the live Config (env file or environment) names it
        self.assertIsNone(notice)
        self.assertNotIn("HEGEL_CACHE_PROMPT", sets)

    def test_environment_setting_is_kept(self):
        with mock.patch.dict(os.environ, {"HEGEL_CACHE_PROMPT": "1"}):
            sets, notice = cli.seeded_sets(Config({"HEGEL_ENV": "/nonexistent"}), Namespace(seed=7, mind="http://x", set=None))
            self.assertIsNone(notice)
            self.assertIs(cli.rehearsal_config(Path("/tmp/x"), sets=sets).cache_prompt, True)

    def test_without_a_seed_or_with_a_stand_in_nothing_changes(self):
        for kw in ({"seed": None}, {"mind": None}, {"mind": "stub"}, {"mind": "stub:no"}):
            sets, notice = self.sets(**kw)
            self.assertIsNone(notice)
            self.assertNotIn("HEGEL_CACHE_PROMPT", sets)
            self.assertIsNone(cli.rehearsal_config(Path("/tmp/x"), sets=sets).cache_prompt)


class WantsScreen(unittest.TestCase):
    def test_every_request_of_all_three_arms_says_false(self):
        calls = ws.requests(FROZEN)
        self.assertEqual({c[2] for c in calls}, {"A", "A2", "W"})
        self.assertTrue(all(c[4]["cache_prompt"] is False for c in calls))
        self.assertEqual(len(calls), 216)


if __name__ == "__main__":
    unittest.main()
