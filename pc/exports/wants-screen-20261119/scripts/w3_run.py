"""W3's 216 calls to the plain live server, spare slot 1 only, behind the natural-step latency guard (DECISIONS 30).

Run from ~/w3/main:  python3 w3_run.py
Resumable: tools/recorded_llama.RecordedClient never re-sends a call that began, and wants_screen.run replays saved records.
A call is refused (and waited for, up to the cutoff) when his latest natural step is slower than the frozen limit, when the
observation is stale, or before his Day 50 has two steps of its own. The outputs are not read here: no measure is run.
"""
import hashlib, json, os, sys, time
from datetime import datetime
from pathlib import Path

HOME = Path.home()
sys.path.insert(0, str(HOME / "w3" / "main"))
from tools import wants_screen as w                                         # noqa: E402
from tools.recorded_llama import LatencyGuard, RecordedClient, TransportError, UnknownRequest   # noqa: E402

SP = Path(os.environ["W3_SP"])                  # the scratchpad (Windows side), where the observer writes
SCREEN = Path(os.environ.get("W3_SCREEN", HOME / "w3" / "screen"))
JOB = Path(os.environ.get("W3_JOB", HOME / "w3" / "job"))
SERVER = os.environ.get("W3_SERVER", "http://127.0.0.1:8082")
LIMIT = float(os.environ.get("W3_LIMIT", "17.0"))
CUTOFF = int(os.environ.get("W3_CUTOFF", "2045"))      # no new call after this HHMM (his bedtime is 21:00)
MIN_DAY_STEPS = int(os.environ.get("W3_MIN_STEPS", "2"))
OBS = SP / "w3-observation.json"
LOG = Path(os.environ.get("W3_LOG", HOME / "w3" / "run.log"))


def log(msg):
    line = f"[{datetime.now():%F %T}] {msg}"
    print(line, flush=True)
    with LOG.open("a") as f:
        f.write(line + "\n")


def hhmm():
    return int(datetime.now().strftime("%H%M"))


class Guard:
    """LatencyGuard plus: his Day 50 must have MIN_DAY_STEPS steps of its own with a mind behind them (a baseline), and the STOP file."""
    def __init__(self):
        self.inner = LatencyGuard(OBS, max_age=300, limit=LIMIT)

    def __call__(self):
        if (SP / "STOP").exists():
            raise TransportError("STOP file")
        row = self.inner()
        if row.get("date") != os.environ.get("W3_DAY_FILE", "2026-11-20") or row.get("day_steps", 0) < MIN_DAY_STEPS:
            raise TransportError(f"waiting for his Day 50 baseline ({row.get('date')}, {row.get('day_steps')} steps)")
        return row


guard = Guard()
client = RecordedClient(SERVER, JOB / "receipts", before_request=guard)
JOB.mkdir(parents=True, exist_ok=True)
state = {"waited": 0, "sent": 0}


def post(key, payload):
    begin = Path(str(client.stem(key)) + ".begin.json")
    while True:
        if hhmm() >= CUTOFF and hhmm() < 2359:
            raise SystemExit(f"cutoff {CUTOFF} reached before {key}")
        try:
            was_new = not begin.exists()
            result = client.post(key, payload)
            if was_new:
                state["sent"] += 1
                if state["sent"] % 12 == 0:
                    log(f"{state['sent']} calls sent this run")
            done = json.loads(Path(str(client.stem(key)) + ".done.json").read_text())
            return result, done
        except UnknownRequest:
            raise
        except TransportError as e:
            if begin.exists():                  # the call was sent and failed: not the guard's refusal; stop for a human
                raise
            if "STOP" in str(e):
                raise SystemExit("STOP file")
            state["waited"] += 1
            if state["waited"] % 10 == 1:
                log(f"guard holds: {e}")
            time.sleep(30)


def main():
    log(f"W3 run starts: limit_s={LIMIT} cutoff={CUTOFF} min_day_steps={MIN_DAY_STEPS} server={SERVER}")
    done = w.run(SCREEN, post)
    n = len(done)
    begins = len(list((JOB / "receipts").glob("*.begin.json")))
    dones = len(list((JOB / "receipts").glob("*.done.json")))
    errs = sum(1 for p in (JOB / "receipts").glob("*.done.json") if json.loads(p.read_text()).get("error"))
    ledger = {"requests": 216, "records_saved": n, "receipts_begin": begins, "receipts_done": dones, "transport_errors": errs,
              "unknown": begins - dones, "limit_s": LIMIT, "cutoff": CUTOFF, "slot": 1, "training_eligible": False,
              "manifest_sha256": hashlib.sha256((SCREEN / "MANIFEST.json").read_bytes()).hexdigest()}
    (JOB / "LEDGER.json").write_text(json.dumps(ledger, indent=1))
    log(f"W3 complete: {json.dumps(ledger)}")


if __name__ == "__main__":
    main()
