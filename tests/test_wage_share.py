"""Why the wage share moves, and why it mostly does not (docs/99).

`docs/98` reported the wage share frozen and concluded the laboratory
redistributes nothing between wage and profit.  That was measured on four
scenarios in which the redistribution channel is switched off by default.
These tests pin what is actually true: the share at the value of
labor-power is an *identity* no quantity rule can move, and the share at
the wage as paid moves whenever bargaining is on.
"""

import unittest

from economy_lab import scenarios as S


def _accumulated(economy):
    names = list(economy.regions)
    return (
        sum(economy.ledger.living_labor.get(n, 0.0) for n in names),
        sum(economy.ledger.necessary_labor.get(n, 0.0) for n in names),
        sum(economy.ledger.wage_deviation_labor.get(n, 0.0) for n in names),
    )


def _window_shares(economy, windows=8, days=30):
    """Per-period shares.  The ledger is cumulative, so a level reading is
    a running average and looks constant however much the flow moves."""
    previous = _accumulated(economy)
    bare, realized = [], []
    for _ in range(windows):
        economy.step(days)
        current = _accumulated(economy)
        living, necessary, deviation = (
            c - p for c, p in zip(current, previous)
        )
        previous = current
        if living <= 0.0:
            continue
        bare.append(necessary / living)
        realized.append((necessary + deviation) / living)
    return bare, realized


def _relative_spread(values):
    mean = sum(values) / len(values)
    return (max(values) - min(values)) / mean if mean else 0.0


class WageShareIdentityTest(unittest.TestCase):
    def test_the_bare_wage_share_is_the_value_of_labor_power_over_the_day(self):
        """``necessary / living`` reduces to ``VLP / ticks_per_worker_day``.

        ``necessary_labor`` accrues ``worker_days x VLP`` and
        ``living_labor`` accrues the ticks performed, and ``worker_days``
        *is* those ticks over the length of the day.  The quantity of
        labor cancels, which is why no rule about how much gets produced
        can move this reading (docs/99 section 1).
        """
        economy = S.equilibrium(0)
        bare, _ = _window_shares(economy, windows=4)
        region = list(economy.regions.values())[0]
        predicted = economy.value_of_labor_power(region) / region.ticks_per_worker_day
        for share in bare:
            # The employment quantum floors worker_days onto a grid, so
            # the realised ratio sits a hair under the identity.
            self.assertAlmostEqual(share, predicted, places=6)

    def test_no_quantity_rule_moves_the_bare_share(self):
        """Purses, posted prices, procurement, entry and exit all on, and
        the share does not move: it cannot, by the identity above."""
        economy = S.gravitation(0, parameters=S.complete_market())
        bare, _ = _window_shares(economy, windows=8)
        self.assertLess(_relative_spread(bare), 1e-5)


class WageShareMovementTest(unittest.TestCase):
    def test_the_channel_is_off_by_default(self):
        """The defect in `docs/98`: the four audited scenarios never form a
        premium, because `wage_bargaining_strength` is zero unless a
        scenario sets it.  A default is not a scenario."""
        economy = S.demand_boom(0, bargaining=False)
        economy.step(120)
        for region in economy.regions.values():
            self.assertEqual(region.wage_premium, 0.0)

    def test_the_realized_share_moves_when_bargaining_is_on(self):
        """A6's fluctuation half, which `docs/98` reported as failing.

        The tighter labor market lifts the wage above the value of
        labor-power, and the share of the product going to labor moves
        with it -- which is the thing Wright's model produces and
        `docs/98` said ours did not.
        """
        economy = S.demand_boom(0, bargaining=True)
        bare, realized = _window_shares(economy, windows=12)
        self.assertGreater(_relative_spread(realized), 0.01)
        # And the bare share still does not move: the premium is booked
        # apart from the value of labor-power, deliberately (docs/46).
        self.assertLess(_relative_spread(bare), 1e-5)

    def test_habituation_is_what_moves_the_bare_share(self):
        """The identity names its own escape: move the value of
        labor-power.  Habituation does exactly that, and is the only rule
        in the laboratory that moves the bare share at all."""
        economy = S.demand_boom(0, bargaining=True, habituation=True)
        bare, _ = _window_shares(economy, windows=12)
        self.assertGreater(_relative_spread(bare), 0.01)

    def test_a_premium_is_a_deduction_from_surplus_not_a_creation(self):
        """The realized share rises only as far as the premium, and living
        labor is unchanged by it (docs/46)."""
        economy = S.demand_boom(0, bargaining=True)
        _, realized = _window_shares(economy, windows=12)
        premium = max(r.wage_premium for r in economy.regions.values())
        self.assertGreater(premium, 0.0)
        self.assertLessEqual(max(realized), min(realized) * (1.0 + premium) + 1e-9)


if __name__ == "__main__":
    unittest.main()
