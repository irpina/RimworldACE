"""Worker mobility between regions (docs/106, docs/107).

`Region.labor_pool` was a parameter that never moved, which made the
reserve army exogenous -- the thing `docs/97` A5 says Wright's is not.
The rule moves labour toward the higher wage at the start of each day,
before `_bargain` reads the employment rate it is the denominator of.
"""

import unittest

from dataclasses import replace

from economy_lab import scenarios as S
from economy_lab.model import Economy


STRENGTH = 0.05


def _boom(strength, *, days_after=1140):
    """The demand boom with bargaining on, stepped past the shock."""
    parameters = S._bargaining(
        replace(S.ScenarioParameters(), worker_mobility_strength=strength)
    )
    economy = S.seeded_two_region_economy(
        route_capacity_per_day=parameters.standard_route_capacity_per_day,
        freight_per_unit=parameters.standard_freight_per_unit,
        travel_days=parameters.standard_travel_days,
        parameters=parameters,
    )
    economy.step(60)
    region = economy.regions["Dust Basin"]
    region.base_daily_demand[S.YAYO] *= parameters.boom_demand_multiplier
    economy.step(days_after)
    return economy


def _pools(economy):
    return {name: r.labor_pool for name, r in sorted(economy.regions.items())}


def _wages(economy):
    return {name: r.wage_rate() for name, r in sorted(economy.regions.items())}


class TheRuleIsGatedTest(unittest.TestCase):
    def test_it_is_off_by_default(self):
        self.assertEqual(S.ScenarioParameters().worker_mobility_strength, 0.0)
        self.assertEqual(S.equilibrium(0).worker_mobility_strength, 0.0)

    def test_a_negative_strength_is_refused(self):
        with self.assertRaises(ValueError):
            Economy(
                commodities=[],
                regions=[],
                routes=[],
                worker_mobility_strength=-0.1,
            )

    def test_the_parameter_reaches_the_economy(self):
        parameters = replace(
            S.ScenarioParameters(), worker_mobility_strength=STRENGTH
        )
        self.assertEqual(
            S.equilibrium(0, parameters=parameters).worker_mobility_strength,
            STRENGTH,
        )

    def test_zero_strength_moves_nothing(self):
        economy = S.equilibrium(60)
        self.assertEqual(economy.ledger.labor_migrated, {})
        self.assertEqual(_pools(economy), {"Dust Basin": 1.0, "Green River": 1.0})


class TheSeededEquilibriumIsStationaryTest(unittest.TestCase):
    """Prediction 2: equal wages mean every pull is exactly zero."""

    def setUp(self):
        self.off = S.equilibrium(600)
        self.on = S.equilibrium(
            600,
            parameters=replace(
                S.ScenarioParameters(), worker_mobility_strength=STRENGTH
            ),
        )

    def test_nothing_migrates(self):
        self.assertEqual(self.on.ledger.labor_migrated, {})

    def test_the_pools_are_untouched(self):
        self.assertEqual(_pools(self.on), _pools(self.off))

    def test_the_prices_are_bit_identical(self):
        for name, region in self.off.regions.items():
            self.assertEqual(region.prices, self.on.regions[name].prices)

    def test_the_wages_are_bit_identical(self):
        self.assertEqual(_wages(self.on), _wages(self.off))


class TheRuleMovesRatherThanMakesTest(unittest.TestCase):
    """Predictions 3 and 4: the invariants."""

    def test_labour_is_conserved_across_the_run(self):
        economy = _boom(STRENGTH)
        total = sum(r.labor_pool for r in economy.regions.values())
        self.assertAlmostEqual(total, 2.0, delta=1e-12)

    def test_the_migration_ledger_sums_to_zero(self):
        economy = _boom(STRENGTH)
        self.assertAlmostEqual(
            sum(economy.ledger.labor_migrated.values()), 0.0, delta=1e-12
        )

    def test_no_employment_rate_exceeds_one(self):
        parameters = S._bargaining(
            replace(S.ScenarioParameters(), worker_mobility_strength=STRENGTH)
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
        for _ in range(300):
            economy.step(1)
            for region in economy.regions.values():
                self.assertLessEqual(region.employment_rate(), 1.0)

    def test_a_pool_never_falls_below_the_labour_employed_out_of_it(self):
        economy = _boom(STRENGTH, days_after=300)
        for region in economy.regions.values():
            self.assertGreaterEqual(
                region.labor_pool, region.worker_days_earned
            )


class TheRuleFollowsTheWageTest(unittest.TestCase):
    """Predictions 5, 6 and 7: the economics."""

    @classmethod
    def setUpClass(cls):
        cls.on = _boom(STRENGTH)
        cls.off = _boom(0.0)

    def test_labour_flows_toward_the_boom(self):
        pools = _pools(self.on)
        self.assertGreater(pools["Dust Basin"], pools["Green River"])
        self.assertGreater(pools["Dust Basin"], 1.0)

    def test_the_wage_gap_closes(self):
        on, off = _wages(self.on), _wages(self.off)
        gap_on = abs(on["Dust Basin"] - on["Green River"])
        gap_off = abs(off["Dust Basin"] - off["Green River"])
        self.assertLess(gap_on, gap_off)

    def test_mobility_damps_the_premium(self):
        self.assertLess(
            self.on.regions["Dust Basin"].wage_premium,
            self.off.regions["Dust Basin"].wage_premium,
        )


class TheWageShareIdentityHoldsTest(unittest.TestCase):
    """Prediction 8: migration is a quantity change (docs/99)."""

    def test_the_bare_share_is_the_value_of_labor_power_over_ticks(self):
        economy = _boom(STRENGTH)
        for name, region in sorted(economy.regions.items()):
            share = economy.ledger.necessary_labor.get(
                name, 0.0
            ) / economy.ledger.living_labor.get(name, 0.0)
            identity = economy.value_of_labor_power(region) / (
                region.ticks_per_worker_day
            )
            self.assertAlmostEqual(share, identity, places=6)


if __name__ == "__main__":
    unittest.main()
