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


class TheGoodnessOfFitTest(unittest.TestCase):
    """docs/113 section 2.1: a KS distance is not a verdict."""

    def test_a_genuine_power_law_is_not_rejected(self):
        rng = random.Random(4)
        result = D.goodness_of_fit(
            _pareto(rng, 2.5, 4000), synthetics=60, seed=1
        )
        self.assertGreater(result["p"], 0.1)
        self.assertFalse(result["rejected"])

    def test_lognormal_data_is_rejected_as_a_power_law(self):
        # 8000 points, not 4000: at 4000 this same data gives p = 0.25 and
        # is *not* rejected.  That is docs/113 section 3's sample-size
        # point arriving inside the test suite -- the test's power to tell
        # two families apart is a function of n, which is exactly why the
        # firm-size test is run per seed rather than pooled.
        rng = random.Random(4)
        values = [math.exp(rng.gauss(0.0, 1.2)) for _ in range(8000)]
        result = D.goodness_of_fit(values, synthetics=60, seed=1)
        self.assertLessEqual(result["p"], 0.1)
        self.assertTrue(result["rejected"])

    def test_the_same_lognormal_survives_at_half_the_sample(self):
        rng = random.Random(4)
        values = [math.exp(rng.gauss(0.0, 1.2)) for _ in range(4000)]
        result = D.goodness_of_fit(values, synthetics=60, seed=1)
        self.assertGreater(result["p"], 0.1)

    def test_the_rule_of_thumb_is_the_one_csn_state(self):
        rng = random.Random(9)
        result = D.goodness_of_fit(
            _pareto(rng, 2.5, 2000), synthetics=40, seed=2
        )
        self.assertEqual(result["rejected"], result["p"] <= 0.1)


class TheLikelihoodRatioTest(unittest.TestCase):
    """docs/113 section 2.2, and the truncation bug it caught."""

    def setUp(self):
        rng = random.Random(4)
        self.power = _pareto(rng, 2.5, 5000)
        self.lognormal = [math.exp(rng.gauss(0.0, 1.2)) for _ in range(5000)]

    def _ratio(self, data, alternative):
        fit = D.power_law_fit(data)
        return D.likelihood_ratio(
            data, fit["x_min"], fit["alpha"], alternative
        )

    def test_the_power_law_beats_an_exponential_on_power_law_data(self):
        result = self._ratio(self.power, "exponential")
        self.assertGreater(result["normalised"], 2.0)
        self.assertEqual(result["favours"], "power_law")

    def test_the_lognormal_wins_on_lognormal_data(self):
        # The regression this pins: fitting the lognormal *untruncated*
        # while the power law is normalised on the tail rigs the
        # comparison, and reported +9.09 for the power law on data drawn
        # from a lognormal.  The alternative must be fitted on the same
        # support (docs/113 section 2.2).
        result = self._ratio(self.lognormal, "lognormal")
        self.assertLess(result["normalised"], -2.0)
        self.assertEqual(result["favours"], "alternative")

    def test_a_lognormal_is_hard_to_beat_even_on_true_power_law_data(self):
        # CSN's general finding, and the reason a passed goodness-of-fit
        # test is weak evidence: the two families are barely separable.
        result = self._ratio(self.power, "lognormal")
        self.assertFalse(result["determined"])
        self.assertEqual(result["favours"], "neither")

    def test_an_unknown_alternative_is_refused(self):
        fit = D.power_law_fit(self.power)
        with self.assertRaises(ValueError):
            D.likelihood_ratio(self.power, fit["x_min"], fit["alpha"], "cauchy")


class TheExponentialGoodnessOfFitTest(unittest.TestCase):
    def test_exponential_data_is_not_rejected(self):
        rng = random.Random(6)
        values = [rng.expovariate(1.2) for _ in range(400)]
        result = D.exponential_goodness_of_fit(values, synthetics=300, seed=1)
        self.assertGreater(result["p"], 0.1)
        self.assertAlmostEqual(result["lambda"], 1.2, delta=0.15)

    def test_a_heavy_tail_is_rejected_as_exponential(self):
        rng = random.Random(6)
        result = D.exponential_goodness_of_fit(
            _pareto(rng, 2.2, 400), synthetics=300, seed=1
        )
        self.assertLessEqual(result["p"], 0.1)

    def test_too_little_data_is_none(self):
        self.assertIsNone(D.exponential_goodness_of_fit([1.0, 2.0]))


class TheGeometricGoodnessOfFitTest(unittest.TestCase):
    """docs/114 section 4: the right null for integer durations."""

    @staticmethod
    def _geometric(rng, q, count):
        return [
            1 + int(math.log(1.0 - rng.random()) / math.log(q))
            for _ in range(count)
        ]

    def test_true_geometric_data_is_not_rejected(self):
        rng = random.Random(5)
        result = D.geometric_goodness_of_fit(
            self._geometric(rng, 0.31, 481), synthetics=400, seed=2
        )
        self.assertGreater(result["p"], 0.1)

    def test_the_statistic_is_small_on_true_data(self):
        # The regression this pins: carrying the continuous statistic's
        # left-limit term onto a discrete support compares F(1) against an
        # empirical zero and reported KS 0.6881 for data drawn from the
        # very distribution being fitted (docs/114 section 4).
        rng = random.Random(5)
        result = D.geometric_goodness_of_fit(
            self._geometric(rng, 0.31, 481), synthetics=100, seed=2
        )
        self.assertLess(result["ks"], 0.05)

    def test_a_uniform_sample_is_rejected(self):
        rng = random.Random(5)
        values = [1 + int(rng.random() * 5) for _ in range(481)]
        result = D.geometric_goodness_of_fit(values, synthetics=400, seed=2)
        self.assertLessEqual(result["p"], 0.1)

    def test_the_decay_rate_is_reported(self):
        rng = random.Random(5)
        result = D.geometric_goodness_of_fit(
            self._geometric(rng, 0.31, 2000), synthetics=50, seed=2
        )
        # lambda = -ln(1 - p) for the fitted success probability.
        self.assertAlmostEqual(
            result["lambda"], -math.log(1.0 - result["p_success"]), places=9
        )
