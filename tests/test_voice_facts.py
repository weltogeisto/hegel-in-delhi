"""P2, HEGEL_VOICE_FACTS: a voice's own side of the record, its pronoun, and who answers."""
import json,sys,unittest
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parent))
from world import voices
from world.engine import Engine
from world.world import World
from test_world import state

BASE=json.loads('{"ramesh": "You are Ramesh, caretaker of the bungalow for the Central Public Works Department. Looks after the bungalow for the Central Public Works Department. Brings tea before it is asked for, keeps the papers in order and has seen three allottees come and go. Says little and misses less.\\n\\nSaturday 3 October, 19:12, Khan Market. His outfit: white cotton kurta.\\nYou are speaking here, at this current place. The event may also quote words spoken earlier somewhere else; those words do not move you or this place.\\nCurrent observed weather: 30 °C. Earlier weather is unknown unless supplied in the history; do not invent a weather history.\\nRecorded facts within your role, before this exchange (authoritative over conflicting dialogue; checked current payments below still apply):\\n- A fact.\\nRelationship: you have met him. Only the history supplied below establishes what passed between you; do not invent additional encounters or agreements.\\nListed goods and prices here: Samosa ₹20. Do not replace these prices with invented ones.\\nNo payment or purchase is recorded for this exchange. His words may request or promise it; do not narrate taking money or a completed paid handover. You may discuss terms, ask for payment or make an ordinary gesture.\\nWhat is happening (told from his side, so \'you\' there means him): He asks.\\n\\nWhat has passed between you and him:\\n- You met.\\n\\nHe says: “Is it ready?”\\n\\nAnswer with the JSON object only: {\\"says\\": \\"...\\", \\"does\\": null}", "masterji": "You are Masterji, tailor, Khan Market. Has cut collars at Khan Market for forty years, as his father did before him. Measures in silence, speaks in short sentences, and holds a firm view on every neck-cloth he has ever seen.\\n\\nSaturday 3 October, 19:12, Khan Market. His outfit: white cotton kurta.\\nYou are speaking here, at this current place. The event may also quote words spoken earlier somewhere else; those words do not move you or this place.\\nCurrent observed weather: 30 °C. Earlier weather is unknown unless supplied in the history; do not invent a weather history.\\nRecorded facts within your role, before this exchange (authoritative over conflicting dialogue; checked current payments below still apply):\\n- A fact.\\nRelationship: you have met him. Only the history supplied below establishes what passed between you; do not invent additional encounters or agreements.\\nListed goods and prices here: Samosa ₹20. Do not replace these prices with invented ones.\\nNo payment or purchase is recorded for this exchange. His words may request or promise it; do not narrate taking money or a completed paid handover. You may discuss terms, ask for payment or make an ordinary gesture.\\nWhat is happening (told from his side, so \'you\' there means him): He asks.\\n\\nWhat has passed between you and him:\\n- You met.\\n\\nHe says: “Is it ready?”\\n\\nAnswer with the JSON object only: {\\"says\\": \\"...\\", \\"does\\": null}", "nidhi": "You are Nidhi Rao, doctoral student in philosophy, JNU. Writing her doctorate on Hegel. Reads him in German and in English with a pencil, and has views on what he wrote about India that she does not keep to herself. Quick, sardonic, short of money by the end of the month.\\n\\nSaturday 3 October, 19:12, Khan Market. His outfit: white cotton kurta.\\nYou are speaking here, at this current place. The event may also quote words spoken earlier somewhere else; those words do not move you or this place.\\nCurrent observed weather: 30 °C. Earlier weather is unknown unless supplied in the history; do not invent a weather history.\\nRecorded facts within your role, before this exchange (authoritative over conflicting dialogue; checked current payments below still apply):\\n- A fact.\\nRelationship: you have met him. Only the history supplied below establishes what passed between you; do not invent additional encounters or agreements.\\nListed goods and prices here: Samosa ₹20. Do not replace these prices with invented ones.\\nNo payment or purchase is recorded for this exchange. His words may request or promise it; do not narrate taking money or a completed paid handover. You may discuss terms, ask for payment or make an ordinary gesture.\\nWhat is happening (told from his side, so \'you\' there means him): He asks.\\n\\nWhat has passed between you and him:\\n- You met.\\n\\nHe says: “Is it ready?”\\n\\nAnswer with the JSON object only: {\\"says\\": \\"...\\", \\"does\\": null}", "sunil": "You are Sunil, chai seller. Boils tea on a kerosene stove, mornings by the Lodhi Road gate, afternoons in the lane behind Khan Market. Knows the price of everything and the business of everyone.\\n\\nSaturday 3 October, 19:12, Khan Market. His outfit: white cotton kurta.\\nYou are speaking here, at this current place. The event may also quote words spoken earlier somewhere else; those words do not move you or this place.\\nCurrent observed weather: 30 °C. Earlier weather is unknown unless supplied in the history; do not invent a weather history.\\nRecorded facts within your role, before this exchange (authoritative over conflicting dialogue; checked current payments below still apply):\\n- A fact.\\nRelationship: you have met him. Only the history supplied below establishes what passed between you; do not invent additional encounters or agreements.\\nListed goods and prices here: Samosa ₹20. Do not replace these prices with invented ones.\\nNo payment or purchase is recorded for this exchange. His words may request or promise it; do not narrate taking money or a completed paid handover. You may discuss terms, ask for payment or make an ordinary gesture.\\nWhat is happening (told from his side, so \'you\' there means him): He asks.\\n\\nWhat has passed between you and him:\\n- You met.\\n\\nHe says: “Is it ready?”\\n\\nAnswer with the JSON object only: {\\"says\\": \\"...\\", \\"does\\": null}"}')
SIT=dict(day="Saturday 3 October",time="19:12",place="khan",outfit="white cotton kurta",event="He asks.",for_sale=["Samosa ₹20"],weather="30 °C")

