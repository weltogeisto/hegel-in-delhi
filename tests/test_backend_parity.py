"""CPU checks for diagnostic isolation and comparing inputs, without loading a model."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("parity", REPO / "pc/check_backend_parity.py")
parity = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parity)


class BackendParityTests(unittest.TestCase):
    def test_missing_frozen_case_is_not_replaced_by_a_new_prompt(self):
        with self.assertRaisesRegex(ValueError, "exactly one frozen essay"):
            parity.cases_from({"requests": []})

    def test_duplicate_case_is_not_arbitrarily_selected(self):
        row = {"condition": "chat-draft-adapter", "seed": 1, "plan": {"kind": "essay"}}
        with self.assertRaisesRegex(ValueError, "found 2"):
            parity.cases_from({"requests": [row, row]})

    def test_replays_only_the_frozen_adapter_condition_and_seed(self):
        rows = []
        for kind in ("essay", "letter"):
            for seed in (1, 2):
                rows.append({"condition": "chat-draft-adapter", "seed": seed, "plan": {"kind": kind},
                             "label": f"{kind}-{seed}", "payload": {"messages": [{"role": "user", "content": f"{kind}-{seed}"}]}})
        cases = parity.cases_from({"requests": rows})
        self.assertEqual([c["id"] for c in cases], ["state-question", "essay", "letter"])
        self.assertEqual(cases[1]["messages"][0]["content"], "essay-1")
        self.assertEqual(cases[2]["source_label"], "letter-1")

    def test_same_text_with_different_special_token_ids_fails_token_parity(self):
        checks = parity.compare_prompts({"x": {"prompt": "text", "tokens": [1, 2]}},
                                        {"x": {"prompt": "text", "tokens": [1, 9, 2]}})
        self.assertTrue(checks[0]["text_equal"])
        self.assertFalse(checks[0]["tokens_equal"])
        self.assertEqual(checks[0]["first_token_difference"], 1)

    def test_first_difference_detects_extra_generation_boundary(self):
        self.assertEqual(parity.first_difference("prompt", "prompt<assistant>"), 6)
        self.assertIsNone(parity.first_difference([1, 2], [1, 2]))

    def test_atomic_status_write_is_complete_and_does_not_leave_temp_file(self):
        with tempfile.TemporaryDirectory() as root:
            parity.save(root, "status.json", {"status": "running"})
            parity.save(root, "status.json", {"status": "failed", "error": "Exact error"})
            self.assertEqual(json.loads((Path(root) / "status.json").read_text())["error"], "Exact error")
            self.assertFalse((Path(root) / "status.json.tmp").exists())


if __name__ == "__main__":
    unittest.main()
