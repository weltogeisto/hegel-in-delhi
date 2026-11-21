"""HEGEL_SEED_STREAMS (pc/FAST-LANE.md, C): a call's seed from (base, moment, kind, draw), not its running number. Off by default."""
import hashlib
import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest import mock

from world.config import Config
from world.engine import Engine
from world.mind import HTTPMind


class Recorder(HTTPMind):
    """An HTTPMind whose calls return the seed they would have sent, with no server."""

    def chat(self, messages, schema=None, max_tokens=700, temperature=None, *, adapter_scale=None, reasoning_budget=0, dry=0.0, seed=None):
        return self.next_seed(seed)

    def complete(self, prompt, max_tokens=700, temperature=None, seed=None):
        self._kind = "complete"
        return self.next_seed(seed)


class OldChat(HTTPMind):
    """A subclass with the older chat() that never draws a seed."""

    def chat(self, messages, schema=None, max_tokens=700, temperature=None):
        return "{}"


def old(seed, n):
    return int.from_bytes(hashlib.sha256(f"{seed}:{n}".encode()).digest()[:4], "big") & 0x7FFFFFFF


class SeedStreamsTest(unittest.TestCase):
    def mind(self, streams, seed=1831):
        return Recorder("http://pc:8082", seed=seed, seed_streams=streams)

    def test_off_by_default_and_the_running_number_stays(self):
        self.assertFalse(Config({}).seed_streams)
        self.assertTrue(Config({"HEGEL_SEED_STREAMS": "1"}).seed_streams)
        m = self.mind(False)
        m.at("2026-11-22T10:00")
        got = [m.chat_decision([]), m.chat_voice([]), m.chat_writing([]), m.chat([]), m.complete("x")]
        self.assertEqual(got, [old(1831, n) for n in range(1, 6)])

    def test_an_extra_call_moves_no_other_seed(self):
        a, b = self.mind(True), self.mind(True)
        a.at("10:00"); b.at("10:00")
        first = [a.chat_decision([]) for _ in range(4)]
        b.chat_voice([])                                   # B's moment has a voice speak first, and a retry
        b.chat([])
        self.assertEqual([b.chat_decision([]) for _ in range(4)], first)
        self.assertEqual(len(set(first)), 4)               # the four draws of one moment differ
        a.at("10:15"); b.at("10:15")
        self.assertEqual([a.chat_decision([]) for _ in range(2)], [b.chat_decision([]) for _ in range(2)])
        b.chat_decision([])                                # B draws once more at 10:15
        a.at("10:30"); b.at("10:30")
        self.assertEqual(a.chat_decision([]), b.chat_decision([]))   # and the next moment is untouched
        self.assertNotEqual(old(1831, a.calls), old(1831, b.calls))  # where the running number would have parted them

    def test_the_moments_kinds_and_bases_each_have_their_own_stream(self):
        m = self.mind(True)
        m.at("10:00")
        d10, v10 = m.chat_decision([]), m.chat_voice([])
        m.at("10:15")
        d15 = m.chat_decision([])
        self.assertEqual(len({d10, v10, d15}), 3)
        other = self.mind(True, seed=2718)
        other.at("10:00")
        self.assertNotEqual(other.chat_decision([]), d10)
        again = self.mind(True)
        again.at("10:15")                                  # 10:00 never lived: 10:15's first decision is the same
        self.assertEqual(again.chat_decision([]), d15)

    def test_a_given_seed_wins_and_no_base_sends_none(self):
        m = self.mind(True)
        m.at("10:00")
        self.assertEqual(m.chat([], seed=7), 7)
        self.assertIsNone(Recorder("http://pc:8082", seed_streams=True).chat_decision([]))

    def test_the_kind_is_cleared_when_an_older_chat_draws_nothing(self):
        m = OldChat("http://pc:8082", seed=1831, seed_streams=True)
        m.chat_decision([])
        self.assertIsNone(m._kind)

    def test_the_engine_names_the_moment_only_with_streams_on(self):
        for on in (False, True):
            mind = mock.Mock()
            cfg = SimpleNamespace(seed_streams=on)
            e = Engine.__new__(Engine)
            e.cfg, e.mind = cfg, mind
            with mock.patch.object(Engine, "migrate", side_effect=RuntimeError("stop")):
                with self.assertRaises(RuntimeError):
                    e.step({"state": {}}, datetime(2026, 11, 22, 10, 0))
            if on:
                mind.at.assert_called_once_with("2026-11-22T10:00")
            else:
                mind.at.assert_not_called()


if __name__ == "__main__":
    unittest.main()
