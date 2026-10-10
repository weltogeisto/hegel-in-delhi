"""Chat continuations must name an existing manuscript; never guess a target."""
import copy
import json
import unittest
from datetime import date, datetime
from unittest import mock
from world import works
from world.engine import Engine


class Replies:
    def __init__(self, replies):
        self.replies = replies
        self.calls = []

    def chat(self, messages, *args, **kwargs):
        self.calls.append(copy.deepcopy(messages))
        return json.dumps(self.replies[min(len(self.calls)-1, len(self.replies)-1)])


class ContinuationTargetTest(unittest.TestCase):
    def writing(self, title, continues):
        return dict(title=title, kind="notes", to=None, continues=continues,
                    text="The earlier distinction must be developed, rather than simply repeated.")

    def setup_engine(self, replies):
        e = Engine.__new__(Engine)
        e.mind = Replies(replies)
        e.world = mock.Mock()
        e.world.unmet.return_value = []
        st = {}
        works.file(st, self.writing("A difficulty", False), date(2026,10,3))
        return e, st

    def call(self, e, st):
        return e.write_chat([dict(role="system",content="Hegel."),dict(role="user",content="At the desk.")],
                            '{"action":"write"}',dict(t=datetime(2026,10,4,10),known_text="At the desk."),st)

    def test_unknown_continuation_is_corrected_before_filing(self):
        e,st = self.setup_engine([self.writing("A difficulty (continued)",True),self.writing("A difficulty",True)])
        result = self.call(e,st)
        self.assertEqual(result["title"],"A difficulty")
        self.assertEqual(len(e.mind.calls),2)
        self.assertIn("not an existing manuscript",e.mind.calls[1][-1]["content"])
        self.assertIn('A difficulty',e.mind.calls[1][-1]["content"])
        entry = works.file(st,result,date(2026,10,4))
        self.assertEqual(entry["sitting"],2)
        self.assertEqual(len(st["works"]),1)

    def test_repeated_unknown_continuation_is_dropped_without_mutation(self):
        e,st = self.setup_engine([self.writing("A difficulty (continued)",True)])
        before=copy.deepcopy(st)
        with self.assertLogs("world",level="WARNING") as captured:
            self.assertIsNone(self.call(e,st))
        self.assertEqual(st,before)
        self.assertEqual(len(e.mind.calls),2)
        self.assertTrue(any("unknown continuation" in line for line in captured.output))

    def test_explicitly_new_work_with_similar_title_is_allowed(self):
        e,st = self.setup_engine([self.writing("A difficulty (continued)",False)])
        result=self.call(e,st)
        self.assertFalse(result["continues"])
        self.assertEqual(len(e.mind.calls),1)

    def test_existing_title_case_variation_continues_without_retry(self):
        e,st = self.setup_engine([self.writing("a DIFFICULTY",True)])
        result=self.call(e,st)
        self.assertTrue(result["continues"])
        self.assertEqual(len(e.mind.calls),1)
        self.assertEqual(works.file(st,result,date(2026,10,4))["sitting"],2)

    def test_no_existing_works_can_be_corrected_to_a_new_work(self):
        e,st = self.setup_engine([self.writing("First note",True),self.writing("First note",False)])
        st={}
        result=self.call(e,st)
        self.assertFalse(result["continues"])
        self.assertEqual(len(e.mind.calls),2)
        self.assertEqual(st,{})


if __name__ == "__main__":
    unittest.main()
