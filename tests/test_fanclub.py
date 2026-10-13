"""The fan club: one list of parts in three places, and only a publishable key in the public page."""
import base64
import json
import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


class FanClubTest(unittest.TestCase):
    def setUp(self):
        self.visitors = json.loads((REPO / "world/data/visitors.json").read_text(encoding="utf-8"))
        self.page = (REPO / "docs/index.html").read_text(encoding="utf-8")
        self.sql = (REPO / "supabase/fanclub.sql").read_text(encoding="utf-8")

    def ids(self):
        return [r["id"] for g in self.visitors["groups"] for r in g["roles"]]

    def test_every_part_is_complete_and_unique(self):
        places = {"home", "lodhi", "khan", "iic", "gym", "safdarjung", "gandhi", "estates"}
        seen = set()
        for g in self.visitors["groups"]:
            for r in g["roles"]:
                self.assertRegex(r["id"], r"^[a-z]+$")
                self.assertNotIn(r["id"], seen)
                seen.add(r["id"])
                self.assertTrue(r["label"] and r["who"] and r["at"], r["id"])
                self.assertLessEqual(len(r["label"]), 70, r["id"])
                self.assertTrue(set(r["at"]) <= places, r["id"])

    def test_the_page_offers_exactly_the_parts_of_the_data_file(self):
        block = re.search(r'<script type="application/json" id="fanRoles">(.*?)</script>', self.page, re.S)
        page = json.loads(block.group(1))
        self.assertEqual([r["id"] for g in page for r in g["roles"]], self.ids())
        labels = {r["id"]: r["label"] for g in self.visitors["groups"] for r in g["roles"]}
        self.assertEqual({r["id"]: r["label"] for g in page for r in g["roles"]}, labels)

    def test_the_database_accepts_exactly_the_parts_of_the_data_file(self):
        array = re.search(r"roles constant text\[\] := array\[(.*?)\];", self.sql, re.S)
        self.assertEqual(re.findall(r"'([a-z]+)'", array.group(1)), self.ids())

    def test_the_page_holds_no_secret_key(self):
        self.assertNotIn("sb_secret_", self.page)
        for token in re.findall(r"eyJ[\w-]+\.(eyJ[\w-]+)\.[\w-]+", self.page):
            claims = json.loads(base64.urlsafe_b64decode(token + "=" * (-len(token) % 4)))
            self.assertNotEqual(claims.get("role"), "service_role")
        self.assertRegex(self.page, r"key: 'sb_publishable_[\w-]+'")


if __name__ == "__main__":
    unittest.main()
