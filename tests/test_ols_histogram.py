"""Wright's own estimator, added in ``docs/124`` task one."""

import random
import unittest

from economy_lab import distributions as D


def planted(alpha_wright, n, seed=0):
    """Discrete P(x) ~ x ** -(alpha+1) by inverse transform."""
    rng = random.Random(seed)
    exponent = -1.0 / alpha_wright
    return [int((1.0 - rng.random()) ** exponent) for _ in range(n)]


class TestConvention(unittest.TestCase):
    def test_the_exponent_is_already_in_wrights_convention(self):
        # He fits P(x) = x ** -(alpha+1), so slope = -(alpha+1).
        fit = D.ols_histogram_fit(planted(1.5, 20000))
        self.assertAlmostEqual(fit["alpha_wright"], -fit["slope"] - 1.0, places=12)

    def test_to_wright_must_not_be_applied_on_top(self):
        # The trap docs/114 recorded: applying the conversion twice.
        fit = D.ols_histogram_fit(planted(1.5, 20000))
        self.assertNotAlmostEqual(fit["alpha_wright"], D.to_wright(fit["alpha_wright"]))


class TestBias(unittest.TestCase):
    """docs/124 predictions 1 and 3, pinned as regressions."""

    def setUp(self):
        self.sample = planted(1.5, 50000, seed=4)

    def test_it_underestimates_a_planted_exponent(self):
        fit = D.ols_histogram_fit(self.sample, min_count=1)
        self.assertLess(fit["alpha_wright"], 1.5 - 0.3)

    def test_the_discrete_sampler_caveat_is_real_and_bounded(self):
        # Recorded so it cannot be mistaken for an OLS effect later.
        mle = D.power_law_fit(self.sample, discrete=True, min_tail=200)
        self.assertAlmostEqual(mle["alpha_wright"], 1.5, delta=0.25)

    def test_mle_recovers_a_continuous_planted_exponent_exactly(self):
        # On continuous data the MLE is unbiased, which is the reference
        # point the OLS bias is measured against.
        rng = random.Random(9)
        sample = [(1.0 - rng.random()) ** (-1.0 / 1.5) for _ in range(50000)]
        fit = D.power_law_fit(sample)
        self.assertAlmostEqual(D.to_wright(fit["alpha"]), 1.5, delta=0.05)

    def test_ols_is_biased_low_against_mle_on_the_very_same_sample(self):
        # The load-bearing comparison: estimator against estimator, which
        # does not depend on our discrete sampler matching the zeta the
        # discrete MLE assumes.  It does not -- flooring a continuous
        # Pareto reads about 0.16 low under the discrete MLE -- so the
        # nominal 1.5 is not the reference here.
        mle = D.power_law_fit(self.sample, discrete=True, min_tail=200)
        ols = D.ols_histogram_fit(self.sample, min_count=1)
        self.assertLess(ols["alpha_wright"], mle["alpha_wright"] - 0.3)

    def test_dropping_sparse_bins_monotonically_reduces_the_bias(self):
        errors = [abs(D.ols_histogram_fit(self.sample, min_count=m)["alpha_wright"] - 1.5)
                  for m in (1, 2, 5, 10)]
        self.assertEqual(errors, sorted(errors, reverse=True))

    def test_keeping_more_bins_uses_more_bins(self):
        loose = D.ols_histogram_fit(self.sample, min_count=1)
        tight = D.ols_histogram_fit(self.sample, min_count=10)
        self.assertGreater(loose["bins"], tight["bins"])


class TestGuards(unittest.TestCase):
    def test_too_few_bins_returns_none_rather_than_a_two_point_slope(self):
        self.assertIsNone(D.ols_histogram_fit([1, 1, 2, 2]))

    def test_a_single_repeated_value_has_no_slope(self):
        self.assertIsNone(D.ols_histogram_fit([5] * 500))

    def test_values_below_x_min_are_excluded(self):
        sample = planted(1.5, 20000)
        self.assertLess(D.ols_histogram_fit(sample, x_min=5)["bins"],
                        D.ols_histogram_fit(sample, x_min=1)["bins"])

    def test_it_reports_the_fit_quality_so_a_bad_fit_is_visible(self):
        fit = D.ols_histogram_fit(planted(1.5, 50000))
        self.assertIsNotNone(fit["r_squared"])
        self.assertLessEqual(fit["r_squared"], 1.0)


if __name__ == "__main__":
    unittest.main()
