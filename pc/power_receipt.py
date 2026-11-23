"""A receipt for the Power Guard's state before a training night (pc/TRAINING-4-RUN.md).

    python3 -m pc.power_receipt --state <the Guard's state.json> --out <NEW receipt.json> [--restore-by ISO_TIME]

The launchers refuse an intent unless a receipt with status VERIFIED carries the Guard's current request id (pc/run_training1.py,
pc/run_training4.py). The receipt of 6 November was written for the twelve-hour boot state. Since 21 November the limit is 24 hours and
Welt renews each evening, and every renewal has a new id. This writes the receipt from the Guard's own state as it is read, and only if
that state is one a night may rest on:

- no shutdown is pending;
- the cutoff lies in the future, and at least 15 minutes after --restore-by when that is given;
- the state names its boot, its cutoff and its request id.

It reads one file and writes one new file. It renews nothing and changes nothing in the Guard: the renewal is Welt's own tap, made
before this is run. Nobody renews while a run is on, because the launcher stops when the state it froze has changed."""
import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

MARGIN = 900                    # seconds the cutoff must lie after the restore deadline (the launchers' own margin)
NEEDED = ("boot", "deadlineUtc", "lastRequestId")


def epoch(text):
    return datetime.fromisoformat(str(text).replace("Z", "+00:00")).timestamp()


def check(state, now, restore_by=None):
    """The reasons this state cannot carry a night, [] when it can."""
    missing = [k for k in NEEDED if k not in state]
    if missing:
        return ["the state lacks " + ", ".join(missing)]
    faults = []
    if state.get("pendingUtc"):
        faults.append("a shutdown is pending")
    try:
        cutoff = epoch(state["deadlineUtc"])
        epoch(state["boot"])
    except ValueError:
        return faults + ["the state's times cannot be read"]
    if cutoff <= now:
        faults.append("the cutoff is in the past")
    if restore_by is not None and cutoff < epoch(restore_by) + MARGIN:
        faults.append(f"the cutoff does not lie {MARGIN // 60} minutes after the restore deadline")
    return faults


def receipt(state_path, now=None, restore_by=None):
    raw = Path(state_path).read_bytes()
    state = json.loads(raw.decode("utf-8-sig"))
    now = datetime.now(timezone.utc).timestamp() if now is None else now
    faults = check(state, now, restore_by)
    return {"status": "REFUSED" if faults else "VERIFIED", "kind": "GUARD_STATE_AS_READ", "faults": faults, "state": state,
            "state_sha256": hashlib.sha256(raw).hexdigest(), "restore_by": restore_by,
            "utc": datetime.fromtimestamp(now, timezone.utc).isoformat(timespec="seconds"),
            "note": "Read from the Guard's own state. Nothing was renewed or changed."}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--state", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--restore-by")
    a = p.parse_args(argv)
    out = Path(a.out)
    if out.exists():
        p.error(f"{out} exists: a receipt is written once")
    r = receipt(a.state, restore_by=a.restore_by)
    print(json.dumps({k: r[k] for k in ("status", "faults", "utc")}))
    if r["status"] != "VERIFIED":
        return 1                # no file: a refused state leaves no receipt behind
    out.write_text(json.dumps(r, indent=1) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
