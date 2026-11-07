"""Training 3's split rule (tools/decision_split.py): prompts that carry T39's held days never train."""
import json
import subprocess
import unittest

from tools import decision_split as split

# Twelve words of Day 12's record, as a later "You remember" line quotes them.
HELD = "a study in friction i walked fourteen kilometres a physical exhaustion that"


def have_frozen_shadow():
    return subprocess.run(["git", "-C", str(split.REPO), "cat-file", "-e", split.FROZEN_SHADOW + "^{commit}"],
                          capture_output=True).returncode == 0


class SplitRuleTest(unittest.TestCase):
    def test_twelve_shared_words_make_a_prompt_held_related(self):
        keys = {split.key(r) for r in split.runs("one two three four five six seven eight nine ten eleven twelve thirteen")}
        self.assertTrue(split.held_related("You remember: one two three four five six seven eight nine ten eleven twelve.", keys))
        self.assertFalse(split.held_related("You remember: one two three four five six seven eight nine ten eleven.", keys))
        self.assertTrue(split.held_related("ONE two, three: four five six seven eight nine ten eleven twelve", keys))

    def test_the_frozen_runs_hold_the_held_days_text(self):
        self.assertEqual(len(split.frozen_keys()), 8946)
        self.assertTrue(split.held_related("- Day 12 (Tue 13 Oct), 21:14, you thought: “… " + HELD + " …”"))
        self.assertFalse(split.held_related("Nothing in particular happens. The morning goes on. Ramesh brings the tea."))

    def test_the_frozen_shadow_exclusions_lie_within_the_approved_roster(self):
        ids = split.frozen_shadow_exclusions()
        roster = json.loads((split.REPO / "pc/training3-shadow-ids.json").read_text())
        self.assertEqual((len(ids), len(roster) - len(ids)), (38, 71))
        self.assertEqual(list(ids), [i for i in roster if i in set(ids)])

    @unittest.skipUnless(have_frozen_shadow(), "needs the frozen shadow commit in this checkout")
    def test_the_frozen_file_matches_the_shadow_history(self):
        data = split.from_history(split.REPO)
        self.assertEqual((json.dumps(data, indent=1, sort_keys=True) + "\n").encode(), split.RUNS_FILE.read_bytes())


if __name__ == "__main__":
    unittest.main()
