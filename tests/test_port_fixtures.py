"""The committed port fixtures are what the laboratory computes today.

The value solve's (docs/53) and the wage relation's (docs/72).  If either
fails the model moved and the fixtures did not: regenerate them with
``python -m economy_lab.fixtures`` and ``python -m economy_lab.wage_fixtures``
and re-run the C# harness, in that order.
"""

import json
import unittest

from economy_lab import (
    bargaining_fixtures,
    fixtures,
    price_fixtures,
    wage_cost_fixtures,
    wage_fixtures,
)


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


class BargainingFixtureTests(unittest.TestCase):
    def test_the_committed_bargaining_fixtures_are_current(self):
        for name, document in bargaining_fixtures.build_all().items():
            with self.subTest(fixture=name):
                path = bargaining_fixtures.DEFAULT_DIR / f"{name}.json"
                self.assertTrue(
                    path.exists(),
                    f"{path} is missing; run python -m economy_lab.bargaining_fixtures",
                )
                committed = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(committed, document)

    def test_the_rules_are_exactly_stationary_where_the_circuit_is(self):
        """docs/74 s6.2, which is docs/46 s2's claim asserted on sixty days.

        At the seed the employment rate equals the reference to the bit, so
        the target premium is exactly zero and the premium never leaves it.
        A rule that drifted one ulp a day would show sixty here and pass
        any tolerance anyone would write, which is why the fixture is a
        sequence and this assertion is equality.
        """
        document = bargaining_fixtures.build_all()["equilibrium_stationary"]
        self.assertNotEqual(document["problem"]["wage_bargaining_strength"], 0.0)
        for sequence in document["sequences"]:
            with self.subTest(region=sequence["region"]):
                for index, step in enumerate(sequence["steps"]):
                    self.assertEqual(step["wage_premium"], 0.0, f"step {index}")
                    self.assertEqual(step["habitual_scale"], 1.0, f"step {index}")

    def test_the_standard_ratchets_and_never_falls(self):
        """docs/74 s6.4: habituation is upward-only, and some fixture must
        actually turn it.

        The first three fixtures did not: a sequence freezes employment, so
        the premium converges monotonically, and the reversal's premium
        sits below a standard the boom already raised -- leaving the gap
        negative for all sixty steps and the taken branch uncovered.
        `boom_habituating` is in the set because of that (docs/75 s3).
        """
        built = bargaining_fixtures.build_all()
        for name, document in built.items():
            for sequence in document["sequences"]:
                scales = [step["habitual_scale"] for step in sequence["steps"]]
                with self.subTest(fixture=name, region=sequence["region"]):
                    for earlier, later in zip(scales, scales[1:]):
                        self.assertGreaterEqual(later, earlier)
        rises = [
            later > earlier
            for sequence in built["boom_habituating"]["sequences"]
            for earlier, later in zip(
                [step["habitual_scale"] for step in sequence["steps"]],
                [step["habitual_scale"] for step in sequence["steps"]][1:],
            )
        ]
        self.assertTrue(any(rises), "no fixture turns the ratchet")

    def test_the_bargaining_generator_does_not_move_the_laboratory(self):
        """docs/74: both rules mutate, so the sequences run on a copy."""
        economy = bargaining_fixtures.demand_boom(120, bargaining=True)
        region = economy.regions["Dust Basin"]
        before = (region.wage_premium, region.habitual_scale)
        bargaining_fixtures.sequence(economy, "Dust Basin")
        self.assertEqual((region.wage_premium, region.habitual_scale), before)


