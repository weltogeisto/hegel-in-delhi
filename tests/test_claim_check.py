"""Protocol and scalar calibration tests; no server, GPU or ML packages."""
import math
import unittest
from unittest.mock import patch
from world.claim_check import (ClaimProtocolError, MissingVoteError, SupportVerifier, calibrated,
                              calibration_metrics, fit_temperature, parse_probability,
                              request_payload, sentence_spans)


class ClaimProbabilityTest(unittest.TestCase):
    def test_sentence_spans_preserve_initials_and_exact_text(self):
        text = "  I met Mr. R. K. Malhotra and Shri G. Hegde. Then I left.\nUnfinished thought"
        self.assertEqual(["I met Mr. R. K. Malhotra and Shri G. Hegde.",
                          "Then I left.", "Unfinished thought"],
                         [text[a:b] for a,b in sentence_spans(text)])

    def test_attributed_quotation_is_not_severed_from_its_speaker(self):
        text = 'Ramesh said: “The gate is mine. Leave the ink alone.” I waited.'
        self.assertEqual(['Ramesh said: “The gate is mine. Leave the ink alone.”', 'I waited.'],
                         [text[a:b] for a,b in sentence_spans(text)])

    def response(self, yes=.8, no=.2):
        return dict(content='1',completion_probabilities=[dict(top_logprobs=[
            dict(id=10,logprob=math.log(no)),dict(id=11,logprob=math.log(yes))])])

    def test_two_grammar_votes_have_their_own_conditional_probability(self):
        r=parse_probability(self.response(), {"0":10,"1":11})
        self.assertAlmostEqual(.8,r["probability"])
        self.assertAlmostEqual(math.log(4),r["log_odds"])

    def test_missing_vote_is_never_inferred_to_have_zero_probability(self):
        with self.assertRaises(MissingVoteError):
            parse_probability(dict(completion_probabilities=[dict(top_logprobs=[dict(id=10,logprob=0.)])]),{"0":10,"1":11})

    def test_votes_are_conditioned_without_discarding_other_vocabulary_mass(self):
        value=self.response(.7,.1)
        value['completion_probabilities'][0]['top_logprobs'].append(dict(id=12,logprob=math.log(.2)))
        result=parse_probability(value,{'0':10,'1':11})
        self.assertAlmostEqual(.875,result['probability'])
        self.assertAlmostEqual(math.log(7),result['log_odds'])
        self.assertAlmostEqual(.8,result['vote_mass'])

    def test_missing_probabilities_fail_instead_of_fabricating_a_score(self):
        for value in [{},dict(completion_probabilities=[]),dict(completion_probabilities=[dict(top_logprobs=[])]),
                      self.response(.8,.3),self.response(float("nan"),.2)]:
            with self.subTest(value=value), self.assertRaises(ClaimProtocolError):
                parse_probability(value,{"0":10,"1":11})

    def test_unexpected_token_or_duplicate_fails(self):
        for ids in [(10,12),(10,10)]:
            value=dict(completion_probabilities=[dict(top_logprobs=[dict(id=i,logprob=math.log(.5)) for i in ids])])
            with self.subTest(ids=ids), self.assertRaises(ClaimProtocolError):
                parse_probability(value,{"0":10,"1":11})

    def test_request_has_no_sampling_truncation_or_adapter(self):
        p=request_payload("prompt")
        self.assertEqual((64,1,False), (p["n_probs"],p["n_predict"],p["post_sampling_probs"]))
        self.assertEqual(["temperature"],p["samplers"])
        self.assertEqual(1.,p["temperature"]);self.assertEqual([],p["lora"])
        self.assertEqual('root ::= "0" | "1"',p["grammar"])
        self.assertEqual((0,1.,0.),(p["top_k"],p["top_p"],p["min_p"]))

    def test_verifier_checks_tokenization_and_uses_the_model_chat_template(self):
        replies=[dict(tokens=[10]),dict(tokens=[11]),dict(prompt="model chat prompt"),self.response()]
        with patch("world.claim_check.api",side_effect=replies) as post:
            r=SupportVerifier("http://localhost:8082").score("Ramesh spoke.","statement: Ramesh said hello")
        self.assertAlmostEqual(.8,r["probability"])
        self.assertEqual(["/tokenize","/tokenize","/apply-template","/completion"],[c.args[1] for c in post.call_args_list])
        self.assertFalse(post.call_args_list[2].args[2]["chat_template_kwargs"]["enable_thinking"])
        self.assertEqual("model chat prompt",r["request"]["prompt"])

    def test_top_n_expands_when_an_explicit_vote_is_missing(self):
        missing=dict(content='1',completion_probabilities=[dict(top_logprobs=[dict(id=11,logprob=-.01)])])
        replies=[dict(tokens=[10]),dict(tokens=[11]),dict(prompt='prompt'),missing,self.response()]
        with patch('world.claim_check.api',side_effect=replies) as post:
            result=SupportVerifier('http://localhost').score('Text.','records')
        self.assertAlmostEqual(.8,result['probability'])
        self.assertEqual([64,4096],[c.args[2]['n_probs'] for c in post.call_args_list if c.args[1]=='/completion'])
        self.assertEqual(5,len(result['exchanges']))

    def test_raw_exchange_is_audited_before_probability_validation_can_fail(self):
        bad=self.response(float('nan'),.2)
        replies=[dict(tokens=[10]),dict(tokens=[11]),dict(prompt='prompt'),bad]
        seen=[]
        with patch('world.claim_check.api',side_effect=replies), self.assertRaises(ClaimProtocolError):
            SupportVerifier('http://localhost',audit=seen.append).score('Text.','records')
        self.assertEqual(4,len(seen))
        self.assertIs(bad,seen[-1]['response'])

    def test_verifier_rejects_multitoken_vote_or_open_thinking(self):
        for replies in [[dict(tokens=[10,12])],
                        [dict(tokens=[10]),dict(tokens=[11]),dict(prompt="assistant<think>")]]:
            with patch("world.claim_check.api",side_effect=replies), self.assertRaises(ClaimProtocolError):
                SupportVerifier("http://localhost").score("Text.","records")

    def test_scalar_fit_reduces_overconfident_log_loss(self):
        z=[5.]*10+[-5.]*10; y=[1]*8+[0]*2+[0]*8+[1]*2
        t=fit_temperature(z,y)
        self.assertGreater(t,1)
        self.assertAlmostEqual(.8,calibrated(5,t),places=7)
        before=calibration_metrics(z,y);after=calibration_metrics(z,y,t)
        self.assertLess(after["log_loss"],before["log_loss"])
        self.assertAlmostEqual(0,after["ece"],places=7)

    def test_metrics_count_known_calibration_error(self):
        z=[math.log(4)]*10; y=[1]*6+[0]*4
        r=calibration_metrics(z,y)
        self.assertAlmostEqual(.2,r["ece"])
        self.assertAlmostEqual(.28,r["brier"])

    def test_calibration_rejects_missing_classes_or_bad_values(self):
        for z,y in [([],[]),([1],[True]),([float("inf"),0],[0,1]),([1],[1])]:
            with self.subTest(z=z,y=y), self.assertRaises(ValueError):fit_temperature(z,y)
        for t in [0,-1,float("nan")]:
            with self.subTest(t=t), self.assertRaises(ValueError):calibrated(1,t)


if __name__ == "__main__":
    unittest.main()
