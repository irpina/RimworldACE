"""The continuous size exponent of ``docs/118``."""

import unittest

from economy_lab import social_architecture as sa


def run(rule, seed, months=90, **kwargs):
    economy = sa.Economy(seed=seed, market_rule=rule, **kwargs)
    economy.run(months)
    return economy


def state(economy):
    """Everything that would differ if a trajectory diverged by one ulp."""
    return (economy.money, economy.employer, economy.market,
            sorted(economy.firm_sizes()), economy.steps)


class TestEndpointsAreBitIdentical(unittest.TestCase):
    """Prediction 1. If this fails the instrument is not the described one."""

    def test_exponent_one_reproduces_wright_exactly(self):
        for seed in (0, 1, 2):
            self.assertEqual(state(run("scaled", seed, size_exponent=1.0)),
                             state(run("wright", seed)))

    def test_exponent_zero_reproduces_neutral_exactly(self):
        for seed in (0, 1, 2):
            self.assertEqual(state(run("scaled", seed, size_exponent=0.0)),
                             state(run("neutral", seed)))

    def test_the_default_exponent_is_one(self):
        self.assertEqual(sa.Economy().size_exponent, 1.0)

    def test_the_divisive_form_is_what_makes_the_endpoints_exact(self):
        # The multiplicative form rounds 1/members before multiplying.
        # Measured over 200,000 draws it disagrees with x / members on
        # 46,338 of them; this pins the reason the model divides.
        mismatches = 0
        rng = sa.random.Random(0)
        for _ in range(20000):
            members = rng.randrange(1, 400)
            draw = rng.uniform(0.0, 1e5)
            if draw * members ** -1.0 != draw / members:
                mismatches += 1
            self.assertEqual(draw / members ** (1.0 - 0.0), draw / members)
            self.assertEqual(draw / members ** (1.0 - 1.0), draw)
        self.assertGreater(mismatches, 1000)


class TestValidation(unittest.TestCase):
    def test_a_negative_exponent_is_refused(self):
        with self.assertRaises(ValueError):
            sa.Economy(market_rule="scaled", size_exponent=-0.5)

    def test_an_exponent_on_another_rule_is_refused_rather_than_ignored(self):
        with self.assertRaises(ValueError):
            sa.Economy(market_rule="wright", size_exponent=0.5)

    def test_the_default_exponent_is_allowed_on_every_rule(self):
        for rule in sa.MARKET_RULES:
            sa.Economy(market_rule=rule, size_exponent=1.0)


class TestBehaviour(unittest.TestCase):
    def test_money_is_conserved_across_the_sweep_range(self):
        for beta in (0.0, 0.5, 1.0, 1.2, 1.5):
            economy = run("scaled", 3, months=60, size_exponent=beta)
            self.assertAlmostEqual(economy.total_coins(), 100000.0, places=5)

    def test_the_market_pool_never_goes_negative(self):
        for beta in (0.0, 0.7, 1.5):
            self.assertGreaterEqual(
                run("scaled", 4, months=60, size_exponent=beta).market, 0.0)

    def test_a_higher_exponent_concentrates_more(self):
        low = run("scaled", 5, size_exponent=0.5)
        high = run("scaled", 5, size_exponent=1.5)
        self.assertGreater(max(high.firm_sizes()), max(low.firm_sizes()))

    def test_intermediate_exponents_are_their_own_economies(self):
        outcomes = {max(run("scaled", 6, size_exponent=b).firm_sizes())
                    for b in (0.0, 0.25, 0.5, 0.75, 1.0)}
        self.assertGreater(len(outcomes), 3)


if __name__ == "__main__":
    unittest.main()