class VoiceFactsTests(unittest.TestCase):
    def setUp(self):
        self.w=World()
    def facts(self,cid,st,on=True):
        return voices.recorded_facts(self.w,cid,st,voice_facts=on)
    def test_off_adds_nothing(self):
        st=state();st["flags"]["hegde_lodger"]=True
        self.assertEqual(self.facts("hegde",st,False),[]);self.assertEqual(self.facts("saxena",st,False),[])
        self.assertEqual(voices.recorded_facts(self.w,"hegde",st),[])
    def test_hegde_lodger_with_call(self):
        st=state();st["flags"]["hegde_lodger"]=True;st["file"]="Shri Hegde moves into the second bedroom, pending orders.";st["beats"]+=["hegde_note","hegde_call","hegde_gate"]
        self.assertEqual(self.facts("hegde",st),["You live in the second bedroom of the bungalow, because the Professor agreed at the gate.",
            "The Directorate's word on the file today: Shri Hegde moves into the second bedroom, pending orders.",
            "You called at the bungalow at ten, in person, and the Professor received you."])
    def test_hegde_guest_house_with_card(self):
        st=state();st["flags"].pop("hegde_lodger",None);st["file"]="Shri Hegde returns to the guest house in Chanakyapuri, pending orders.";st["beats"]+=["hegde_note","hegde_card"]
        f=self.facts("hegde",st)
        self.assertEqual(f[0],"You are staying at the guest house in Chanakyapuri. You do not live at the bungalow.")
        self.assertIn("Chanakyapuri, pending orders",f[1]);self.assertIn("left your card",f[2]);self.assertNotIn("second bedroom"," ".join(f))
    def test_saxena(self):
        st=state();st["file"]="Back from orders with a query: proof of identity as Shri G. Hegde."
        st["owed"]=[dict(to="the Directorate of Estates",amount=640,why="queried vouchers",since="2026-10-20",at="estates",**{"with":"saxena"}),dict(cost="dhobi",amount=300,**{"with":"ramesh"})]
        st["appointments"]=[dict(date="2026-10-20",t=None,what="the file is due back from orders",beat="saxena_query"),dict(date="2026-10-19",t="10:00",what="Shri Hegde calls at the bungalow",beat="hegde_call")]
        self.assertEqual(self.facts("saxena",st),["The file's status line today: Back from orders with a query: proof of identity as Shri G. Hegde.",
            "Owed and queried at your desk: ₹640, queried vouchers, since 2026-10-20.",
            "Due at your desk: the file is due back from orders, on 2026-10-20."])
    def test_saxena_nothing_owed(self):
        st=state();st["owed"]=[];st["appointments"]=[]
        self.assertIn("Nothing is recorded as queried or owed at your desk.",self.facts("saxena",st))
    def test_pronouns(self):
        for cid,c in self.w.cast.items():
            self.assertIn(c.get("pronoun"),("he","she"),cid)
        self.assertEqual(self.w.cast["nidhi"]["pronoun"],"she");self.assertEqual(self.w.cast["hegde"]["pronoun"],"he")
    def render(self,cid,on=False):
        return voices.render(self.w.cast[cid],SIT,"Khan Market","Is it ready?",["You met."],first_meeting=False,purchases=[],world_facts=["A fact."],**({"voice_facts":True} if on else {}))
    def test_off_prompt_is_todays(self):
        for cid in BASE:
            with self.subTest(cid=cid):self.assertEqual(self.render(cid),BASE[cid])
    def test_on_prompt_tells_pronoun(self):
        self.assertIn("Says little and misses less. Ramesh is a man: he, him.\n",self.render("ramesh",True))
        self.assertIn("Nidhi Rao is a woman: she, her.",self.render("nidhi",True))
        self.assertEqual(self.render("ramesh",True).replace(" Ramesh is a man: he, him.",""),BASE["ramesh"])
        self.assertIn("The ticket clerk is a man: he, him.",voices.render(self.w.cast["clerk"],SIT,"Tomb","x",[],voice_facts=True))
    def test_samosa_goes_to_sunil_only_with_switch(self):
        c=self.w.cast;p=["masterji","bookseller","sunil"]
        self.assertEqual(voices.pick(c,"One samosa, please.",p),"masterji")
        self.assertEqual(voices.pick(c,"One samosa, please.",p,facts=True),"sunil")
        self.assertEqual(voices.pick(c,"One samosa, please.",["bookseller","sunil"],facts=True),"sunil")
    def test_explicit_recipient_wins(self):
        c=self.w.cast
        self.assertEqual(voices.pick(c,"One samosa, please.",["bookseller","sunil"],recipient="bookseller",facts=True),"bookseller")
    def test_order_of_preference(self):
        c=self.w.cast;p=["masterji","sunil","bookseller"]
        self.assertEqual(voices.pick(c,"Sunil, a book for Masterji?",p,facts=True),"sunil")
        self.assertEqual(voices.pick(c,"Thank you.",p,facts=True,purchases=[dict(item="Samosa",price=20)]),"sunil")
        ent=[dict(k="said",by="The bookseller",to="Hegel",t="10:00",text="x")]
        seg=lambda at:[{"from":"09:00","to":"11:00","at":at}]
        self.assertEqual(voices.pick(c,"Thank you.",p,facts=True,entries=ent,segments=seg("khan"),place="khan"),"bookseller")
        self.assertEqual(voices.pick(c,"Thank you.",p,facts=True,entries=ent,segments=seg("lodhi"),place="khan"),"masterji")
        self.assertEqual(voices.pick(c,"Thank you.",p,facts=True),"masterji")
    def test_engine_reply_follows_switch(self):
        for on,want in ((True,"sunil"),(False,"masterji")):
            e=Engine.__new__(Engine);e.world=self.w;e.cfg=SimpleNamespace(voice_facts=on);got=[]
            e.voice=lambda cid,day,sit,says,purchases=None:got.append(cid)
            e.reply({"entries":[],"segments":[]},dict(place="khan",time="10:00"),dict(present=["masterji","bookseller","sunil"]),"One samosa, please.")
            self.assertEqual(got,[want])

if __name__=="__main__":unittest.main()
