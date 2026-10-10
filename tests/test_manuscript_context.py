import copy,json,tempfile,unittest
from datetime import date
from pathlib import Path
from world.engine import Days
from world.memory import Memory
from world import works

class ManuscriptContextTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.days=Days(Path(self.temp.name));self.memory=Memory(self.days,None)
    def tearDown(self):self.temp.cleanup()
    def day(self,d):
        return dict(date=d,n=1,title='A day',holiday=None,entries=[],state={'works':[]})
    def writing(self,day,text,title='A difficulty',continues=False,t='10:00'):
        e=works.file(day['state'],dict(title=title,kind='notes',to=None,continues=continues,text=text),date.fromisoformat(day['date']))
        e['t']=t;day['entries'].append(e);return e
    def test_prior_draft_enters_context_with_attribution(self):
        day=self.day('2026-10-03');self.writing(day,'The register is not before me. I do not know whose name it bears.')
        before=copy.deepcopy(day);text=self.memory.manuscripts(day,before_time='12:00')
        self.assertIn('2026-10-03 10:00, sitting 1',text)
        self.assertIn('I do not know whose name it bears.',text)
        self.assertIn('not independent evidence of events',text)
        self.assertEqual(day,before)
    def test_cross_day_retrieval_and_current_memory_take_precedence(self):
        first=self.day('2026-10-03');self.writing(first,'The first premise is still open.');self.days.save(first)
        second=self.day('2026-10-04');second['state']=copy.deepcopy(first['state']);self.days.save(second)
        self.writing(second,'The next difficulty follows from that premise.',continues=True,t='09:00')
        self.writing(second,'FUTURE WRITING MUST NOT LEAK',continues=True,t='13:00')
        text=self.memory.manuscripts(second,before_time='12:00')
        self.assertIn('The first premise is still open.',text);self.assertIn('The next difficulty follows',text)
        self.assertNotIn('FUTURE WRITING',text)
    def test_old_work_start_survives_more_than_fourteen_days(self):
        first=self.day('2026-09-01');self.writing(first,'Old opening premise.');self.days.save(first)
        last=self.day('2026-10-04');last['state']=copy.deepcopy(first['state'])
        self.writing(last,'Latest development.',continues=True,t='09:00')
        text=self.memory.manuscripts(last,before_time='12:00')
        self.assertIn('Old opening premise.',text);self.assertIn('Latest development.',text)
    def test_budget_shares_space_between_works_and_marks_omission(self):
        day=self.day('2026-10-03')
        for n in range(3):
            self.writing(day,f'Opening premise {n}. '+'Unfinished argument. '*250+f' Final qualification {n}.',title=f'Work {n}',t=f'0{n+7}:00')
        text=self.memory.manuscripts(day,before_time='12:00',limit=4000)
        self.assertLessEqual(len(text),4000)
        for n in range(3):self.assertIn(f'Opening premise {n}.',text);self.assertIn(f'Final qualification {n}.',text)
        self.assertIn('middle of this sitting omitted',text)
    def test_no_work_and_unknown_legacy_work_have_no_fabricated_text(self):
        day=self.day('2026-10-03');self.assertEqual(self.memory.manuscripts(day),'')
        day['state']['works']=[dict(title='Old work',kind='letter',sittings=1)]
        self.assertEqual(self.memory.manuscripts(day),'')

class ThesisReminderTest(unittest.TestCase):
    def test_disabling_repeated_reminder_preserves_stored_beliefs(self):
        import sys
        from unittest import mock
        sys.path.insert(0,str(Path(__file__).resolve().parent))
        from test_world import Sandbox
        from world.world import at_dt
        box=Sandbox()
        try:
            engine=box.engine();engine.cfg.thesis_reminders=False
            day=engine.new_day(box.days.load(date(2026,10,2)),date(2026,10,3))
            day['state']['asleep']=False
            before=copy.deepcopy(day['state']['theses']);seen=[]
            def decide(messages,sit):
                seen.append(copy.deepcopy(sit))
                return json.dumps(dict(thought='I rest briefly.',action='rest',place='home',minutes=15,says=None,buys=[],revision=None,looks_up=None))
            with mock.patch.object(engine.mind,'decide',side_effect=decide):engine.step(day,at_dt(date(2026,10,3),720))
            self.assertTrue(seen)
            self.assertFalse(any(line.startswith('Your theses: ') for line in seen[0]['on_mind']))
            self.assertEqual(day['state']['theses'],before)
        finally:box.close()

if __name__=='__main__':unittest.main()