"""The committed solver fixtures are what the laboratory computes today (docs/53).

If this fails the model moved and the fixtures did not: regenerate them with
``python -m economy_lab.fixtures`` and re-run the C# harness, in that order.
"""

import json
import unittest

from economy_lab import fixtures


class PortFixtureTests(unittest.TestCase):
    def test_the_committed_fixtures_are_current(self):
        for name, document in fixtures.build_all().items():
            with self.subTest(fixture=name):
                path = fixtures.DEFAULT_DIR / f"{name}.json"
                self.assertTrue(path.exists(), f"{path} is missing; run python -m economy_lab.fixtures")
                committed = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(committed, document)

    def test_cold_and_warm_starts_agree_where_the_solve_decides(self):
        """docs/53 s5.4: the fixed point is the fixed point from either side.

        A stale commodity -- one nobody produced -- keeps whatever value it
        started with, by design (docs/19 section 4), so it keeps 0.0 from a
        cold start and its old value from a warm one.  The claim is about
        the values the solve determines.
        """
        for name, document in fixtures.build_all().items():
            warm, cold = document["cases"]
            stale = set(warm["expected"]["stale"])
            with self.subTest(fixture=name):
                self.assertEqual(stale, set(cold["expected"]["stale"]))
                self.assertEqual(
                    [pair for pair in warm["expected"]["labor_values"] if pair[0] not in stale],
                    [pair for pair in cold["expected"]["labor_values"] if pair[0] not in stale],
                )
                self.assertEqual(
                    warm["expected"]["regional_labor_values"],
                    cold["expected"]["regional_labor_values"],
                )


if __name__ == "__main__":
    unittest.main()
