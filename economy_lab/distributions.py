"""Distribution estimators, stdlib only (docs/111).

The project has no third-party dependency and this slice does not
introduce one, so numpy, scipy and the `powerlaw` package are all
unavailable and the estimators are written rather than imported.

The power-law fit follows Clauset, Shalizi and Newman: choose ``x_min``
by minimising the Kolmogorov-Smirnov distance between the empirical tail
and the fitted one, then take the maximum-likelihood exponent above it.
No OLS on a log-log histogram -- Wright used that, it is the wrong
estimator for a tail, and it is why his figures carry no confidence
intervals.

**Exponent conventions differ and the difference is exactly one.**
Wright writes ``P(x) ∝ x^-(alpha+1)``; the CSN estimator fits
``p(x) ∝ x^-alpha``.  Functions here return the **CSN** exponent;
:func:`to_wright` converts.  Zipf is ``alpha_csn = 2.0``.
"""

from __future__ import annotations

import math
import random
from typing import List, Optional, Sequence, Tuple


def to_wright(alpha_csn: float) -> float:
    """CSN's exponent in Wright's convention (docs/111 section 2)."""
    return alpha_csn - 1.0


# ------------------------------------------------------------- moments


def mean(values: Sequence[float]) -> float:
    return sum(values) / len(values)


def variance(values: Sequence[float]) -> float:
    if len(values) < 2:
        return 0.0
    average = mean(values)
    return sum((value - average) ** 2 for value in values) / (len(values) - 1)


def _standard_moment(values: Sequence[float], order: int) -> Optional[float]:
    if len(values) < 3:
        return None
    average = mean(values)
    deviation = math.sqrt(
        sum((value - average) ** 2 for value in values) / len(values)
    )
    if deviation <= 0.0:
        return None
    total = sum((value - average) ** order for value in values)
    return total / (len(values) * deviation ** order)


def skewness(values: Sequence[float]) -> Optional[float]:
    return _standard_moment(values, 3)


def excess_kurtosis(values: Sequence[float]) -> Optional[float]:
    """Kurtosis less three: **0 for a Gaussian, 3 for a Laplace**.

    The shape test for facts 2 and 3, chosen because it does not depend
    on how the histogram is binned -- Wright's tent-shape reading does.
    """
    moment = _standard_moment(values, 4)
    return None if moment is None else moment - 3.0


# --------------------------------------------------------- simple fits


def exponential_lambda(values: Sequence[float]) -> Optional[float]:
    """MLE rate of an exponential: the reciprocal of the mean."""
    positive = [value for value in values if value > 0.0]
    if not positive:
        return None
    average = mean(positive)
    return 1.0 / average if average > 0.0 else None


def lognormal_fit(values: Sequence[float]) -> Optional[Tuple[float, float]]:
    """MLE ``(mu, sigma)`` of the logs of the positive values."""
    logs = [math.log(value) for value in values if value > 0.0]
    if len(logs) < 2:
        return None
    mu = mean(logs)
    sigma = math.sqrt(sum((value - mu) ** 2 for value in logs) / len(logs))
    return mu, sigma


def laplace_fit(values: Sequence[float]) -> Optional[Tuple[float, float]]:
    """MLE ``(location, scale)``: the median, and the mean absolute
    deviation from it."""
    if not values:
        return None
    ordered = sorted(values)
    middle = len(ordered) // 2
    location = (
        ordered[middle]
        if len(ordered) % 2
        else (ordered[middle - 1] + ordered[middle]) / 2.0
    )
    scale = mean([abs(value - location) for value in values])
    return location, scale


# ------------------------------------------------------ the power law


def _alpha_continuous(tail: Sequence[float], x_min: float) -> Optional[float]:
    total = 0.0
    for value in tail:
        ratio = value / x_min
        if ratio <= 0.0:
            return None
        total += math.log(ratio)
    if total <= 0.0:
        return None
    return 1.0 + len(tail) / total


def _alpha_discrete(tail: Sequence[float], x_min: float) -> Optional[float]:
    """CSN's discrete approximation: ``x_min - 0.5`` in the denominator."""
    return _alpha_continuous(tail, x_min - 0.5) if x_min > 0.5 else None


