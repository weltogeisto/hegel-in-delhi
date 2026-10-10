"""Only actual charged transactions enter current purchase memory; fixtures never train."""
import copy,unittest
from datetime import date
from world.world import World,at_dt
from test_world import state,answer

class PurchaseMemoryTest(unittest.TestCase):
    def test_actual_corrected_charge_not_requested_price_is_remembered(self):
        w=World();st=state();st['place']='lodhi';day={'steps':[],'entries':[],'segments':[]};at=at_dt(date(2026,10,3),540)
        sit,ctx=w.situation(at,st,day)
        ans=answer(action='buy',place='lodhi',minutes=5,buys=[{'item':'Chai','price_inr':5}])
        errors,warnings,rep=w.check(ans,sit,ctx,st);self.assertEqual(errors,[]);self.assertTrue(warnings)
        cash=st['imprest'];step=w.apply(rep[0],rep[1],sit,ctx,st,day);day['steps'].append(step)
        self.assertEqual(cash-st['imprest'],20)
        self.assertEqual(step['decision']['buys'][0]['price_inr'],5)
        nextsit,_=w.situation(at_dt(date(2026,10,3),545),st,day,step)
        line=next(x for x in nextsit['on_mind'] if x.startswith('Recorded purchases/payments'))
        self.assertIn('₹20',line);self.assertNotIn('₹5',line)
    def test_intentions_and_unpriced_items_do_not_become_paid_transactions(self):
        w=World();st=state();st['place']='home';w.ledger(st);st['costs']['dhobi']='2026-10-03'
        day={'steps':[{'t':'09:00','decision':answer(action='buy',buys=[{'item':'Imagined book','price_inr':100}])}], 'entries':[{'k':'plan','t':'08:00','text':'Buy a book for 100'}, {'k':'bag','t':'08:30','item':'A received parcel'}]}
        before=copy.deepcopy(day);sit,_=w.situation(at_dt(date(2026,10,3),600),st,day)
        self.assertFalse(any(x.startswith('Recorded purchases/payments') for x in sit['on_mind']))
        self.assertEqual(day,before)

    def test_actual_automatic_debt_payment_is_remembered(self):
        w=World();st=state();st['place']='home';w.ledger(st);st['costs']['dhobi']='2026-10-03'
        st['owed']=[{'to':'the dhobi','why':'the washing','item':'The dhobi','amount':300}]
        at=at_dt(date(2026,10,3),480);cash=st['imprest']
        lines,entries=w.settle(at,st,'home',[],{})
        self.assertEqual(cash-st['imprest'],300);self.assertTrue(lines)
        for entry in entries:entry['t']='08:00'
        day={'steps':[],'entries':entries}
        sit,_=w.situation(at_dt(date(2026,10,3),540),st,day)
        line=next(x for x in sit['on_mind'] if x.startswith('Recorded purchases/payments'))
        self.assertIn('The dhobi ₹300',line)
    def test_unsettled_debt_and_income_are_not_paid_out(self):
        w=World();st=state();st['place']='home';st['imprest']=17
        st['owed']=[{'to':'the dhobi','why':'the washing','item':'The dhobi','amount':300}]
        lines,entries=w.settle(at_dt(date(2026,10,3),480),st,'home',[],{})
        self.assertEqual(entries,[]);self.assertEqual(st['imprest'],17)
        day={'steps':[],'entries':[{'k':'income','t':'08:00','item':'A cheque','amount':500}, {'k':'expense','t':'08:00','item':'Unsettled bill','amount':300,'settles':False}]}
        sit,_=w.situation(at_dt(date(2026,10,3),540),st,day)
        self.assertFalse(any(x.startswith('Recorded purchases/payments') for x in sit['on_mind']))

    def test_just_settled_payment_is_visible_before_step_saved(self):
        w=World();st=state();st['place']='home';w.ledger(st);st['costs']['dhobi']='2026-10-03'
        st['owed']=[{'to':'the dhobi','why':'the washing','item':'The dhobi','amount':300}]
        day={'steps':[],'entries':[]};cash=st['imprest']
        sit,ctx=w.situation(at_dt(date(2026,10,3),510),st,day)
        self.assertEqual(cash-st['imprest'],300)
        self.assertEqual(day['entries'],[])
        self.assertTrue(any(e.get('k')=='expense' and e.get('settles') for e in ctx['public']))
        line=next(x for x in sit['on_mind'] if x.startswith('Recorded purchases/payments'))
        self.assertIn('08:30 The dhobi ₹300',line)

if __name__=='__main__':unittest.main()
