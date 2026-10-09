"""docs/145: the docking battery at another size, written after every run.

    python3.12 -m economy_lab.redock out.json [seeds] [commodities]

The ``docs/138`` instrument (``wright_battery.measure_ours`` with
``DOCKED``, and ``measure_sa`` as the control), with the commodity count
as the one change.  Rows have ``wright_battery.main``'s layout; a run the
model refuses is a row with ``error`` set.  Written after every run, so
a run that is stopped keeps what it had.
"""
from __future__ import annotations

import json
import sys
from multiprocessing import Pool

from . import wright_battery as wb


def _job(job):
    which, seed, commodities = job
    if which == "sa":
        run = wb.measure_sa(seed)
    else:
        run = wb.measure_ours(seed, commodities=commodities, **wb.DOCKED)
    if "error" in run:
        return {"model": which, "seed": seed, "error": run["error"], "day": run.get("day")}
    return dict(wb.facts(run), model=run["model"], seed=run["seed"],
                **{key: run.get(key) for key in wb.STRUCTURAL})


def main(argv):
    out = argv[1]
    seeds = int(argv[2]) if len(argv) > 2 else 20
    commodities = int(argv[3]) if len(argv) > 3 else 647
    # Ours first: they are the long ones.
    jobs = [("ours", seed, commodities) for seed in range(seeds)]
    jobs += [("sa", seed, commodities) for seed in range(seeds)]
    rows = []
    with Pool(4) as pool:
        for row in pool.imap_unordered(_job, jobs, chunksize=1):
            rows.append(row)
            rows.sort(key=lambda r: (r["model"], r["seed"]))
            with open(out, "w") as handle:
                json.dump(rows, handle)
            print(f"{len(rows)}/{len(jobs)}: {row['model']} seed {row['seed']}"
                  + (f" REFUSED: {row['error']}" if "error" in row else ""), flush=True)


if __name__ == "__main__":
    main(sys.argv)
