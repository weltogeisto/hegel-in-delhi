"""An automatically settled bill must not be paid again through the same decision."""
import copy,json,unittest
from datetime import date
from pathlib import Path
from world.world import World,at_dt
R=Path(__file__).resolve().parents[1]
ITEM="Groceries for Ramesh's kitchen"

class DuplicateSettlementTests(unittest.TestCase):
 def fixture(self):
  w=World();day=json.loads((R/'docs/days/2026-10-02.json').read_text());st=copy.deepcopy(day['state']);st.update(place='home',asleep=False,today={});w.ledger(st)
  sit=dict(place='home',open_now=['home'],event='You pay Ramesh ₹1,500 for groceries.',imprest_left=st['imprest'],present=['Ramesh'])
  paid=dict(k='expense',item=ITEM,amount=1500,to='Ramesh',why='groceries',settles=True)
  ctx=dict(t=at_dt(date(2026,10,4),6*60+4),present=['ramesh'],public=[paid],recent=[],known_text='Ramesh has been met.')
  ans=dict(thought='The groceries have been paid, and I will wait for breakfast.',action='stay',place='home',minutes=30,says=None,buys=[dict(item=ITEM,price_inr=1500)],revision=None)
  return w,st,sit,ctx,ans
 def test_recorded_automatic_payment_rejects_duplicate_buy(self):
  w,st,sit,ctx,ans=self.fixture();before=copy.deepcopy(st);errors,_,_=w.check(ans,sit,ctx,st)
  self.assertTrue(any('already paid' in e for e in errors));self.assertEqual(st['imprest'],before['imprest'])
 def test_case_and_whitespace_cannot_disguise_the_same_bill(self):
  w,st,sit,ctx,ans=self.fixture();ans['buys'][0]['item']="  GROCERIES   FOR RAMESH'S KITCHEN  "
  self.assertTrue(any('already paid' in e for e in w.check(ans,sit,ctx,st)[0]))
 def test_same_settled_charge_with_a_different_amount_is_still_duplicate(self):
  w,st,sit,ctx,ans=self.fixture();ans['buys'][0]['price_inr']=300
  self.assertTrue(any('already paid' in e for e in w.check(ans,sit,ctx,st)[0]))
 def test_reported_but_unsettled_expense_is_not_blocked_by_this_guard(self):
  w,st,sit,ctx,ans=self.fixture();ctx['public'][0]['settles']=False
  self.assertFalse(any('already paid' in e for e in w.check(ans,sit,ctx,st)[0]))
 def test_unrelated_purchase_and_legacy_context_keep_existing_rules(self):
  w,st,sit,ctx,ans=self.fixture();ans['buys'][0]=dict(item='Additional groceries for the kitchen',price_inr=300)
  self.assertFalse(any('already paid' in e for e in w.check(ans,sit,ctx,st)[0]))
  ans['buys'][0]=dict(item=ITEM,price_inr=1500);ctx.pop('public')
  self.assertFalse(any('already paid' in e for e in w.check(ans,sit,ctx,st)[0]))
 def test_corrected_decision_omitting_the_duplicate_is_accepted(self):
  w,st,sit,ctx,ans=self.fixture();ans['buys']=[]
  errors,_,rep=w.check(ans,sit,ctx,st);self.assertFalse(errors);self.assertEqual(rep[0]['buys'],[])

if __name__=='__main__':unittest.main()
