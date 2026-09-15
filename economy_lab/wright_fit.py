"""Gather Wright's seven measures across seeds (docs/111, docs/112).

Runs the SR model with a burn-in discarded and then records his own
window -- "data collected over 15 simulated years" -- writing one record
per seed as JSON for the fitting in `economy_lab.distributions`.

    python -m economy_lab.wright_fit fits.json 100
"""
import json, sys
from multiprocessing import Pool
from economy_lab import social_architecture as sa

BURN_IN = 120      # 10 years, discarded
WINDOW = 180       # 15 simulated years, Wright's own pooling window

def one(seed):
    e = sa.Economy(seed=seed)
    e.run(BURN_IN)
    e.start_recording()
    e.run(WINDOW)
    h = e.history
    return {
        "seed": seed,
        "firm_sizes": h.firm_sizes,
        "demises": h.demises_per_month,
        "gdp": h.gdp,
        "firm_growth": h.firm_growth,
        "incomes": h.incomes,
        "profit_rates": h.profit_rates,
        "wage_shares": h.wage_shares,
        "unemployment": e.unemployment_rate(),
        "coins": e.total_coins(),
    }

if __name__ == "__main__":
    seeds = list(range(int(sys.argv[2]) if len(sys.argv) > 2 else 100))
    with Pool(4) as pool:
        out = pool.map(one, seeds)
    json.dump(out, open(sys.argv[1], "w"))
    print("seeds:", len(out))
