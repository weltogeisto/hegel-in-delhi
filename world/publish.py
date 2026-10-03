"""Commit and push the day files. Never force, never rewrite history."""
import logging
import subprocess
import time

log = logging.getLogger("world")


class GitError(Exception):
    pass


class Git:
    def __init__(self, cfg):
        self.cfg = cfg

    def run(self, *args, check=True):
        p = subprocess.run(["git", "-C", str(self.cfg.repo), *args], capture_output=True, text=True, timeout=120)
        if check and p.returncode != 0:
            raise GitError(f"git {' '.join(args)}: {(p.stderr or p.stdout).strip()[-400:]}")
        return p

    def branch_ok(self):
        head = self.run("rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
        if head != self.cfg.branch:
            raise GitError(f"checked out on '{head}', configured for '{self.cfg.branch}' (HEGEL_BRANCH)")

    def sync(self):
        """Take in what others pushed (page changes from Claude, say) before writing."""
        if not self.cfg.push:
            return
        self.branch_ok()
        p = self.run("pull", "--ff-only", "--quiet", "origin", self.cfg.branch, check=False)
        if p.returncode != 0:
            log.warning("pull --ff-only failed, will merge on push: %s", (p.stderr or "").strip()[-200:])

    def publish(self, paths, message):
        self.branch_ok()
        self.run("add", "--", *[str(x) for x in paths])
        if self.run("diff", "--cached", "--quiet", check=False).returncode == 0:
            return False
        self.run("commit", "-q", "-m", message)
        if not self.cfg.push:
            return True
        for attempt in range(4):
            p = self.run("push", "-q", "origin", f"HEAD:{self.cfg.branch}", check=False)
            if p.returncode == 0:
                return True
            err = (p.stderr or "").lower()
            if "rejected" in err or "fetch first" in err or "non-fast-forward" in err:
                self.run("pull", "--no-rebase", "--no-edit", "-q", "origin", self.cfg.branch)
                continue
            time.sleep(2 ** (attempt + 1))
        raise GitError("push failed four times: " + (p.stderr or "").strip()[-300:])
