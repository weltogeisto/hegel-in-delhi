"""HEGEL_NOTEBOOK (pc/NOTEBOOK.md): each night the owl rewrites his notebook of the age, and it is in his prompt the next
day. Off, nothing changes: not the owl's call, not the state, not his prompt."""
import copy
import json
import unittest
from pathlib import Path
from types import SimpleNamespace

from world import contract, owl
from world.config import Config

R = Path(__file__).resolve().parents[1]


class Mind:
    def __init__(self, notebook="Machines answer when spoken to. The Directorate keeps time by files, not by clocks."):
        self.calls, self.notebook = [], notebook

    def chat(self, messages, schema, **kw):
        self.calls.append((messages, schema, kw))
        out = {"diary": "He walked to the market and back, and wrote nothing that mattered. " * 2,
               "revision_log": "", "theses": []}
        if "notebook" in schema["properties"]:
            out["notebook"] = self.notebook
        return json.dumps(out)


def cfg():
    return SimpleNamespace(repo=R, owl_reasoning_tokens=0, outcome_memory=False, evidence_view="full")


def day():
    return {"n": 49, "date": "2026-11-19", "title": "Thursday", "complete": True, "segments": [], "steps": [],
            "entries": [{"k": "diary", "t": "09:30", "text": "The tea is hot."}]}


class NotebookTest(unittest.TestCase):
    def test_off_by_default_and_the_owl_is_asked_as_before(self):
        self.assertFalse(Config({}).notebook)
        self.assertTrue(Config({"HEGEL_NOTEBOOK": "1"}).notebook)
        mind, st = Mind(), {"theses": []}
        before = copy.deepcopy(st)
        written = owl.write(cfg(), day(), st, mind)
        self.assertNotIn("notebook", mind.calls[0][1]["properties"])
        self.assertNotIn("notebook", mind.calls[0][0][1]["content"])
        self.assertNotIn("notebook", written)
        self.assertEqual(st, before)

    def test_on_the_owl_rewrites_it_and_the_state_keeps_it(self):
        mind, st = Mind(), {"theses": [], "notebook": {"text": "Trains run under the city.", "written": "2026-11-18"}}
        written = owl.write(cfg(), day(), st, mind, notebook=True)
        ask = mind.calls[0][0][1]["content"]
        self.assertIn("Trains run under the city.", ask)                      # the old notebook is shown to the owl
        self.assertIn("notebook", mind.calls[0][1]["properties"])
        self.assertEqual(mind.calls[0][2]["max_tokens"], 1700)
        self.assertEqual(written["notebook"], mind.notebook)
        self.assertEqual(st["notebook"], {"text": mind.notebook, "written": "2026-11-19", "day": 49})

    def test_an_empty_notebook_is_begun(self):
        mind = Mind()
        owl.write(cfg(), day(), {"theses": []}, mind, notebook=True)
        self.assertIn("(empty: begin it tonight)", mind.calls[0][0][1]["content"])

    def test_it_is_capped_and_cut_after_a_sentence(self):
        st = {"theses": []}
        owl.write(cfg(), day(), st, Mind(notebook="A train is a house that runs on iron. " * 80), notebook=True)
        text = st["notebook"]["text"]
        self.assertLessEqual(len(text), owl.NOTEBOOK_CHARS)
        self.assertTrue(text.endswith("."))

    def test_the_knowledge_gate_reads_the_notebook_too(self):
        seen = []
        def problems(text):
            seen.append(text)
            return []
        owl.write(cfg(), day(), {"theses": []}, Mind(notebook="The telephone is a voice without a face."), problems=problems, notebook=True)
        self.assertIn("The telephone is a voice without a face.", seen[0])

    def test_his_prompt_shows_it_only_when_given(self):
        sit = {"day": "Friday 20 November", "time": "09:15", "place": "home", "weather": "21 °C, clear", "aqi": "150",
               "outfit": "kurta", "imprest_left": 100, "present": [], "open_now": ["home"], "event": "You wake."}
        self.assertNotIn("notebook of this age", contract.render(sit))
        self.assertIn("Your notebook of this age, as you keep it each night:\nTrains run under the city.",
                      contract.render(dict(sit, notebook="Trains run under the city.")))


if __name__ == "__main__":
    unittest.main()
