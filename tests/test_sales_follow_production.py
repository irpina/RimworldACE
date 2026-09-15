"""Revenue conditional on having produced (docs/104, docs/105).

`docs/103` found F1's floor necessary and not sufficient: the drained
producer idled on a fifth of all days but never twice running, because
idling repaired the purse.  This rule removes the one channel that paid
it -- `_supply_shares`' capacity fallback -- and the oscillation breaks.
"""

import unittest

from dataclasses import replace

from economy_lab import scenarios as S


def _cash_circuit(quantum=0.0, follow=False, days=1200):
    parameters = replace(
        S.ScenarioParameters(),
        capital_goods=True,
        producer_cash=True,
        producer_employment_quantum=quantum,
        sales_follow_production=follow,
    )
    return S.equilibrium(days, parameters=parameters)


class TheRuleIsGatedTest(unittest.TestCase):
    def test_it_is_off_by_default(self):
        self.assertFalse(S.ScenarioParameters().sales_follow_production)
        self.assertFalse(S.equilibrium(0).sales_follow_production)

    def test_it_is_inert_where_nobody_is_ever_idle(self):
        """Every commodity has a producer that ran, every day, so the
        fallback is never reached and the run is bit-identical."""
        for build in (
            lambda p: S.equilibrium(240, parameters=p),
            lambda p: S.gravitation(720, parameters=p),
        ):
            off = build(S.ScenarioParameters())
            on = build(replace(S.ScenarioParameters(), sales_follow_production=True))
            region = "Dust Basin"
            self.assertEqual(off.cash_balance(), on.cash_balance())
            self.assertEqual(off.regions[region].prices, on.regions[region].prices)


class TheTwoRulesAreJointlyEffectiveTest(unittest.TestCase):
    def test_the_floor_alone_does_not_kill(self):
        """`docs/103`'s result, kept as a guard: the quantum on its own
        leaves the producer oscillating and alive."""
        economy = _cash_circuit(quantum=1e-3, follow=False)
        self.assertEqual(len(economy.ledger.bankruptcies), 0)

    def test_the_flag_alone_does_not_kill(self):
        """Without the floor nobody is ever idle after the opening day,
        so removing the fallback changes almost nothing."""
        economy = _cash_circuit(quantum=0.0, follow=True)
        self.assertEqual(len(economy.ledger.bankruptcies), 0)

    def test_the_flag_alone_still_perturbs_the_opening_day(self):
        """`docs/105` prediction 3, which failed: day 1 has no yesterday,
        so every commodity falls back there.  Under the rule the fund is
        paid for the seeded inventory instead of the producers -- a real
        difference, and the better reading, but not the inertness that
        was predicted.
        """
        off = _cash_circuit(quantum=0.0, follow=False)
        on = _cash_circuit(quantum=0.0, follow=True)
        self.assertNotEqual(
            sum(off.ledger.liquidity_curtailment.values()),
            sum(on.ledger.liquidity_curtailment.values()),
        )
        # But it is a perturbation, not a different economy.
        self.assertEqual(
            off.regions["Dust Basin"].prices, on.regions["Dust Basin"].prices
        )

    def test_together_they_reach_the_death(self):
        """The point of the whole arc: an endogenous firm death, caused by
        an unpayable wage bill, in a model that had never had one."""
        economy = _cash_circuit(quantum=1e-3, follow=True)
        bankruptcies = economy.ledger.bankruptcies
        self.assertGreaterEqual(len(bankruptcies), 1)
        for _day, _region, name in bankruptcies:
            producer = next(
                p
                for r in economy.regions.values()
                for p in r.producers
                if p.name == name
            )
            self.assertEqual(producer.commodity, "components")
            self.assertFalse(producer.active)


class TheConsequencesTest(unittest.TestCase):
    def test_money_is_conserved_through_the_death(self):
        economy = _cash_circuit(quantum=1e-3, follow=True)
        self.assertLess(abs(economy.cash_balance()), 1e-6)

    def test_the_death_cascades_through_department_one(self):
        """`docs/105` prediction 8, which failed the other way: the
        producer was marginal in *employment* and structural in
        *function*.  Losing the capital-goods sector starves plant
        replacement across the circuit."""
        economy = _cash_circuit(quantum=1e-3, follow=True)
        lost = economy.ledger.capacity_lost
        self.assertGreater(lost.get("components", 0.0), 0.0)
        collateral = sum(
            v for k, v in lost.items() if k != "components" and v > 0.0
        )
        self.assertGreater(collateral, 0.0)
        self.assertLess(economy.regions["Dust Basin"].employment_rate(), 0.20)

    def test_the_wage_share_identity_survives(self):
        """`docs/99` again: a quantity rule cannot move the bare share,
        and a bankruptcy plus a cascade is a quantity change."""
        economy = _cash_circuit(quantum=1e-3, follow=True)
        names = list(economy.regions)
        living = sum(economy.ledger.living_labor.get(n, 0.0) for n in names)
        necessary = sum(economy.ledger.necessary_labor.get(n, 0.0) for n in names)
        region = economy.regions["Dust Basin"]
        identity = (
            economy.value_of_labor_power(region) / region.ticks_per_worker_day
        )
        self.assertAlmostEqual(necessary / living, identity, places=6)


if __name__ == "__main__":
    unittest.main()
