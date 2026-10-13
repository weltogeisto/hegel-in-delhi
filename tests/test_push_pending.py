"""A push the network refused goes out on the next tick, without anyone stepping in."""
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from world import publish
from world.engine import Engine
from world.publish import Git, GitError


def git(cwd, *args):
    return subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True, check=True).stdout.strip()


class PushPendingTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="hegel-push-")
        root = Path(self.tmp.name)
        self.remote, self.work = root / "remote.git", root / "work"
        subprocess.run(["git", "init", "-q", "--bare", str(self.remote)], check=True)
        subprocess.run(["git", "clone", "-q", str(self.remote), str(self.work)], check=True, capture_output=True)
        git(self.work, "config", "user.email", "world@example.org"); git(self.work, "config", "user.name", "world")
        git(self.work, "checkout", "-q", "-b", "shadow")
        (self.work / "a.json").write_text("{}\n"); git(self.work, "add", "a.json"); git(self.work, "commit", "-q", "-m", "start")
        git(self.work, "push", "-q", "-u", "origin", "shadow")
        self.g = Git(SimpleNamespace(repo=self.work, branch="shadow", push=True))

    def tearDown(self):
        self.tmp.cleanup()

    def test_refused_push_is_held_then_goes_out(self):
        self.assertEqual(self.g.unpushed(), 0)
        self.assertFalse(self.g.push_pending())                                      # nothing held back: no network at all
        off = self.remote.with_name("remote.off"); self.remote.rename(off)            # the network goes away
        (self.work / "b.json").write_text("{}\n")
        with mock.patch.object(publish.time, "sleep"), self.assertRaises(GitError):
            self.g.publish([self.work / "b.json"], "Day 12, 06:30")
        self.assertEqual(self.g.unpushed(), 1)
        self.assertFalse(self.g.push_pending())                                       # still away: held, no exception
        off.rename(self.remote)                                                        # and comes back
        self.assertTrue(self.g.push_pending())
        self.assertEqual(self.g.unpushed(), 0)
        self.assertEqual(git(self.work, "rev-parse", "HEAD"), subprocess.run(["git", "--git-dir", str(self.remote), "rev-parse", "shadow"], capture_output=True, text=True).stdout.strip())

    def test_tick_tries_even_when_no_step_is_due(self):
        e = Engine.__new__(Engine)
        e.git = mock.Mock(); e.owl_ready = lambda now: None; e.due = lambda now: False
        self.assertEqual(e.tick(None), [])
        e.git.push_pending.assert_called_once()
        e.git.sync.assert_not_called()

    def test_a_failing_retry_does_not_stop_the_tick(self):
        e = Engine.__new__(Engine)
        e.git = mock.Mock(); e.git.push_pending.side_effect = GitError("wrong branch")
        e.owl_ready = lambda now: None; e.due = lambda now: False
        self.assertEqual(e.tick(None), [])


if __name__ == "__main__":
    unittest.main()
