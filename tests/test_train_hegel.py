"""Tests for pc/train_hegel.py: everything that does not need a GPU. The training itself (unsloth, torch) cannot run here; what can is the data check,
the packing, the loss masks and the arithmetic, and that the file imports and checks data without any of the heavy libraries.

The examples are synthetic fixtures for these tests, written into temporary folders only."""
import contextlib
import importlib.util
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_world import REPO  # noqa: E402  (this also keeps the tests off the Pi's env file)

spec = importlib.util.spec_from_file_location("train_hegel", REPO / "pc/train_hegel.py")
th = importlib.util.module_from_spec(spec)
spec.loader.exec_module(th)

DECISION = {"thought": "The grocer sells tea and I note how the stalls close one by one.", "action": "stay", "place": "khan", "minutes": 30,
            "says": None, "buys": [], "revision": None}
PLAN = {"plan": [{"time": "07:30", "intention": "Walk to the park"}, {"time": "10:00", "intention": "Khan Market"}, {"time": "13:00", "intention": "Lunch"}]}
WRITING = {"title": "A page", "kind": "notes", "to": None, "continues": False, "text": "Some text for the page."}
VOICE = {"says": "Yes, sir.", "does": None}


def chat(answer, extra=0, system=True):
    msgs = ([{"role": "system", "content": "You are Hegel."}] if system else []) + [{"role": "user", "content": "Situation. Decide."}]
    for _ in range(extra):
        msgs += [{"role": "assistant", "content": json.dumps(DECISION)}, {"role": "user", "content": "Write."}]
    return {"messages": msgs + [{"role": "assistant", "content": answer if isinstance(answer, str) else json.dumps(answer)}], "meta": {"kind": "x"}}


def write(folder, name, rows):
    with open(Path(folder) / name, "w", encoding="utf-8") as f:
        for r in rows:
            f.write((r if isinstance(r, str) else json.dumps(r, ensure_ascii=False)) + "\n")


def check(folder, **kw):
    out = io.StringIO()
    ok, ready = th.check_data(folder, kw.pop("seq_corpus", 2048), kw.pop("seq_format", 4096), say=lambda *a: out.write(" ".join(map(str, a)) + "\n"), **kw)
    return ok, ready, out.getvalue()


class Tmp(unittest.TestCase):
    def tmp(self):
        d = Path(tempfile.mkdtemp(prefix="hegel-train-hegel-"))
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        return d

    def good(self):
        d = self.tmp()
        write(d, "corpus.jsonl", [{"text": "Hegel, Philosophie des Rechts, §188\n\n" + "Wort " * 100}, {"text": "Hegel's Logic\n\n" + "word " * 100}])
        write(d, "decisions.jsonl", [chat(DECISION)] * 3)
        write(d, "plans.jsonl", [chat(PLAN)])
        write(d, "writings.jsonl", [chat(WRITING, extra=1)])
        write(d, "voices.jsonl", [chat(VOICE, system=True)])
        write(d, "general.jsonl", [{"messages": [{"role": "user", "content": "Hello there."}, {"role": "assistant", "content": "Hello, how can I help?"}]}] * 5)
        return d


class ImportTest(unittest.TestCase):
    def test_importing_and_checking_data_needs_none_of_the_heavy_libraries(self):
        code = f"""
import importlib.util, sys
spec = importlib.util.spec_from_file_location('train_hegel', {str(REPO / 'pc/train_hegel.py')!r})
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
m.check_data({tempfile.gettempdir()!r}, 2048, 4096, say=lambda *a: None)
bad = [x for x in ('torch', 'unsloth', 'transformers', 'datasets', 'trl', 'peft') if x in sys.modules]
print('heavy imports:', bad)
sys.exit(1 if bad else 0)
"""
        r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=REPO)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("heavy imports: []", r.stdout)


