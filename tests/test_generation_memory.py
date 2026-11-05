"""CPU-only reproduction of the training -> held generation -> training transition."""
import contextlib
import os
from types import SimpleNamespace
import unittest
from unittest import mock
import weakref

from pc import restyle_round2 as r2


class Buffer:
    shape = (1, 4)

    def to(self, device):
        return self


class Tokens:
    def __len__(self):
        return 3

    def __getitem__(self, key):
        return [4, 5, 0][key]


class Output:
    def __init__(self, refs):
        self.refs = refs
        self.cycle = self

    def __getitem__(self, key):
        tokens = Tokens()
        self.refs.append(weakref.ref(tokens))
        return tokens


class Tokenizer:
    eos_token_id = 0
    padding_side = "right"

    def __init__(self, refs):
        self.refs = refs

    def apply_chat_template(self, messages, **kwargs):
        return "prompt"

    def __call__(self, text, **kwargs):
        inputs = {"input_ids": Buffer(), "attention_mask": Buffer()}
        self.refs.extend(weakref.ref(value) for value in inputs.values())
        return inputs

    def decode(self, ids, **kwargs):
        return "saved answer"


class Model:
    def __init__(self, tok, refs, device="cuda", fail=False):
        self.training = True
        self.gradient_checkpointing = "unsloth"
        self.config = SimpleNamespace(use_cache=False, text_config=SimpleNamespace(use_cache=False))
        self.child = SimpleNamespace(training=False, gradient_checkpointing=False)
        self._saved_temp_tokenizer = tok
        self.refs = refs
        self.fail = fail
        self.device = SimpleNamespace(type=device, index=0 if device == "cuda" else None)
        self.weight = SimpleNamespace(device=self.device, grad=object(), value=7)
        self.restored_modes = []
        self.arguments = None

    def parameters(self):
        return iter([self.weight])

    def modules(self):
        return iter([self, self.child])

    def eval(self):
        self.train(False)

    def train(self, mode=True):
        self.training = self.child.training = mode

    def generate(self, **kwargs):
        self.arguments = {k: v for k, v in kwargs.items() if k not in ("input_ids", "attention_mask")}
        # Installed Unsloth FastBaseModel.for_inference mutates these during generate.
        self.gradient_checkpointing = self.child.gradient_checkpointing = False
        self._flag_for_generation = self.child._flag_for_generation = True
        self.config.use_cache = self.config.text_config.use_cache = True
        self._saved_temp_tokenizer.padding_side = "left"
        os.environ["UNSLOTH_RETURN_LOGITS"] = "1"
        os.environ["UNSLOTH_RETURN_HIDDEN_STATES"] = "0"
        self._cache = Buffer()
        self.child._flex_attention_cache = Buffer()
        self.weight._fast_lora = Buffer()
        self.refs.extend([weakref.ref(self._cache), weakref.ref(self.child._flex_attention_cache),
                          weakref.ref(self.weight._fast_lora)])
        if self.fail:
            raise RuntimeError("generation failed")
        answer = Output(self.refs)
        self.refs.append(weakref.ref(answer))
        return answer

    def for_training(self, use_gradient_checkpointing=True):
        self.restored_modes.append(use_gradient_checkpointing)
        self.gradient_checkpointing = self.child.gradient_checkpointing = use_gradient_checkpointing
        self.train()
        if hasattr(self.weight, "_fast_lora"):
            del self.weight._fast_lora


def fake_torch(on_empty=lambda: None):
    torch = SimpleNamespace(seed=99, calls=[])
    @contextlib.contextmanager
    def fork(**kwargs):
        before = torch.seed
        try:
            yield
        finally:
            torch.seed = before
    @contextlib.contextmanager
    def device(value):
        torch.calls.append(("device", value.index))
        yield
    def empty():
        torch.calls.append(("empty",))
        on_empty()
    torch.random = SimpleNamespace(fork_rng=fork)
    torch.inference_mode = contextlib.nullcontext
    torch.manual_seed = lambda seed: setattr(torch, "seed", seed)
    torch.cuda = SimpleNamespace(synchronize=lambda dev: torch.calls.append(("sync", dev.index)),
                                 device=device, empty_cache=empty)
    return torch


