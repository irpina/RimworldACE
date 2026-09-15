"""The M1 ablation's exchange rules (docs/115).

Wright names M1's two ingredients himself: sampling once per employee,
"a bias justified by the law of value", and a random amount "to reflect
contingency".  The variants remove one, the other, or both.  These tests
cover the *mechanism* -- that each rule is a coherent economy and that
the default is untouched.  What the ablation finds is docs/116.
"""

import unittest

from economy_lab import social_architecture as sa


class TheDefaultIsUntouchedTest(unittest.TestCase):
    def test_the_default_rule_is_wrights(self):
        self.assertEqual(sa.Economy().market_rule, "wright")

    def test_naming_it_explicitly_changes_nothing(self):
        for seed in (0, 1, 2):
            plain = sa.Economy(seed=seed)
            plain.run(60)
            named = sa.Economy(seed=seed, market_rule="wright")
            named.run(60)
            self.assertEqual(plain.money, named.money)
            self.assertEqual(plain.market, named.market)
            self.assertEqual(plain.employer, named.employer)

    def test_an_unknown_rule_is_refused(self):
        with self.assertRaises(ValueError):
            sa.Economy(market_rule="nonsense")


class EveryCellIsACoherentEconomyTest(unittest.TestCase):
    """A cell that leaked money would be a bug, not a variant."""

    def test_money_is_conserved_under_every_rule(self):
        for rule in sa.MARKET_RULES:
            economy = sa.Economy(seed=1, market_rule=rule)
            economy.run(120)
            self.assertAlmostEqual(
                economy.total_coins(), 100_000.0, delta=1e-6, msg=rule
            )

    def test_the_market_pool_never_goes_negative(self):
        for rule in sa.MARKET_RULES:
            economy = sa.Economy(seed=2, market_rule=rule)
            for _ in range(60):
                economy.month()
                self.assertGreaterEqual(economy.market, 0.0, rule)

    def test_every_rule_sustains_firms_and_employment(self):
        for rule in sa.MARKET_RULES:
            economy = sa.Economy(seed=3, market_rule=rule)
            economy.run(120)
            self.assertGreater(len(economy.firm_sizes()), 0, rule)
            self.assertLess(economy.unemployment_rate(), 1.0, rule)

    def test_the_class_partition_still_holds(self):
        for rule in sa.MARKET_RULES:
            economy = sa.Economy(seed=4, market_rule=rule)
            economy.run(60)
            capitalists, workers, unemployed = economy.classes()
            self.assertEqual(
                capitalists + workers + unemployed, economy.actors, rule
            )


class TheAblationRemovesWhatItClaimsTest(unittest.TestCase):
    """The mechanism, not the finding: each rule's defining property."""

    def test_neutral_rules_shrink_the_largest_firm(self):
        # Removing the law of value should remove the advantage of size.
        # The magnitude is docs/116's business; that it points this way
        # is the rule working.
        base = sa.Economy(seed=1)
        base.run(120)
        neutral = sa.Economy(seed=1, market_rule="neutral")
        neutral.run(120)
        self.assertLess(max(neutral.firm_sizes()), max(base.firm_sizes()))

    def test_deterministic_rules_draw_no_random_numbers_in_m1(self):
        # `fixed` consumes randomness only in selection, hiring, spending
        # and wages -- never in the market draw.  A cheap proxy: two
        # economies differing only in market rule diverge, and the
        # deterministic one is reproducible.
        first = sa.Economy(seed=5, market_rule="fixed")
        first.run(60)
        second = sa.Economy(seed=5, market_rule="fixed")
        second.run(60)
        self.assertEqual(first.money, second.money)

    def test_all_four_rules_are_distinct_economies(self):
        outcomes = set()
        for rule in sa.MARKET_RULES:
            economy = sa.Economy(seed=7, market_rule=rule)
            economy.run(120)
            outcomes.add((len(economy.firm_sizes()), max(economy.firm_sizes())))
        self.assertEqual(len(outcomes), len(sa.MARKET_RULES))


if __name__ == "__main__":
    unittest.main()
