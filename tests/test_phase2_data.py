"""No test fixture in this module is exported as training data."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools import phase2_data as p
from world.config import Config


class Phase2DataTest(unittest.TestCase):
    def test_generation_preserves_raw_target_and_requires_review(self):
        request = dict(id='test', category='argument', messages=[dict(role='user',content='test')],
                       max_tokens=10, seed=1, schema=None)
        answer = 'Unedited fixture answer.'
        response = dict(choices=[dict(finish_reason='stop',message=dict(content=answer))])
        def api(url, route, data=None, **kw):
            return {'/health': {'status':'ok'}, '/lora-adapters': [], '/v1/models': {'data':[]},
                    '/v1/chat/completions': response}[route]
        with tempfile.TemporaryDirectory() as td:
            out=Path(td);p.jsonl(out/'requests.jsonl',[request])
            class Args: pass
            a=Args();a.out=out;a.url='fixture://not-a-server'
            with patch.object(p,'api',api),patch.object(p,'verify_frozen'):
                p.generate(a)
            result=p.rows(out/'qwen-candidates.jsonl')[0]
            self.assertEqual(result['messages'][-1]['content'],answer)
            self.assertEqual(result['response'],response)
            self.assertEqual(result['target_sha256'],p.digest(answer))
            self.assertEqual(result['review'],'pending')
            self.assertFalse((out/'accepted.jsonl').exists())
            with patch.object(p,'api',api),patch.object(p,'verify_frozen'):
                p.generate(a)
            self.assertEqual(len(p.rows(out/'qwen-candidates.jsonl')),1)

    def test_nonempty_adapter_inventory_blocks_generation(self):
        with tempfile.TemporaryDirectory() as td:
            class Args: pass
            a=Args();a.out=Path(td);a.url='fixture://not-a-server'
            with patch.object(p,'verify_frozen'),patch.object(p,'api',side_effect=[{'status':'ok'},[{'scale':1}]]):
                with self.assertRaisesRegex(SystemExit,'unadapted Qwen'):
                    p.generate(a)

    def test_length_stop_is_not_treated_as_complete(self):
        response={'choices':[{'finish_reason':'length','message':{'content':'Cut off'}}]}
        self.assertIn('not completed: length',p.screen({'category':'argument'},response))

    def test_hash_gate_detects_changed_request(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)
            (out/'requests.jsonl').write_text('changed')
            p.dump(out/'frozen-hashes.json',{'requests.jsonl':p.digest('original')})
            with self.assertRaisesRegex(SystemExit,'Frozen input changed'):
                p.verify_frozen(out)

    def test_persona_override_is_local_and_default_is_preserved(self):
        cfg=Config({'HEGEL_REPO':'/tmp/example','HEGEL_SOUL_FILE':'mind/soul-v2.md'})
        self.assertEqual(cfg.soul_file,Path('/tmp/example/mind/soul-v2.md'))
        cfg=Config({'HEGEL_REPO':'/tmp/example','HEGEL_SOUL_FILE':'mind/soul.md'})
        self.assertEqual(cfg.soul_file,Path('/tmp/example/mind/soul.md'))


if __name__=='__main__':unittest.main()
