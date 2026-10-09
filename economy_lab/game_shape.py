"""docs/141 slice 0: the docked configuration at the game's shape.

The docking (docs/136-139) measured two regions, 200 commodities and
thirty-six months. The game has six to ten faction regions, may carry the
whole 647-commodity population, and runs past thirty-six months. This
records the docked economy month by month at those shapes, so that
docs/141's predictions 1-6 can be scored before any of it is ported.

    python -m economy_lab.game_shape out.json [seeds] [days]
"""
from __future__ import annotations

import json
import sys
import time
from multiprocessing import Pool

from .wright_battery import DOCKED, MONTH, build_ours, employment, money_totals

#: (regions, commodities): the battery's shape, then the game's.
SHAPES = ((2, 200), (6, 200), (10, 200), (6, 647))
DAYS = 1800


def at_bounds(economy) -> float:
    """Share of commodity-region prices sitting at their floor or ceiling."""
    pinned = total = 0
    for region in economy.regions.values():
        for name, price in region.prices.items():
            good = economy.commodities[name]
            low = good.reference_price * good.minimum_price_factor
            high = good.reference_price * good.maximum_price_factor
            total += 1
            if price <= low * (1 + 1e-12) or price >= high * (1 - 1e-12):
                pinned += 1
    return pinned / max(total, 1)


def trajectory(job):
    """One docked economy at one shape, one row a month."""
    seed, regions, commodities, days = job
    record = {"seed": seed, "regions": regions, "commodities": commodities,
              "months": []}
    try:
        economy = build_ours(seed, regions=regions, commodities=commodities,
                             **DOCKED)
    except RuntimeError as failure:
        record["error"] = str(failure)
        return record
    record["producers"] = sum(len(r.producers) for r in economy.regions.values())
    money_stock = economy.ledger.initial_cash
    last = money_totals(economy)
    started = time.perf_counter()
    for _ in range(days // MONTH):
        try:
            economy.step(MONTH)
        except RuntimeError as failure:
            record["error"] = str(failure)
            record["error_day"] = economy.day
            break
        now = money_totals(economy)
        wages, receipts, purchases, construction = (b - a for a, b in zip(last, now))
        last = now
        employing = employment(economy)
        record["months"].append({
            "day": economy.day,
            "employing": len(employing),
            "workers": sum(employing.values()),
            "value_added_per_day": (receipts - purchases) / MONTH,
            "wages_per_day": wages / MONTH,
            "construction_per_day": construction / MONTH,
            "cash_balance": economy.cash_balance() / money_stock,
            "fund_share": sum(r.cash for r in economy.regions.values()) / money_stock,
            "at_bounds": at_bounds(economy),
            "bankruptcies": len(economy.ledger.bankruptcies),
        })
    record["seconds"] = time.perf_counter() - started
    record["days_run"] = economy.day
    return record


def main(argv):
    out = argv[1]
    seeds = int(argv[2]) if len(argv) > 2 else 3
    days = int(argv[3]) if len(argv) > 3 else DAYS
    # Largest first, so the pool is not left waiting on one long job.
    jobs = sorted(((seed, r, c, days) for r, c in SHAPES for seed in range(seeds)),
                  key=lambda job: -job[1] * job[2])
    records = []
    with Pool(4) as pool:
        # Written after every run, so a run that is stopped keeps what it had.
        for record in pool.imap_unordered(trajectory, jobs, chunksize=1):
            records.append(record)
            records.sort(key=lambda r: (r["regions"], r["commodities"], r["seed"]))
            with open(out, "w") as handle:
                json.dump(records, handle)
            print(f"{len(records)}/{len(jobs)}: seed {record['seed']}, "
                  f"{record['regions']} regions, {record['commodities']} commodities, "
                  f"{record.get('seconds', 0.0):.0f} s{', ' + record['error'] if 'error' in record else ''}",
                  flush=True)


if __name__ == "__main__":
    main(sys.argv)
