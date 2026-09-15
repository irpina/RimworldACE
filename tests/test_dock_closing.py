"""The two corrections that closed the Wright audit (docs/108).

`docs/98` recorded A2 as a dead branch and asked for A6 to be
re-measured once the reserve army could move.  Both were done; both
answers differ from what the question assumed, and both are pinned here
so neither can revert without a test saying so.
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


def _support(economy):
    return sum(economy.ledger.fund_wage_support.values())


class TheFundBearsSomeWageRiskTest(unittest.TestCase):
    """A2 is live, not latent -- but only jointly (docs/108 section 1)."""

    def test_it_is_dust_in_the_configuration_docs_98_measured(self):
        self.assertLess(_support(_cash_circuit()), 1e-9)

    def test_neither_rule_alone_reaches_the_branch(self):
        self.assertLess(_support(_cash_circuit(quantum=1e-3)), 1e-9)
        self.assertLess(_support(_cash_circuit(follow=True)), 1e-9)

    def test_the_two_rules_together_reach_it(self):
        economy = _cash_circuit(quantum=1e-3, follow=True)
        self.assertGreater(_support(economy), 1e-6)

    def test_the_support_does_not_prevent_the_death(self):
        economy = _cash_circuit(quantum=1e-3, follow=True)
        self.assertEqual(len(economy.ledger.bankruptcies), 2)
        wages = sum(economy.ledger.wages_paid.values())
        # Four parts in a hundred million: real, and nowhere near enough
        # to keep the machinists alive.
        self.assertLess(_support(economy) / wages, 1e-6)


def _realized_share_windows(mobility, windows=20, days=30):
    """The realized wage share over successive windows of `demand_boom`."""
    parameters = S._bargaining(
        replace(S.ScenarioParameters(), worker_mobility_strength=mobility)
    )
    economy = S.seeded_two_region_economy(
        route_capacity_per_day=parameters.standard_route_capacity_per_day,
        freight_per_unit=parameters.standard_freight_per_unit,
        travel_days=parameters.standard_travel_days,
        parameters=parameters,
    )
    economy.step(60)
    economy.regions["Dust Basin"].base_daily_demand[S.YAYO] *= (
        parameters.boom_demand_multiplier
    )
    ledger = economy.ledger

    def snapshot():
        return (
            sum(ledger.necessary_labor.values()),
            sum(ledger.living_labor.values()),
            sum(ledger.wage_deviation_labor.values()),
        )

    previous = snapshot()
    shares = []
    for _ in range(windows):
        economy.step(days)
        current = snapshot()
        necessary, living, deviation = (
            current[i] - previous[i] for i in range(3)
        )
        previous = current
        shares.append((necessary + deviation) / living)
    return shares


class MobilityDampsTheWageShareTest(unittest.TestCase):
    """A6 re-measured: the share moves, and moves *less* (docs/108 s2)."""

    @classmethod
    def setUpClass(cls):
        cls.off = _realized_share_windows(0.0)
        cls.on = _realized_share_windows(0.05)

    @staticmethod
    def _relative_spread(shares):
        return (max(shares) - min(shares)) / (sum(shares) / len(shares))

    def test_the_share_still_moves_by_more_than_one_percent(self):
        # docs/97 prediction 5's threshold, with the reserve army moving.
        self.assertGreater(self._relative_spread(self.on), 0.01)

    def test_an_endogenous_reserve_army_calms_rather_than_agitates(self):
        self.assertLess(
            self._relative_spread(self.on), self._relative_spread(self.off)
        )

    def test_mobility_lowers_the_ceiling_and_leaves_the_floor(self):
        # The floor is the docs/99 identity, read before the boom bites;
        # a damping rule cannot move it.
        self.assertAlmostEqual(min(self.on), min(self.off), places=9)
        self.assertLess(max(self.on), max(self.off))


if __name__ == "__main__":
    unittest.main()
