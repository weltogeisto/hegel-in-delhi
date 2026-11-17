"""P3: flags_in and flags_not in an offer's conditions."""
import unittest
from datetime import datetime
from world.money import Economy

def ok(w, flags):
    m = Economy.__new__(Economy)
    st = {"imprest": 100, "owed": [], "met_days": {}, "visits": {}, "people": [], "flags": flags, "cheques": [], "works": []}
    return m.when_ok(w, datetime(2026, 10, 3, 9, 0), st)

class WhenFlags(unittest.TestCase):
    def test_flags_in(self):
        w = {"flags_in": {"f": ["a", "b"]}}
        self.assertTrue(ok(w, {"f": "a"})); self.assertTrue(ok(w, {"f": "b"}))
        self.assertFalse(ok(w, {"f": "c"})); self.assertFalse(ok(w, {}))
    def test_flags_in_null_accepts_unset(self):
        w = {"flags_in": {"f": [None, "a"]}}
        self.assertTrue(ok(w, {})); self.assertTrue(ok(w, {"f": "a"})); self.assertFalse(ok(w, {"f": "z"}))
    def test_flags_not_value(self):
        w = {"flags_not": {"f": "a"}}
        self.assertFalse(ok(w, {"f": "a"})); self.assertTrue(ok(w, {"f": "b"})); self.assertTrue(ok(w, {}))
    def test_flags_not_list(self):
        w = {"flags_not": {"f": ["a", "b"]}}
        self.assertFalse(ok(w, {"f": "a"})); self.assertFalse(ok(w, {"f": "b"})); self.assertTrue(ok(w, {"f": "c"})); self.assertTrue(ok(w, {}))
    def test_flags_not_null_refuses_unset(self):
        w = {"flags_not": {"f": [None, "a"]}}
        self.assertFalse(ok(w, {})); self.assertFalse(ok(w, {"f": "a"})); self.assertTrue(ok(w, {"f": "b"}))
        self.assertFalse(ok({"flags_not": {"f": None}}, {})); self.assertTrue(ok({"flags_not": {"f": None}}, {"f": "x"}))
    def test_all_keys_must_hold(self):
        w = {"flags": {"g": 1}, "flags_in": {"f": ["a"]}, "flags_not": {"h": "x"}}
        self.assertTrue(ok(w, {"g": 1, "f": "a"})); self.assertFalse(ok(w, {"g": 1, "f": "a", "h": "x"})); self.assertFalse(ok(w, {"f": "a"}))
    def test_old_conditions_unchanged(self):
        self.assertTrue(ok({}, {})); self.assertTrue(ok({"flags": {"f": 1}}, {"f": 1})); self.assertFalse(ok({"flags": {"f": 1}}, {}))

if __name__ == "__main__": unittest.main()
