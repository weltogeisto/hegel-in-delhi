import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools import lora_fresh_verdict as w8


def encoded(value):
    return json.dumps(value,sort_keys=True).encode()


def fixture():
    files = {}
    keys = {}
    manifest = {"readers":{}}
    for rater, prefix in (("sol","S"),("claude","C"),("welt","H")):
        ballots, packet, key = [], [], {}
        for i in range(72):
            confirm = i//12 in (0,4)
            if rater=="welt" and not confirm:
                continue
            item = prefix+str(i+1)
            text = {v:f"case {i} {v}." for v in ("source",*w8.VERSIONS)}
            mapping = {"A":"plain1","B":"adapter","C":"plain2"} if rater=="sol" else {"A":"adapter","B":"plain2","C":"plain1"}
            if rater=="welt":
                mapping = {"X":"plain1","Y":"adapter","Z":"source"}
                row = dict(id=item, most="Y", least="Z")
            else:
                row = dict(id=item, adapter_guess="none", **{l:{"mark":"P"} for l in mapping})
            entry = {l:text[v] for l,v in mapping.items()}
            if rater!="welt":
                entry["source"] = text["source"]
            packet.append(dict(id=item, **entry))
            ballots.append(row)
            key[item] = dict(case=f"case{i}", day=44+i//12, set="confirmation" if confirm else "development",
                             group="occasion" if i%2 else "ordinary", **mapping)
        keys[rater] = key
        pb = encoded(packet)
        bb = b"\n".join(encoded(b) for b in ballots)+b"\n"
        files[f"packet-{rater}.json"] = pb
        files[f"ballot-{rater}.jsonl"] = bb
        files[f"ballot-{rater}.sha256"] = (w8.sha(bb)+"\n").encode()
        manifest["readers"][rater] = dict(items=len(packet),packet_sha256=w8.sha(pb),key_sha256=w8.sha(encoded(key)))
    return manifest,files,keys


class W8Tests(unittest.TestCase):
    def setUp(self):
        self.manifest,self.files,self.keys = fixture()

    def aligned(self):
        ballots, packets, _, waiting = w8.sealed_ballots(set(self.files), self.files.__getitem__, self.manifest)
        self.assertEqual(waiting,[])
        return w8.align(ballots,packets,self.keys.__getitem__)

    def test_complete_and_independent_shuffles(self):
        cases = self.aligned()
        self.assertEqual(len(cases),72)
        result = w8.verdict(cases)
        self.assertEqual(result["status"],"PASS")
        self.assertEqual(result["sets"]["confirmation"]["counts"]["occasion_most_adapter"],12)
        self.assertEqual(len(result["sets"]["development"]["cases"]),48)
        self.assertEqual(len(result["bars"]),5)

    def test_either_substantive_joint_once(self):
        cases = self.aligned()
        case = cases["case0"]
        case["sol"]["marks"]["adapter"] = {"mark":"C","weight":"substantive"}
        case["claude"]["marks"]["adapter"] = {"mark":"E","weight":"minor"}
        r = w8.verdict(cases)
        self.assertEqual(r["status"],"FAIL")
        self.assertEqual(r["bars"]["no_joint_substantive"]["observed"],1)
        self.assertEqual(r["bars"]["joint_minor_within_plain_band"]["observed"],0)
        case["claude"]["marks"]["adapter"] = {"mark":"R"}
        self.assertEqual(w8.verdict(cases)["status"],"PASS")

    def test_development_cannot_change_confirmation_verdict(self):
        cases = self.aligned()
        for r in ("sol","claude"):
            cases["case12"][r]["marks"]["adapter"]={"mark":"E","weight":"substantive"}
        result = w8.verdict(cases)
        self.assertEqual(result["status"],"PASS")
        self.assertEqual(result["sets"]["development"]["counts"]["adapter_substantive"],1)

    def test_exact_preference_edges_none_and_noise(self):
        from collections import Counter
        c = Counter(adapter_minor=3,plain1_minor=2,plain2_minor=1,occasion=12,ordinary=12,
                    occasion_most_adapter=8,occasion_most_plain1=4,ordinary_least_adapter=3)
        self.assertTrue(all(x["passed"] for x in w8.bars(c).values()))
        c.update(adapter_minor=1,ordinary_least_adapter=1,occasion_most_plain1=4)
        bars = w8.bars(c)
        for key in ("joint_minor_within_plain_band","ordinary_adapter_least","occasion_plain_most_lower"):
            self.assertFalse(bars[key]["passed"])
        c["occasion_most_adapter"]=7
        self.assertFalse(w8.bars(c)["occasion_adapter_most"]["passed"])
        self.assertIsNone(w8.bars(Counter())["ordinary_adapter_least"]["passed"])

    def test_no_key_access_while_unsealed(self):
        del self.files["ballot-sol.sha256"]
        with patch.object(w8,"git_inputs",return_value=("test",self.manifest,set(self.files),self.files.__getitem__)):
            with patch.object(Path,"read_bytes",side_effect=AssertionError("opened a key")):
                self.assertEqual(w8.evaluate("test",Path("/unused"))["missing"],["sol"])

    def test_all_seals_and_key_hashes(self):
        with tempfile.TemporaryDirectory() as p, patch.object(w8,"git_inputs",return_value=("test",self.manifest,set(self.files),self.files.__getitem__)):
            root=Path(p)
            for r,k in self.keys.items():
                (root/f"key-{r}.json").write_bytes(encoded(k))
            self.assertEqual(w8.evaluate("test",root)["status"],"PASS")
            (root/"key-welt.json").write_bytes(b"{}")
            with self.assertRaisesRegex(ValueError,"key hash"):
                w8.evaluate("test",root)
        self.files["ballot-sol.jsonl"]+=b" "
        with self.assertRaisesRegex(ValueError,"seal mismatch"):
            w8.sealed_ballots(set(self.files),self.files.__getitem__,self.manifest)

    def test_conflicting_cross_reader_values(self):
        self.keys["sol"]["S1"].update(A="adapter",B="plain1")
        with self.assertRaisesRegex(ValueError,"different text"):
            self.aligned()

    def test_duplicate_rows_or_keys(self):
        with self.assertRaisesRegex(ValueError,"duplicated item"):
            w8.indexed([{"id":"S1"},{"id":"S1"}])
        with self.assertRaisesRegex(ValueError,"duplicate JSON"):
            w8.parse('{"id":"S1","id":"S2"}')
