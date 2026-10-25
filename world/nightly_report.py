"""Publish yesterday's completed, owl-written report from the normal locked tick."""
import json
import logging
import os
import subprocess
import sys
import tempfile
from datetime import timedelta
from pathlib import Path

log = logging.getLogger("world")


class ReportError(Exception):
    pass


def _day(path, wanted):
    if not path.exists():
        return None
    day = json.loads(path.read_text(encoding="utf-8"))
    return day if day.get("date") == wanted and day.get("complete") and day.get("owl") else None


def _ledger(path):
    raw = path.read_bytes() if path.exists() else b""
    dates = set()
    for line in raw.splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if not isinstance(row, dict) or not row.get("date") or row["date"] in dates:
            raise ReportError("invalid or duplicate date in reports.jsonl; original retained")
        dates.add(row["date"])
    return raw, dates


def publish_yesterday(cfg, now, git):
    """Append once after the owl; retry an uncommitted row without rerunning its report.

    Called only while cmd_tick holds tick.lock. Only yesterday is eligible: no
    historical backfill, unfinished day or owl generation happens here.
    """
    wanted = (now.date() - timedelta(days=1)).isoformat()
    day_path = cfg.docs / "days" / (wanted + ".json")
    day = _day(day_path, wanted)
    if day is None:
        return False
    path = cfg.docs / "days" / "reports.jsonl"
    raw, dates = _ledger(path)
    if wanted not in dates:
        git.sync()
        day = _day(day_path, wanted)
        if day is None:
            return False
        raw, dates = _ledger(path)
        if wanted not in dates:
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "world", "report", wanted,
                     "--docs", str(cfg.docs), "--json"], cwd=cfg.repo,
                    capture_output=True, text=True, encoding="utf-8", timeout=120)
            except subprocess.TimeoutExpired as exc:
                raise ReportError("report command timed out; original ledger retained") from exc
            if result.returncode:
                raise ReportError("report command failed: " + result.stderr.strip()[-400:])
            lines = result.stdout.splitlines()
            if len(lines) != 1:
                raise ReportError("report command did not return exactly one row")
            row = json.loads(lines[0])
            if not isinstance(row, dict) or row.get("date") != wanted or row.get("n") != day.get("n") or not row.get("complete") or not row.get("owl"):
                raise ReportError("report command returned an ineligible row")
            # Preserve every previous byte. Replacement is atomic, so a failed
            # write cannot leave half a row or damage the earlier ledger.
            addition = (b"\n" if raw and not raw.endswith(b"\n") else b"") + lines[0].encode("utf-8") + b"\n"
            temp = None
            try:
                with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".reports-", suffix=".tmp", delete=False) as stream:
                    temp = Path(stream.name)
                    stream.write(raw + addition)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(temp, path)
            finally:
                if temp is not None:
                    temp.unlink(missing_ok=True)
            log.info("nightly report wrote day %s", day["n"])
    # This also finishes a row whose earlier commit failed. A committed row is
    # unchanged, so Git.publish returns without a new commit or network call.
    return git.publish([path], f"Day {day['n']}: nightly report")
