import gzip
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import zipfile
from pc.blind_review import archived_texts,build,fresh_tasks


class BlindReviewTest(unittest.TestCase):
    def test_decision_prose_preserved_without_exposing_action_schema(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);raw=json.dumps(dict(thought='A difficult case.',says='Let us wait.',action='rest'))
            key={'D01-A':dict(arm='test-arm',text_sha256=hashlib.sha256(raw.encode()).hexdigest())}
            (root/'key.json').write_text(json.dumps(key))
            with zipfile.ZipFile(root/'source.zip','w') as z:
                z.writestr('review-only/masked-writing.json','[]')
                z.writestr('review-only/masked-decisions.json',json.dumps([dict(candidates=[dict(id='D01-A',text=raw)])]))
            rows,_=archived_texts(root/'source.zip',root/'key.json')
            self.assertEqual([('D01-A','A difficult case.\n\n“Let us wait.”')],rows)
            key['D01-A']['text_sha256']='wrong';(root/'key.json').write_text(json.dumps(key))
            with self.assertRaisesRegex(ValueError,'fingerprint'):
                archived_texts(root/'source.zip',root/'key.json')

    def test_private_key_cannot_be_written_into_a_rater_packet_or_repository(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'rater'
            with self.assertRaisesRegex(ValueError,'outside'):
                build(None,None,None,None,None,out,out/'secret.json')

    def test_fresh_cases_are_sixteen_blank_human_slots(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'template.json'
            path.write_text(json.dumps(dict(cases=[dict(id='',kind='',task='',observations=[dict(text='')])],author='')))
            rows=fresh_tasks(path)['cases']
            self.assertEqual(8,sum(r['kind']=='essay' for r in rows))
            self.assertEqual(8,sum(r['kind']=='letter' for r in rows))
            self.assertTrue(all(not r['task'] and not r['observations'][0]['text'] for r in rows))
            self.assertEqual(16,len({r['id'] for r in rows}))
            rows[0]['observations'][0]['text']='human enters a situation'
            self.assertEqual('',rows[1]['observations'][0]['text'])

