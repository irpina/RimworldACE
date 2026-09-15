"""The ablation grid (docs/109): cross every gated rule with every other.

The laboratory carries ten independently gated behavioural rules, each
off by default and bit-identical when off, so that each can be
attributed.  That discipline has been used deliberately once --
`docs/105` crossing the producer quantum with sales-follow-production --
and it found the two are only *jointly* effective.  This runs the whole
lattice, 2**10 cells, and reports where a rule changes what another rule
does.

Reads only.  It adds no rule and changes no default; `python -m
economy_lab.baseline` is unaffected by its existence.
"""

from __future__ import annotations

import json
import sys
from dataclasses import replace
from itertools import combinations
from typing import Dict, List, Sequence, Tuple

from .model import Economy
from .scenarios import ScenarioParameters, YAYO, seeded_two_region_economy

#: The ten gated rules, with the value each takes when switched on.
#: Order is fixed: it indexes the bitmask that names a cell.
FACTORS: Tuple[Tuple[str, object], ...] = (
    ("producer_cash", True),
    ("posted_prices", True),
    ("procurement", True),
    ("entry_on_margin", True),
    ("exit_on_return", True),
    ("producer_employment_quantum", 1e-3),
    ("sales_follow_production", True),
    ("worker_mobility_strength", 0.05),
    ("wage_bargaining_strength", 1.0),
    ("habituation_speed", 0.02),
)

NAMES: Tuple[str, ...] = tuple(name for name, _ in FACTORS)

SEED_DAYS = 60
BOOM_DAYS = 1140


def cell_parameters(mask: int) -> ScenarioParameters:
    """The scenario parameters for one cell of the grid.

    ``mask`` bit *i* set means ``FACTORS[i]`` is switched on.  Capital
    goods are held on in every cell so Department I exists and
    `docs/105`'s machinists are present to be killed.
    """
    parameters = replace(ScenarioParameters(), capital_goods=True)
    changes = {
        name: value
        for index, (name, value) in enumerate(FACTORS)
        if mask >> index & 1
    }
    return replace(parameters, **changes)


def run_cell(mask: int) -> Economy:
    """Seed, shock and run one cell.  The shock is `demand_boom`'s."""
    parameters = cell_parameters(mask)
    economy = seeded_two_region_economy(
        route_capacity_per_day=parameters.standard_route_capacity_per_day,
        freight_per_unit=parameters.standard_freight_per_unit,
        travel_days=parameters.standard_travel_days,
        parameters=parameters,
    )
    economy.step(SEED_DAYS)
    economy.regions["Dust Basin"].base_daily_demand[YAYO] *= (
        parameters.boom_demand_multiplier
    )
    economy.step(BOOM_DAYS)
    return economy


def measure(economy: Economy) -> Dict[str, float]:
    """Fourteen readings spanning the ledgers (docs/109 section 3)."""
    ledger = economy.ledger
    dust = economy.regions["Dust Basin"]
    necessary = sum(ledger.necessary_labor.values())
    living = sum(ledger.living_labor.values())
    deviation = sum(ledger.wage_deviation_labor.values())
    surplus = economy.rate_of_surplus_value("Dust Basin")
    return {
        "employment": sum(
            region.worker_days_earned for region in economy.regions.values()
        ),
        "bankruptcies": float(len(ledger.bankruptcies)),
        "exits": float(len(ledger.exits)),
        "capacity_lost": sum(ledger.capacity_lost.values()),
        "yayo_price": dust.prices["yayo"],
        "meals_price": dust.prices["meals"],
        "wage_share": (necessary + deviation) / living if living else 0.0,
        "wage_premium": dust.wage_premium,
        "production": sum(ledger.production.values()),
        "cash_residual": economy.cash_balance(),
        "fund_wage_support": sum(ledger.fund_wage_support.values()),
        "labor_migrated": ledger.labor_migrated.get("Dust Basin", 0.0),
        "liquidity_curtailment": sum(ledger.liquidity_curtailment.values()),
        "rate_of_surplus_value": surplus if surplus is not None else 0.0,
    }


METRICS: Tuple[str, ...] = (
    "employment",
    "bankruptcies",
    "exits",
    "capacity_lost",
    "yayo_price",
    "meals_price",
    "wage_share",
    "wage_premium",
    "production",
    "cash_residual",
    "fund_wage_support",
    "labor_migrated",
    "liquidity_curtailment",
    "rate_of_surplus_value",
)


