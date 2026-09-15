"""The stdlib estimators (docs/111, docs/112).

numpy, scipy and the `powerlaw` package are unavailable under the
project's no-dependency rule, so these are written rather than imported
and therefore need testing against distributions whose answers are
known in advance.
"""

import math
import random
import unittest

from economy_lab import distributions as D


def _pareto(rng, alpha, count):
    """Continuous power law with exponent ``alpha``, x_min 1."""
    return [(1.0 - rng.random()) ** (-1.0 / (alpha - 1.0)) for _ in range(count)]


def _laplace(rng, count):
    values = []
    for _ in range(count):
        u = rng.random() - 0.5
        values.append(-math.copysign(1.0, u) * math.log(1.0 - 2.0 * abs(u)))
    return values


class TheExponentConventionTest(unittest.TestCase):
    """docs/111 section 2: Wright's alpha and CSN's differ by one."""

    def test_zipf_is_two_in_csn_and_one_in_wright(self):
        self.assertEqual(D.to_wright(2.0), 1.0)

    def test_the_fit_reports_both(self):
        rng = random.Random(3)
        fit = D.power_law_fit(_pareto(rng, 2.5, 20000))
        self.assertAlmostEqual(fit["alpha"] - fit["alpha_wright"], 1.0)


class ThePowerLawFitRecoversAKnownExponentTest(unittest.TestCase):
    def test_continuous(self):
        rng = random.Random(7)
        fit = D.power_law_fit(_pareto(rng, 2.5, 50000))
        self.assertAlmostEqual(fit["alpha"], 2.5, delta=0.05)

    def test_a_steeper_one(self):
        rng = random.Random(11)
        fit = D.power_law_fit(_pareto(rng, 3.2, 50000))
        self.assertAlmostEqual(fit["alpha"], 3.2, delta=0.08)

    def test_discrete(self):
        rng = random.Random(7)
        values = [float(int(v)) for v in _pareto(rng, 2.5, 50000) if v >= 1.0]
        fit = D.power_law_fit(values, discrete=True, min_tail=200)
        self.assertAlmostEqual(fit["alpha"], 2.5, delta=0.10)

    def test_too_little_data_is_none_rather_than_a_guess(self):
        self.assertIsNone(D.power_law_fit([1.0, 2.0, 3.0], min_tail=50))


class TheShapeMomentsTest(unittest.TestCase):
    """Excess kurtosis is the binning-free test for facts 2 and 3."""

    def test_a_gaussian_has_zero_excess_kurtosis(self):
        rng = random.Random(5)
        values = [rng.gauss(0.0, 1.0) for _ in range(50000)]
        self.assertAlmostEqual(D.excess_kurtosis(values), 0.0, delta=0.15)

    def test_a_laplace_has_three(self):
        rng = random.Random(5)
        self.assertAlmostEqual(
            D.excess_kurtosis(_laplace(rng, 50000)), 3.0, delta=0.5
        )

    def test_a_symmetric_sample_has_no_skew(self):
        rng = random.Random(5)
        values = [rng.gauss(0.0, 1.0) for _ in range(50000)]
        self.assertAlmostEqual(D.skewness(values), 0.0, delta=0.1)

    def test_a_right_tail_skews_positive(self):
        rng = random.Random(5)
        self.assertGreater(D.skewness(_pareto(rng, 2.5, 20000)), 0.0)


class TheSimpleFitsTest(unittest.TestCase):
    def test_exponential_rate(self):
        rng = random.Random(2)
        values = [rng.expovariate(0.5) for _ in range(20000)]
        self.assertAlmostEqual(D.exponential_lambda(values), 0.5, delta=0.02)

    def test_lognormal_parameters(self):
        rng = random.Random(2)
        values = [math.exp(rng.gauss(1.5, 0.4)) for _ in range(20000)]
        mu, sigma = D.lognormal_fit(values)
        self.assertAlmostEqual(mu, 1.5, delta=0.02)
        self.assertAlmostEqual(sigma, 0.4, delta=0.02)

    def test_laplace_location_and_scale(self):
        rng = random.Random(2)
        values = [3.0 + 2.0 * v for v in _laplace(rng, 40000)]
        location, scale = D.laplace_fit(values)
        self.assertAlmostEqual(location, 3.0, delta=0.05)
        # The MLE scale of a Laplace is the mean absolute deviation.
        self.assertAlmostEqual(scale, 2.0, delta=0.05)


if __name__ == "__main__":
    unittest.main()
