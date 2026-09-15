"""The 2x2 ablation of Wright's market rule M1.

Design in ``docs/115``, results in ``docs/116``.

    python -m economy_lab.m1_ablation out.json 50

Each cell is one setting of ``social_architecture.Economy.market_rule``.
Runs a burn-in, starts recording, then runs the measurement window.
"""

import json
import statistics as st
import sys
from multiprocessing import Pool

from economy_lab import distributions as D
from economy_lab import social_architecture as sa

BURN_IN = 120
WINDOW = 180

LABEL = {
    "wright": "wright (L+R)",
    "neutral": "neutral (R only)",
    "fixed": "fixed (L only)",
    "fixed_neutral": "fixed_neutral (-)",
}


def run_cell(job):
    """Run one (rule, seed) and return its recorded history as plain data."""
    rule, seed = job
    economy = sa.Economy(seed=seed, market_rule=rule)
    economy.run(BURN_IN)
    economy.start_recording()
    economy.run(WINDOW)
    history = economy.history
    return {
        "rule": rule,
        "seed": seed,
        "firm_sizes": history.firm_sizes,
        "demises": history.demises_per_month,
        "gdp": history.gdp,
        "firm_growth": history.firm_growth,
        "incomes": history.incomes,
        "profit_rates": history.profit_rates,
        "wage_shares": history.wage_shares,
        "unemployment": economy.unemployment_rate(),
        "firms": len(economy.firm_sizes()),
        "largest": max(economy.firm_sizes() or [0]),
        "coins": economy.total_coins(),
    }


def sweep(seeds=50, processes=4):
    """Every rule against every seed, returned in (rule, seed) order."""
    jobs = [(rule, seed) for rule in sa.MARKET_RULES for seed in range(seeds)]
    with Pool(processes) as pool:
        return pool.map(run_cell, jobs)


def pooled(runs, rule):
    """The distributional readings for one cell, fitted on the pooled seeds."""
    group = [run for run in runs if run["rule"] == rule]
    sizes, growth, shares, demises, incomes, profits = [], [], [], [], [], []
    gdp_growth, recessions = [], []
    for run in group:
        sizes.extend(run["firm_sizes"])
        growth.extend(run["firm_growth"])
        shares.extend(run["wage_shares"])
        demises.extend(run["demises"])
        incomes.extend(value for value in run["incomes"] if value > 0)
        profits.extend(run["profit_rates"])
        history = sa.History(gdp=run["gdp"])
        gdp_growth.extend(history.gdp_growth())
        recessions.extend(history.recessions())
    fit = D.power_law_fit(sizes, discrete=True, min_tail=200) or {}
    income_fit = D.power_law_fit(incomes, min_tail=500) or {}
    geometric = D.geometric_goodness_of_fit(recessions, synthetics=200, seed=1) or {}
    return {
        "largest": st.mean(run["largest"] for run in group),
        "firms": st.mean(run["firms"] for run in group),
        "unemployment": st.mean(run["unemployment"] for run in group),
        "alpha": fit.get("alpha_wright"),
        "x_min": fit.get("x_min"),
        "demises": st.mean(demises),
        "growth_kurtosis": D.excess_kurtosis(growth),
        "gdp_kurtosis": D.excess_kurtosis(gdp_growth) if len(gdp_growth) > 3 else None,
        "wage_share": st.mean(shares) if shares else None,
        "profit_skew": D.skewness(profits) if len(profits) > 3 else None,
        "recession_lambda": geometric.get("lambda"),
        "income_alpha": income_fit.get("alpha_wright"),
    }


def per_seed(runs, rule, metric):
    """One reading per seed, for the across-seed spread the pooled fits hide."""
    readings = {
        "largest": lambda run: float(run["largest"]),
        "firms": lambda run: float(run["firms"]),
        "unemployment": lambda run: run["unemployment"],
        "demises": lambda run: st.mean(run["demises"]),
        "wage_share": lambda run: st.mean(run["wage_shares"]),
        "growth_kurtosis": lambda run: D.excess_kurtosis(run["firm_growth"]),
    }
    return [readings[metric](run) for run in runs if run["rule"] == rule]


def decompose(cell_means):
    """Main effects and the interaction of M1's two ingredients.

    ``L`` is the size-proportional draw, on in ``wright`` and ``fixed``.
    ``R`` is the random draw, on in ``wright`` and ``neutral``.
    """
    wright = cell_means["wright"]
    neutral = cell_means["neutral"]
    fixed = cell_means["fixed"]
    neither = cell_means["fixed_neutral"]
    spread = max(cell_means.values()) - min(cell_means.values())
    interaction = (wright - neutral - fixed + neither) / 2
    return {
        "main_l": ((wright - neutral) + (fixed - neither)) / 2,
        "main_r": ((wright - fixed) + (neutral - neither)) / 2,
        "interaction": interaction,
        "interaction_fraction": abs(interaction) / spread if spread else 0.0,
    }


def main(argv):
    path = argv[1]
    seeds = int(argv[2]) if len(argv) > 2 else 50
    runs = sweep(seeds)
    with open(path, "w") as handle:
        json.dump(runs, handle)
    print("runs:", len(runs))


if __name__ == "__main__":
    main(sys.argv)
