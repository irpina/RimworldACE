"""The committed port fixtures are what the laboratory computes today.

The value solve's (docs/53) and the wage relation's (docs/72).  If either
fails the model moved and the fixtures did not: regenerate them with
``python -m economy_lab.fixtures`` and ``python -m economy_lab.wage_fixtures``
and re-run the C# harness, in that order.
"""

import json
import unittest

from economy_lab import fixtures, wage_fixtures


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


class WageFixtureTests(unittest.TestCase):
    def test_the_committed_wage_fixtures_are_current(self):
        for name, document in wage_fixtures.build_all().items():
            with self.subTest(fixture=name):
                path = wage_fixtures.DEFAULT_DIR / f"{name}.json"
                self.assertTrue(
                    path.exists(),
                    f"{path} is missing; run python -m economy_lab.wage_fixtures",
                )
                committed = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(committed, document)

    def test_the_neutral_case_takes_both_skipped_multiplies(self):
        """docs/72 s5.4: the skips are a property, not a hope.

        Where there is no premium the wage *is* the basket, and where the
        standard has not moved the value of labor-power *is* the basket at
        values -- to the bit, because the laboratory branches around the
        multiply rather than doing it by one.  A port that folded the
        branch away would still pass within tolerance and fail here the
        first time the neutral value changed.
        """
        document = wage_fixtures.build_all()["equilibrium_day60"]
        for reading in document["readings"]:
            with self.subTest(region=reading["region"]):
                self.assertEqual(reading["wage_rate"], reading["basket_cost"])
                self.assertEqual(
                    reading["value_of_labor_power"], reading["basket_labor_value"]
                )
                self.assertEqual(reading["premium_over_value"], 0.0)

    def test_every_branch_of_the_wage_is_taken_by_some_fixture(self):
        """docs/72 s4: each fixture is there because it takes a branch.

        If a branch stops being reachable the fixture set is no longer
        covering the port, and the right response is to say so rather than
        to invent an economy that reaches it.
        """
        built = wage_fixtures.build_all()
        premium = [
            reading
            for reading in built["wage_deviation_day180"]["readings"]
            if reading["wage_rate"] != reading["basket_cost"]
        ]
        self.assertTrue(premium, "no region carries a wage premium")
        standard = [
            reading
            for reading in built["habituation_day240"]["readings"]
            if reading["value_of_labor_power"] != reading["basket_labor_value"]
        ]
        self.assertTrue(standard, "no region carries a habitual standard")
        # The second arm of the deviation branch, which is the wage *below*
        # value: a premium that habituation has already absorbed.  The
        # totals are absolute, so the day's posting is the difference.
        posted = [
            settlement["after"]["wage_deviation_labor"]
            - settlement["before"]["wage_deviation_labor"]
            for settlement in built["habituation_day240"]["settlements"]
        ]
        self.assertTrue(any(value < 0.0 for value in posted))

    def test_the_settlement_totals_are_absolute_and_not_differences(self):
        """docs/72 s2 and the fixture's own comment.

        `Ledger.add` accumulates onto a running total, so what a day posts
        depends on what was already there: the same wage bill lands on a
        different last bit against a larger base.  A fixture of differences
        would let a port agree with the fixture while disagreeing with the
        model, so the fixture carries both ends — and at least one reading
        must actually show the effect, or the risk is theoretical and the
        shape is unjustified.
        """
        loose = 0
        for document in wage_fixtures.build_all().values():
            for settlement in document["settlements"]:
                before, after = settlement["before"], settlement["after"]
                self.assertEqual(sorted(before), sorted(after))
                posted = after["wages_paid"] - before["wages_paid"]
                moved = before["cash"] - after["cash"]
                if posted != moved:
                    loose += 1
        self.assertGreater(
            loose, 0, "no fixture shows the accumulated-base effect"
        )

    def test_the_wage_fixture_generator_does_not_move_the_laboratory(self):
        """docs/72 s6: the generator reads; it must not settle anything.

        `_settle_labor` pays a wage bill and posts to the ledger, so the
        fixture calls it on a deep copy.  The economy it was handed must be
        where it was afterwards.
        """
        economy = wage_fixtures.equilibrium(days=60)
        region = economy.regions["Dust Basin"]
        before = (
            region.cash,
            region.worker_cash,
            region.worker_days_earned,
            dict(economy.ledger.wages_paid),
            dict(economy.ledger.necessary_labor),
        )
        wage_fixtures.settlement(economy, "Dust Basin")
        self.assertEqual(
            (
                region.cash,
                region.worker_cash,
                region.worker_days_earned,
                dict(economy.ledger.wages_paid),
                dict(economy.ledger.necessary_labor),
            ),
            before,
        )


if __name__ == "__main__":
    unittest.main()
