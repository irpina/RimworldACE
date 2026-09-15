"""The three parameter sweeps of ``docs/134``.

    python -m economy_lab.parameter_sweeps out.json [A|B|C|all]

Each cell is :func:`wright_battery.measure_ours` with knobs, scored by
:func:`wright_battery.facts`; a run the model refuses is kept as its
error.  Results in ``docs/135``.
"""

import json
import sys
from multiprocessing import Pool

from economy_lab import wright_battery as wb

BASE = dict(demand=800.0, producers_per_commodity=4, fund_spending=True, accumulate=True)

CELLS = {
    "A": [dict(cash_multiplier=m) for m in (10.0, 3.0, 1.0, 0.3, 0.1)],
    "B": [dict(cost_spread=c) for c in (0.1, 0.3, 0.6, 1.0)],
    "C": [dict(retention_rate=r, construction_cost_multiplier=u)
          for r in (0.5, 0.2, 0.05) for u in (60.0, 20.0)],
}
SEEDS = {"A": 1, "B": 5, "C": 3}


def _job(job):
    sweep, cell, seed = job
    run = wb.measure_ours(seed, **dict(BASE, **cell))
    row = {"sweep": sweep, "seed": seed, **cell}
    if "error" in run:
        row.update(error=run["error"], day=run["day"])
        return row
    row.update(wb.facts(run))
    row.update({key: run.get(key) for key in wb.STRUCTURAL})
    return row


def main(argv):
    which = argv[2] if len(argv) > 2 else "all"
    sweeps = list(CELLS) if which == "all" else [which]
    jobs = [(sweep, cell, seed) for sweep in sweeps
            for cell in CELLS[sweep] for seed in range(SEEDS[sweep])]
    with Pool(4) as pool:
        rows = pool.map(_job, jobs)
    with open(argv[1], "w") as handle:
        json.dump(rows, handle)
    print("rows:", len(rows))


if __name__ == "__main__":
    main(sys.argv)
