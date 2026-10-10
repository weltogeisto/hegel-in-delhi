"""Recent thought is attributed, not promoted to an observed event; fixtures never enter training."""
import copy,unittest
from datetime import date
from world.world import World,at_dt
from test_world import state

class RecentAttributionTest(unittest.TestCase):
    def scene(self,steps):
        st=state();st['place']='lodhi'
        day={'date':'2026-10-03','steps':copy.deepcopy(steps)}
        before=copy.deepcopy(day)
        sit,ctx=World().situation(at_dt(date(2026,10,3),720),st,day)
        self.assertEqual(day,before)
        return sit
    def test_repaired_stay_and_false_thought_have_separate_provenance(self):
        sit=self.scene([{'t':'11:27','decision':{'action':'stay','place':'lodhi','thought':'I have stood at the Directorate door. The file is silent.'},'mind':{'warnings':['walks to where he already is; treated as stay']}}])
        line=sit['earlier'][0]
        self.assertIn('recorded step: stay (lodhi)',line)
        self.assertIn('you thought: “I have stood at the Directorate door.”',line)
        self.assertIn('Engine note: walks to where he already is; treated as stay.',line)
        self.assertEqual(sit['place'],'lodhi')
    def test_old_steps_without_engine_notes_stay_usable_and_bounded(self):
        steps=[{'t':f'10:{n:02d}','decision':{'action':'read','place':'home','thought':f'Thought number {n}. More text.'}} for n in range(8)]
        sit=self.scene(steps)
        self.assertEqual(len(sit['earlier']),6)
        self.assertNotIn('Thought number 0',' '.join(sit['earlier']))
        self.assertNotIn('Engine note:',' '.join(sit['earlier']))
        self.assertIn('you thought: “Thought number 7.”',sit['earlier'][-1])


    def test_long_recall_is_bounded_and_latest_correction_survives(self):
        steps=[{'t':f'10:{n:02d}','decision':{'action':'stay','place':'lodhi','thought':('A fallible long recollection ' * 30)+'.'},'mind':{'warnings':['walks to where he already is; treated as stay']}} for n in range(8)]
        sit=self.scene(steps)
        self.assertLessEqual(sum(len(x)+3 for x in sit['earlier']),480)
        self.assertTrue(sit['earlier'][-1].startswith('10:07 recorded step: stay (lodhi)'))
        self.assertIn('you thought:',sit['earlier'][-1]);self.assertIn('…',sit['earlier'][-1])
        self.assertIn('walks to where he already is; treated as stay',sit['earlier'][-1])

if __name__=='__main__':unittest.main()