def _ks_distance(tail: Sequence[float], x_min: float, alpha: float) -> float:
    """Largest gap between the empirical and fitted CDFs above x_min."""
    ordered = sorted(tail)
    count = len(ordered)
    worst = 0.0
    for position, value in enumerate(ordered):
        fitted = 1.0 - (value / x_min) ** (1.0 - alpha)
        empirical_below = position / count
        empirical_above = (position + 1) / count
        worst = max(
            worst, abs(fitted - empirical_below), abs(fitted - empirical_above)
        )
    return worst


def power_law_fit(
    values: Sequence[float],
    *,
    discrete: bool = False,
    min_tail: int = 50,
    ks_sample: int = 20000,
    max_candidates: int = 200,
) -> Optional[dict]:
    """Fit a power law, choosing ``x_min`` by KS minimisation (CSN).

    Returns the CSN exponent, the chosen ``x_min``, the tail size and the
    KS distance -- or ``None`` when no tail of at least ``min_tail``
    points exists.  Convert the exponent with :func:`to_wright` before
    comparing against the paper.

    The exponent for each candidate ``x_min`` comes from a suffix sum of
    ``log x`` computed once, so the scan is linear in the number of
    distinct values rather than quadratic in the sample; the KS distance
    is evaluated on at most ``ks_sample`` evenly spaced points of the
    tail, which bounds the cost on the pooled millions of firm sizes.

    At most ``max_candidates`` values of ``x_min`` are tried, spaced
    evenly through the sorted sample.  Continuous data makes every point
    a distinct candidate, so an uncapped scan is quadratic; capping is
    what CSN's own implementations do on large samples, and the grid is
    far finer than the exponent's own confidence interval.
    """
    ordered = sorted(value for value in values if value > 0.0)
    count = len(ordered)
    if count < min_tail:
        return None
    suffix = 0.0
    suffixes = [0.0] * (count + 1)
    for i in range(count - 1, -1, -1):
        suffix += math.log(ordered[i])
        suffixes[i] = suffix

    limit = count - min_tail
    stride = max(1, (limit + 1) // max_candidates)
    best = None
    start = 0
    while start <= limit:
        x_min = ordered[start]
        nxt = start + stride
        while nxt < count and ordered[nxt] == x_min:
            nxt += 1
        tail_size = count - start
        base = x_min - 0.5 if discrete else x_min
        if base > 0.0:
            total = suffixes[start] - tail_size * math.log(base)
            if total > 0.0:
                alpha = 1.0 + tail_size / total
                if alpha > 1.0:
                    distance = _ks_distance_sampled(
                        ordered, start, x_min, alpha, ks_sample
                    )
                    if best is None or distance < best["ks"]:
                        best = {
                            "alpha": alpha,
                            "alpha_wright": to_wright(alpha),
                            "x_min": x_min,
                            "tail": tail_size,
                            "ks": distance,
                        }
        start = nxt
    return best


def _ks_distance_sampled(
    ordered: Sequence[float],
    start: int,
    x_min: float,
    alpha: float,
    ks_sample: int,
) -> float:
    """KS distance on the tail ``ordered[start:]``, at most ``ks_sample``
    evenly spaced points."""
    count = len(ordered)
    tail_size = count - start
    step = 1 if tail_size <= ks_sample else tail_size // ks_sample
    worst = 0.0
    index = start
    while index < count:
        position = index - start
        fitted = 1.0 - (ordered[index] / x_min) ** (1.0 - alpha)
        below = position / tail_size
        above = (position + 1) / tail_size
        if fitted - below > worst:
            worst = fitted - below
        if above - fitted > worst:
            worst = above - fitted
        index += step
    return worst


def bootstrap_alpha(
    values: Sequence[float],
    *,
    discrete: bool = False,
    resamples: int = 200,
    seed: int = 0,
    min_tail: int = 50,
) -> Optional[Tuple[float, float]]:
    """A 95% percentile interval for the CSN exponent, by resampling."""
    rng = random.Random(seed)
    population = list(values)
    if not population:
        return None
    draws: List[float] = []
    for _ in range(resamples):
        sample = [rng.choice(population) for _ in range(len(population))]
        fit = power_law_fit(sample, discrete=discrete, min_tail=min_tail)
        if fit is not None:
            draws.append(fit["alpha"])
    if len(draws) < 20:
        return None
    draws.sort()
    low = draws[int(0.025 * len(draws))]
    high = draws[min(int(0.975 * len(draws)), len(draws) - 1)]
    return low, high
