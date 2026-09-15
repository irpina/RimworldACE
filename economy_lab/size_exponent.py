"""The continuous size-exponent sweep of ``docs/118``.

Design in ``docs/118``, results in ``docs/119``.

    python -m economy_lab.size_exponent out.json 50

Asks whether Wright's fit is a basin or a knife edge, by making M1's
size bias continuous: expected revenue goes as ``members ** beta``, with
``beta = 1`` the paper's rule and ``beta = 0`` the size-neutral ablation.

Each worker **fits its own run** and returns summary numbers rather than
the raw streams.  ``docs/114`` is why: the fitted exponent drifts upward
with sample size, so pooling 50 seeds before fitting -- which is what
``docs/116`` did -- gives a number that cannot be read against Wright's.
Per seed the firm-size sample is n ~ 21,900, his own scale.  It also
keeps the records small; pooled-style records would run to ~240 MB here.
"""

import json
import math
import statistics as st
import sys
from multiprocessing import Pool

from economy_lab import distributions as D
from economy_lab import social_architecture as sa

BURN_IN = 120
WINDOW = 180

#: docs/118: [0, 1.5] at 0.1, refined either side of 1 where the
#: interesting structure is predicted to be.
BETAS = tuple(sorted({round(0.1 * step, 2) for step in range(16)}
                     | {0.85, 0.95, 1.05, 1.15}))

#: docs/118 s4, fixed before the run and not to be moved afterwards.
#: ``None`` for an open end.  Wright's reported value in the comment.
BANDS = {
    "firm_alpha": (0.8, 1.4),        # 1.038
    "growth_kurtosis": (2.0, None),  # Laplace = 3
    "gdp_kurtosis": (1.0, None),     # Laplace = 3, pooled
    "demises": (12.0, 26.0),         # 18 per month
    "recession_lambda": (0.95, 1.55),  # 1.22, pooled
    "income_alpha": (0.9, 1.9),      # 1.3
    "wage_share": (0.45, 0.65),      # 0.55
}

#: Reported alongside the seven but not one of them (docs/118 s4).
DIAGNOSTIC = {"unemployment": (0.10, 0.25)}  # ~0.17

#: The two that cannot be fitted per seed, because ``gdp`` and
#: ``wage_shares`` are yearly and the window holds 15 of them.
POOLED = ("gdp_kurtosis", "recession_lambda")


def run_cell(job):
    """Run one (beta, seed), fit it, and return summaries plus small series."""
    beta, seed = job
    economy = sa.Economy(seed=seed, market_rule="scaled", size_exponent=beta)
    economy.run(BURN_IN)
    economy.start_recording()
    economy.run(WINDOW)
    history = economy.history

    firm_fit = D.power_law_fit(history.firm_sizes, discrete=True, min_tail=200)
    incomes = [value for value in history.incomes if value > 0]
    income_fit = D.power_law_fit(incomes, min_tail=500)
    sizes = economy.firm_sizes()
    return {
        "beta": beta,
        "seed": seed,
        # fitted per seed, at Wright's own scale
        "firm_alpha": firm_fit.get("alpha_wright") if firm_fit else None,
        "firm_x_min": firm_fit.get("x_min") if firm_fit else None,
        "firm_n": len(history.firm_sizes),
        "growth_kurtosis": D.excess_kurtosis(history.firm_growth),
        "income_alpha": income_fit.get("alpha_wright") if income_fit else None,
        "profit_skew": (D.skewness(history.profit_rates)
                        if len(history.profit_rates) > 3 else None),
        "demises": st.mean(history.demises_per_month),
        "wage_share": st.mean(history.wage_shares) if history.wage_shares else None,
        "unemployment": economy.unemployment_rate(),
        "firms": len(sizes),
        "largest": max(sizes or [0]),
        "coins": economy.total_coins(),
        # yearly, so too short to fit alone -- pooled in ``pooled_readings``
        "gdp": history.gdp,
    }


def sweep(betas=BETAS, seeds=50, processes=4):
    """Every beta against every seed, in (beta, seed) order."""
    jobs = [(beta, seed) for beta in betas for seed in range(seeds)]
    with Pool(processes) as pool:
        return pool.map(run_cell, jobs)


def _median(values):
    present = [value for value in values if value is not None]
    return st.median(present) if present else None


def pooled_readings(runs):
    """The two facts the 1Y rule leaves too short to fit per seed.

    ``lambda`` comes from the closed form the geometric estimator
    documents rather than its bootstrap: only the point estimate is
    needed here, and ``docs/114`` already settled the family question.
    """
    growth, durations = [], []
    for run in runs:
        history = sa.History(gdp=run["gdp"])
        growth.extend(history.gdp_growth())
        durations.extend(history.recessions())
    counts = [int(round(value)) for value in durations if value >= 1]
    average = sum(counts) / len(counts) if counts else 0.0
    return {
        "gdp_kurtosis": D.excess_kurtosis(growth) if len(growth) > 3 else None,
        "recession_lambda": (-math.log(1.0 - 1.0 / average)
                             if average > 1.0 else None),
        "recessions": len(counts),
    }


def readings(runs, beta):
    """One row of the sweep: per-seed medians, plus the two pooled facts."""
    group = [run for run in runs if run["beta"] == beta]
    row = {key: _median([run[key] for run in group])
           for key in ("firm_alpha", "firm_x_min", "growth_kurtosis",
                       "income_alpha", "profit_skew", "demises", "wage_share",
                       "unemployment", "firms", "largest")}
    row.update(pooled_readings(group))
    row["seeds"] = len(group)
    row["condensed"] = sum(1 for run in group if run["largest"] > 500)
    row["worst_money_error"] = max(abs(run["coins"] - 100_000.0) for run in group)
    return row


def holds(row, fact):
    """Whether one of the seven facts is inside its pre-registered band."""
    value = row.get(fact)
    if value is None:
        return False
    low, high = BANDS[fact]
    return (low is None or value >= low) and (high is None or value <= high)


def satisfied(row):
    """Which of the seven hold at this beta."""
    return {fact for fact in BANDS if holds(row, fact)}


def all_seven_region(rows):
    """The betas where all seven hold, and the width of that set.

    Width is the span of the *contiguous* run containing the widest
    stretch, not the span of the whole set: two isolated betas either
    side of a gap are not a basin.
    """
    good = sorted(beta for beta, row in rows.items() if len(satisfied(row)) == 7)
    if not good:
        return {"betas": [], "width": 0.0, "contiguous": []}
    order = sorted(rows)
    runs, current = [], [good[0]]
    for previous, beta in zip(good, good[1:]):
        if order.index(beta) == order.index(previous) + 1:
            current.append(beta)
        else:
            runs.append(current)
            current = [beta]
    runs.append(current)
    widest = max(runs, key=lambda run: run[-1] - run[0])
    return {"betas": good, "width": widest[-1] - widest[0], "contiguous": widest}


def main(argv):
    path = argv[1]
    seeds = int(argv[2]) if len(argv) > 2 else 50
    runs = sweep(seeds=seeds)
    with open(path, "w") as handle:
        json.dump(runs, handle)
    print("runs:", len(runs), "betas:", len(BETAS))


if __name__ == "__main__":
    main(sys.argv)
