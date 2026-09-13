"""The docking instrument (docs/97, docs/98).

These tests pin the instrument's invariants and the two findings the
reconstruction turned on.  They do not test our economy; the whole point
of `economy_lab.social_architecture` is that it cannot reach it.
"""

import unittest

from economy_lab.social_architecture import Economy, gini, hill, top_share


class SocialArchitectureTest(unittest.TestCase):
    def test_the_instrument_cannot_reach_the_laboratory(self):
        """It imports nothing from the model and nothing third-party, so
        no rule here can move a baseline metric (docs/97 section 6).

        Read from the import graph rather than by searching the text: the
        module's own docstring names ``economy_lab.model`` in prose, and a
        substring check calls that an import.
        """
        import ast
        import sys

        import economy_lab.social_architecture as sa

        with open(sa.__file__, encoding="utf-8") as handle:
            tree = ast.parse(handle.read())

        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                # `level` > 0 is a relative import, i.e. inside the package.
                imported.add(("." * node.level) + (node.module or ""))

        for name in imported:
            self.assertNotIn("model", name, f"{name} reaches the laboratory")

        allowed = set(sys.stdlib_module_names)
        for name in imported:
            root = name.lstrip(".").split(".")[0]
            if not root:
                continue
            self.assertIn(root, allowed, f"{name} is not in the standard library")

    def test_money_is_conserved_exactly(self):
        """Coins are integers and every rule is a transfer, so this is
        exact rather than within a tolerance (docs/98 prediction 8)."""
        for seed in range(4):
            economy = Economy(actors=120, coins=60_000, seed=seed)
            start = economy.total_coins()
            economy.run(40)
            self.assertEqual(economy.total_coins(), start)

    def test_a_run_is_reproducible_under_its_seed(self):
        first = Economy(actors=120, coins=60_000, seed=3)
        second = Economy(actors=120, coins=60_000, seed=3)
        first.run(25)
        second.run(25)
        self.assertEqual(first.money, second.money)
        self.assertEqual(first.employer, second.employer)
        self.assertEqual(first.market, second.market)

    def test_a_different_seed_is_a_different_draw(self):
        """The model is stochastic; a single run is a draw, not a result."""
        first = Economy(actors=120, coins=60_000, seed=3)
        second = Economy(actors=120, coins=60_000, seed=4)
        first.run(25)
        second.run(25)
        self.assertNotEqual(first.money, second.money)

    def test_the_staff_index_agrees_with_a_scan(self):
        economy = Economy(actors=150, coins=75_000, seed=1)
        for _ in range(30):
            economy.month()
            self.assertTrue(economy.check_staff_index())

    def test_classes_emerge_from_a_symmetric_start(self):
        """Every actor starts unemployed and equally rich; three classes
        appear, and employers stay a minority (docs/98 prediction 7)."""
        economy = Economy(actors=500, coins=250_000, seed=2)
        self.assertEqual(economy.classes(), (0, 0, 500))
        economy.run(60)
        employers, employees, unemployed = economy.classes()
        self.assertGreater(employers, 0)
        self.assertGreater(employees, 0)
        self.assertGreater(unemployed, 0)
        self.assertLess(employers / economy.actors, 0.20)

    def test_hiring_needs_the_average_wage_not_the_maximum(self):
        """The first reconstruction deadlocked: at a symmetric start every
        actor holds exactly the mean, so a threshold at ``wage_max``
        clears nobody and no firm is ever born (docs/98 section 3)."""
        economy = Economy(actors=200, coins=20_000, wage_max=100, seed=1)
        self.assertEqual(economy.money[0], economy.wage_max)
        economy.run(30)
        self.assertGreater(economy.classes()[0], 0)

    def test_firing_on_funds_monopolises_and_on_revenue_does_not(self):
        """The finding the reconstruction turned on (docs/98 section 3).

        Tested against an owner's accumulated purse, a rich owner buffers
        its wage bill indefinitely and one firm absorbs the economy.
        Tested against the trailing month's revenue -- the corroborated
        wording -- the firm-size distribution is stationary and a reserve
        army persists.
        """
        common = dict(actors=400, coins=200_000, seed=5)
        funds = Economy(firing_test="funds", **common)
        revenue = Economy(firing_test="revenue", **common)
        funds.run(400)
        revenue.run(400)

        self.assertGreater(max(funds.firm_sizes()) / funds.actors, 0.5)
        self.assertLess(funds.unemployment_rate(), 0.02)

        self.assertLess(max(revenue.firm_sizes()) / revenue.actors, 0.5)
        self.assertGreater(revenue.unemployment_rate(), 0.10)

    def test_the_reserve_army_is_endogenous_and_persistent(self):
        """Wright's central result, and the one A5 says our lab has no
        counterpart for: unemployment is an outcome that neither vanishes
        nor swallows the economy."""
        economy = Economy(actors=400, coins=200_000, seed=6)
        readings = []
        for _ in range(8):
            economy.run(25)
            readings.append(economy.unemployment_rate())
        for rate in readings:
            self.assertGreater(rate, 0.05)
            self.assertLess(rate, 0.70)
        self.assertGreater(max(readings) - min(readings), 0.0)

    def test_an_unknown_rule_variant_is_refused(self):
        with self.assertRaises(ValueError):
            Economy(actors=50, coins=10_000, candidate_pool="nonsense").run(1)
        with self.assertRaises(ValueError):
            Economy(actors=50, coins=10_000, firing_test="nonsense").run(1)


class StatisticsTest(unittest.TestCase):
    def test_gini_is_zero_when_everyone_is_equal(self):
        self.assertAlmostEqual(gini([5.0] * 50), 0.0, places=12)

    def test_gini_approaches_one_when_one_holds_everything(self):
        values = [0.0] * 999 + [1000.0]
        self.assertGreater(gini(values), 0.99)

    def test_gini_of_nothing_is_zero_rather_than_an_error(self):
        self.assertEqual(gini([]), 0.0)
        self.assertEqual(gini([0.0, 0.0]), 0.0)

    def test_top_share_of_an_equal_population_is_the_fraction(self):
        self.assertAlmostEqual(top_share([1.0] * 100, 0.1), 0.1, places=12)

    def test_hill_is_none_when_the_tail_is_too_small_to_estimate(self):
        self.assertIsNone(hill([1.0, 2.0, 3.0]))

    def test_hill_recovers_a_known_pareto_index(self):
        """A Pareto sample with index 1 should read near 1."""
        import random

        rng = random.Random(11)
        sample = [(1.0 - rng.random()) ** -1.0 for _ in range(20_000)]
        estimate = hill(sample, tail=0.05)
        self.assertIsNotNone(estimate)
        self.assertGreater(estimate, 0.85)
        self.assertLess(estimate, 1.15)


if __name__ == "__main__":
    unittest.main()
