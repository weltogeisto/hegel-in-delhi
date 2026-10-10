"""Regression checks for losing the afternoon from the owl's nightly memory."""
import unittest
from world import owl

class OwlChronologyTest(unittest.TestCase):
    def day(self):
        entries=[dict(t=f'{6+i//6:02d}:{(i%6)*10:02d}',k='diary',text='I considered this difficult question. '*14) for i in range(90)]
        entries.extend([dict(t='21:10',k='said',by='Nidhi Rao',text='The appointment is Tuesday, not Monday.'),dict(t='22:00',k='expense',item='Groceries',amount=400)])
        return dict(n=2,title='Saturday',holiday=None,entries=entries,segments=[])

    def test_large_day_keeps_evening_correction_and_transaction(self):
        day=self.day();text=owl.record(day)
        self.assertLessEqual(len(text),24000)
        self.assertIn('21:10 Nidhi Rao said to you: “The appointment is Tuesday, not Monday.”',text)
        self.assertIn('22:00 paid: Groceries, ₹400',text)
        for entry in day['entries']:
            self.assertIn(entry['t'],text)
        self.assertIn('Long entries shortened',text)

    def test_small_complete_day_is_unchanged(self):
        day=self.day();day['entries']=day['entries'][-2:]
        self.assertEqual(owl.record(day),'Day 2, Saturday.\n21:10 Nidhi Rao said to you: “The appointment is Tuesday, not Monday.”\n22:00 paid: Groceries, ₹400')

    def test_small_budget_does_not_silently_drop_late_records(self):
        with self.assertRaisesRegex(owl.OwlError,'no diary generated'):
            owl.record(self.day(),limit=500)

    def test_compaction_keeps_thought_distinct_from_observation(self):
        day=self.day();day['entries'][0]['text']='The appointment may be Monday. '+'Other thought. '*800
        text=owl.record(day,limit=9000)
        self.assertLessEqual(len(text),9000)
        self.assertIn('06:00 thought: The appointment may be Monday.',text)
        self.assertIn('21:10 Nidhi Rao said to you: “The appointment is Tuesday, not Monday.”',text)
        self.assertLess(text.index('06:00 thought:'),text.index('21:10 Nidhi Rao'))

class OwlOutcomeTest(unittest.TestCase):
    def test_closing_inventory_distinguishes_dialogue_from_completed_return(self):
        day=dict(n=2,title='Saturday',holiday=None,segments=[],entries=[dict(t='20:00',k='said',by='Masterji',text='Your jacket is finished; take it tonight.')],
                 state=dict(imprest=1500,wearing='kurta',wardrobe=[dict(item='Bandhgala',status="At Masterji's. Ready Thursday.")],file='Shri Hegde calls Monday.'))
        text=owl.record(day)
        self.assertIn('Masterji said to you',text)
        self.assertIn("Recorded wardrobe: Bandhgala: At Masterji's. Ready Thursday.",text)
        self.assertIn('dialogue, plans and manuscripts do not by themselves change these outcomes',text)
        self.assertIn('Recorded cash: ₹1,500.',text)
    def test_primary_reading_is_not_mislabeled_as_phone_lookup(self):
        day=dict(n=2,title='Saturday',holiday=None,segments=[],entries=[dict(t='16:00',k='read',source='Primary shelf',title='Logic',text='An exact source paragraph.',work='wallace-logic',ref='§119',source_sha256='verified')],state={'wearing':'kurta'})
        text=owl.record(day)
        self.assertIn('16:00 read, from Primary shelf',text)
        self.assertIn('Reading actually delivered at 16:00: Primary shelf, Logic; wallace-logic, §119.',text)
        self.assertNotIn('read on his phone',text)

if __name__=='__main__':unittest.main()