"""The law-of-value economy's invariants (docs/147)."""

import unittest

from economy_lab.law_of_value import (
    GOODS,
    SECOND,
    Technique,
    run_capitalist,
    run_simple,
)


class TechniqueTest(unittest.TestCase):
    def test_values_solve_v_equals_l_plus_av(self):
        tech = Technique(3)
        v = tech.values()
        for i in range(GOODS):
            carried = sum(c * v[j] for j, c in tech.A[i])
            self.assertAlmostEqual(v[i], tech.labor[i] + carried, places=12)

    def test_inputs_come_only_from_shallower_depths(self):
        tech = Technique(5)
        for i, row in enumerate(tech.A):
            for j, _ in row:
                self.assertLess(tech.depth[j], tech.depth[i])

    def test_prices_of_production_at_zero_profit_are_values(self):
        tech = Technique(7)
        for p, v in zip(tech.prices_of_production(0.0), tech.values()):
            self.assertAlmostEqual(p, v, places=12)

    def test_the_null_permutes_the_labour(self):
        tech = Technique(0)
        self.assertEqual(sorted(tech.permutation), list(range(GOODS)))
        self.assertNotEqual(tech.null_values(), tech.values())


class RunTest(unittest.TestCase):
    def test_money_is_conserved(self):
        self.assertLess(run_simple(1, 200)["worst_money_drift"], 1e-9)
        self.assertLess(run_simple(1, 200, shock_day=100)["worst_money_drift"], 1e-9)
        self.assertLess(run_capitalist(1, 200)["worst_money_drift"], 1e-9)

    def test_runs_are_deterministic(self):
        self.assertEqual(run_simple(2, 150), run_simple(2, 150))
        self.assertEqual(run_capitalist(2, 150), run_capitalist(2, 150))

    def test_the_second_experiment_conserves_money_and_is_deterministic(self):
        self.assertLess(run_simple(1, 200, **SECOND)["worst_money_drift"], 1e-9)
        self.assertLess(run_capitalist(1, 200, **SECOND)["worst_money_drift"], 1e-9)
        self.assertEqual(run_simple(2, 150, **SECOND), run_simple(2, 150, **SECOND))
        self.assertEqual(run_capitalist(2, 150, **SECOND), run_capitalist(2, 150, **SECOND))

    def test_the_switches_off_are_the_first_experiment(self):
        a = run_simple(4, 120)
        b = run_simple(4, 120, explore=0.0, buffer=1.0)
        self.assertEqual(a, b)


if __name__ == "__main__":
    unittest.main()
