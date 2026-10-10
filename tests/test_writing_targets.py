import gzip
import json
import tempfile
import unittest
from pathlib import Path

from tools import writing_targets as wt


class SourceIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.path = self.root/'mind/shelf/wallace-logic.txt.gz'
        self.path.parent.mkdir(parents=True)
        self.text = '# A heading\n\nAn exact first paragraph.\n\n§ 12. A complete second paragraph.\n'
        with gzip.open(self.path, 'wt', encoding='utf-8') as f:
            f.write(self.text)
        self.source = dict(list(wt.paragraphs(self.text))[1], work='wallace-logic',
                           source_file='mind/shelf/wallace-logic.txt.gz',
                           source_file_sha256=wt.file_hash(self.path))

    def test_paragraphs_are_exact_not_sentence_fragments(self):
        parts = list(wt.paragraphs(self.text))
        self.assertEqual(len(parts), 2)
        self.assertEqual(parts[0]['ref'], 'A heading')
        self.assertEqual(parts[1]['ref'], '§12')
        for part in parts:
            self.assertEqual(self.text[part['start']:part['end']], part['text'])
        wt.verify_source(self.root, self.source)

    def test_changed_target_rejected_even_with_new_hash(self):
        self.source['text'] = 'A rewritten imitation.'
        self.source['sha256'] = wt.digest(self.source['text'])
        with self.assertRaisesRegex(ValueError, 'span'):
            wt.verify_source(self.root, self.source)

    def test_matching_substring_is_not_a_whole_paragraph(self):
        self.source['start'] += 7
        self.source['text'] = self.text[self.source['start']:self.source['end']]
        self.source['sha256'] = wt.digest(self.source['text'])
        with self.assertRaisesRegex(ValueError, 'complete original paragraph'):
            wt.verify_source(self.root, self.source)

    def test_changed_source_rejected(self):
        with gzip.open(self.path, 'wt') as f:
            f.write(self.text + 'Additional words.')
        with self.assertRaisesRegex(ValueError, 'file changed'):
            wt.verify_source(self.root, self.source)

    def test_reserved_work_rejected(self):
        self.source['work'] = 'haldane-2'
        with self.assertRaisesRegex(ValueError, 'Unapproved'):
            wt.verify_source(self.root, self.source)

    def test_unrelated_source_path_rejected(self):
        self.source['source_file'] = 'mind/train/corpus.jsonl'
        with self.assertRaisesRegex(ValueError, 'path'):
            wt.verify_source(self.root, self.source)


class CandidateFilterTests(unittest.TestCase):
    def row(self):
        return dict(work='wallace-logic', text=' '.join('word'+str(i) for i in range(200))+'.')

    def test_benchmark_eight_word_overlap_rejected(self):
        row=self.row()
        self.assertEqual(wt.source_filter(row, wt.shingles(row['text'],8), set(),None),'benchmark overlap')

    def test_prior_target_overlap_rejected(self):
        row=self.row()
        self.assertEqual(wt.source_filter(row,set(),wt.shingles(row['text']),None),'prior small-pilot overlap')

    def test_length_cap_rejects_instead_of_truncating(self):
        row=dict(work='wallace-logic',text=('substantialword '*200)+'.')
        before=row['text']
        self.assertIn('length',wt.source_filter(row,set(),set(),None))
        self.assertEqual(row['text'],before)

    def test_quoted_other_author_is_not_a_hegel_target(self):
        row=self.row()
        row['text']='Hegel cites another writer: “'+row['text']+'”'
        self.assertIn('quoted speech',wt.source_filter(row,set(),set(),None))


class BriefTests(unittest.TestCase):
    def response(self, **changes):
        brief=dict(title='A question of method',
                   task='Consider whether a method can be justified before it has been put to work. What difficulty does this demand create for a science seeking to establish its own beginning?',
                   suitable=True,review_note='Needs an individual alignment review.')
        brief.update(changes)
        return {'choices':[{'finish_reason':'stop','message':{'content':json.dumps(brief)}}]}

    def test_question_is_never_the_target(self):
        source={'text':'A separate authentic historical paragraph.'}
        original=dict(source)
        brief,flags=wt.screen_brief(source,self.response())
        self.assertEqual(flags,[])
        self.assertEqual(source,original)
        self.assertNotIn('accepted',brief)

    def test_copied_source_words_are_flagged(self):
        task='Consider whether a method can be justified before it has been put to work and examine the reasons for thinking that this question admits more than one answer.'
        _,flags=wt.screen_brief({'text':task+' Extra words.'},self.response(task=task))
        self.assertTrue(any('copies eight' in x for x in flags))

    def test_explanations_of_supplied_answer_are_flagged(self):
        _,flags=wt.screen_brief({'text':'Historical paragraph.'},self.response(task='Explain the supplied passage in ordinary language and discuss whether the argument it contains offers a convincing account of how a science should begin.'))
        self.assertTrue(any('depends on supplied' in x for x in flags))

    def test_unsuitable_or_invalid_outputs_remain_rejected(self):
        _,flags=wt.screen_brief({'text':'Historical paragraph.'},self.response(suitable=False))
        self.assertIn('generator marks source unsuitable',flags)
        _,flags=wt.screen_brief({'text':'Historical paragraph.'},{'choices':[{'finish_reason':'length','message':{'content':'{"title":'}}]})
        self.assertEqual(flags,['generation did not finish normally','invalid JSON'])

    def test_extra_answer_field_rejected(self):
        _,flags=wt.screen_brief({'text':'Historical paragraph.'},self.response(answer='Invented target prose.'))
        self.assertIn('wrong fields',flags)


if __name__=='__main__':
    unittest.main()
