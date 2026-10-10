"""Actual engine passes checked transactions to NPCs; own speech cannot manufacture money."""
import json,unittest
from datetime import date
from world.mind import StubMind
from world.world import at_dt
from test_world import Sandbox,answer

class CapturingMind(StubMind):
    def __init__(self,decision):self.decision=decision;self.calls=[]
    def decide(self,messages,sit):return json.dumps(self.decision)
    def chat(self,messages,schema=None,**kwargs):
        self.calls.append(messages)
        return super().chat(messages,schema,**kwargs)

class VoiceTransactionTest(unittest.TestCase):
    def run_step(self,decision,already_paid=False):
        box=Sandbox();self.addCleanup(box.close);mind=CapturingMind(decision);e=box.engine(mind);day=e.new_day(box.days.load(date(2026,10,2)),date(2026,10,3));day['state'].update(place=decision['place'],asleep=False)
        if already_paid:day["state"]["costs"]["dhobi"]="2026-10-03"
        step=e.step(day,at_dt(date(2026,10,3),510))
        return day,step,[m[-1]['content'] for m in mind.calls if 'This exchange includes' in m[-1]['content'] or 'No payment or purchase is recorded' in m[-1]['content']]
    def test_npc_receives_canonical_price_of_current_checked_purchase(self):
        day,step,packets=self.run_step(answer(action='buy',place='lodhi',minutes=5,says='Sunil, one chai.',buys=[{'item':'Chai','price_inr':5}]))
        self.assertEqual(len(packets),1)
        line=next(x for x in packets[0].splitlines() if x.startswith('This exchange includes'))
        self.assertIn('₹20',line);self.assertNotIn('₹5',line)
        self.assertIn('Do not charge or request payment',line)
        charged=[e['price'] for e in day['entries'] if e['k']=='bag'];self.assertIn(20,charged)
    def test_spoken_cash_offer_without_buys_is_not_reported_as_payment(self):
        day,step,packets=self.run_step(answer(action='talk',place='home',minutes=5,says='Ramesh, take three hundred rupees for the dhobi.',buys=[]),already_paid=True)
        self.assertEqual(len(packets),1)
        self.assertIn('No payment or purchase is recorded for this exchange',packets[0])
        self.assertIn('do not narrate taking money',packets[0])
        self.assertEqual(step['decision']['buys'],[])

    def test_npc_sees_automatic_payment_made_in_current_situation(self):
        day,step,packets=self.run_step(answer(action='talk',place='home',minutes=5,says='Ramesh, the dhobi bill.',buys=[]))
        self.assertEqual(len(packets),1)
        self.assertIn('This exchange includes',packets[0])
        self.assertIn('The dhobi ₹300',packets[0])
        self.assertNotIn('No payment or purchase is recorded',packets[0])
        self.assertEqual(len([e for e in day['entries'] if e['k']=='expense' and e.get('settles') and e['amount']==300]),1)

if __name__=='__main__':unittest.main()