def run_and_measure(mask: int) -> Dict[str, object]:
    """One cell, as a record.  A cell that throws is itself a finding."""
    record: Dict[str, object] = {"mask": mask}
    try:
        record["metrics"] = measure(run_cell(mask))
    except Exception as error:
        record["error"] = f"{type(error).__name__}: {error}"
    return record


def sweep(progress=None, processes: int | None = None) -> List[Dict[str, object]]:
    """Run all 2**len(FACTORS) cells.  Returns one record per cell.

    Cells are independent and each is deterministic in its own
    parameters, so they are run in a process pool: the results do not
    depend on the order they finish in, and the records are sorted back
    into mask order before returning.  Serial and parallel sweeps give
    the same file.
    """
    cells = 1 << len(FACTORS)
    masks = list(range(cells))
    if processes == 1:
        records = []
        for done, mask in enumerate(masks, start=1):
            records.append(run_and_measure(mask))
            if progress is not None and done % 32 == 0:
                progress(done, cells)
        return records

    from multiprocessing import Pool

    records = []
    with Pool(processes=processes) as pool:
        for done, record in enumerate(
            pool.imap_unordered(run_and_measure, masks), start=1
        ):
            records.append(record)
            if progress is not None and done % 32 == 0:
                progress(done, cells)
    records.sort(key=lambda record: record["mask"])
    return records


# --- the arithmetic (docs/109 section 3) ---------------------------------


def _values(records, metric: str) -> Dict[int, float]:
    return {
        record["mask"]: record["metrics"][metric]
        for record in records
        if "metrics" in record
    }


def spread(records, metric: str) -> float:
    values = list(_values(records, metric).values())
    return (max(values) - min(values)) if values else 0.0


def main_effect(records, metric: str, factor: int) -> float:
    """Mean change in the metric from switching one factor on."""
    values = _values(records, metric)
    bit = 1 << factor
    deltas = [
        values[mask | bit] - values[mask]
        for mask in values
        if not mask & bit and (mask | bit) in values
    ]
    return sum(deltas) / len(deltas) if deltas else 0.0


def interaction(records, metric: str, factors: Sequence[int]) -> float:
    """The n-way interaction: the nth difference, averaged over the rest.

    Zero means the factors are additive -- each does the same thing
    whether or not the others are on.  The sign convention is the
    standard one: the alternating sum over the subsets of `factors`.
    """
    values = _values(records, metric)
    bits = [1 << factor for factor in factors]
    combined = 0
    for bit in bits:
        combined |= bit
    total, count = 0.0, 0
    for mask in values:
        if mask & combined:
            continue  # iterate over the cells with all of them off
        accumulated, complete = 0.0, True
        for size in range(len(bits) + 1):
            for chosen in combinations(range(len(bits)), size):
                target = mask
                for index in chosen:
                    target |= bits[index]
                if target not in values:
                    complete = False
                    break
                sign = -1.0 if (len(bits) - size) % 2 else 1.0
                accumulated += sign * values[target]
            if not complete:
                break
        if complete:
            total += accumulated
            count += 1
    return total / count if count else 0.0


def additive_fraction(records, metric: str) -> float:
    """Share of the metric's variance an additive main-effect model explains."""
    values = _values(records, metric)
    if not values:
        return 0.0
    mean = sum(values.values()) / len(values)
    total = sum((value - mean) ** 2 for value in values.values())
    if total <= 0.0:
        return 1.0
    effects = [main_effect(records, metric, i) for i in range(len(FACTORS))]
    residual = 0.0
    for mask, value in values.items():
        predicted = mean
        for index, effect in enumerate(effects):
            # centred: on contributes +half an effect, off minus half
            predicted += effect * (0.5 if mask >> index & 1 else -0.5)
        residual += (value - predicted) ** 2
    return 1.0 - residual / total


def main(argv: Sequence[str] | None = None) -> int:
    argv = list(argv if argv is not None else sys.argv[1:])
    destination = argv[0] if argv else "grid_results.json"
    processes = int(argv[1]) if len(argv) > 1 else None

    def progress(done: int, total: int) -> None:
        print(f"  {done}/{total} cells", flush=True)

    print(f"running {1 << len(FACTORS)} cells", flush=True)
    records = sweep(progress=progress, processes=processes)
    with open(destination, "w") as handle:
        json.dump({"factors": list(NAMES), "cells": records}, handle)
    failures = [r for r in records if "error" in r]
    print(f"done: {len(records)} cells, {len(failures)} failed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
