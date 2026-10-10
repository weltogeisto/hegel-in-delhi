"""Recorded action effects reach the next decision; dialogue cannot create a meal."""
import copy,unittest
from datetime import date
from world.world import World,at_dt
from test_world import state,answer

class ActivityFeedbackTests(unittest.TestCase):
    def setUp(self):self.world=World();self.st=state();self.day={'steps':[],'segments':[],'entries':[]}
    def scene(self,hour,minute=0,d=date(2026,10,3)):
        return self.world.situation(at_dt(d,60*hour+minute),self.st,self.day)
    def test_npc_food_claim_cannot_execute_an_unavailable_meal(self):
        sit,ctx=self.scene(18,12);sit['event']='Ramesh says: the parathas are ready.'
        before=copy.deepcopy(self.st)
        errors,_,_=self.world.check(answer(action='eat'),sit,ctx,self.st)
        self.assertTrue(any('next service is dinner from 19:30' in x for x in errors))
        self.assertEqual(self.st,before)
        self.assertTrue(any('No household meal is available' in x for x in sit['on_mind']))
    def test_available_meal_executes_and_advances_food_clock(self):
        sit,ctx=self.scene(13,2)
        errors,_,rep=self.world.check(answer(action='eat'),sit,ctx,self.st)
        self.assertEqual(errors,[])
        self.world.apply(*rep,sit,ctx,self.st,self.day)
        self.assertEqual(self.st['last_meal'],'2026-10-03T13:02+05:30')
    def test_arrival_time_controls_availability_not_departure(self):
        self.st['place']='lodhi';sit,ctx=self.scene(12,50)
        errors,_,rep=self.world.check(answer(action='eat',place='home'),sit,ctx,self.st)
        self.assertEqual(errors,[])
        self.assertGreaterEqual(rep[1]['arrival'].hour,13)
    def test_absent_cook_or_unpaid_kitchen_cannot_be_overruled_by_dialogue(self):
        sit,ctx=self.scene(13,10,d=date(2026,10,7))
        self.assertTrue(self.world.check(answer(action='eat'),sit,ctx,self.st)[0])
        self.st=state();sit,ctx=self.scene(13,10);self.st['owed']=[{'cost':'groceries','amount':100000}];self.st['imprest']=0
        self.assertTrue(self.world.check(answer(action='eat'),sit,ctx,self.st)[0])
    def test_executed_stroll_is_distinct_from_a_false_recollection(self):
        self.st['place']='lodhi'
        self.day['segments']=[{'from':'08:00','to':'08:20','mode':'walk','a':'home','b':'lodhi'},
                              {'from':'08:20','to':'09:20','mode':'stroll','at':'lodhi','now':'Walking the paths of Lodhi Gardens.'},
                              {'from':'09:20','to':'09:30','mode':'stand','at':'lodhi','now':'Talking with Sunil.'}]
        self.day['steps']=[{'t':'08:20','end':'09:20','decision':answer(action='stay',place='lodhi',thought='I have sat at the gate all morning.')}]
        before=copy.deepcopy(self.day);sit,_=self.scene(10)
        line=sit['earlier'][0]
        self.assertIn('executed activity: Walking the paths of Lodhi Gardens.',line)
        self.assertIn('you thought: “I have sat at the gate all morning.”',line)
        self.assertNotIn('Talking with Sunil',line);self.assertEqual(self.day,before)

if __name__=='__main__':unittest.main()
