"""pc/power_receipt.py: a receipt from the Guard's own state, only when a night may rest on it."""
import json
import tempfile
import unittest
from pathlib import Path

from pc import power_receipt as pr

NOW = pr.epoch("2026-11-25T20:45:00+00:00")
STATE = {"boot": "2026-11-21T15:51:34.500Z", "deadlineUtc": "2026-11-26T20:30:00Z", "lastRequestId": "abc-1", "reason": "explicit renewal"}


class ReceiptTest(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.d = Path(self.td.name)

    def tearDown(self):
        self.td.cleanup()

    def state(self, **change):
        path = self.d / "state.json"
        path.write_text(json.dumps({k: v for k, v in {**STATE, **change}.items() if v is not None}))
        return path

    def test_a_renewed_state_is_verified_with_its_request_id(self):
        r = pr.receipt(self.state(), NOW, "2026-11-26T08:15:00+01:00")
        self.assertEqual((r["status"], r["faults"]), ("VERIFIED", []))
        self.assertEqual(r["state"]["lastRequestId"], "abc-1")              # what the launchers compare
        self.assertEqual(len(r["state_sha256"]), 64)

    def test_what_a_night_cannot_rest_on_is_refused(self):
        self.assertIn("a shutdown is pending", pr.receipt(self.state(pendingUtc="2026-11-25T21:00:00Z"), NOW)["faults"])
        self.assertIn("the cutoff is in the past", pr.receipt(self.state(deadlineUtc="2026-11-25T20:00:00Z"), NOW)["faults"])
        late = pr.receipt(self.state(deadlineUtc="2026-11-26T07:20:00Z"), NOW, "2026-11-26T08:15:00+01:00")   # cutoff 08:20 Berlin
        self.assertEqual(late["status"], "REFUSED")
        self.assertEqual(pr.receipt(self.state(lastRequestId=None), NOW)["faults"], ["the state lacks lastRequestId"])
        self.assertEqual(pr.receipt(self.state(boot="yesterday"), NOW)["status"], "REFUSED")

    def test_the_command_writes_once_and_leaves_nothing_when_refused(self):
        out = self.d / "receipt.json"
        self.assertEqual(pr.main(["--state", str(self.state(deadlineUtc="2099-01-01T00:00:00Z")), "--out", str(out)]), 0)
        self.assertEqual(json.loads(out.read_text())["status"], "VERIFIED")
        with self.assertRaises(SystemExit):
            pr.main(["--state", str(self.state()), "--out", str(out)])       # a receipt is written once
        refused = self.d / "refused.json"
        self.assertEqual(pr.main(["--state", str(self.state(deadlineUtc="2000-01-01T00:00:00Z")), "--out", str(refused)]), 1)
        self.assertFalse(refused.exists())

    def test_a_state_file_with_a_byte_order_mark_is_read(self):
        path = self.d / "bom.json"
        path.write_bytes(b"\xef\xbb\xbf" + json.dumps(dict(STATE, deadlineUtc="2099-01-01T00:00:00Z")).encode())
        self.assertEqual(pr.receipt(path, NOW)["status"], "VERIFIED")


if __name__ == "__main__":
    unittest.main()
