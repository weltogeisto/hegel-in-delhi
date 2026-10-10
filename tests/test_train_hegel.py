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
from unittest import mock

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
        self.assertEqual((captured["epochs_restyle"], captured["lr_restyle"], captured["seq_restyle"]), (2, 2e-4, 1024))
        th.train = lambda args: captured.update(vars(args))
        th.main(["--base", "x/y", "--phase", "restyle"])
        self.assertEqual(captured["phase"], "restyle")

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


RESTYLE_ORIGINAL = "The state is the actuality of the ethical idea, the ethical spirit as the revealed will, plain to itself and substantial."
RESTYLE_PLAIN = "The state is what makes the ethical idea real. It is the shared will, open to itself, and it holds together."


def restyle_row(i, split="train", plain=RESTYLE_PLAIN, original=RESTYLE_ORIGINAL):
    return {"id": f"dyde-right:{i}", "work": "dyde-right", "ref": f"§{i}", "split": split, "plain": plain + f" Number {i}.", "original": original + f" Number {i}."}


def restyle_folder(test, train=6, held=2):
    d = test.tmp()
    write(d, "hegelizer.jsonl", [restyle_row(i) for i in range(train)] + [restyle_row(100 + i, "held") for i in range(held)])
    return d


class RestyleDataTest(Tmp):
    def test_the_check_reports_the_file_the_counts_and_the_longest_example(self):
        ok, ready, text = check(restyle_folder(self), phase="restyle")
        self.assertTrue(ok, text)
        self.assertEqual(ready, {"restyle": True})
        self.assertRegex(text, r"hegelizer +6 train \+ 2 held-out examples")
        self.assertRegex(text, r"longest about \d+ tokens \(limit 1024\)")
        self.assertIn("phase 3 (restyle): ready, 6 to train on and 2 held out", text)
        self.assertTrue(text.rstrip().endswith("data ok"))
        self.assertNotIn("corpus", text)                                    # only hegelizer.jsonl is looked at for this phase

    def test_the_longest_example_is_estimated_from_the_prompt_the_plain_text_and_the_answer(self):
        row = restyle_row(0)
        want = sum(len(m["content"]) for m in th.restyle_chat(row)) / th.CHARS_PER_TOKEN + th.TEMPLATE_TOKENS
        self.assertEqual(th.restyle_tokens(row), want)
        self.assertEqual([m["role"] for m in th.restyle_chat(row)], ["system", "user", "assistant"])
        self.assertEqual(th.restyle_chat(row)[:2], th.restyle.messages(row["plain"]))
        self.assertEqual(th.restyle_chat(row)[2]["content"], row["original"])
        _, _, text = check(restyle_folder(self), phase="restyle", seq_restyle=100)
        self.assertIn("(limit 100)", text)
        self.assertIn("8 probably longer (skipped, never truncated)", text)

    def test_a_missing_file_is_not_ready_and_does_not_fail_the_other_phases(self):
        d = self.good()
        ok, ready, text = check(d)
        self.assertTrue(ok, text)
        self.assertEqual(ready, {"corpus": True, "format": True})            # the first two phases' answer is as it was
        self.assertIn("phase 3 (restyle): NOT ready, hegelizer.jsonl is missing", text)
        self.assertTrue(check(d, strict=True)[0])
        ok, ready, text = check(d, phase="restyle")
        self.assertFalse(ok)
        self.assertEqual(ready, {"restyle": False})
        self.assertIn("data NOT ok", text)

    def test_the_other_phases_report_the_restyle_data_beside_theirs_without_being_held_up_by_it(self):
        d = self.good()
        write(d, "hegelizer.jsonl", [restyle_row(0), restyle_row(1, "held")])
        ok, ready, text = check(d)
        self.assertTrue(ok, text)
        self.assertEqual(ready, {"corpus": True, "format": True})
        self.assertIn("phase 3 (restyle): ready, 1 to train on and 1 held out", text)
        write(d, "hegelizer.jsonl", [restyle_row(0, "weird")])
        ok, _, text = check(d)
        self.assertTrue(ok, text)                                          # a fault in it is the restyle phase's business
        self.assertIn("phase 3 (restyle): NOT ready, 1 fault(s)", text)

    def test_it_needs_something_to_train_on_and_something_held_out_to_measure_it_by(self):
        for train, held in ((0, 3), (3, 0)):
            ok, ready, text = check(restyle_folder(self, train, held), phase="restyle")
            self.assertFalse(ok, (train, held))
            self.assertEqual(ready, {"restyle": False})
            self.assertIn("it needs examples of both splits", text)

    def test_faults_are_named_by_line_and_a_row_with_a_fault_is_left_out(self):
        d = self.tmp()
        write(d, "hegelizer.jsonl", [restyle_row(0), {**restyle_row(1), "split": "validation"}, {**restyle_row(2), "plain": "  "}, {**restyle_row(3), "original": 5},
                                     "{not json", restyle_row(0, "held"), [1], restyle_row(4, "held")])
        rows, bad = th.load_restyle(d)
        self.assertEqual(([r["id"] for r in rows["train"]], [r["id"] for r in rows["held"]]), (["dyde-right:0"], ["dyde-right:4"]))
        self.assertEqual(len(bad), 6)
        self.assertIn("hegelizer.jsonl:2: 'split' must be train or held", bad)
        self.assertIn("hegelizer.jsonl:3: no 'plain' text", bad)
        self.assertIn("hegelizer.jsonl:4: no 'original' text", bad)
        self.assertTrue(bad[3].startswith("hegelizer.jsonl:5: not JSON"))
        self.assertIn("hegelizer.jsonl:6: a second row for id dyde-right:0", bad)
        self.assertIn("hegelizer.jsonl:7: not an object", bad)
        ok, _, text = check(d, phase="restyle")
        self.assertFalse(ok)
        self.assertIn("✗ hegelizer.jsonl:2: 'split' must be train or held", text)

    def test_over_a_fifth_of_the_examples_too_long_is_a_fault(self):
        d = self.tmp()
        big = "word " * 1200
        write(d, "hegelizer.jsonl", [restyle_row(i) for i in range(8)] + [restyle_row(100, "held")] + [restyle_row(9, original=big)])
        ok, _, text = check(d, phase="restyle")
        self.assertTrue(ok, text)                                           # one in ten: skipped and counted
        self.assertIn("1 probably longer", text)
        write(d, "hegelizer.jsonl", [restyle_row(0), restyle_row(100, "held")] + [restyle_row(i, original=big) for i in (1, 2, 3)])
        ok, _, text = check(d, phase="restyle")
        self.assertFalse(ok)
        self.assertIn("over a fifth of the examples are probably longer than 1024 tokens; raise --seq-restyle", text)

    def test_the_command_line_checks_restyle_data_without_torch_and_exits_by_the_answer(self):
        d = restyle_folder(self)
        r = subprocess.run([sys.executable, str(REPO / "pc/train_hegel.py"), "--check-data", "--phase", "restyle", "--data", str(d)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("phase 3 (restyle): ready", r.stdout)
        r = subprocess.run([sys.executable, str(REPO / "pc/train_hegel.py"), "--check-data", "--phase", "restyle", "--data", str(self.tmp())], capture_output=True, text=True)
        self.assertEqual(r.returncode, 1)
        self.assertIn("hegelizer.jsonl is missing", r.stdout)
        code = f"""
import importlib.util, sys
spec = importlib.util.spec_from_file_location('train_hegel', {str(REPO / 'pc/train_hegel.py')!r})
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
m.check_data({str(d)!r}, 2048, 4096, say=lambda *a: None, phase='restyle')
print('heavy imports:', [x for x in ('torch', 'unsloth', 'transformers', 'datasets', 'trl', 'peft') if x in sys.modules])
"""
        r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=REPO)
        self.assertIn("heavy imports: []", r.stdout, r.stderr)


class RestyleSequenceTest(Tmp):
    Tok = SequenceTest.Tok

    def test_the_encoded_example_has_loss_on_the_answer_only(self):
        row = restyle_row(7)
        enc = th.encode_chat(self.Tok(), th.restyle_chat(row), 10 ** 6)
        text = "".join(chr(i) for i in enc["input_ids"])
        trained = "".join(chr(i) for i, l in zip(enc["input_ids"], enc["labels"]) if l != -100)
        self.assertEqual(trained, row["original"] + "<|im_end|>\n")
        self.assertIn(th.restyle.RESTYLE_SYSTEM, text)
        self.assertIn("Rewrite in Hegel's manner:\n\n" + row["plain"], text)
        self.assertNotIn(row["plain"], trained)
        self.assertNotIn(th.restyle.RESTYLE_SYSTEM, trained)
        self.assertEqual(len(enc["labels"]), len(enc["input_ids"]))
        self.assertTrue(all(l == i for i, l in zip(enc["input_ids"], enc["labels"]) if l != -100))
        prompt, completion = th.split_chat(self.Tok(), th.restyle_chat(row))
        self.assertTrue(prompt.endswith("<|im_start|>assistant\n<think>\n\n</think>\n\n"))
        self.assertEqual(completion, row["original"] + "<|im_end|>\n")

    def test_examples_longer_than_the_sequence_are_skipped_and_counted_never_cut(self):
        d = restyle_folder(self, 5, 3)
        rows, _ = th.load_restyle(d)
        rows["train"][2] = restyle_row(2, plain="long " * 400)
        rows["held"][1] = restyle_row(101, "held", original="long " * 400)
        size = len(th.encode_chat(self.Tok(), th.restyle_chat(rows["train"][0]), 10 ** 6)["input_ids"])
        encoded, skipped = th.encode_restyle(self.Tok(), rows, size + 50)
        self.assertEqual(skipped, {"train": 1, "held": 1})
        self.assertEqual((len(encoded["train"]), len(encoded["held"])), (4, 2))
        self.assertTrue(all(len(e["input_ids"]) <= size + 50 for e in encoded["train"] + encoded["held"]))

    def test_the_default_folders_and_phases(self):
        self.assertEqual(th.default_out("restyle", False), th.OUT / "hegelizer-lora")
        self.assertEqual(th.default_out("restyle", True), th.OUT / "hegelizer-lora-dryrun")
        self.assertEqual(th.default_out("both", False), th.OUT / "hegel-lora")
        self.assertEqual(th.default_out("format", True), th.OUT / "hegel-lora-dryrun")

    def test_epochs_measured_before_a_crash_are_kept_for_a_resume_up_to_the_checkpoint(self):
        d = self.tmp()
        (d / "epochs.json").write_text(json.dumps([{"epoch": 1.0, "step": 244, "train_loss": 1.2, "heldout_loss": 1.3}, {"epoch": 2.0, "step": 488, "train_loss": 0.9, "heldout_loss": 1.1}]))
        self.assertEqual([e["epoch"] for e in th.kept_epochs(d / "epochs.json", 300)], [1.0])
        self.assertEqual([e["epoch"] for e in th.kept_epochs(d / "epochs.json", 500)], [1.0, 2.0])
        self.assertEqual(th.kept_epochs(d / "epochs.json", 100), [])
        self.assertEqual(th.kept_epochs(d / "none.json", 100), [])
        (d / "bad.json").write_text("{")
        self.assertEqual(th.kept_epochs(d / "bad.json", 100), [])


class RestyleTrainTest(Tmp):
    """train() for --phase restyle with the model, the tokenizer and the training stood in for: what is loaded, what is trained on and measured, what is written."""

    class Model:
        def save_pretrained(self, path):
            Path(path).mkdir(parents=True, exist_ok=True)
            (Path(path) / "adapter_model.safetensors").write_bytes(b"adapter")

    class Tok(SequenceTest.Tok):
        def save_pretrained(self, path):
            pass

    def run_train(self, d, out, *extra):
        seen = {"loads": []}

        def load(args, adapter=None):
            seen["loads"].append(adapter)
            return RestyleTrainTest.Model(), RestyleTrainTest.Tok()

        def phase(name, model, tokenizer, rows, lr, epochs, args, folder, held=None):
            seen.update(name=name, rows=rows, held=held, lr=lr, epochs=epochs, folder=folder, dry=args.dry_run)
            return {"steps": 4, "planned_steps": 4, "final_loss": 1.5, "minutes": 1.0, "heldout_loss": 1.9, "heldout_examples": len(held or []),
                    "epochs": [{"epoch": 1.0, "step": 2, "train_loss": 1.7, "heldout_loss": 2.1}, {"epoch": 2.0, "step": 4, "train_loss": 1.5, "heldout_loss": 1.9}]}

        said = io.StringIO()
        with mock.patch.object(th, "load_model", load), mock.patch.object(th, "run_phase", phase), mock.patch.object(th, "versions", return_value={}), \
                contextlib.redirect_stdout(said):
            th.main(["--base", "x/y", "--phase", "restyle", "--data", str(d), "--out", str(out), *extra])
        return seen, said.getvalue()

    def test_a_fresh_lora_on_the_train_rows_with_the_held_out_rows_to_measure(self):
        d = restyle_folder(self, 6, 2)
        out = self.tmp() / "adapter"
        seen, said = self.run_train(d, out)
        self.assertEqual(seen["loads"], [None])                             # one load, with no adapter of phase 1 to start from
        self.assertEqual((seen["name"], seen["lr"], seen["epochs"]), ("restyle", 2e-4, 2))
        self.assertEqual((len(seen["rows"]), len(seen["held"])), (6, 2))
        trained = ["".join(chr(i) for i, l in zip(r["input_ids"], r["labels"]) if l != -100) for r in seen["rows"]]
        self.assertEqual(sorted(trained), sorted(restyle_row(i)["original"] + "<|im_end|>\n" for i in range(6)))
        held = ["".join(chr(i) for i, l in zip(r["input_ids"], r["labels"]) if l != -100) for r in seen["held"]]
        self.assertEqual(sorted(held), sorted(restyle_row(100 + i, "held")["original"] + "<|im_end|>\n" for i in range(2)))
        self.assertTrue(str(seen["folder"]).endswith("work/restyle"))
        self.assertIn("restyle: 6 train + 2 held-out examples; 0 + 0 longer than 1024 tokens skipped, not cut", said)
        self.assertIn("template check, prompt ends", said)
        self.assertIn("restyle: train loss 1.5, held-out loss 1.9 (per epoch: 1.0: 1.7 / 2.1; 2.0: 1.5 / 1.9)", said)
        self.assertIn("adapter saved to", said)

    def test_training_json_has_the_train_loss_and_the_held_out_loss_of_each_epoch(self):
        out = self.tmp() / "adapter"
        self.run_train(restyle_folder(self), out)
        log = json.loads((out / "training.json").read_text(encoding="utf-8"))
        r = log["phases"]["restyle"]
        self.assertEqual((r["final_loss"], r["heldout_loss"]), (1.5, 1.9))
        self.assertEqual([(e["epoch"], e["train_loss"], e["heldout_loss"]) for e in r["epochs"]], [(1.0, 1.7, 2.1), (2.0, 1.5, 1.9)])
        self.assertEqual((r["skipped_too_long"], r["heldout_skipped_too_long"]), (0, 0))
        self.assertEqual(set(log["phases"]), {"restyle"})
        self.assertEqual((log["args"]["phase"], log["args"]["lr_restyle"], log["args"]["epochs_restyle"], log["args"]["seq_restyle"]), ("restyle", 2e-4, 2, 1024))
        self.assertTrue((out / "adapter_model.safetensors").exists())

    def test_the_options_reach_the_phase_and_a_dry_run_goes_to_its_own_folder(self):
        d = restyle_folder(self)
        seen, _ = self.run_train(d, self.tmp() / "a", "--epochs-restyle", "1", "--lr-restyle", "1e-4", "--dry-run")
        self.assertEqual((seen["lr"], seen["epochs"], seen["dry"]), (1e-4, 1, True))

    def test_it_stops_when_the_data_is_not_ready(self):
        with self.assertRaises(SystemExit) as cm, contextlib.redirect_stdout(io.StringIO()):
            self.run_train(self.tmp(), self.tmp() / "a")
        self.assertIn("--check-data --phase restyle", str(cm.exception))

    def test_the_default_phase_does_not_include_it_and_the_other_phases_do_not_read_it(self):
        d = self.good()
        write(d, "hegelizer.jsonl", [restyle_row(0), restyle_row(1, "held")])
        loads = []

        def stop(args, adapter=None):
            loads.append(args.phase)
            raise SystemExit("stop")

        with mock.patch.object(th, "load_model", stop), mock.patch.object(th, "versions", return_value={}), contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(SystemExit):
                th.main(["--base", "x/y", "--data", str(d), "--out", str(self.tmp() / "a")])
        self.assertEqual(loads, ["both"])                                   # (phase 1 loads first, and the stand-in stops it there)
        self.assertEqual(th.phases_of("both"), ["corpus", "format"])
        self.assertEqual((th.phases_of("restyle"), th.phases_of("format")), (["restyle"], ["format"]))


if __name__ == "__main__":
    unittest.main()
