import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from pc.train_phase2 import read_selected, encode_selected

class PilotInputs(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name); self.parent=self.root/'parent'; self.parent.mkdir()
        self.data=self.root/'pilot'; self.data.mkdir()
        self.raw={'id':'p0','category':'primary','messages':[{'role':'user','content':'Continue'},{'role':'assistant','content':'Authentic words.'}]}
        (self.parent/'source-candidates.jsonl').write_text(json.dumps(self.raw)+'\n')
        (self.parent/'qwen-candidates.jsonl').write_text('')
        self.row=dict(self.raw,review='accepted')
        self.save(self.row)
    def save(self,row):
        row['target_sha256']=hashlib.sha256(row['messages'][-1]['content'].encode()).hexdigest()
        p=self.data/'accepted.jsonl'; p.write_text(json.dumps(row)+'\n')
        (self.data/'selection.json').write_text(json.dumps({'parent':str(self.parent),'parent_frozen_hashes':{},'accepted_sha256':hashlib.sha256(p.read_bytes()).hexdigest()}))
    def test_unchanged_parent_accepted(self):
        self.assertEqual(read_selected(self.data)[0][0]['id'],'p0')
    def test_rehashing_edited_target_does_not_launder_it(self):
        self.row['messages'][-1]['content']='Invented prose.'; self.save(self.row)
        with self.assertRaisesRegex(ValueError,'Original messages changed'): read_selected(self.data)
    def test_json_wrapper_cannot_change_primary_prose(self):
        self.row.update(id='wrapped',parent_id='p0',category='source-writing')
        self.row['messages'][-1]['content']=json.dumps({'kind':'chapter','continues':True,'text':'Invented prose.'})
        self.save(self.row)
        with self.assertRaisesRegex(ValueError,'Primary prose changed'): read_selected(self.data)
    def test_review_gate_cannot_be_skipped(self):
        self.row['review']='pending'; self.save(self.row)
        with self.assertRaisesRegex(ValueError,'Unreviewed'): read_selected(self.data)
    def test_overlength_fails_instead_of_silently_dropping(self):
        class Tok:
            def apply_chat_template(self,messages,**kw):
                return '|'.join(m['content'] for m in messages)+('|' if kw.get('add_generation_prompt') else '')
            def __call__(self,text,**kw): return {'input_ids':list(text.encode())}
        with self.assertRaisesRegex(ValueError,'Overlength'):
            encode_selected(Tok(),[self.row],3)

    def authentic_parent(self, letter=False):
        text='Authentic words.'
        self.raw.update(category='letter-source' if letter else 'primary', source=dict(author='Hegel',text=text,sha256=hashlib.sha256(text.encode()).hexdigest()))
        if letter:self.raw['source']['to']='Marie'
        (self.parent/'source-candidates.jsonl').write_text(json.dumps(self.raw)+'\n')
        self.row.update(id='authentic',parent_id='p0',category='authentic-writing',messages=[dict(role='user',content='Write the historical excerpt.'),dict(role='assistant',content=json.dumps(dict(title='Excerpt',kind='letter' if letter else 'essay',to='Marie' if letter else None,continues=False,text=text)))])
        self.save(self.row)
    def test_authentic_letter_preserves_source_and_recipient(self):
        self.authentic_parent(letter=True)
        self.assertEqual(read_selected(self.data)[0][0]['category'],'authentic-writing')
    def test_authentic_wrapper_rejects_rehashed_edited_prose(self):
        self.authentic_parent()
        v=json.loads(self.row['messages'][-1]['content']);v['text']='Invented prose.'
        self.row['messages'][-1]['content']=json.dumps(v);self.save(self.row)
        with self.assertRaisesRegex(ValueError,'Authentic writing prose'):read_selected(self.data)
    def test_authentic_letter_rejects_changed_recipient(self):
        self.authentic_parent(letter=True)
        v=json.loads(self.row['messages'][-1]['content']);v['to']='Schelling'
        self.row['messages'][-1]['content']=json.dumps(v);self.save(self.row)
        with self.assertRaisesRegex(ValueError,'Authentic writing prose'):read_selected(self.data)
    def test_authentic_answer_rejects_nonhegel_source(self):
        self.authentic_parent()
        self.raw['source']['author']='Not Hegel'
        (self.parent/'source-candidates.jsonl').write_text(json.dumps(self.raw)+'\n')
        self.row['category']='authentic-answer';self.row['messages'][-1]['content']='Authentic words.';self.save(self.row)
        with self.assertRaisesRegex(ValueError,'Invalid authentic source'):read_selected(self.data)
    def test_authentic_answer_accepts_only_exact_source(self):
        self.authentic_parent()
        self.row['category']='authentic-answer';self.row['messages'][-1]['content']='Authentic words.';self.save(self.row)
        self.assertEqual(read_selected(self.data)[0][0]['category'],'authentic-answer')
        self.row['messages'][-1]['content']='Edited';self.save(self.row)
        with self.assertRaisesRegex(ValueError,'Authentic answer prose changed'):read_selected(self.data)
