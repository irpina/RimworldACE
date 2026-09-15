"""The docking instrument (docs/97, docs/98, docs/100).

`economy_lab.social_architecture` is now a *transcription* of Wright's SR
model, not a reconstruction.  These tests check it against the paper's
formal rules -- especially F1, whose misreading was `docs/98`'s central
error -- and pin the instrument's invariants.  They do not test our own
economy; the point of the module is that it cannot reach it.
"""

import unittest

from economy_lab.social_architecture import Economy, gini, hill, top_share


class InstrumentTest(unittest.TestCase):
    def test_the_instrument_cannot_reach_the_laboratory(self):
        """It imports nothing from the model and nothing third-party, so
        no rule here can move a baseline metric (docs/97 section 6).

        Read from the import graph rather than by searching the text: the
        module's docstring names ``economy_lab.model`` in prose.
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
                imported.add(("." * node.level) + (node.module or ""))

        allowed = set(sys.stdlib_module_names)
        for name in imported:
            self.assertNotIn("model", name, f"{name} reaches the laboratory")
            root = name.lstrip(".").split(".")[0]
            if root:
                self.assertIn(root, allowed, f"{name} is not stdlib")

    def test_money_is_conserved(self):
        """``sum(m) + V == M``.  Money is real-valued in the paper
        (``m_i in R+``), so this holds to float precision rather than
        exactly -- which is itself a correction to the first version of
        this module, which made coins integers (docs/100 error 6).
        """
        for seed in range(3):
            economy = Economy(actors=200, coins=20_000.0, seed=seed)
            start = economy.total_coins()
            economy.run(40)
            self.assertAlmostEqual(economy.total_coins(), start, places=6)

    def test_a_run_is_reproducible_under_its_seed(self):
        first = Economy(actors=200, coins=20_000.0, seed=3)
        second = Economy(actors=200, coins=20_000.0, seed=3)
        first.run(20)
        second.run(20)
        self.assertEqual(first.money, second.money)
        self.assertEqual(first.employer, second.employer)

    def test_the_staff_index_agrees_with_a_scan(self):
        economy = Economy(actors=200, coins=20_000.0, seed=1)
        for _ in range(20):
            economy.month()
            self.assertTrue(economy.check_staff_index())

    def test_nobody_employs_themselves(self):
        """The state constraint ``e_i != i``; self-employment is excluded
        from the model (paper section 2.4)."""
        economy = Economy(actors=200, coins=20_000.0, seed=2)
        economy.run(40)
        for i, e in enumerate(economy.employer):
            self.assertNotEqual(e, i)

    def test_the_three_classes_are_disjoint_and_exhaustive(self):
        """``C``, ``W`` and ``U`` partition ``A``, and are derived from the
        state rather than assigned."""
        economy = Economy(actors=200, coins=20_000.0, seed=4)
        economy.run(40)
        for i in range(economy.actors):
            flags = [
                economy.is_capitalist(i),
                economy.is_worker(i),
                economy.is_unemployed(i),
            ]
            self.assertEqual(sum(flags), 1, f"actor {i} is in {flags}")
        self.assertEqual(sum(economy.classes()), economy.actors)


class PaperRuleTest(unittest.TestCase):
    """The rule bodies, checked one at a time against the paper."""

    def test_F1_fires_down_to_what_money_holdings_afford(self):
        """``u = max(|W_a| - floor(m_a / <w>), 0)`` -- against ``m_a``, the
        firm's *money*, not its trailing revenue.

        This is `docs/98`'s central error (docs/100 error 3): the paper's
        prose in section 2.7 says "if current revenues do not cover the
        expected wage bill", which is what every secondary source quotes,
        but the formal rule is the floor above.
        """
        economy = Economy(actors=10, coins=0.0, seed=0)
        for worker in range(1, 6):
            economy._attach(worker, 0)
        self.assertEqual(len(economy.employees(0)), 5)
        # <w> = 50; 160 coins affords three wages, so two go.
        economy.money[0] = 160.0
        economy.revenue[0] = 0.0
        economy._fire(0)
        self.assertEqual(len(economy.employees(0)), 3)

    def test_F1_fires_nobody_when_holdings_cover_the_bill(self):
        economy = Economy(actors=10, coins=0.0, seed=0)
        for worker in range(1, 4):
            economy._attach(worker, 0)
        economy.money[0] = 150.0
        economy._fire(0)
        self.assertEqual(len(economy.employees(0)), 3)

    def test_a_firm_that_fires_everyone_ceases_trading(self):
        economy = Economy(actors=10, coins=0.0, seed=0)
        for worker in range(1, 4):
            economy._attach(worker, 0)
        economy.money[0] = 0.0
        economy._fire(0)
        self.assertEqual(economy.employees(0), [])
        self.assertTrue(economy.is_unemployed(0))

    def test_H1_tests_the_threshold_after_the_draw(self):
        """A hire fails when the actor drawn cannot cover the average
        wage; the vacancy is not passed to somebody who can (docs/100
        error 1)."""
        economy = Economy(actors=2, coins=0.0, seed=0)
        economy.money = [0.0, 10.0]  # 10 < <w> = 50
        economy._hire(0)
        self.assertTrue(economy.is_unemployed(0))
        economy.money[1] = 60.0
        economy._hire(0)
        self.assertEqual(economy.employer[0], 1)

    def test_W1_part_pays_when_the_employer_cannot_cover_the_wage(self):
        """"If [the employer] has insufficient funds to pay w then w is
        selected from the discrete interval [0, m_a]" -- a short employer
        pays something, not nothing (docs/100 error 5)."""
        economy = Economy(actors=4, coins=0.0, seed=1)
        economy._attach(1, 0)
        economy.money[0] = 5.0  # below wage_min = 10
        economy._pay(0)
        self.assertLessEqual(economy.money[0], 5.0)
        self.assertGreaterEqual(economy.money[0], 0.0)
        self.assertAlmostEqual(economy.money[0] + economy.money[1], 5.0, places=9)

    def test_W1_pays_the_whole_payroll_when_the_employer_acts(self):
        """Wages go out when the *employer* is the active actor, not when
        each employee is (docs/100 error 4)."""
        economy = Economy(actors=6, coins=0.0, seed=1)
        for worker in (1, 2, 3):
            economy._attach(worker, 0)
        economy.money[0] = 1000.0
        economy._pay(0)
        for worker in (1, 2, 3):
            self.assertGreater(economy.money[worker], 0.0)


class StylizedFactTest(unittest.TestCase):
    """Wright's reported results, at Wright's reported parameters."""

    def test_the_economy_is_stationary_rather_than_monopolising(self):
        """`docs/98` reported that firing against accumulated funds sends
        the model to monopoly.  That was an artifact of five other
        deviations: the paper's own rule does no such thing.
        """
        economy = Economy(actors=400, coins=40_000.0, seed=5)
        economy.run(150)
        sizes = economy.firm_sizes()
        self.assertGreater(len(sizes), 10)
        self.assertLess(max(sizes) / economy.actors, 0.5)

    def test_a_reserve_army_persists(self):
        """Unemployment is an outcome that neither vanishes nor swallows
        the economy -- Wright's central result, and the one A5 says our
        laboratory has no counterpart for."""
        economy = Economy(actors=400, coins=40_000.0, seed=6)
        readings = []
        for _ in range(6):
            economy.run(20)
            readings.append(economy.unemployment_rate())
        for rate in readings:
            self.assertGreater(rate, 0.01)
            self.assertLess(rate, 0.60)

    def test_classes_emerge_from_a_symmetric_start(self):
        economy = Economy(actors=400, coins=40_000.0, seed=7)
        self.assertEqual(economy.classes(), (0, 0, 400))
        economy.run(60)
        capitalists, workers, unemployed = economy.classes()
        self.assertGreater(capitalists, 0)
        self.assertGreater(workers, 0)
        self.assertGreater(unemployed, 0)
        self.assertLess(capitalists / economy.actors, 0.30)

    def test_the_firm_size_distribution_has_a_heavy_tail(self):
        """Hill near 1 is Zipf's law of firm size.  No exponent is claimed
        to *match* the paper's fitted value; this asserts the tail is
        heavy, which is what a bare Hill reading can support."""
        economy = Economy(actors=600, coins=60_000.0, seed=8)
        economy.run(120)
        estimate = hill([float(x) for x in economy.firm_sizes()])
        self.assertIsNotNone(estimate)
        self.assertLess(estimate, 3.0)

    def test_the_wage_share_fluctuates(self):
        """Wright reports "fluctuating wage and profit shares in national
        income".  Ours does too, once bargaining is on (docs/99) -- but
        there the channel has to be switched on, and here it is intrinsic.
        """
        economy = Economy(actors=400, coins=40_000.0, seed=9)
        economy.run(80)
        shares = []
        for _ in range(40):
            economy.month()
            share = economy.wage_share()
            if share is not None:
                shares.append(share)
        self.assertGreater(len(shares), 20)
        self.assertGreater(max(shares) - min(shares), 0.05)


class StatisticsTest(unittest.TestCase):
    def test_gini_is_zero_when_everyone_is_equal(self):
        self.assertAlmostEqual(gini([5.0] * 50), 0.0, places=12)

    def test_gini_approaches_one_when_one_holds_everything(self):
        self.assertGreater(gini([0.0] * 999 + [1000.0]), 0.99)

    def test_gini_of_nothing_is_zero_rather_than_an_error(self):
        self.assertEqual(gini([]), 0.0)
        self.assertEqual(gini([0.0, 0.0]), 0.0)

    def test_top_share_of_an_equal_population_is_the_fraction(self):
        self.assertAlmostEqual(top_share([1.0] * 100, 0.1), 0.1, places=12)

    def test_hill_is_none_when_the_tail_is_too_small_to_estimate(self):
        self.assertIsNone(hill([1.0, 2.0, 3.0]))

    def test_hill_recovers_a_known_pareto_index(self):
        import random

        rng = random.Random(11)
        sample = [(1.0 - rng.random()) ** -1.0 for _ in range(20_000)]
        estimate = hill(sample, tail=0.05)
        self.assertIsNotNone(estimate)
        self.assertGreater(estimate, 0.85)
        self.assertLess(estimate, 1.15)


if __name__ == "__main__":
    unittest.main()