class GenerationMemoryTest(unittest.TestCase):
    def fixture(self, **kwargs):
        refs = []
        tok = Tokenizer(refs)
        model = Model(tok, refs, **kwargs)
        return refs, tok, model

    def assert_restored(self, model, tok):
        self.assertTrue(model.training)
        self.assertFalse(model.child.training)
        self.assertEqual(model.gradient_checkpointing, "unsloth")
        self.assertIs(model.child.gradient_checkpointing, False)
        self.assertFalse(model.config.use_cache)
        self.assertFalse(model.config.text_config.use_cache)
        self.assertEqual(tok.padding_side, "right")
        self.assertFalse(hasattr(model, "_flag_for_generation"))
        self.assertFalse(hasattr(model.child, "_flag_for_generation"))

    def test_releases_temporaries_before_empty_cache_and_keeps_weights(self):
        refs, tok, model = self.fixture()
        weight, grad = model.weight, model.weight.grad
        def released():
            self.assert_restored(model, tok)
            self.assertTrue(all(ref() is None for ref in refs))
        torch = fake_torch(released)
        with mock.patch.dict(os.environ, {"UNSLOTH_RETURN_LOGITS": "0",
                                        "UNSLOTH_RETURN_HIDDEN_STATES": "1"}):
            answer = r2.generate_for_model(model, tok, "plain", 1831, 100, torch)
            self.assertEqual(os.environ["UNSLOTH_RETURN_LOGITS"], "0")
            self.assertEqual(os.environ["UNSLOTH_RETURN_HIDDEN_STATES"], "1")
        self.assertEqual(answer, dict(text="saved answer", generated_tokens=3, finish_reason="stop"))
        self.assertEqual(torch.calls, [("sync", 0), ("device", 0), ("empty",)])
        self.assertIs(model.weight, weight)
        self.assertIs(model.weight.grad, grad)
        self.assertEqual(model.weight.value, 7)
        self.assertEqual(model.restored_modes, ["unsloth"])
        self.assertEqual(torch.seed, 99)

    def test_restores_state_and_releases_cache_on_generation_error(self):
        refs, tok, model = self.fixture(fail=True)
        torch = fake_torch()
        with self.assertRaisesRegex(RuntimeError, "generation failed"):
            r2.generate_for_model(model, tok, "plain", 1831, 100, torch)
        self.assert_restored(model, tok)
        self.assertEqual(torch.seed, 99)
        self.assertEqual(torch.calls[-1], ("empty",))

    def test_cpu_generation_never_uses_cuda(self):
        refs, tok, model = self.fixture(device="cpu")
        torch = fake_torch()
        r2.generate_for_model(model, tok, "plain", 1831, 100, torch)
        self.assertEqual(torch.calls, [])
        self.assert_restored(model, tok)

    def test_repeated_generations_keep_exact_sampling_and_training_state(self):
        refs, tok, model = self.fixture()
        torch = fake_torch()
        for seed in (1831, 1848):
            r2.generate_for_model(model, tok, "plain", seed, 100, torch)
            self.assert_restored(model, tok)
            self.assertEqual(torch.seed, 99)
        self.assertEqual(model.arguments, dict(max_new_tokens=100, temperature=0.9, do_sample=True,
                                              pad_token_id=0, use_cache=True, disable_compile=True))

    def test_preserves_preexisting_cache_and_mixed_module_flags(self):
        refs, tok, model = self.fixture()
        before = object()
        model._cache = before
        model.child._flag_for_generation = False
        with r2._preserve_generation_state(model, tok):
            model._cache = Buffer()
            model.child._flag_for_generation = True
            model.gradient_checkpointing = False
        self.assertIs(model._cache, before)
        self.assertIs(model.child._flag_for_generation, False)
        self.assertEqual(model.gradient_checkpointing, "unsloth")
        self.assertFalse(model.child.training)

    def test_plain_model_without_unsloth_restore_hook(self):
        model = SimpleNamespace(training=True, gradient_checkpointing=True)
        model.train = lambda value: setattr(model, "training", value)
        tok = SimpleNamespace(padding_side="right")
        with r2._preserve_generation_state(model, tok):
            model.training = model.gradient_checkpointing = False
            model._flag_for_generation = True
        self.assertTrue(model.training)
        self.assertTrue(model.gradient_checkpointing)
        self.assertFalse(hasattr(model, "_flag_for_generation"))


if __name__ == "__main__":
    unittest.main()