class PriceFixtureTests(unittest.TestCase):
    def test_the_committed_price_fixtures_are_current(self):
        for name, document in price_fixtures.build_all().items():
            with self.subTest(fixture=name):
                path = price_fixtures.DEFAULT_DIR / f"{name}.json"
                self.assertTrue(
                    path.exists(),
                    f"{path} is missing; run python -m economy_lab.price_fixtures",
                )
                committed = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(committed, document)

    def test_the_stationary_circuit_does_not_move_its_prices(self):
        """docs/77 s6.1: at the seed the pressure is exactly zero.

        Which makes `exp` exactly 1.0 in any libm, the desired price
        exactly the anchor, and the anchor exactly the reference -- so the
        damped step moves nothing.  This is the one `exp` result the port
        can rely on whatever else disagrees, and the four-year equilibrium
        price range resting at exactly zero depends on it.
        """
        document = price_fixtures.build_all()["equilibrium_day60"]
        before = {
            region["name"]: dict(region["prices"])
            for region in document["problem"]["regions"]
        }
        for expected in document["expected"]:
            with self.subTest(region=expected["region"]):
                for name, price in expected["prices"]:
                    self.assertEqual(price, before[expected["region"]][name])

    def test_some_fixture_drives_the_pressure_both_ways(self):
        """docs/77 s5: the fixture set has to exercise `exp` off zero.

        One fixture with a stock above target, so the gap is negative and
        `exp` runs below one, and one with unmet demand, so the second
        term is positive.  Without both the slice's only transcendental is
        never called with an interesting argument.
        """
        built = price_fixtures.build_all()
        moved = []
        for name, document in built.items():
            before = {
                region["name"]: dict(region["prices"])
                for region in document["problem"]["regions"]
            }
            for expected in document["expected"]:
                for good, price in expected["prices"]:
                    old = before[expected["region"]][good]
                    if price > old:
                        moved.append((name, "up"))
                    elif price < old:
                        moved.append((name, "down"))
        self.assertIn("up", [direction for _, direction in moved])
        self.assertIn("down", [direction for _, direction in moved])

    def test_the_price_generator_does_not_move_the_laboratory(self):
        """docs/77: `_update_prices` mutates, so the fixture copies first."""
        economy = price_fixtures.equilibrium(days=60)
        before = {
            name: dict(region.prices) for name, region in economy.regions.items()
        }
        price_fixtures.expected(economy)
        self.assertEqual(
            {name: dict(region.prices) for name, region in economy.regions.items()},
            before,
        )


class WageCostFixtureTests(unittest.TestCase):
    def test_the_committed_wage_cost_fixtures_are_current(self):
        for name, document in wage_cost_fixtures.build_all().items():
            with self.subTest(fixture=name):
                path = wage_cost_fixtures.DEFAULT_DIR / f"{name}.json"
                self.assertTrue(
                    path.exists(),
                    f"{path} is missing; run python -m economy_lab.wage_cost_fixtures",
                )
                committed = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(committed, document)

    def test_no_scenario_has_a_joint_process_and_that_is_the_finding(self):
        """docs/79 s3a: mass apportionment is unreachable in this laboratory.

        `share_of_cost` (docs/08) splits a process's joint cost across its
        outputs by mass, and both the value solve and the wage-cost
        refresh call it.  **Every process in every scenario has exactly
        one output**, so it returns 1.0 every time and has never been
        exercised by anything -- not by the 2,988 value-solve readings
        either.

        This test pins that, rather than pretending a fixture covers it.
        When a joint process is finally added, this fails, and the right
        response is to write the fixture the branch then needs.
        """
        for name, document in wage_cost_fixtures.build_all().items():
            for region in document["problem"]["regions"]:
                for producer in region["producers"]:
                    with self.subTest(fixture=name, producer=producer["name"]):
                        self.assertEqual(
                            len(producer["process"]["outputs"]),
                            1,
                            "a joint process exists now; docs/79 s3a is stale "
                            "and the apportionment needs a fixture",
                        )

    def test_the_wage_cost_generator_does_not_move_the_laboratory(self):
        """docs/79: the refresh writes to every active producer."""
        economy = wage_cost_fixtures.equilibrium(days=60)
        region = economy.regions["Dust Basin"]
        before = [p.wage_cost_per_unit for p in region.producers]
        wage_cost_fixtures.expected(economy, "Dust Basin")
        self.assertEqual([p.wage_cost_per_unit for p in region.producers], before)


if __name__ == "__main__":
    unittest.main()
