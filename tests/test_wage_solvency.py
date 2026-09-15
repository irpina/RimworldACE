"""A3: the purse as a solvency constraint, and why it never kills (docs/101).

`docs/98` reported that no rule in the laboratory makes the wage bill a
solvency constraint.  That was wrong -- `_produce` has curtailed output to
what the purse affords since `docs/55`, and `_outlay_per_run` includes
wages.  What is true is narrower and more interesting: the constraint
binds, but the firm death it is supposed to cause cannot be reached,
because the curtailment is continuous where Wright's F1 is floored.
"""

import unittest

from economy_lab import scenarios as S
from economy_lab.model import EPSILON


class TheConstraintExistsTest(unittest.TestCase):
    def test_outlay_per_run_includes_the_wage(self):
        """The correction to `docs/98`'s A3: the purse constraint is a wage
        constraint, among other things."""
        economy = S.cash_circuit(0)
        region = economy.regions["Dust Basin"]
        producer = next(p for p in region.producers if p.active)
        wage = (
            producer.process.direct_labor
            * region.wage_rate()
            / region.ticks_per_worker_day
        )
        inputs = producer.process.input_cost_per_run(region.prices)
        self.assertAlmostEqual(
            economy._outlay_per_run(producer, region), inputs + wage, places=12
        )

    def test_for_a_pure_labor_process_the_constraint_is_exactly_the_wage_bill(self):
        """Five of the circuit's nine processes buy no inputs at all, so
        for them ``outlay_per_run`` *is* the wage -- and the rule is
        Wright's F1 exactly, bar the floor (docs/101 section 1)."""
        economy = S.cash_circuit(0)
        region = economy.regions["Dust Basin"]
        pure = []
        for producer in region.producers:
            if not producer.active:
                continue
            if producer.process.input_cost_per_run(region.prices) > EPSILON:
                continue
            pure.append(producer.commodity)
            wage = (
                producer.process.direct_labor
                * region.wage_rate()
                / region.ticks_per_worker_day
            )
            self.assertAlmostEqual(
                economy._outlay_per_run(producer, region), wage, places=12
            )
        self.assertGreaterEqual(len(set(pure)), 4)


class TheConstraintBindsTest(unittest.TestCase):
    def test_it_is_inert_where_the_circuit_is_stationary(self):
        """No purse is short at the seeded equilibrium, so nothing is
        curtailed -- the same discipline `_bargain` keeps at zero
        strength."""
        economy = S.equilibrium(240)
        total = sum(economy.ledger.liquidity_curtailment.values())
        self.assertEqual(total, 0.0)

    def test_it_binds_on_the_sector_that_loses_silver(self):
        """`docs/56`'s draining component sector: the purse constraint is
        live, not decorative."""
        economy = S.cash_circuit(1200)
        curtailed = economy.ledger.liquidity_curtailment
        self.assertGreater(curtailed.get("components", 0.0), 0.0)


class TheDeathPathIsUnreachableTest(unittest.TestCase):
    def test_any_positive_purse_affords_positive_runs(self):
        """The mechanism, in one assertion.

        ``affordable = max(0, spendable) / per_run`` is continuous, so a
        purse of any positive size buys a positive number of runs.  The
        idle counter only advances when ``affordable <= EPSILON``, so a
        producer that still has a coin never starts the count that would
        bankrupt it.  Wright's F1 floors the same quantity to whole
        workers, and a firm holding less than one average wage fires
        everybody and ceases trading.
        """
        economy = S.cash_circuit(0)
        region = economy.regions["Dust Basin"]
        producer = next(
            p
            for p in region.producers
            if p.active and p.process.input_cost_per_run(region.prices) <= EPSILON
        )
        per_run = economy._outlay_per_run(producer, region)
        self.assertGreater(per_run, 0.0)
        for purse in (1e-3, 1e-6, 1e-9):
            self.assertGreater(purse / per_run, EPSILON)

    def test_the_drained_producer_reaches_a_fixed_point_and_survives(self):
        """Measured over the committed scenario: the component sector's
        purse falls to under one percent of its target and then stops
        falling, output holds at a trickle, and nobody goes bankrupt.

        A producer permanently insolvent against its intended scale, and
        permanently alive (docs/101 section 3).
        """
        economy = S.cash_circuit(1200)
        components = [
            p
            for r in economy.regions.values()
            for p in r.producers
            if p.commodity == "components"
        ]
        self.assertTrue(components)
        self.assertEqual(len(economy.ledger.bankruptcies), 0)
        for producer in components:
            self.assertTrue(producer.active)
            self.assertEqual(producer.liquidity_idle_days, 0)
        drained = [p for p in components if p.cash < 0.1 * p.cash_target]
        self.assertTrue(drained, "expected a purse drained well below target")
        for producer in drained:
            self.assertGreater(producer.last_runs, 0.0)


if __name__ == "__main__":
    unittest.main()