class CheckDataTest(Tmp):
    def test_good_data_is_ok_and_both_phases_are_ready(self):
        ok, ready, text = check(self.good())
        self.assertTrue(ok, text)
        self.assertEqual(ready, {"corpus": True, "format": True})
        self.assertRegex(text, r"decisions\s+3 examples")
        self.assertRegex(text, r"corpus\s+2 documents")
        self.assertIn("data ok", text)

    def test_the_command_line_exits_zero_on_good_data_and_one_on_bad(self):
        d = self.good()
        r = subprocess.run([sys.executable, str(REPO / "pc/train_hegel.py"), "--check-data", "--data", str(d)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        write(d, "decisions.jsonl", ["{not json"])
        r = subprocess.run([sys.executable, str(REPO / "pc/train_hegel.py"), "--check-data", "--data", str(d)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 1)
        self.assertIn("decisions.jsonl:1: not JSON", r.stdout)

    def test_a_file_that_is_missing_is_reported_and_only_strict_makes_it_fail(self):
        d = self.good()
        (d / "general.jsonl").unlink()
        ok, ready, text = check(d)
        self.assertTrue(ok)
        self.assertEqual(ready, {"corpus": True, "format": False})
        self.assertIn("phase 2 (format): NOT ready", text)
        self.assertFalse(check(d, strict=True)[0])

    def test_nothing_to_check_is_not_ok(self):
        ok, ready, text = check(self.tmp())
        self.assertFalse(ok)
        self.assertIn("run tools/train_data.py first", text)

    def test_only_the_corpus_is_enough_for_phase_one(self):
        d = self.tmp()
        write(d, "corpus.jsonl", [{"text": "Hegel\n\n" + "word " * 100}])
        ok, ready, text = check(d)
        self.assertTrue(ok, text)
        self.assertEqual(ready, {"corpus": True, "format": False})

    def test_faults_are_named_by_file_and_line_and_grouped(self):
        d = self.good()
        write(d, "corpus.jsonl", [{"text": "x" * 300}, {"text": "short"}, {"text": "y" * 300, "extra": 1}, "nope"])
        write(d, "decisions.jsonl", [chat(DECISION), chat({**DECISION, "action": "fly"}), chat({**DECISION, "place": "mars"}), {"messages": "no"}])
        ok, _, text = check(d)
        self.assertFalse(ok)
        self.assertIn("corpus.jsonl:2:", text)
        self.assertIn("(and 1 more like it)", text)                     # line 3 has the same fault as line 2
        self.assertIn("corpus.jsonl:4: not JSON", text)
        self.assertIn("decisions.jsonl:2: the decision breaks the contract: unknown action 'fly'", text)
        self.assertIn("decisions.jsonl:3: the decision breaks the contract: unknown place 'mars'", text)
        self.assertIn("decisions.jsonl:4: no 'messages' list", text)

    def test_roles_must_alternate_and_end_with_the_assistant(self):
        for msgs in ([{"role": "user", "content": "a"}],
                     [{"role": "user", "content": "a"}, {"role": "user", "content": "b"}],
                     [{"role": "assistant", "content": "a"}, {"role": "user", "content": "b"}],
                     [{"role": "system", "content": "s"}, {"role": "user", "content": "a"}],
                     [{"role": "user", "content": "a"}, {"role": "assistant", "content": "  "}]):
            self.assertIsNotNone(th.chat_problem("general", {"messages": msgs}), msgs)
        self.assertIsNone(th.chat_problem("general", {"messages": [{"role": "user", "content": "a"}, {"role": "assistant", "content": "b"}]}))
        self.assertIsNone(th.chat_problem("general", chat("fine", extra=2, system=False)))

    def test_each_kind_of_answer_has_its_own_shape(self):
        self.assertIsNone(th.chat_problem("plans", chat(PLAN)))
        self.assertIsNotNone(th.chat_problem("plans", chat({"plan": PLAN["plan"][:2]})))
        self.assertIsNotNone(th.chat_problem("plans", chat({"plan": [{"time": "07:30"}] * 3})))
        self.assertIsNone(th.chat_problem("writings", chat(WRITING, extra=1)))
        self.assertIsNotNone(th.chat_problem("writings", chat({"title": "x"}, extra=1)))
        self.assertIsNone(th.chat_problem("voices", chat(VOICE)))
        self.assertIsNotNone(th.chat_problem("voices", chat({"says": "x"})))
        self.assertIsNotNone(th.chat_problem("voices", chat("plain prose")))

    def test_text_from_a_stand_in_mind_is_never_data(self):
        for mark in ("(rehearsal)", "(stub)"):
            self.assertIn("stand-in", th.chat_problem("decisions", chat({**DECISION, "thought": f"{mark} The grocer sells tea in the market today."})))
            self.assertIn("stand-in", th.chat_problem("general", chat(f"{mark} an answer.")))
        d = self.good()
        write(d, "voices.jsonl", [chat({"says": "(rehearsal) Ji, sir.", "does": None})])
        ok, _, text = check(d)
        self.assertFalse(ok)
        self.assertIn("voices.jsonl:1: stand-in text", text)

    def test_examples_that_will_not_fit_are_counted_and_too_many_is_a_fault(self):
        d = self.good()
        big = chat({**DECISION, "thought": "word " * 4000})
        write(d, "decisions.jsonl", [chat(DECISION)] * 9 + [big])
        ok, _, text = check(d)
        self.assertTrue(ok, text)
        self.assertIn("1 probably longer than 4096 tokens (skipped, never truncated)", text)
        write(d, "decisions.jsonl", [chat(DECISION)] * 2 + [big] * 2)
        ok, _, text = check(d)
        self.assertFalse(ok)
        self.assertIn("over a fifth of the examples", text)


class SequenceTest(unittest.TestCase):
    """The loss masks and the packing, with a stand-in tokenizer that renders chats the way a ChatML template with a thinking switch does."""

    class Tok:
        eos_token_id = 0

        def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=False, enable_thinking=True):
            out = ""
            for i, m in enumerate(messages):
                think = "<think>\n\n</think>\n\n" if m["role"] == "assistant" and i == len(messages) - 1 else ""     # only the last assistant turn carries one
                out += f"<|im_start|>{m['role']}\n{think}{m['content']}<|im_end|>\n"
            if add_generation_prompt:
                out += "<|im_start|>assistant\n" + ("<think>\n\n</think>\n\n" if not enable_thinking else "")
            return out

        def __call__(self, text, add_special_tokens=True):
            return {"input_ids": [ord(c) for c in text]}

    def test_split_chat_cuts_where_the_live_prompt_ends(self):
        msgs = chat("ANSWER", system=True)["messages"]
        prompt, completion = th.split_chat(self.Tok(), msgs)
        self.assertTrue(prompt.endswith("<|im_start|>assistant\n<think>\n\n</think>\n\n"))
        self.assertEqual(completion, "ANSWER<|im_end|>\n")

    def test_only_the_final_assistant_turn_has_loss(self):
        enc = th.encode_chat(self.Tok(), chat("ANSWER", extra=1)["messages"], 10 ** 6)
        text = "".join(chr(i) for i in enc["input_ids"])
        trained = "".join(chr(i) for i, l in zip(enc["input_ids"], enc["labels"]) if l != -100)
        self.assertEqual(trained, "ANSWER<|im_end|>\n")
        self.assertIn("Situation. Decide.", text)
        self.assertIn(json.dumps(DECISION), text)                       # the earlier assistant turn is context, not target
        self.assertNotIn(json.dumps(DECISION), trained)
        self.assertEqual(len(enc["labels"]), len(enc["input_ids"]))
        self.assertEqual(enc["attention_mask"], [1] * len(enc["input_ids"]))
        self.assertTrue(all(l == i for i, l in zip(enc["input_ids"], enc["labels"]) if l != -100))

    def test_a_chat_that_is_too_long_is_skipped_not_cut(self):
        msgs = chat("ANSWER")["messages"]
        full = len(th.encode_chat(self.Tok(), msgs, 10 ** 6)["input_ids"])
        self.assertIsNotNone(th.encode_chat(self.Tok(), msgs, full))
        self.assertIsNone(th.encode_chat(self.Tok(), msgs, full - 1))

    def test_a_template_that_does_not_render_the_prompt_as_a_prefix_stops_the_run(self):
        class Odd(self.Tok):
            def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=False, enable_thinking=True):
                return "PROMPT" if add_generation_prompt else "something else"

        with self.assertRaises(SystemExit) as cm:
            th.split_chat(Odd(), chat("A")["messages"])
        self.assertIn("Report this to Welt", str(cm.exception))

    def test_pack_makes_blocks_of_exactly_seq_with_an_end_mark_after_each_document(self):
        blocks = th.pack([[1, 2, 3], [4, 5], [6, 7, 8, 9]], 4, eos=0)
        self.assertEqual([b["input_ids"] for b in blocks], [[1, 2, 3, 0], [4, 5, 0, 6], [7, 8, 9, 0]])
        self.assertTrue(all(b["labels"] == b["input_ids"] and b["attention_mask"] == [1] * 4 for b in blocks))
        self.assertEqual(th.pack([[1, 2]], 4, eos=0), [])                 # the short rest is dropped

    def test_mix_is_one_to_one_and_uses_all_the_general_ones_if_there_are_fewer(self):
        fmt, gen = [f"f{i}" for i in range(10)], [f"g{i}" for i in range(30)]
        mixed = th.mix_format(fmt, gen, seed=1)
        self.assertEqual(len(mixed), 20)
        self.assertEqual(sum(x.startswith("f") for x in mixed), 10)
        self.assertEqual(len(th.mix_format(fmt, gen[:4], seed=1)), 14)
        self.assertEqual(th.mix_format(fmt, gen, seed=1), th.mix_format(fmt, gen, seed=1))

    def test_steps_for(self):
        self.assertEqual(th.steps_for(100, 1, 16, 1), 7)
        self.assertEqual(th.steps_for(100, 1, 16, 2), 14)
        self.assertEqual(th.steps_for(16, 1, 16, 1), 1)

    def test_load_chats_reads_the_messages_of_the_named_files(self):
        d = Path(tempfile.mkdtemp(prefix="hegel-train-hegel-"))
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        write(d, "decisions.jsonl", [chat(DECISION)] * 2)
        write(d, "plans.jsonl", [chat(PLAN)])
        self.assertEqual(len(th.load_chats(d, th.FORMAT)), 3)
        self.assertEqual(th.load_chats(d, ["general"]), [])


class SettingsTest(unittest.TestCase):
    def test_the_defaults_are_the_agreed_ones(self):
        import argparse
        captured = {}
        original = th.train
        th.train = lambda args: captured.update(vars(args))
        try:
            th.main(["--base", "x/y"])
        finally:
            th.train = original
        self.assertEqual((captured["rank"], captured["alpha"], captured["batch"], captured["accum"]), (32, 32, 1, 16))
        self.assertEqual((captured["lr_corpus"], captured["lr_format"], captured["epochs_corpus"], captured["epochs_format"]), (1e-4, 5e-5, 1, 2))
        self.assertEqual((captured["seq_corpus"], captured["phase"], captured["bf16"]), (2048, "both", False))

    def test_the_memory_options_of_the_first_run_are_off_by_default_and_checked(self):
        captured = {}
        original = th.train
        th.train = lambda args: captured.update(vars(args))
        try:
            th.main(["--base", "x/y"])
            self.assertEqual((captured["text_only"], captured["loss_target_gib"]), (False, None))
            th.main(["--base", "x/y", "--rank", "16", "--text-only", "--loss-target-gib", "0.125"])
            self.assertEqual((captured["rank"], captured["text_only"], captured["loss_target_gib"]), (16, True, 0.125))
            for bad in ("0", "-1", "nan", "inf"):
                with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                    th.main(["--base", "x/y", "--loss-target-gib", bad])
        finally:
            th.train = original

    def test_a_base_is_required_for_training_but_not_for_the_check(self):
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                th.main([])


if __name__ == "__main__":
    unittest.main()
