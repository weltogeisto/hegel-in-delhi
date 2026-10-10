"""An NPC's fluent promises cannot override the world it is speaking in."""
import copy,unittest
from unittest import mock
from world.engine import Engine
from world.world import World
from world import voices
from test_world import state

class VoiceWorldFactsTests(unittest.TestCase):
    def engine(self):
        e=Engine.__new__(Engine);e.world=World();e.voice_prompt="Delhi NPC"
        e.memory=mock.Mock();e.memory.before.return_value=[];e.memory.moments.return_value=["You said the garment was finished early."]
        e.mind=mock.Mock(spec=["chat"]);e.mind.chat.return_value='{"says":"Ji.","does":null}'
        return e
    def call(self,e,st,cid="masterji",purchases=None):
        day={"date":"2026-10-03","state":st};sit=dict(day="Saturday 3 October",time="19:12",place="khan",outfit="white cotton kurta",event="He asks about the order.",for_sale=[])
        before=copy.deepcopy(day)
        e.voice(cid,day,sit,"Is it ready?",purchases=purchases)
        self.assertEqual(day,before)
        return e.mind.chat.call_args.args[0][-1]["content"]
    def test_unfinished_order_remains_authoritative_over_prior_claim(self):
        e=self.engine();st=state();st["flags"]["bandhgala"]="ordered"
        text=self.call(e,st)
        self.assertIn("ordered; not yet ready for collection",text)
        self.assertIn("You said the garment was finished early",text)
        self.assertIn("authoritative over conflicting dialogue",text)
    def test_ready_and_collected_orders_are_distinguished(self):
        for phase,phrase in [("ready","ready for collection; not yet collected"),("collected","already collected; do not charge")]:
            e=self.engine();st=state();st["flags"]["bandhgala"]=phase
            st["wardrobe"]=[dict(id="bandhgala",item="Bandhgala",status=phase)]
            self.assertIn(phrase,self.call(e,st))
    def test_current_checked_payment_is_not_erased_by_pre_exchange_state(self):
        e=self.engine();st=state();st["flags"]["bandhgala"]="ready"
        text=self.call(e,st,purchases=[dict(item="Bandhgala balance",price=3500)])
        self.assertIn("before this exchange",text);self.assertIn("checked current payments below still apply",text)
        self.assertIn("Bandhgala balance ₹3,500",text)
    def test_cost_is_read_from_world_and_is_not_a_visit_schedule(self):
        e=self.engine();e.world.costs=[dict(id="dhobi",amount=425,when=dict(weekday="Tue"))]
        facts=voices.recorded_facts(e.world,"ramesh",state())
        self.assertIn("₹425, due each Tue",facts[0]);self.assertIn("not a confirmed collection or delivery visit",facts[0])
    def test_scope_does_not_reveal_other_characters_or_private_thoughts(self):
        e=self.engine();st=state();st["private_thought"]="A secret manuscript";st["flags"]["bandhgala"]="ordered"
        text=self.call(e,st,cid="sunil")
        self.assertNotIn("Your bandhgala order",text);self.assertNotIn("washing charge",text);self.assertNotIn("A secret manuscript",text)
    def test_missing_order_does_not_invent_an_agreement(self):
        e=self.engine();self.assertEqual(voices.recorded_facts(e.world,"masterji",{}),[])

    def test_paid_washing_cannot_be_requested_again(self):
        e=self.engine();st=state();st["owed"]=[];st["costs"]={"dhobi":"2026-10-03"}
        text=self.call(e,st,cid="ramesh")
        self.assertIn("current recorded unpaid washing balance is ₹0",text)
        self.assertIn("Do not request payment for a settled or not-yet-due charge",text)
    def test_balance_sums_only_actual_unpaid_washing(self):
        e=self.engine();st=state();st["owed"]=[dict(cost="dhobi",amount=300),dict(cost="dhobi",amount=300),dict(cost="groceries",amount=1500)]
        before=copy.deepcopy(st);facts=voices.recorded_facts(e.world,"dhobi",st)
        self.assertEqual(st,before);self.assertIn("unpaid washing balance is ₹600",facts[-1])
        self.assertNotIn("₹1,500"," ".join(facts))
    def test_missing_ledger_does_not_claim_a_zero_balance(self):
        e=self.engine();facts=voices.recorded_facts(e.world,"ramesh",{})
        self.assertNotIn("unpaid washing balance"," ".join(facts))

if __name__=="__main__":unittest.main()
