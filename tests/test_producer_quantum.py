"""The producer employment quantum (docs/102, docs/103).

The rule builds F1's floor: affordable labour is rounded down onto whole
units of employment, so a purse that cannot afford one unit affords none.
It does what it was specified to do, and it does **not** produce the firm
death it was built for -- because idling for a day repairs the purse, so a
marginal producer oscillates instead of dying.
"""

import unittest

from dataclasses import replace

from economy_lab import scenarios as S
from economy_lab.model import EPSILON


def _cash_circuit(quantum, days=1200):
    parameters = replace(
        S.ScenarioParameters(),
        capital_goods=True,
        producer_cash=True,
        producer_employment_quantum=quantum,
    )
    return S.equilibrium(days, parameters=parameters)


class TheRuleIsGatedTest(unittest.TestCase):
    def test_it_is_off_by_default(self):
        self.assertEqual(S.ScenarioParameters().producer_employment_quantum, 0.0)
        self.assertEqual(S.equilibrium(0).producer_employment_quantum, 0.0)

    def test_a_negative_quantum_is_refused(self):
        with self.assertRaises(ValueError):
            S.equilibrium(
                0,
                parameters=replace(
                    S.ScenarioParameters(), producer_employment_quantum=-1.0
                ),
            )

    def test_it_is_inert_where_the_purse_does_not_bind(self):
        """`equilibrium` never curtails anybody, so the floor is never
        applied to a binding quantity and the run is bit-identical
        (docs/103 prediction 2)."""
        off = S.equilibrium(240)
        on = S.equilibrium(
            240,
            parameters=replace(
                S.ScenarioParameters(), producer_employment_quantum=1e-3
            ),
        )
        region = "Dust Basin"
        self.assertEqual(off.cash_balance(), on.cash_balance())
        self.assertEqual(off.regions[region].prices, on.regions[region].prices)
        self.assertEqual(
            off.regions[region].worker_days_earned,
            on.regions[region].worker_days_earned,
        )


class TheFloorArithmeticTest(unittest.TestCase):
    def test_it_floors_onto_whole_units_of_employment(self):
        economy = _cash_circuit(1e-3, days=0)
        region = economy.regions["Dust Basin"]
        producer = next(
            p for p in region.producers if p.active and p.process.direct_labor > 0
        )
        labor = producer.process.direct_labor
        ticks = region.ticks_per_worker_day
        # Two and a half quanta of employment floors to two.
        runs = 2.5e-3 * ticks / labor
        got = economy._quantize_employment(producer, region, runs)
        self.assertAlmostEqual(got * labor / ticks, 2e-3, places=12)

    def test_less_than_one_unit_affords_none(self):
        """F1's cliff, in one assertion."""
        economy = _cash_circuit(1e-3, days=0)
        region = economy.regions["Dust Basin"]
        producer = next(
            p for p in region.producers if p.active and p.process.direct_labor > 0
        )
        labor = producer.process.direct_labor
        runs = 0.9e-3 * region.ticks_per_worker_day / labor
        self.assertEqual(economy._quantize_employment(producer, region, runs), 0.0)

    def test_a_process_with_no_direct_labor_is_untouched(self):
        """A rule about employment must not destroy a producer that
        employs nobody."""
        economy = _cash_circuit(1e-3, days=0)
        region = economy.regions["Dust Basin"]
        producer = next(p for p in region.producers if p.active)
        original = producer.process.direct_labor
        try:
            object.__setattr__(producer.process, "direct_labor", 0.0)
        except Exception:
            producer.process.direct_labor = 0.0
        try:
            self.assertEqual(
                economy._quantize_employment(producer, region, 7.0), 7.0
            )
        finally:
            try:
                object.__setattr__(producer.process, "direct_labor", original)
            except Exception:
                producer.process.direct_labor = original


class TheFloorDoesNotKillTest(unittest.TestCase):
    """docs/103's central result: prediction 3 failed."""

    def test_the_floor_bites_without_killing(self):
        """At a quantum that idles the drained producer on a fifth of all
        days, nobody goes bankrupt: idling is never consecutive enough to
        reach `bankruptcy_idle_days`."""
        quantised = _cash_circuit(1e-3)
        plain = _cash_circuit(0.0)
        # The floor is doing something: more output is curtailed.
        self.assertGreater(
            sum(quantised.ledger.liquidity_curtailment.values()),
            sum(plain.ledger.liquidity_curtailment.values()),
        )
        # And yet nobody dies.
        self.assertEqual(len(quantised.ledger.bankruptcies), 0)
        for region in quantised.regions.values():
            for producer in region.producers:
                self.assertLess(producer.liquidity_idle_days, 30)

    def test_a_quantum_large_enough_to_kill_kills_everything(self):
        """There is no window. The transition is from no effect to
        collapse, because a quantum above a producer's whole employment
        idles it permanently -- and that is true of nearly every producer
        at once (docs/103 section 3)."""
        collapsed = _cash_circuit(1e-2)
        self.assertGreater(len(collapsed.ledger.bankruptcies), 50)
        self.assertLess(
            collapsed.regions["Dust Basin"].employment_rate(), 0.01
        )

    def test_money_survives_the_collapse(self):
        """`_retire` returns the purse to the fund, a hundred times over."""
        collapsed = _cash_circuit(1e-2)
        self.assertLess(abs(collapsed.cash_balance()), 1e-6)

    def test_the_wage_share_identity_survives_the_collapse(self):
        """`docs/99`: the bare share is `value_of_labor_power` over the
        length of the day, and no quantity rule can move it -- not even a
        hundred bankruptcies and employment falling to zero."""
        collapsed = _cash_circuit(1e-2)
        names = list(collapsed.regions)
        living = sum(collapsed.ledger.living_labor.get(n, 0.0) for n in names)
        necessary = sum(
            collapsed.ledger.necessary_labor.get(n, 0.0) for n in names
        )
        region = collapsed.regions["Dust Basin"]
        identity = (
            collapsed.value_of_labor_power(region) / region.ticks_per_worker_day
        )
        self.assertAlmostEqual(necessary / living, identity, places=6)


if __name__ == "__main__":
    unittest.main()
