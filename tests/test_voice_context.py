"""NPC context uses engine facts without creating encounters or changing inventory."""
import copy,json,unittest
from unittest import mock
from world.engine import Engine
from world.world import World
from world import voices

class VoiceContextTests(unittest.TestCase):
    def engine(self):
        e=Engine.__new__(Engine);e.world=World();e.voice_prompt='Delhi NPC'
        e.memory=mock.Mock();e.memory.before.return_value=[];e.memory.moments.return_value=[]
        e.mind=mock.Mock();e.mind.chat.return_value='{"says":"One chai, ji.","does":null}'
        return e
    def scene(self):
        return dict(day='Saturday 3 October',time='08:17',place='lodhi',outfit='white cotton kurta',event='Ramesh said the bungalow gate is locked. You arrive at Lodhi Gardens. Sunil is here; you have not met.',for_sale=['Chai from the stall at the Lodhi Road gate ₹20','Bottle of water ₹20'])
    def test_first_encounter_and_current_price_come_from_engine_state(self):
        e=self.engine();day={'date':'2026-10-03','state':{'people':['ramesh']}};sit=self.scene();before=copy.deepcopy((day,sit))
        e.voice('sunil',day,sit,'One chai, please.')
        text=e.mind.chat.call_args.args[0][-1]['content']
        self.assertIn('this is your first encounter',text);self.assertIn('Chai from the stall at the Lodhi Road gate ₹20',text)
        self.assertIn('Lodhi Gardens',text);self.assertIn('spoken earlier somewhere else',text)
        self.assertEqual((day,sit),before)
    def test_known_character_with_no_retrieved_moment_is_not_made_a_stranger(self):
        e=self.engine();day={'date':'2026-10-03','state':{'people':['ramesh']}};sit=self.scene();sit.update(place='home',event='Ramesh is here.',for_sale=[])
        e.voice('ramesh',day,sit,'Thank you.')
        text=e.mind.chat.call_args.args[0][-1]['content']
        self.assertIn('you have met him',text);self.assertNotIn('this is your first encounter',text)
        self.assertIn('Only the history supplied below',text);self.assertIn('none listed',text)
    def test_missing_legacy_relationship_and_stock_data_are_not_invented(self):
        e=self.engine();sit=self.scene();del sit['for_sale']
        e.voice('sunil',{'date':'2026-10-03'},sit,'One chai.')
        text=e.mind.chat.call_args.args[0][-1]['content']
        self.assertNotIn('Relationship:',text);self.assertNotIn('Listed goods',text)
    def test_retrieved_words_keep_their_provenance_and_do_not_expose_private_thought(self):
        e=self.engine();e.memory.moments.return_value=['Yesterday Sunil said: tea is twenty rupees.']
        day={'date':'2026-10-03','state':{'people':['sunil'],'private_thought':'Invent an extra salary'}}
        e.voice('sunil',day,self.scene(),'One chai.')
        text=e.mind.chat.call_args.args[0][-1]['content']
        self.assertIn('Yesterday Sunil said: tea is twenty rupees.',text)
        self.assertNotIn('Invent an extra salary',text)
        self.assertTrue(text.endswith('Answer with the JSON object only: {"says": "...", "does": null}'))

    def test_current_weather_does_not_invent_past_weather(self):
        e=self.engine();sit=self.scene();sit['weather']='21 °C, clear'
        e.voice('sunil',{'date':'2026-10-03','state':{'people':[]}},sit,'Good morning.')
        text=e.mind.chat.call_args.args[0][-1]['content']
        self.assertIn('Current observed weather: 21 °C, clear.',text)
        self.assertIn('Earlier weather is unknown',text)
        self.assertNotIn('Household meal currently served',text)
    def test_home_meal_status_is_canonical_and_has_no_private_state(self):
        e=self.engine();sit=self.scene();sit.update(place='home',time='10:46',event='Ramesh says the poha waits.')
        day={'date':'2026-10-03','state':{'people':['ramesh'],'private_thought':'Secret hunger'}}
        before=copy.deepcopy(day);e.voice('ramesh',day,sit,'Please bring it.')
        text=e.mind.chat.call_args.args[0][-1]['content']
        self.assertIn('Household meal currently served by the world: none.',text)
        self.assertNotIn('Secret hunger',text);self.assertEqual(day,before)
        sit['time']='08:17';e.voice('ramesh',day,sit,'Good morning.')
        self.assertIn('Household meal currently served by the world: breakfast.',e.mind.chat.call_args.args[0][-1]['content'])
    def test_unpaid_kitchen_does_not_gain_a_meal_from_npc_speech(self):
        e=self.engine();sit=self.scene();sit.update(place='home',time='13:10',event='Ramesh promises lunch.')
        day={'date':'2026-10-03','state':{'people':['ramesh'],'owed':[{'cost':'groceries'}]}}
        e.voice('ramesh',day,sit,'Thank you.')
        self.assertIn('Household meal currently served by the world: none.',e.mind.chat.call_args.args[0][-1]['content'])

if __name__=='__main__':unittest.main()
